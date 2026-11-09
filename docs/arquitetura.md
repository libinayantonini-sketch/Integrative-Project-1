# Arquitetura

## As peças e quem fala com quem

```
┌──────────────────┐   HTTP    ┌───────────────────────────────┐   SQL    ┌──────────────────────┐
│ FRONT            │ ────────► │ API  (backend/api/api.py)      │ ───────► │ MYSQL                │
│ (frontend/)      │ ◄──────── │ http://127.0.0.1:8000          │ ◄─────── │ projeto_sinalizacoes │
│ no navegador     │  JSON,    │  ├─ visao/detector.py ─► modelo│          │ localhost:3306       │
└──────────────────┘  vídeos,  │  │   (modelos/detector_v1.pt)  │          └──────────────────────┘
                      imagens  │  └─ visao/pipeline.py          │
                               └──────────────┬─────────────────┘
                                              │ arquivos
                                              ▼
                               backend/storage/  (vídeos original e anotado)
```

- O **front nunca acessa o banco**: só conversa com a API.
- O **modelo não sabe** que existem banco ou front: recebe um frame e devolve uma lista de caixas.
- A **API** é a única peça ligada a todas as outras. Ela também entrega os arquivos do front,
  então tudo funciona em um só endereço: `http://127.0.0.1:8000`.

## O fluxo de uma análise

1. **Front → API** — `POST /api/analises` com o vídeo, local, data, horário e observações.
2. **API → banco** — cadastra `videos`, `video_metadados` e `processamentos` (status `aguardando`)
   e responde na hora com o `id`. O vídeo vai para a fila (`visao/fila.py`), um de cada vez.
3. **Pipeline** (`visao/pipeline.py`), numa thread separada:
   1. converte o vídeo para MP4 H.264 (`storage/videos/<pasta>/original.mp4`);
   2. lê **todos** os frames; cada um vai para o **modelo** (`detector.detectar(frame)`),
      que devolve `[{classe, confianca, x_min, y_min, x_max, y_max}]`;
   3. desenha as caixas e grava o **vídeo anotado** (`storage/processamentos/<id>/anotado.mp4`);
   4. a cada `INTERVALO_EXTRACAO_S` segundos (padrão 1), guarda no banco o **frame original**
      (`frames.imagem`) e as caixas dele (`deteccoes`);
   5. atualiza `processamentos.progresso` durante o caminho e, no fim, grava as métricas e o status
      `concluido` (ou `erro` com a mensagem).
4. **Front ↔ API** — o front consulta `/status` a cada 2 s e mostra o progresso. Ao concluir, mostra:
   - o **vídeo com as placas rotuladas** (com download do anotado e do original);
   - a **consulta de frames**: por número do frame, por tempo ou pela faixa de miniaturas,
     exibindo lado a lado o **frame original** (do banco) e o **rotulado** (desenhado pela API
     com as caixas do banco);
   - a lista de detecções, com **confirmar / rejeitar / corrigir** (grava em `revisoes`).

## Onde cada dado fica

| Dado | Onde |
|---|---|
| Vídeo original (H.264) e vídeo anotado | Disco: `backend/storage/` (o banco guarda o caminho relativo) |
| Imagem original dos frames guardados | Banco: `frames.imagem` |
| Imagem rotulada do frame | Não é guardada: a API desenha na hora a partir de `deteccoes` |
| Caixas, confiança, classe | Banco: `deteccoes` |
| Revisão humana | Banco: `revisoes` |
| Modelo | Disco: `backend/modelos/detector_v1.pt` |

## Por que só alguns frames vão para o banco

Um vídeo de 40 s a 30 fps tem 1.200 frames. Guardar todos (≈250 MB por vídeo) deixaria o banco
pesado e a revisão impraticável. O vídeo anotado mantém **todos** os frames; o banco guarda
1 frame por segundo (≈40 imagens, alguns MB), o suficiente para consulta e revisão.
Para guardar mais, diminua `INTERVALO_EXTRACAO_S` no `backend/.env` (ex.: `0.5`).

As métricas contam **detecções nos frames guardados**, não placas únicas: a mesma placa aparece
em vários frames. Para contar placas únicas no futuro, basta adicionar rastreamento
(`model.track`) e uma coluna `track_id` em `deteccoes`.

## Organização do código

| Pasta | Responsabilidade |
|---|---|
| `frontend/` | Telas (HTML/CSS/JS puro). Só `api.js` fala com o back-end |
| `backend/api/api.py` | Rotas HTTP, validação e tradução entre banco e front |
| `backend/db/` | Conexão e todas as consultas SQL (`repositorio.py`); criação do banco (`criar_banco.py`) |
| `backend/visao/` | Modelo (`detector.py`), vídeo/FFmpeg (`video.py`), processamento (`pipeline.py`), fila (`fila.py`) |
| `backend/modelos/` | Modelo treinado |
| `database/` | Scripts SQL da equipe de banco |
| `notebooks/` | Treino do modelo (Colab) |
