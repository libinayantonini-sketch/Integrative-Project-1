"""Todas as consultas ao MySQL ficam aqui. A API e o pipeline só chamam estas funções.

Tabelas (database/migracoes): videos, video_metadados, frames, processamentos, deteccoes, revisoes.
Uma "análise" do front = uma linha de processamentos (+ o vídeo e os metadados dela).
"""
from sqlalchemy import text

from db.conexao import engine


def _linhas(resultado):
    return [dict(r._mapping) for r in resultado]


def _uma(resultado):
    r = resultado.first()
    return dict(r._mapping) if r else None


def verificar_conexao():
    with engine.connect() as c:
        c.execute(text("SELECT 1"))


# ---------------------------------------------------------------- criação e processamento

def criar_analise(*, nome_arquivo, caminho_arquivo, info, local, data, horario, observacoes,
                  nome_modelo, versao_modelo, intervalo, limiar):
    """Cadastra vídeo + metadados + processamento ('aguardando'). Devolve o id_processamento."""
    with engine.begin() as c:
        id_video = c.execute(text(
            "INSERT INTO videos (nome_arquivo, origem, caminho_arquivo, duracao_segundos, fps, largura, altura) "
            "VALUES (:nome, 'upload', :caminho, :dur, :fps, :larg, :alt)"),
            dict(nome=nome_arquivo, caminho=caminho_arquivo, dur=info["duracao"], fps=info["fps"],
                 larg=info["largura"], alt=info["altura"])).lastrowid
        c.execute(text(
            "INSERT INTO video_metadados (id_video, local_gravacao, data_gravacao, horario_gravacao, observacoes) "
            "VALUES (:id, :local, :data, :horario, :obs)"),
            dict(id=id_video, local=local, data=data, horario=horario, obs=observacoes))
        return c.execute(text(
            "INSERT INTO processamentos (id_video, nome_modelo, versao_modelo, intervalo_extracao_segundos, "
            "limiar_confianca, status) VALUES (:id, :modelo, :versao, :intervalo, :limiar, 'aguardando')"),
            dict(id=id_video, modelo=nome_modelo, versao=versao_modelo, intervalo=intervalo,
                 limiar=limiar)).lastrowid


def dados_processamento(id_proc):
    with engine.connect() as c:
        return _uma(c.execute(text(
            "SELECT p.id_processamento, p.id_video, p.intervalo_extracao_segundos, p.status, "
            "       v.caminho_arquivo, v.fps "
            "FROM processamentos p JOIN videos v ON v.id_video = p.id_video "
            "WHERE p.id_processamento = :id"), dict(id=id_proc)))


def iniciar_processamento(id_proc, id_video):
    """Marca como 'processando' e apaga resultados de uma tentativa anterior interrompida."""
    with engine.begin() as c:
        c.execute(text("DELETE FROM deteccoes WHERE id_processamento = :id"), dict(id=id_proc))
        c.execute(text("DELETE FROM frames WHERE id_video = :v"), dict(v=id_video))
        c.execute(text(
            "UPDATE processamentos SET status = 'processando', progresso = 0, mensagem_erro = NULL, "
            "iniciado_em = NOW(), finalizado_em = NULL WHERE id_processamento = :id"), dict(id=id_proc))


def atualizar_video(id_video, *, caminho_arquivo, info):
    """Depois da conversão para H.264, guarda o novo caminho e as medidas reais do vídeo."""
    with engine.begin() as c:
        c.execute(text(
            "UPDATE videos SET caminho_arquivo = :caminho, duracao_segundos = :dur, fps = :fps, "
            "largura = :larg, altura = :alt WHERE id_video = :id"),
            dict(id=id_video, caminho=caminho_arquivo, dur=info["duracao"], fps=info["fps"],
                 larg=info["largura"], alt=info["altura"]))


def atualizar_progresso(id_proc, progresso):
    with engine.begin() as c:
        c.execute(text("UPDATE processamentos SET progresso = :p WHERE id_processamento = :id"),
                  dict(p=round(min(max(progresso, 0), 1), 3), id=id_proc))


def salvar_frames(id_video, id_proc, frames):
    """frames: [{numero, tempo, jpeg(bytes), caixas:[{classe, confianca, x_min, y_min, x_max, y_max}]}]"""
    with engine.begin() as c:
        for f in frames:
            id_frame = c.execute(text(
                "INSERT INTO frames (id_video, numero_frame, tempo_segundos, imagem, tipo_imagem) "
                "VALUES (:v, :n, :t, :img, 'image/jpeg')"),
                dict(v=id_video, n=f["numero"], t=round(f["tempo"], 3), img=f["jpeg"])).lastrowid
            if f["caixas"]:
                c.execute(text(
                    "INSERT INTO deteccoes (id_processamento, id_frame, classe_prevista, confianca, "
                    "x_min, y_min, x_max, y_max) VALUES (:p, :f, :classe, :conf, :x1, :y1, :x2, :y2)"),
                    [dict(p=id_proc, f=id_frame, classe=b["classe"], conf=round(b["confianca"], 4),
                          x1=b["x_min"], y1=b["y_min"], x2=b["x_max"], y2=b["y_max"]) for b in f["caixas"]])


def concluir_processamento(id_proc, *, caminho_anotado, total_deteccoes, frames_com_placa):
    with engine.begin() as c:
        c.execute(text(
            "UPDATE processamentos SET status = 'concluido', progresso = 1, caminho_video_anotado = :cam, "
            "total_deteccoes = :td, frames_com_placa = :fp, finalizado_em = NOW() "
            "WHERE id_processamento = :id"),
            dict(cam=caminho_anotado, td=total_deteccoes, fp=frames_com_placa, id=id_proc))


def falhar_processamento(id_proc, mensagem):
    with engine.begin() as c:
        c.execute(text(
            "UPDATE processamentos SET status = 'erro', mensagem_erro = :msg, finalizado_em = NOW() "
            "WHERE id_processamento = :id"), dict(msg=str(mensagem)[:4000], id=id_proc))


def processamentos_pendentes():
    """Ao ligar a API: análises que estavam na fila ou foram interrompidas voltam para a fila."""
    with engine.begin() as c:
        c.execute(text("UPDATE processamentos SET status = 'aguardando' WHERE status = 'processando'"))
        return [r[0] for r in c.execute(text(
            "SELECT id_processamento FROM processamentos WHERE status = 'aguardando' "
            "ORDER BY id_processamento"))]


# ---------------------------------------------------------------- consultas do front

_SELECT_ANALISE = """
SELECT p.id_processamento, p.status, p.progresso, p.mensagem_erro, p.nome_modelo, p.versao_modelo,
       p.intervalo_extracao_segundos, p.limiar_confianca, p.total_deteccoes, p.frames_com_placa,
       p.caminho_video_anotado, p.criado_em, p.iniciado_em, p.finalizado_em,
       v.id_video, v.nome_arquivo, v.caminho_arquivo, v.duracao_segundos, v.fps, v.largura, v.altura,
       v.data_envio, m.local_gravacao, m.data_gravacao, m.horario_gravacao, m.observacoes,
       (SELECT COUNT(*) FROM frames f WHERE f.id_video = v.id_video) AS frames_guardados
FROM processamentos p
JOIN videos v               ON v.id_video = p.id_video
LEFT JOIN video_metadados m ON m.id_video = p.id_video
"""


def listar_analises(limite=None):
    sql = _SELECT_ANALISE + " ORDER BY p.criado_em DESC, p.id_processamento DESC"
    if limite:
        sql += f" LIMIT {int(limite)}"
    with engine.connect() as c:
        return _linhas(c.execute(text(sql)))


def obter_analise(id_proc):
    with engine.connect() as c:
        return _uma(c.execute(text(_SELECT_ANALISE + " WHERE p.id_processamento = :id"), dict(id=id_proc)))


_SELECT_DETECCAO = """
SELECT d.id_deteccao, d.classe_prevista, d.confianca, d.x_min, d.y_min, d.x_max, d.y_max,
       f.numero_frame, f.tempo_segundos, v.largura, v.altura,
       COALESCE(r.status, 'pendente') AS revisao, r.classe_corrigida, r.comentario, r.data_revisao
FROM deteccoes d
JOIN frames f        ON f.id_frame = d.id_frame
JOIN videos v        ON v.id_video = f.id_video
LEFT JOIN revisoes r ON r.id_deteccao = d.id_deteccao
"""


def listar_deteccoes(id_proc, numero_frame=None):
    sql = _SELECT_DETECCAO + " WHERE d.id_processamento = :id"
    params = dict(id=id_proc)
    if numero_frame is not None:
        sql += " AND f.numero_frame = :n"
        params["n"] = numero_frame
    with engine.connect() as c:
        return _linhas(c.execute(text(sql + " ORDER BY f.numero_frame, d.id_deteccao"), params))


def obter_deteccao(id_proc, id_det):
    with engine.connect() as c:
        return _uma(c.execute(text(
            _SELECT_DETECCAO + " WHERE d.id_processamento = :p AND d.id_deteccao = :d"),
            dict(p=id_proc, d=id_det)))


def revisar(id_det, status, classe_corrigida=None, comentario=None):
    """Cria ou atualiza a revisão (1 por detecção). A detecção original da IA nunca é alterada."""
    with engine.begin() as c:
        existe = c.execute(text("SELECT id_revisao FROM revisoes WHERE id_deteccao = :d FOR UPDATE"),
                           dict(d=id_det)).first()
        params = dict(d=id_det, s=status, cc=classe_corrigida, com=comentario)
        if existe:
            c.execute(text("UPDATE revisoes SET status = :s, classe_corrigida = :cc, comentario = :com, "
                           "data_revisao = NOW() WHERE id_deteccao = :d"), params)
        else:
            c.execute(text("INSERT INTO revisoes (id_deteccao, status, classe_corrigida, comentario, data_revisao) "
                           "VALUES (:d, :s, :cc, :com, NOW())"), params)


def listar_frames(id_proc):
    with engine.connect() as c:
        return _linhas(c.execute(text(
            "SELECT f.numero_frame, f.tempo_segundos, COUNT(d.id_deteccao) AS qtd_placas "
            "FROM processamentos p "
            "JOIN frames f ON f.id_video = p.id_video "
            "LEFT JOIN deteccoes d ON d.id_frame = f.id_frame AND d.id_processamento = p.id_processamento "
            "WHERE p.id_processamento = :id "
            "GROUP BY f.id_frame, f.numero_frame, f.tempo_segundos ORDER BY f.numero_frame"), dict(id=id_proc)))


def obter_frame(id_proc, numero, com_imagem=False):
    colunas = "f.id_frame, f.numero_frame, f.tempo_segundos" + (", f.imagem, f.tipo_imagem" if com_imagem else "")
    with engine.connect() as c:
        return _uma(c.execute(text(
            f"SELECT {colunas} FROM processamentos p JOIN frames f ON f.id_video = p.id_video "
            "WHERE p.id_processamento = :id AND f.numero_frame = :n"), dict(id=id_proc, n=numero)))


# ---------------------------------------------------------------- painéis

def dashboard(dias):
    with engine.connect() as c:
        totais = _uma(c.execute(text(
            "SELECT COUNT(*) AS analises, COALESCE(SUM(p.total_deteccoes), 0) AS deteccoes, "
            "       COALESCE(SUM(p.frames_com_placa), 0) AS frames_com_placa "
            "FROM processamentos p WHERE p.criado_em >= CURDATE() - INTERVAL :d DAY"), dict(d=dias - 1)))
        totais["pendentes"] = c.execute(text(
            "SELECT COUNT(*) FROM deteccoes d JOIN processamentos p ON p.id_processamento = d.id_processamento "
            "LEFT JOIN revisoes r ON r.id_deteccao = d.id_deteccao "
            "WHERE (r.id_revisao IS NULL OR r.status = 'pendente') "
            "AND p.criado_em >= CURDATE() - INTERVAL :d DAY"), dict(d=dias - 1)).scalar()
        por_dia = _linhas(c.execute(text(
            "SELECT DATE(p.criado_em) AS dia, COALESCE(SUM(p.total_deteccoes), 0) AS total "
            "FROM processamentos p WHERE p.criado_em >= CURDATE() - INTERVAL :d DAY "
            "GROUP BY DATE(p.criado_em)"), dict(d=dias - 1)))
        distribuicao = _linhas(c.execute(text(
            "SELECT d.classe_prevista AS classe, COUNT(*) AS total FROM deteccoes d "
            "JOIN processamentos p ON p.id_processamento = d.id_processamento "
            "WHERE p.criado_em >= CURDATE() - INTERVAL :d DAY "
            "GROUP BY d.classe_prevista ORDER BY total DESC"), dict(d=dias - 1)))
    return totais, por_dia, distribuicao


def relatorio(de=None, ate=None, local=None):
    filtros, params = [], {}
    data_ref = "COALESCE(m.data_gravacao, DATE(v.data_envio))"
    if de:
        filtros.append(f"{data_ref} >= :de"); params["de"] = de
    if ate:
        filtros.append(f"{data_ref} <= :ate"); params["ate"] = ate
    if local:
        filtros.append("m.local_gravacao LIKE :local"); params["local"] = f"%{local}%"
    onde = ("WHERE " + " AND ".join(filtros)) if filtros else ""
    base = ("FROM processamentos p JOIN videos v ON v.id_video = p.id_video "
            "LEFT JOIN video_metadados m ON m.id_video = p.id_video ")
    with engine.connect() as c:
        analises = c.execute(text(f"SELECT COUNT(*) {base} {onde}"), params).scalar()
        por_classe = _linhas(c.execute(text(
            f"SELECT d.classe_prevista AS classe, COUNT(*) AS total {base} "
            f"JOIN deteccoes d ON d.id_processamento = p.id_processamento {onde} "
            "GROUP BY d.classe_prevista ORDER BY total DESC"), params))
        revisao = _linhas(c.execute(text(
            f"SELECT COALESCE(r.status, 'pendente') AS status, COUNT(*) AS total {base} "
            f"JOIN deteccoes d ON d.id_processamento = p.id_processamento "
            f"LEFT JOIN revisoes r ON r.id_deteccao = d.id_deteccao {onde} "
            "GROUP BY COALESCE(r.status, 'pendente')"), params))
    return analises, por_classe, revisao
