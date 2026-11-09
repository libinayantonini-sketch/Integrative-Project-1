# 🗺️ Arquitetura visual do projeto

Este documento mostra, com desenhos, **como as três partes do projeto se encaixam**:
o **front-end** (as telas), o **back-end** (a API + o modelo de visão computacional) e o **banco de dados** (MySQL).

> Os diagramas são desenhados automaticamente pelo GitHub (Mermaid).
> Se você abrir este arquivo no VS Code e não aparecerem os desenhos, instale a extensão
> *Markdown Preview Mermaid Support* e use **Ctrl + Shift + V**.

---

## 1. Visão geral em uma frase

> O usuário envia um vídeo pelo **front**; a **API** guarda o vídeo, passa cada frame pelo **modelo**,
> grava os resultados no **banco** e devolve ao front o **vídeo com as placas rotuladas** e os **frames para consulta**.

---

## 2. As peças e quem conversa com quem

```mermaid
flowchart LR
    U(["👤 Usuário"])

    subgraph NAV["Navegador"]
        FRONT["🖥️ FRONT-END<br/>frontend/<br/>HTML + CSS + JavaScript"]
    end

    subgraph BACK["Back-end — Python (http://127.0.0.1:8000)"]
        API["🔌 API Flask<br/>backend/api/api.py"]
        FILA["⏳ Fila de processamento<br/>backend/visao/fila.py"]
        PIPE["⚙️ Pipeline<br/>backend/visao/pipeline.py"]
        MOD["🧠 Modelo YOLO26<br/>backend/visao/detector.py<br/>modelos/detector_v1.pt"]
        REPO["🗂️ Consultas SQL<br/>backend/db/repositorio.py"]
    end

    DISCO[("💾 Disco<br/>backend/storage/<br/>vídeos original e anotado")]
    DB[("🐬 MySQL<br/>projeto_sinalizacoes")]

    U --> FRONT
    FRONT -- "HTTP / JSON" --> API
    API -- "JSON, vídeos e imagens" --> FRONT
    API --> FILA --> PIPE
    PIPE -- "1 frame" --> MOD
    MOD -- "lista de caixas" --> PIPE
    API --> REPO
    PIPE --> REPO
    REPO -- "SQL" --> DB
    PIPE -- "grava vídeos" --> DISCO
    API -- "lê vídeos" --> DISCO
```

**Três regras que explicam quase tudo:**

| Regra | Por quê |
|---|---|
| O **front nunca fala com o banco** | Só a API conhece a senha do banco. O front pede tudo à API |
| O **modelo não conhece o banco nem o front** | Ele só recebe uma imagem e devolve as caixas encontradas. Quem decide o que fazer com isso é o pipeline |
| A **API é o centro** | É a única peça ligada a todas as outras. Ela também entrega as páginas do front, por isso tudo funciona no mesmo endereço |

---

## 3. O caminho de um vídeo, do envio ao resultado

```mermaid
sequenceDiagram
    autonumber
    actor U as Usuário
    participant F as Front
    participant A as API
    participant B as MySQL
    participant P as Pipeline
    participant M as Modelo
    participant D as Disco

    U->>F: escolhe o vídeo e preenche local, data e horário
    F->>A: POST /api/analises (vídeo + dados)
    A->>D: salva o arquivo enviado
    A->>B: INSERT videos, video_metadados, processamentos (aguardando)
    A-->>F: 201 { id }
    A->>P: coloca o id na fila

    loop a cada 2 segundos
        F->>A: GET /api/analises/{id}/status
        A->>B: lê status e progresso
        A-->>F: { status, progresso }
    end

    P->>B: status = processando
    P->>D: converte para original.mp4 (H.264)
    loop para CADA frame do vídeo
        P->>M: frame
        M-->>P: caixas [{classe, confiança, x_min, y_min, x_max, y_max}]
        P->>D: escreve o frame com as caixas no anotado.mp4
        opt 1 frame por segundo
            P->>B: INSERT frames (imagem original) e deteccoes (caixas)
        end
    end
    P->>B: status = concluido + métricas

    F->>A: GET /api/analises/{id}
    A-->>F: dados + endereço do vídeo anotado
    F->>A: GET /api/analises/{id}/video?versao=anotado
    A->>D: lê anotado.mp4
    A-->>F: vídeo com as placas rotuladas
    U->>F: consulta o frame 61
    F->>A: GET /api/analises/{id}/frames/61/imagem?versao=original e versao=anotado
    A->>B: lê a imagem e as caixas do frame
    A-->>F: imagem original e imagem rotulada (desenhada na hora)
```

---

## 4. A vida de uma análise (status)

```mermaid
stateDiagram-v2
    [*] --> na_fila: vídeo enviado
    na_fila --> processando: a fila chega nele
    processando --> concluida: todos os frames analisados
    processando --> falhou: erro (vídeo corrompido, disco cheio...)
    processando --> na_fila: API foi desligada no meio (retoma ao ligar)
    concluida --> [*]
    falhou --> [*]
```

| No front | No banco (`processamentos.status`) | O que significa |
|---|---|---|
| Na fila | `aguardando` | Esperando outro vídeo terminar (os vídeos são processados um de cada vez) |
| Processando | `processando` | O modelo está analisando; `progresso` vai de 0 a 1 |
| Concluída | `concluido` | Vídeo anotado e frames prontos para consulta |
| Falhou | `erro` | A mensagem fica em `processamentos.mensagem_erro` |

---

## 5. Onde cada informação fica guardada

```mermaid
flowchart TB
    subgraph MYSQL["🐬 MySQL — projeto_sinalizacoes"]
        direction LR
        T1["videos<br/>nome, duração, fps, resolução,<br/>caminho do original"]
        T2["video_metadados<br/>local, data, horário, observações"]
        T3["processamentos<br/>modelo, status, progresso,<br/>caminho do anotado, métricas"]
        T4["frames<br/>nº do frame, tempo,<br/>IMAGEM ORIGINAL (1 por segundo)"]
        T5["deteccoes<br/>classe, confiança,<br/>caixa em pixels"]
        T6["revisoes<br/>confirmada / rejeitada / corrigida"]
    end
    subgraph STORAGE["💾 backend/storage/"]
        direction LR
        V1["videos/&lt;pasta&gt;/original.mp4"]
        V2["processamentos/&lt;id&gt;/anotado.mp4"]
    end
    subgraph MODELO["🧠 backend/modelos/"]
        W["detector_v1.pt<br/>detector_v1_info.json"]
    end
    T1 -. "caminho" .-> V1
    T3 -. "caminho" .-> V2
```

| Informação | Onde fica | Observação |
|---|---|---|
| Vídeo original e vídeo anotado | Disco (`backend/storage/`) | O banco guarda só o **caminho** |
| Imagem original dos frames de consulta | Banco (`frames.imagem`) | Só 1 frame por segundo de vídeo |
| Imagem **rotulada** dos frames | **Não é guardada** | A API desenha as caixas na hora, usando a tabela `deteccoes` |
| Caixas, classe, confiança | Banco (`deteccoes`) | Em pixels do frame original |
| Revisões humanas | Banco (`revisoes`) | A resposta da IA nunca é alterada |
| Modelo treinado | Disco (`backend/modelos/`) | Vai para o GitHub (≈5 MB) |

---

## 6. Por que só 1 frame por segundo vai para o banco?

```mermaid
flowchart LR
    V["🎞️ Vídeo de 40 s a 30 fps<br/>= 1.200 frames"] --> M["🧠 Modelo analisa<br/>TODOS os 1.200"]
    M --> A["🎬 anotado.mp4<br/>1.200 frames com caixas<br/>(disco)"]
    M --> S{"É frame de<br/>1 em 1 segundo?"}
    S -- "sim (40 frames)" --> B[("🐬 banco:<br/>imagem original<br/>+ caixas")]
    S -- "não (1.160 frames)" --> X["só vão para o vídeo"]
```

Guardar os 1.200 frames ocuparia ≈250 MB por vídeo no banco e tornaria a revisão impraticável.
Com 1 por segundo, são ≈40 imagens (alguns MB), suficientes para **consultar** e **revisar**.
O intervalo pode ser mudado em `INTERVALO_EXTRACAO_S` no `backend/.env`.

> As métricas mostradas (ex.: "Detecções: 41") contam **detecções nos frames guardados**,
> e não placas diferentes: a mesma placa aparece em vários frames seguidos.

---

## 7. Organização das pastas

```mermaid
flowchart TB
    R["📁 Integrative-Project-1"]
    R --> FE["📁 frontend/<br/>telas do sistema"]
    R --> BE["📁 backend/"]
    R --> DBF["📁 database/<br/>scripts SQL"]
    R --> NB["📁 notebooks/<br/>treino do modelo (Colab)"]
    R --> DOC["📁 docs/<br/>esta documentação"]
    BE --> BA["📁 api/<br/>api.py — rotas<br/>requirements.txt"]
    BE --> BD["📁 db/<br/>conexao.py · repositorio.py · criar_banco.py"]
    BE --> BV["📁 visao/<br/>detector.py · pipeline.py · video.py · fila.py"]
    BE --> BM["📁 modelos/<br/>detector_v1.pt"]
    BE --> BS["📁 storage/<br/>vídeos (fora do Git)"]
    BE --> BC["config.py · .env.example"]
    DBF --> DM["📁 migracoes/<br/>01_criar_banco.sql · 02_integracao.sql"]
    DBF --> DE["📁 exemplos/<br/>consultas e revisões de exemplo"]
```

---

## 8. Quem cuida de quê

| Parte | Equipe | Arquivos principais | Documento |
|---|---|---|---|
| Telas | Front-end | `frontend/` | [05_FRONTEND.md](05_FRONTEND.md) |
| Rotas, regras e integração | Back-end | `backend/api/`, `backend/db/` | [04_API.md](04_API.md) |
| Modelo e processamento do vídeo | Visão computacional | `backend/visao/`, `backend/modelos/`, `notebooks/` | [04_API.md](04_API.md#7-o-modelo-e-o-pipeline) |
| Estrutura dos dados | Banco de dados | `database/` | [03_BANCO_DE_DADOS.md](03_BANCO_DE_DADOS.md) |
| Rodar tudo na sua máquina | Todos | — | [02_MANUAL_DE_EXECUCAO.md](02_MANUAL_DE_EXECUCAO.md) |

**O "contrato" entre as equipes** são as rotas da API e os formatos JSON descritos em [04_API.md](04_API.md).
Se uma equipe muda algo nesse contrato, avisa as outras e atualiza a documentação no mesmo Pull Request.
