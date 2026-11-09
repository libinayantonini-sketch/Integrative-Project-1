# 🔌 API — o back-end que liga front, banco e modelo

A API é um programa em **Python + Flask** (`backend/api/api.py`) que fica ligado em
**http://127.0.0.1:8000**. Ela é a **única peça que conversa com todas as outras**:

- recebe pedidos do **front** (pela internet do próprio computador, via HTTP);
- lê e grava no **banco MySQL**;
- passa os frames dos vídeos pelo **modelo YOLO26**;
- guarda e entrega os **vídeos** (pasta `backend/storage/`);
- e ainda entrega as **páginas do front** (por isso tudo funciona num só endereço).

> **O que é uma API?** É um "balcão de atendimento" para programas. O front não sabe onde os dados
> ficam nem como o modelo funciona: ele só faz pedidos padronizados (ex.: "me dê a análise 7") e
> recebe respostas padronizadas (JSON). Esse combinado de pedidos e respostas é o **contrato** entre as equipes.

---

## Sumário

1. [Como ligar e testar](#1-como-ligar-e-testar)
2. [Configurações (.env)](#2-configurações-env)
3. [Organização do código](#3-organização-do-código)
4. [Conceitos para ler as rotas](#4-conceitos-para-ler-as-rotas)
5. [Todas as rotas](#5-todas-as-rotas)
6. [Formatos dos objetos (JSON)](#6-formatos-dos-objetos-json)
7. [O modelo e o pipeline](#7-o-modelo-e-o-pipeline)
8. [Erros e mensagens](#8-erros-e-mensagens)
9. [Testando a API sem o front](#9-testando-a-api-sem-o-front)
10. [Como fazer mudanças](#10-como-fazer-mudanças)
11. [Limitações conhecidas](#11-limitações-conhecidas)

---

## 1. Como ligar e testar

Com o ambiente ativado e o banco criado (veja [02_MANUAL_DE_EXECUCAO.md](02_MANUAL_DE_EXECUCAO.md)):

```bash
python backend/api/api.py
```

Ao ligar, a API faz nesta ordem:

```mermaid
flowchart LR
    A["Lê backend/.env"] --> B{"Conecta no<br/>MySQL?"}
    B -- não --> X["Para com mensagem<br/>explicando o que fazer"]
    B -- sim --> C["Carrega o modelo<br/>detector_v1.pt"]
    C --> D["Liga a fila de<br/>processamento"]
    D --> E["Retoma análises que<br/>ficaram pela metade"]
    E --> F["Atende em<br/>http://127.0.0.1:8000"]
```

Teste rápido: abra **http://127.0.0.1:8000/api/saude** no navegador. Deve aparecer algo como:

```json
{"ok": true, "banco": true, "modelo": "detector_v1", "classes": ["placa"], "intervaloFrames": 1.0,
 "video": {"minS": 10.0, "maxS": 40.0, "maxMB": 200}}
```

---

## 2. Configurações (.env)

Todas as configurações ficam em `backend/.env` (copiado de `backend/.env.example`) e são lidas por `backend/config.py`.

| Variável | Padrão | Para que serve |
|---|---|---|
| `DB_URL` | — | Endereço do MySQL: `mysql+pymysql://usuario:senha@localhost:3306/projeto_sinalizacoes` |
| `HOST` | `127.0.0.1` | Em qual endereço a API atende. `127.0.0.1` = só este computador. `0.0.0.0` = outros computadores da rede também |
| `PORTA` | `8000` | Porta da API (e do front) |
| `STORAGE_DIR` | `storage` | Pasta dos vídeos (relativa a `backend/`) |
| `MODELO_PESOS` | `modelos/detector_v1.pt` | Arquivo do modelo |
| `FRONTEND_DIR` | `../frontend` | Pasta do front que a API entrega |
| `INTERVALO_EXTRACAO_S` | `1` | A cada quantos segundos de vídeo um frame é guardado no banco |
| `QUALIDADE_JPEG` | `90` | Qualidade das imagens dos frames guardados (0–100) |
| `DISPOSITIVO` | vazio | Vazio = automático (usa GPU NVIDIA se houver). `cpu` força o processador |
| `VIDEO_MIN_S` / `VIDEO_MAX_S` | `10` / `40` | Duração mínima e máxima aceitas (segundos) |
| `TAM_MAX_MB` | `200` | Tamanho máximo do arquivo enviado |

> Os limites de vídeo também existem no front (`frontend/api.js`). Se mudar aqui, mude lá também.

---

## 3. Organização do código

```
backend/
├── config.py            → lê o .env e define as configurações
├── api/
│   ├── api.py           → as ROTAS: recebe pedidos, valida, chama o banco e a fila, monta as respostas
│   └── requirements.txt → bibliotecas necessárias
├── db/
│   ├── conexao.py       → abre a conexão com o MySQL
│   ├── repositorio.py   → TODAS as consultas SQL do sistema
│   └── criar_banco.py   → cria/atualiza o banco a partir de database/migracoes/
├── visao/
│   ├── detector.py      → carrega o modelo e detecta placas num frame; desenha as caixas
│   ├── video.py         → lê informações do vídeo e escreve MP4 (FFmpeg)
│   ├── pipeline.py      → processa uma análise inteira (vídeo → modelo → banco + vídeo anotado)
│   └── fila.py          → executa os processamentos um de cada vez, em segundo plano
├── modelos/             → detector_v1.pt + detector_v1_info.json
└── storage/             → vídeos enviados e anotados (fora do Git)
```

**Quem chama quem:**

```mermaid
flowchart LR
    API["api.py<br/>(rotas)"] --> REPO["db/repositorio.py<br/>(SQL)"]
    API --> FILA["visao/fila.py"]
    API --> DET["visao/detector.py<br/>(desenhar caixas)"]
    API --> VID["visao/video.py<br/>(ler duração)"]
    FILA --> PIPE["visao/pipeline.py"]
    PIPE --> DET
    PIPE --> VID
    PIPE --> REPO
    REPO --> CON["db/conexao.py"] --> MY[("MySQL")]
    DET --> PT["modelos/detector_v1.pt"]
```

**Por que separar assim?** Cada equipe mexe na sua parte sem quebrar as outras:

| Se você quer mudar… | Mexa em… |
|---|---|
| Uma rota, uma validação ou o formato de uma resposta | `backend/api/api.py` |
| Uma consulta ao banco | `backend/db/repositorio.py` |
| O modelo ou como as caixas são desenhadas | `backend/visao/detector.py` |
| Quais frames são guardados, o que é medido | `backend/visao/pipeline.py` |
| Formato/qualidade dos vídeos gerados | `backend/visao/video.py` |
| Um limite ou caminho | `backend/.env` (e `config.py` se for uma configuração nova) |

---

## 4. Conceitos para ler as rotas

| Termo | Significado |
|---|---|
| **Rota** | Um endereço que a API atende, ex.: `/api/analises/7` |
| **GET** | Pedido para **ler** algo (não muda nada) |
| **POST** | Pedido para **criar ou fazer** algo (enviar vídeo, revisar) |
| **JSON** | Formato de texto para dados: `{"id": 7, "status": "concluida"}` |
| **multipart** | Formato usado para enviar arquivos (o vídeo) junto com campos de formulário |
| **Código HTTP** | Número que diz se deu certo: `200` ok · `201` criado · `400` pedido inválido · `404` não encontrado · `409` ainda não está pronto · `413` arquivo grande demais · `500` erro no servidor |
| `<id>` na rota | Troque pelo número da análise (o `id_processamento`) |

Todas as rotas de dados começam com **`/api`**. Rotas sem `/api` entregam os arquivos do front.

---

## 5. Todas as rotas

### Resumo

| Método | Rota | Para quê | Usada pelo front em |
|---|---|---|---|
| POST | `/api/analises` | Enviar um vídeo | Nova análise |
| GET | `/api/analises` | Listar análises | Análises |
| GET | `/api/analises/<id>` | Dados de uma análise | Detalhe |
| GET | `/api/analises/<id>/status` | Andamento do processamento | Nova análise, Detalhe |
| GET | `/api/analises/<id>/deteccoes` | Detecções da análise | Detalhe |
| POST | `/api/analises/<id>/deteccoes/<id_det>/confirmar` | Confirmar detecção | Detalhe |
| POST | `/api/analises/<id>/deteccoes/<id_det>/rejeitar` | Rejeitar detecção | Detalhe |
| POST | `/api/analises/<id>/deteccoes/<id_det>/corrigir` | Corrigir a classe | Detalhe |
| GET | `/api/analises/<id>/ocorrencias` | Reservada (sempre `[]`) | — |
| GET | `/api/analises/<id>/video` | Vídeo anotado ou original | Detalhe |
| GET | `/api/analises/<id>/frames` | Lista de frames guardados | Detalhe (consulta de frames) |
| GET | `/api/analises/<id>/frames/<n>` | Um frame e suas detecções | Detalhe (consulta de frames) |
| GET | `/api/analises/<id>/frames/<n>/imagem` | Imagem original ou rotulada | Detalhe (consulta de frames) |
| GET | `/api/dashboard` | Números da Visão Geral | Visão Geral |
| GET | `/api/relatorios` | Números dos Relatórios | Relatórios |
| GET | `/api/saude` | API e banco estão ok? | Configurações |
| GET | `/` e `/<arquivo>` | Páginas do front | Navegador |

---

### `POST /api/analises` — enviar um vídeo

**Envia** (multipart/form-data):

| Campo | Obrigatório | Regras |
|---|---|---|
| `video` | ✅ | Arquivo `.mp4`, `.mov`, `.webm`, `.m4v`, `.avi` ou `.mkv`; duração entre `VIDEO_MIN_S` e `VIDEO_MAX_S`; até `TAM_MAX_MB` |
| `local` | ✅ | Texto de até 150 caracteres |
| `data` | — | `AAAA-MM-DD` |
| `horario` | — | `HH:MM` |
| `observacoes` | — | Texto de até 2000 caracteres |

**Recebe:** `201` com
```json
{"id": 7, "status": "na_fila"}
```

**O que acontece por dentro:** salva o arquivo em `backend/storage/videos/<pasta>/`, lê a duração,
grava `videos` + `video_metadados` + `processamentos` no banco e coloca o `id` na fila.
A resposta volta **na hora**; o processamento acontece depois, em segundo plano.

**Erros:** `400` (sem vídeo, formato não aceito, sem local, data/horário inválidos, duração fora do limite) · `413` (arquivo grande demais).

---

### `GET /api/analises` — listar análises

**Recebe:** `200` com uma lista de [Analise](#analise), da mais recente para a mais antiga.

### `GET /api/analises/<id>` — uma análise

**Recebe:** `200` com uma [Analise](#analise) · `404` se não existir.

### `GET /api/analises/<id>/status` — andamento

Chamada pelo front **a cada 2 segundos** enquanto a análise não termina.

```json
{"status": "processando", "progresso": 0.45, "erro": null}
```

| `status` | Significado |
|---|---|
| `na_fila` | Esperando a vez |
| `processando` | Em análise; `progresso` de 0 a 1 |
| `concluida` | Pronto |
| `falhou` | Deu erro; o motivo vem em `erro` |

### `GET /api/analises/<id>/deteccoes` — detecções

**Recebe:** lista de [Deteccao](#deteccao), ordenada por frame. São as detecções dos **frames guardados** (1 por segundo).

### `POST /api/analises/<id>/deteccoes/<id_det>/<ação>` — revisar

`<ação>` = `confirmar`, `rejeitar` ou `corrigir`.

**Envia** (JSON):

| Ação | Corpo |
|---|---|
| confirmar | `{}` ou `{"obs": "comentário"}` |
| rejeitar | `{}` ou `{"obs": "era um outdoor"}` |
| corrigir | `{"classe": "Semáforo", "obs": "justificativa"}` — `classe` é obrigatória |

**Recebe:** `200` com a [Deteccao](#deteccao) atualizada (`revisao` = `confirmada`, `rejeitada` ou `corrigida`).

**Erros:** `404` (ação inválida ou detecção não pertence à análise) · `400` (corrigir sem classe).

Pode revisar a mesma detecção de novo: a revisão anterior é substituída.

### `GET /api/analises/<id>/ocorrencias`

Sempre `[]`. Reservada para quando o modelo detectar ocorrências (buracos etc.).

### `GET /api/analises/<id>/video` — vídeo

| Parâmetro | Valores | Padrão |
|---|---|---|
| `versao` | `anotado` (com as caixas) ou `original` | `anotado` |
| `download` | `1` para baixar como arquivo | — |

Exemplos: `/api/analises/7/video?versao=anotado` · `/api/analises/7/video?versao=original&download=1`

**Recebe:** o arquivo MP4 (H.264, toca em qualquer navegador). Aceita pedidos parciais (*Range*),
o que permite avançar e voltar no player sem baixar tudo.

**Erros:** `409` se a análise ainda não terminou · `404` se o arquivo sumiu do disco.

### `GET /api/analises/<id>/frames` — frames guardados

```json
[
  {"numero": 1,  "tempo": 0.0, "qtdPlacas": 2,
   "originalUrl": "/api/analises/7/frames/1/imagem?versao=original",
   "anotadoUrl":  "/api/analises/7/frames/1/imagem?versao=anotado"},
  {"numero": 31, "tempo": 1.0, "qtdPlacas": 0, "originalUrl": "...", "anotadoUrl": "..."}
]
```

### `GET /api/analises/<id>/frames/<n>` — um frame

```json
{"numero": 61, "tempo": 2.0,
 "originalUrl": "/api/analises/7/frames/61/imagem?versao=original",
 "anotadoUrl":  "/api/analises/7/frames/61/imagem?versao=anotado",
 "deteccoes": [ /* Deteccao */ ]}
```

**Erro:** `404` se esse frame não foi guardado (só 1 por segundo é guardado). O front, nesse caso,
procura sozinho o frame guardado mais próximo.

### `GET /api/analises/<id>/frames/<n>/imagem` — imagem do frame

| Parâmetro | Valores | Padrão |
|---|---|---|
| `versao` | `original` ou `anotado` | `original` |
| `largura` | número de pixels (ex.: `220`) para receber uma **miniatura** | tamanho real |

**Recebe:** uma imagem JPEG.

- `original` vem direto do banco (`frames.imagem`).
- `anotado` é **desenhado na hora**: a API pega a imagem original e desenha as caixas da tabela `deteccoes`.
  Nada disso é gravado.

### `GET /api/dashboard?dias=7` — Visão Geral

`dias` = `7`, `30` ou `90` (outros valores viram 7).

```json
{"totais": {"analises": 3, "deteccoes": 41, "framesComPlaca": 19, "pendentes": 38},
 "serie": [{"rotulo": "03/11", "valor": 0}, {"rotulo": "09/11", "valor": 41}],
 "distribuicao": [{"classe": "Placa", "total": 41}],
 "recentes": [ /* até 5 Analise */ ]}
```

`serie` tem uma barra por **dia** (7 dias), por **semana** (30 dias) ou por **quinzena** (90 dias); a última barra termina hoje.

### `GET /api/relatorios?de=&ate=&local=` — Relatórios

Todos os filtros são opcionais. `de`/`ate` filtram pela data da gravação (ou do envio, se não houver);
`local` busca por parte do texto.

```json
{"analises": 3,
 "porClasse": [{"classe": "Placa", "total": 41}],
 "revisao": {"confirmadas": 2, "rejeitadas": 1, "corrigidas": 0, "pendentes": 38}}
```

### `GET /api/saude` — está tudo ligado?

`200` quando a API e o banco estão ok (exemplo na seção 1) · `503` com `{"ok": false, "banco": false, "erro": "..."}` se o banco caiu.

### `GET /` e `GET /<arquivo>` — o front

A API entrega os arquivos da pasta `frontend/` (`index.html`, `app.js`, `api.js`, `style.css`).
É por isso que basta abrir `http://127.0.0.1:8000`.

---

## 6. Formatos dos objetos (JSON)

### Analise

```js
{
  "id": 7,                          // número da análise (processamentos.id_processamento)
  "video": "av_higienopolis.mp4",   // nome do arquivo enviado
  "local": "Av. Higienópolis, Centro",
  "data": "2026-11-08",             // data da gravação (ou null)
  "horario": "14:30",               // horário da gravação (ou null)
  "observacoes": null,
  "duracao": 32.5,                  // segundos
  "fps": 30.0, "largura": 1920, "altura": 1080,
  "status": "concluida",            // na_fila | processando | concluida | falhou
  "progresso": 1.0,                 // 0 a 1
  "erro": null,                     // mensagem, se falhou
  "deteccoes": 41,                  // detecções nos frames guardados
  "framesComPlaca": 19,             // frames guardados com ao menos 1 placa
  "framesGuardados": 33,            // quantos frames foram guardados
  "intervaloFrames": 1.0,           // 1 frame guardado a cada X segundos
  "modelo": "yolo26n", "versaoModelo": "detector_v1", "limiarConfianca": 0.25,
  "enviadoEm": "2026-11-09T10:12:03",
  "concluidoEm": "2026-11-09T10:13:20",
  "videoUrl": "/api/analises/7/video?versao=anotado",          // null até concluir
  "videoOriginalUrl": "/api/analises/7/video?versao=original"  // null até concluir
}
```

### Deteccao

```js
{
  "id": 315,                        // deteccoes.id_deteccao
  "frame": 61,                      // número do frame
  "tempo": 2.0,                     // segundos
  "classe": "Placa",                // o que a IA previu
  "confianca": 0.93,                // 0 a 1
  "revisao": "pendente",            // pendente | confirmada | rejeitada | corrigida
  "classeCorrigida": null,          // preenchida quando corrigida
  "obs": null,                      // comentário da revisão
  "bbox":  {"x_min": 120, "y_min": 55, "x_max": 190, "y_max": 160},   // pixels
  "caixa": {"x": 0.0625, "y": 0.0509, "l": 0.0365, "a": 0.0972}       // 0 a 1 (proporção da imagem)
}
```

`bbox` e `caixa` são a mesma caixa em dois formatos: pixels (como está no banco) e proporção da imagem
(prático para desenhar em telas de qualquer tamanho).

### De onde vem cada campo (banco → API → front)

| Campo no JSON | Coluna no banco |
|---|---|
| `id` (Analise) | `processamentos.id_processamento` |
| `video`, `duracao`, `fps`, `largura`, `altura` | `videos.*` |
| `local`, `data`, `horario`, `observacoes` | `video_metadados.local_gravacao`, `data_gravacao`, `horario_gravacao`, `observacoes` |
| `status` | `processamentos.status`, traduzido (veja abaixo) |
| `progresso`, `erro`, `deteccoes`, `framesComPlaca` | `processamentos.progresso`, `mensagem_erro`, `total_deteccoes`, `frames_com_placa` |
| `framesGuardados` | contagem em `frames` |
| `id` (Deteccao), `confianca`, `bbox` | `deteccoes.*` |
| `classe` | `deteccoes.classe_prevista` com a primeira letra maiúscula (`placa` → `Placa`) |
| `frame`, `tempo` | `frames.numero_frame`, `tempo_segundos` |
| `revisao`, `classeCorrigida`, `obs` | `revisoes.status`, `classe_corrigida`, `comentario` (sem linha = `pendente`) |

**Tradução de status** (feita só na API; banco e front não precisam mudar):

| Banco | API / Front |
|---|---|
| `aguardando` | `na_fila` |
| `processando` | `processando` |
| `concluido` | `concluida` |
| `erro` | `falhou` |

| Ação no front (rota) | Gravado em `revisoes.status` |
|---|---|
| `confirmar` | `confirmada` |
| `rejeitar` | `rejeitada` |
| `corrigir` | `corrigida` |

---

## 7. O modelo e o pipeline

### O modelo (`backend/visao/detector.py`)

- Arquivo: `backend/modelos/detector_v1.pt` — **YOLO26n** treinado no notebook `notebooks/treino_detector_placas_yolo26.ipynb`.
- Configurações vêm de `detector_v1_info.json`: classe `placa`, imagem de entrada 640 px, confiança mínima `0.25`, IoU `0.7`.
- Métricas no teste: **mAP50 0,957 · mAP50-95 0,765 · precisão 0,957 · recall 0,931** (gráficos em `docs/modelo/`).

O modelo é carregado **uma única vez**, quando a API liga. Depois, cada frame passa por:

```python
caixas = detector.detectar(frame)
# → [{"classe": "placa", "confianca": 0.93, "x_min": 120, "y_min": 55, "x_max": 190, "y_max": 160}, ...]
```

| O modelo recebe | O modelo devolve |
|---|---|
| Uma imagem (um frame do vídeo, em formato OpenCV) | Uma lista de caixas: classe, confiança e posição em pixels |
| **De quem:** do pipeline | **Para quem:** para o pipeline (que desenha e grava) |

O modelo **não sabe** que existem banco, front ou vídeo inteiro. A mesma função `desenhar(frame, caixas)`
é usada para o vídeo anotado e para as imagens rotuladas da consulta de frames, então as caixas ficam iguais nos dois.

### O pipeline (`backend/visao/pipeline.py`)

Executa uma análise completa:

```mermaid
flowchart TB
    A["Recebe o id da análise (da fila)"] --> B["status = processando"]
    B --> C["Converte o vídeo enviado para original.mp4<br/>(H.264, FPS constante, sem áudio)"]
    C --> D["Abre o original.mp4 e o gravador do anotado.mp4"]
    D --> E["Lê o próximo frame"]
    E --> F["Modelo detecta as placas"]
    F --> G{"Frame de 1 em 1 s?"}
    G -- sim --> H["Guarda imagem original + caixas<br/>(em lotes de 10 no banco)"]
    G -- não --> I
    H --> I["Desenha as caixas e escreve no anotado.mp4"]
    I --> J{"Acabaram os frames?"}
    J -- não --> K["Atualiza o progresso<br/>(a cada 15 frames)"] --> E
    J -- sim --> L["Fecha o anotado.mp4<br/>status = concluido + métricas"]
    C -. erro .-> Z["status = erro + mensagem"]
    F -. erro .-> Z
```

**Por que converter o vídeo?** Vídeos de celular costumam vir em HEVC (o Chrome não toca) e com FPS variável
(o número do frame não bateria com o tempo). A conversão para H.264 com FPS constante resolve as duas coisas.

**Onde os arquivos ficam:**

```
backend/storage/
├── videos/<pasta aleatória>/original.mp4      ← o vídeo enviado, convertido
└── processamentos/<id da análise>/anotado.mp4 ← o vídeo com as placas rotuladas
```

### A fila (`backend/visao/fila.py`)

- Os vídeos são processados **um de cada vez**, numa linha de execução separada (thread).
- Por isso o envio responde na hora e o front pode acompanhar o progresso.
- Se a API for desligada no meio de uma análise, ao ligar de novo ela **retoma** do começo as que estavam em andamento ou na fila.

### Desempenho

Todo frame passa pelo modelo, então o tempo cresce com a duração do vídeo.
No processador (sem placa de vídeo), um vídeo de 40 s leva alguns minutos; com GPU NVIDIA, bem menos.

### Trocando o modelo

1. Treine um novo modelo com o notebook (ex.: `MODEL_VERSION = "detector_v2"`).
2. Copie `detector_v2.pt` e `detector_v2_info.json` para `backend/modelos/`.
3. No `backend/.env`: `MODELO_PESOS=modelos/detector_v2.pt` e reinicie a API.

As análises novas registram `versao_modelo = detector_v2` no banco, o que permite comparar os modelos.

---

## 8. Erros e mensagens

Toda resposta de erro da API vem no mesmo formato, com uma mensagem em português que o front mostra ao usuário:

```json
{"error": "A duração (52s) deve estar entre 10s e 40s."}
```

| Código | Quando acontece | Exemplos de mensagem |
|---|---|---|
| `400` | O pedido tem algum dado inválido | "Informe o local da gravação." · "Formato não aceito." · "Informe a classe correta." |
| `404` | Não existe | "Análise não encontrada." · "Este frame não foi guardado." · "Detecção não encontrada." |
| `409` | Ainda não está pronto | "Vídeo ainda não disponível." |
| `413` | Arquivo grande demais | "O arquivo excede 200 MB." |
| `500` | Erro inesperado no servidor | "Erro interno no servidor." (o detalhe aparece no terminal da API) |
| `503` | Banco fora do ar (só em `/api/saude`) | — |

**Onde ver o que aconteceu:** o terminal onde a API está rodando mostra um registro de cada análise
(`Análise 7 recebida`, `Análise 7 concluída: 975 frames…`) e o erro completo quando algo falha.

---

## 9. Testando a API sem o front

Útil para quem trabalha no back-end ou quer entender as respostas.

**No navegador** (só rotas GET): abra, por exemplo,
`http://127.0.0.1:8000/api/analises` ou `http://127.0.0.1:8000/api/analises/1/frames`.

**No PowerShell:**

```bash
Invoke-RestMethod http://127.0.0.1:8000/api/saude
```
```bash
Invoke-RestMethod http://127.0.0.1:8000/api/analises/1/status
```

Enviar um vídeo (o `curl.exe` já vem no Windows 10/11):

```bash
curl.exe -F "video=@C:\videos\teste.mp4" -F "local=Rua Sergipe, Centro" -F "data=2026-11-08" http://127.0.0.1:8000/api/analises
```

Confirmar a detecção 15 da análise 1:

```bash
curl.exe -X POST -H "Content-Type: application/json" -d "{}" http://127.0.0.1:8000/api/analises/1/deteccoes/15/confirmar
```

---

## 10. Como fazer mudanças

**Regra de ouro:** as rotas e os formatos JSON são o **contrato** entre back-end e front-end.
Se mudar algum, no **mesmo Pull Request**: atualize `frontend/api.js` (se o front usar) e este documento.

**Adicionar uma rota nova (exemplo):**

1. Se precisar do banco, crie a função em `backend/db/repositorio.py`:
   ```python
   def contar_videos():
       with engine.connect() as c:
           return c.execute(text("SELECT COUNT(*) FROM videos")).scalar()
   ```
2. Crie a rota em `backend/api/api.py`, junto das outras:
   ```python
   @api.get("/estatisticas/videos")
   def estatisticas_videos():
       return jsonify(total=repo.contar_videos())
   ```
3. Reinicie a API e teste em `http://127.0.0.1:8000/api/estatisticas/videos`.
4. No front, adicione a chamada em `frontend/api.js` (veja [05_FRONTEND.md](05_FRONTEND.md)).

**Mudou o banco?** Crie um script novo em `database/migracoes/` (veja [03_BANCO_DE_DADOS.md](03_BANCO_DE_DADOS.md#6-como-o-banco-é-criado-e-atualizado-migrações)) e ajuste `repositorio.py`.

---

## 11. Limitações conhecidas

| Limitação | Consequência | Possível evolução |
|---|---|---|
| Sem login | Qualquer pessoa que acesse o endereço usa o sistema | Ok para uso local; necessário antes de publicar na internet |
| Um vídeo processado por vez | Vários envios ficam na fila | Fila com mais trabalhadores (exige mais memória) |
| Conta detecções, não placas únicas | A mesma placa conta várias vezes | Rastreamento (`model.track`) + coluna `track_id` |
| Só a classe `placa` | Semáforos/buracos não são detectados | Treinar um modelo com mais classes |
| Servidor de desenvolvimento do Flask | Adequado para uso local e apresentação | Para produção: `waitress` ou `gunicorn` |
| Sem rota para apagar análises | Precisa apagar pelo banco e pela pasta `storage` | Rota `DELETE /api/analises/<id>` |
