# Contrato da API

Base: `http://127.0.0.1:8000/api`. Respostas em JSON (exceto vídeos e imagens).
Erros: código HTTP 4xx/5xx com `{"error": "mensagem"}`.

## Análises

| Método e rota | Envia | Recebe |
|---|---|---|
| `POST /analises` | multipart: `video` (MP4/MOV/WebM, 10–40 s, ≤200 MB), `local` (obrigatório, ≤150), `data` (AAAA-MM-DD), `horario` (HH:MM), `observacoes` | `201 {id, status:"na_fila"}` |
| `GET /analises` | — | `[Analise]` (mais recentes primeiro) |
| `GET /analises/<id>` | — | `Analise` |
| `GET /analises/<id>/status` | — | `{status, progresso, erro}` |
| `GET /analises/<id>/deteccoes` | — | `[Deteccao]` |
| `POST /analises/<id>/deteccoes/<id_det>/confirmar` | `{obs?}` | `Deteccao` atualizada |
| `POST /analises/<id>/deteccoes/<id_det>/rejeitar` | `{obs?}` | `Deteccao` atualizada |
| `POST /analises/<id>/deteccoes/<id_det>/corrigir` | `{classe, obs?}` | `Deteccao` atualizada |
| `GET /analises/<id>/ocorrencias` | — | `[]` (reservado para o futuro) |

## Vídeos e frames

| Método e rota | Recebe |
|---|---|
| `GET /analises/<id>/video?versao=anotado` | MP4 com as placas rotuladas (todos os frames). `&download=1` baixa o arquivo |
| `GET /analises/<id>/video?versao=original` | MP4 original (convertido para H.264) |
| `GET /analises/<id>/frames` | `[{numero, tempo, qtdPlacas, originalUrl, anotadoUrl}]` — frames guardados (1 a cada `intervaloFrames` s) |
| `GET /analises/<id>/frames/<numero>` | `{numero, tempo, originalUrl, anotadoUrl, deteccoes:[Deteccao]}` (404 se o frame não foi guardado) |
| `GET /analises/<id>/frames/<numero>/imagem?versao=original` | JPEG do frame original (vem de `frames.imagem`) |
| `GET /analises/<id>/frames/<numero>/imagem?versao=anotado` | JPEG com as caixas desenhadas pela API a partir de `deteccoes` |
| `…/imagem?…&largura=220` | Miniatura com a largura informada |

## Painéis

| Método e rota | Recebe |
|---|---|
| `GET /dashboard?dias=7\|30\|90` | `{totais:{analises, deteccoes, framesComPlaca, pendentes}, serie:[{rotulo, valor}], distribuicao:[{classe, total}], recentes:[Analise]}` |
| `GET /relatorios?de=&ate=&local=` | `{analises, porClasse:[{classe, total}], revisao:{confirmadas, rejeitadas, corrigidas, pendentes}}` |
| `GET /saude` | `{ok, banco, modelo, classes, intervaloFrames, video:{minS, maxS, maxMB}}` (503 se o banco estiver fora) |

## Objetos

```js
Analise = {
  id: 7,                              // processamentos.id_processamento
  video: "av_higienopolis.mp4", local: "Av. Higienópolis, Centro", data: "2026-11-08", horario: "14:30",
  observacoes: null, duracao: 32.5, fps: 30, largura: 1920, altura: 1080,
  status: "concluida",                // na_fila | processando | concluida | falhou
  progresso: 1, erro: null,
  deteccoes: 41,                      // detecções nos frames guardados
  framesComPlaca: 19, framesGuardados: 33, intervaloFrames: 1,
  modelo: "yolo26n", versaoModelo: "detector_v1", limiarConfianca: 0.25,
  enviadoEm: "2026-11-09T10:12:03", concluidoEm: "2026-11-09T10:13:20",
  videoUrl: "/api/analises/7/video?versao=anotado",        // null enquanto não conclui
  videoOriginalUrl: "/api/analises/7/video?versao=original"
}

Deteccao = {
  id: 315, frame: 61, tempo: 2.0,
  classe: "Placa", confianca: 0.93,
  revisao: "pendente",                // pendente | confirmada | rejeitada | corrigida
  classeCorrigida: null, obs: null,
  bbox:  { x_min: 120, y_min: 55, x_max: 190, y_max: 160 },        // pixels do frame original
  caixa: { x: 0.0625, y: 0.0509, l: 0.0365, a: 0.0972 }            // 0–1, canto superior esquerdo
}
```

## Correspondência front ↔ banco (feita só na API)

| Front | Banco |
|---|---|
| `status` `na_fila / processando / concluida / falhou` | `processamentos.status` `aguardando / processando / concluido / erro` |
| ação `confirmar / rejeitar / corrigir` | `revisoes.status` `confirmada / rejeitada / corrigida` |
| `revisao: "pendente"` | sem linha em `revisoes` |
| `local, data, horario, observacoes` | `video_metadados.local_gravacao, data_gravacao, horario_gravacao, observacoes` |
| `classe: "Placa"` | `deteccoes.classe_prevista = 'placa'` |
| `classeCorrigida, obs` | `revisoes.classe_corrigida, comentario` |
| `tempo`, `frame` | `frames.tempo_segundos`, `frames.numero_frame` |
