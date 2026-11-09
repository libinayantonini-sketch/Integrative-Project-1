"""API do Monitoramento de Vias Públicas de Londrina.

Liga as três partes do projeto:
  front (pasta frontend/)  <->  esta API  <->  MySQL (projeto_sinalizacoes)
                                   |
                                   +-> modelo YOLO26 (backend/modelos/detector_v1.pt)

Execução (na raiz do repositório, com o venv ativado):
    python backend/api/api.py
Depois abra http://127.0.0.1:8000 no navegador (a API também entrega o front).

Todas as rotas de dados ficam em /api/... e respondem JSON (exceto vídeos e imagens).
O contrato completo está em docs/contrato_api.md.
"""
import datetime as dt
import logging
import re
import shutil
import sys
import uuid
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))   # permite importar config, db e visao

import cv2
import numpy as np
from flask import Blueprint, Flask, abort, jsonify, request, send_file, send_from_directory
from flask_cors import CORS
from werkzeug.exceptions import HTTPException
from werkzeug.utils import secure_filename

import config
from db import repositorio as repo
from visao.detector import DetectorPlacas, desenhar
from visao.fila import FilaProcessamento
from visao.video import ler_info

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("api")

# Nomes usados pelo banco -> nomes usados pelo front
STATUS_FRONT = {"aguardando": "na_fila", "processando": "processando", "concluido": "concluida", "erro": "falhou"}
ACOES = {"confirmar": "confirmada", "rejeitar": "rejeitada", "corrigir": "corrigida"}

app = Flask(__name__, static_folder=None)
app.config["MAX_CONTENT_LENGTH"] = (config.TAM_MAX_MB + 5) * 1024 * 1024
app.json.ensure_ascii = False
CORS(app)   # permite usar o front também pelo Live Server (outra porta)
api = Blueprint("api", __name__, url_prefix="/api")

detector = None   # carregados em iniciar()
fila = None


# ---------------------------------------------------------------- utilidades

def erro(mensagem, codigo=400):
    return jsonify(error=mensagem), codigo


def _num(v):
    return float(v) if isinstance(v, Decimal) else v


def _data(v):
    return v.isoformat() if isinstance(v, (dt.date, dt.datetime)) else None


def _hora(v):
    if isinstance(v, dt.timedelta):          # o PyMySQL devolve TIME como timedelta
        s = int(v.total_seconds())
        return f"{s // 3600:02d}:{s % 3600 // 60:02d}"
    if isinstance(v, dt.time):
        return v.strftime("%H:%M")
    return None


def nome_classe(c):
    return str(c or "").replace("_", " ").strip().capitalize()


def url_video(id_proc, versao):
    return f"/api/analises/{id_proc}/video?versao={versao}"


def url_imagem(id_proc, numero, versao):
    return f"/api/analises/{id_proc}/frames/{numero}/imagem?versao={versao}"


def analise_json(a):
    status = STATUS_FRONT.get(a["status"], a["status"])
    pronto = status == "concluida" and a["caminho_video_anotado"]
    return {
        "id": a["id_processamento"],
        "video": a["nome_arquivo"],
        "local": a["local_gravacao"],
        "data": _data(a["data_gravacao"]),
        "horario": _hora(a["horario_gravacao"]),
        "observacoes": a["observacoes"],
        "duracao": _num(a["duracao_segundos"]),
        "fps": _num(a["fps"]),
        "largura": a["largura"],
        "altura": a["altura"],
        "status": status,
        "progresso": _num(a["progresso"]),
        "erro": a["mensagem_erro"],
        "deteccoes": a["total_deteccoes"] or 0,
        "framesComPlaca": a["frames_com_placa"] or 0,
        "framesGuardados": a["frames_guardados"] or 0,
        "intervaloFrames": _num(a["intervalo_extracao_segundos"]),
        "modelo": a["nome_modelo"],
        "versaoModelo": a["versao_modelo"],
        "limiarConfianca": _num(a["limiar_confianca"]),
        "enviadoEm": _data(a["criado_em"]),
        "concluidoEm": _data(a["finalizado_em"]),
        "videoUrl": url_video(a["id_processamento"], "anotado") if pronto else None,
        "videoOriginalUrl": url_video(a["id_processamento"], "original") if status == "concluida" else None,
    }


def deteccao_json(d):
    w, h = d["largura"] or 1, d["altura"] or 1
    return {
        "id": d["id_deteccao"],
        "frame": d["numero_frame"],
        "tempo": _num(d["tempo_segundos"]),
        "classe": nome_classe(d["classe_prevista"]),
        "confianca": _num(d["confianca"]),
        "revisao": d["revisao"],
        "classeCorrigida": d["classe_corrigida"],
        "obs": d["comentario"],
        "bbox": {"x_min": d["x_min"], "y_min": d["y_min"], "x_max": d["x_max"], "y_max": d["y_max"]},
        "caixa": {"x": d["x_min"] / w, "y": d["y_min"] / h,
                  "l": (d["x_max"] - d["x_min"]) / w, "a": (d["y_max"] - d["y_min"]) / h},
    }


def obter_analise_ou_404(id_proc):
    a = repo.obter_analise(id_proc)
    if a is None:
        abort(404, description="Análise não encontrada.")
    return a


# ---------------------------------------------------------------- rotas: análises

@api.post("/analises")
def enviar_video():
    """Recebe o vídeo + dados da gravação, cadastra no banco e coloca na fila do modelo."""
    arquivo = request.files.get("video")
    if not arquivo or not arquivo.filename:
        return erro("Envie o vídeo no campo 'video'.")
    extensao = Path(secure_filename(arquivo.filename)).suffix.lower()
    if extensao not in config.FORMATOS_VIDEO:
        return erro("Formato não aceito. Use MP4, MOV ou WebM.")

    local = (request.form.get("local") or "").strip()
    if not local:
        return erro("Informe o local da gravação.")
    if len(local) > 150:
        return erro("O local deve ter no máximo 150 caracteres.")
    data = (request.form.get("data") or "").strip() or None
    horario = (request.form.get("horario") or "").strip() or None
    observacoes = (request.form.get("observacoes") or "").strip()[:2000] or None
    try:
        if data:
            dt.date.fromisoformat(data)
        if horario and not re.fullmatch(r"\d{2}:\d{2}(:\d{2})?", horario):
            raise ValueError
    except ValueError:
        return erro("Data (AAAA-MM-DD) ou horário (HH:MM) inválido.")

    pasta = config.STORAGE_DIR / "videos" / uuid.uuid4().hex
    pasta.mkdir(parents=True)
    enviado = pasta / f"envio{extensao}"
    try:
        arquivo.save(enviado)
        info = ler_info(enviado)
        if not config.VIDEO_MIN_S <= info["duracao"] <= config.VIDEO_MAX_S:
            raise ValueError(f"A duração ({info['duracao']:.0f}s) deve estar entre "
                             f"{config.VIDEO_MIN_S:.0f}s e {config.VIDEO_MAX_S:.0f}s.")
        id_proc = repo.criar_analise(
            nome_arquivo=arquivo.filename[:255], caminho_arquivo=enviado.relative_to(config.STORAGE_DIR).as_posix(),
            info=info, local=local, data=data, horario=horario, observacoes=observacoes,
            nome_modelo=detector.nome, versao_modelo=detector.versao,
            intervalo=config.INTERVALO_EXTRACAO_S, limiar=detector.conf)
    except ValueError as e:
        shutil.rmtree(pasta, ignore_errors=True)
        return erro(str(e))
    except Exception:
        shutil.rmtree(pasta, ignore_errors=True)
        raise
    fila.adicionar(id_proc)
    log.info("Análise %s recebida (%s, %.1fs)", id_proc, arquivo.filename, info["duracao"])
    return jsonify(id=id_proc, status="na_fila"), 201


@api.get("/analises")
def listar_analises():
    return jsonify([analise_json(a) for a in repo.listar_analises()])


@api.get("/analises/<int:id_proc>")
def obter_analise(id_proc):
    return jsonify(analise_json(obter_analise_ou_404(id_proc)))


@api.get("/analises/<int:id_proc>/status")
def status_processamento(id_proc):
    a = obter_analise_ou_404(id_proc)
    return jsonify(status=STATUS_FRONT.get(a["status"], a["status"]), progresso=_num(a["progresso"]),
                   erro=a["mensagem_erro"])


@api.get("/analises/<int:id_proc>/deteccoes")
def listar_deteccoes(id_proc):
    obter_analise_ou_404(id_proc)
    return jsonify([deteccao_json(d) for d in repo.listar_deteccoes(id_proc)])


@api.post("/analises/<int:id_proc>/deteccoes/<int:id_det>/<acao>")
def revisar_deteccao(id_proc, id_det, acao):
    if acao not in ACOES:
        return erro("Ação inválida. Use confirmar, rejeitar ou corrigir.", 404)
    if repo.obter_deteccao(id_proc, id_det) is None:
        return erro("Detecção não encontrada.", 404)
    corpo = request.get_json(silent=True) or {}
    classe = (corpo.get("classe") or "").strip()[:100] or None
    obs = (corpo.get("obs") or "").strip()[:2000] or None
    if acao == "corrigir" and not classe:
        return erro("Informe a classe correta.")
    repo.revisar(id_det, ACOES[acao], classe if acao == "corrigir" else None, obs)
    return jsonify(deteccao_json(repo.obter_deteccao(id_proc, id_det)))


@api.get("/analises/<int:id_proc>/ocorrencias")
def listar_ocorrencias(id_proc):
    obter_analise_ou_404(id_proc)
    return jsonify([])   # o modelo atual detecta só placas; ocorrências (buracos etc.) ficam para o futuro


# ---------------------------------------------------------------- rotas: vídeos e frames

@api.get("/analises/<int:id_proc>/video")
def baixar_video(id_proc):
    """?versao=anotado (padrão) ou original; &download=1 para baixar como arquivo."""
    a = obter_analise_ou_404(id_proc)
    versao = request.args.get("versao", "anotado")
    relativo = a["caminho_video_anotado"] if versao == "anotado" else a["caminho_arquivo"]
    if versao not in ("anotado", "original") or STATUS_FRONT.get(a["status"]) != "concluida" or not relativo:
        return erro("Vídeo ainda não disponível.", 409 if versao in ("anotado", "original") else 400)
    caminho = (config.STORAGE_DIR / relativo).resolve()
    if config.STORAGE_DIR.resolve() not in caminho.parents or not caminho.is_file():
        return erro("Arquivo de vídeo não encontrado.", 404)
    return send_file(caminho, mimetype="video/mp4", conditional=True,
                     as_attachment=request.args.get("download") == "1",
                     download_name=f"analise_{id_proc}_{versao}.mp4")


@api.get("/analises/<int:id_proc>/frames")
def listar_frames(id_proc):
    obter_analise_ou_404(id_proc)
    return jsonify([{
        "numero": f["numero_frame"], "tempo": _num(f["tempo_segundos"]), "qtdPlacas": f["qtd_placas"],
        "originalUrl": url_imagem(id_proc, f["numero_frame"], "original"),
        "anotadoUrl": url_imagem(id_proc, f["numero_frame"], "anotado"),
    } for f in repo.listar_frames(id_proc)])


@api.get("/analises/<int:id_proc>/frames/<int:numero>")
def obter_frame(id_proc, numero):
    obter_analise_ou_404(id_proc)
    f = repo.obter_frame(id_proc, numero)
    if f is None:
        return erro("Este frame não foi guardado. Consulte a lista em /frames.", 404)
    return jsonify(numero=numero, tempo=_num(f["tempo_segundos"]),
                   originalUrl=url_imagem(id_proc, numero, "original"),
                   anotadoUrl=url_imagem(id_proc, numero, "anotado"),
                   deteccoes=[deteccao_json(d) for d in repo.listar_deteccoes(id_proc, numero)])


@api.get("/analises/<int:id_proc>/frames/<int:numero>/imagem")
def imagem_frame(id_proc, numero):
    """?versao=original (padrão) ou anotado; &largura=N para miniatura."""
    f = repo.obter_frame(id_proc, numero, com_imagem=True)
    if f is None:
        return erro("Frame não encontrado.", 404)
    versao = request.args.get("versao", "original")
    largura = request.args.get("largura", type=int)
    dados, tipo = f["imagem"], f["tipo_imagem"] or "image/jpeg"
    if versao == "anotado" or largura:
        img = cv2.imdecode(np.frombuffer(dados, np.uint8), cv2.IMREAD_COLOR)
        if img is None:
            return erro("Imagem do frame corrompida.", 500)
        if versao == "anotado":   # as caixas vêm do banco (tabela deteccoes)
            caixas = [{"classe": d["classe_prevista"], "confianca": float(d["confianca"]),
                       "x_min": d["x_min"], "y_min": d["y_min"], "x_max": d["x_max"], "y_max": d["y_max"]}
                      for d in repo.listar_deteccoes(id_proc, numero)]
            desenhar(img, caixas)
        if largura and 32 <= largura < img.shape[1]:
            img = cv2.resize(img, (largura, round(img.shape[0] * largura / img.shape[1])), interpolation=cv2.INTER_AREA)
        dados, tipo = cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, 88])[1].tobytes(), "image/jpeg"
    resp = app.response_class(dados, mimetype=tipo)
    resp.headers["Cache-Control"] = "no-cache"   # revisões não mudam a imagem, mas reprocessar sim
    return resp


# ---------------------------------------------------------------- rotas: painéis

@api.get("/dashboard")
def dashboard():
    dias = request.args.get("dias", 7, type=int)
    dias = dias if dias in (7, 30, 90) else 7
    totais, por_dia, distribuicao = repo.dashboard(dias)
    hoje = dt.date.today()
    contagem = {r["dia"]: int(r["total"]) for r in por_dia}
    tamanho = 1 if dias == 7 else 7 if dias == 30 else 15       # barras: dia, semana ou quinzena
    serie = []   # da mais antiga para a mais recente; a última barra termina hoje
    for inicio in range(0, dias, tamanho):          # inicio/fim em "dias atrás"
        datas = [hoje - dt.timedelta(days=d) for d in range(inicio, min(inicio + tamanho, dias))]
        serie.insert(0, {"rotulo": min(datas).strftime("%d/%m"), "valor": sum(contagem.get(d, 0) for d in datas)})
    return jsonify(
        totais={"analises": totais["analises"], "deteccoes": int(totais["deteccoes"]),
                "framesComPlaca": int(totais["frames_com_placa"]), "pendentes": int(totais["pendentes"] or 0)},
        serie=serie,
        distribuicao=[{"classe": nome_classe(d["classe"]), "total": d["total"]} for d in distribuicao],
        recentes=[analise_json(a) for a in repo.listar_analises(limite=5)])


@api.get("/relatorios")
def relatorios():
    analises, por_classe, revisao = repo.relatorio(request.args.get("de"), request.args.get("ate"),
                                                   (request.args.get("local") or "").strip())
    contagem = {r["status"]: r["total"] for r in revisao}
    return jsonify(analises=analises,
                   porClasse=[{"classe": nome_classe(c["classe"]), "total": c["total"]} for c in por_classe],
                   revisao={"confirmadas": contagem.get("confirmada", 0), "rejeitadas": contagem.get("rejeitada", 0),
                            "corrigidas": contagem.get("corrigida", 0), "pendentes": contagem.get("pendente", 0)})


@api.get("/saude")
def saude():
    try:
        repo.verificar_conexao()
    except Exception as e:
        return jsonify(ok=False, banco=False, erro=str(e)[:300]), 503
    return jsonify(ok=True, banco=True, modelo=detector.versao, classes=list(detector.classes.values()),
                   intervaloFrames=config.INTERVALO_EXTRACAO_S,
                   video={"minS": config.VIDEO_MIN_S, "maxS": config.VIDEO_MAX_S, "maxMB": config.TAM_MAX_MB})


@api.errorhandler(HTTPException)
def erro_http(e):
    return erro(e.description if e.code in (404, 409) else e.name, e.code)


@api.errorhandler(Exception)
def erro_interno(e):
    if isinstance(e, HTTPException):
        return erro_http(e)
    log.exception("Erro na rota %s", request.path)
    return erro("Erro interno no servidor.", 500)


@app.errorhandler(413)
def arquivo_grande(_):
    return erro(f"O arquivo excede {config.TAM_MAX_MB} MB.", 413)


app.register_blueprint(api)


# ---------------------------------------------------------------- front (pasta frontend/)

@app.get("/")
def front_inicio():
    return send_from_directory(config.FRONTEND_DIR, "index.html")


@app.get("/<path:arquivo>")
def front_arquivos(arquivo):
    if arquivo.startswith("api/"):
        return erro("Rota não encontrada.", 404)
    return send_from_directory(config.FRONTEND_DIR, arquivo)


# ---------------------------------------------------------------- inicialização

def iniciar():
    global detector, fila
    config.STORAGE_DIR.mkdir(parents=True, exist_ok=True)
    try:
        repo.verificar_conexao()
    except Exception as e:
        sys.exit(f"\nNão foi possível conectar ao MySQL ({e.__class__.__name__}).\n"
                 "Confira se o MySQL está ligado e se o DB_URL do backend/.env está correto.\n"
                 "Se o banco ainda não existe, rode: python backend/db/criar_banco.py\n")
    detector = DetectorPlacas(config.MODELO_PESOS, config.DISPOSITIVO)
    log.info("Modelo %s carregado (classes: %s)", detector.versao, list(detector.classes.values()))
    fila = FilaProcessamento(detector)
    for id_proc in repo.processamentos_pendentes():
        log.info("Retomando análise %s que estava na fila", id_proc)
        fila.adicionar(id_proc)


if __name__ == "__main__":
    iniciar()
    print(f"\n  Abra no navegador: http://{config.HOST}:{config.PORTA}\n")
    app.run(host=config.HOST, port=config.PORTA, debug=False, threaded=True)
