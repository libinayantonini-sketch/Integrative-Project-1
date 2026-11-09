# 🚦 Monitoramento de Vias Públicas de Londrina

![Status](https://img.shields.io/badge/status-em%20desenvolvimento-yellow)

Sistema que recebe vídeos gravados no trânsito de Londrina, detecta **placas de trânsito** com visão
computacional (YOLO26) e permite consultar o vídeo com as placas rotuladas, comparar cada frame
original com a versão rotulada e revisar as detecções da IA.

Projeto Integrador de Visão Computacional — Universidade Tecnológica Federal do Paraná (UTFPR),
campus Londrina, sob orientação do professor Danilo.

---

## 📋 Sumário

- [Como funciona](#-como-funciona)
- [Documentação](#-documentação)
- [Estrutura do repositório](#-estrutura-do-repositório)
- [Como executar (Windows)](#-como-executar-windows)
- [Usando o sistema](#-usando-o-sistema)
- [Problemas comuns](#-problemas-comuns)
- [Tecnologias](#️-tecnologias)
- [Equipe](#-equipe)
- [Como contribuir](#-como-contribuir)

---

## 🔄 Como funciona

```mermaid
flowchart LR
    U(["👤 Usuário"]) --> F["🖥️ Front<br/>frontend/"]
    F -- "HTTP / JSON" --> A["🔌 API Flask<br/>backend/api/"]
    A --> M["🧠 Modelo YOLO26<br/>backend/modelos/detector_v1.pt"]
    A -- SQL --> D[("🐬 MySQL<br/>projeto_sinalizacoes")]
    A --> S[("💾 Vídeos<br/>backend/storage/")]
```

1. O usuário envia um vídeo (10–40 s) com o **local**, a **data** e o **horário** da gravação.
2. A API cadastra o vídeo no banco e o coloca na fila de processamento.
3. Cada frame passa pelo modelo. A API grava o **vídeo anotado** e guarda no banco
   **1 frame por segundo** (imagem original) com as **detecções** dele.
4. O front mostra o progresso e, ao terminar, o vídeo com as placas rotuladas, a consulta de frames
   (original × rotulado) e a lista de detecções para revisão.

## 📚 Documentação

| Documento | Conteúdo |
|---|---|
| [🗺️ Arquitetura visual](docs/01_ARQUITETURA_VISUAL.md) | Como as partes se encaixam, com diagramas — **comece por aqui** |
| [▶️ Manual de execução](docs/02_MANUAL_DE_EXECUCAO.md) | Passo a passo completo para rodar na sua máquina e usar a página |
| [🐬 Banco de dados](docs/03_BANCO_DE_DADOS.md) | Tabelas, relacionamentos e o que acontece no banco durante o uso |
| [🔌 API](docs/04_API.md) | Todas as rotas, formatos JSON, modelo e pipeline |
| [🖥️ Front-end](docs/05_FRONTEND.md) | As telas e como conversam com a API |

## 📁 Estrutura do repositório

```
├── frontend/              # Interface web (HTML, CSS, JS) — servida pela própria API
├── backend/
│   ├── api/               # api.py (rotas) e requirements.txt
│   ├── db/                # conexão MySQL, consultas e criar_banco.py
│   ├── visao/             # modelo (detector.py), vídeo, pipeline e fila de processamento
│   ├── modelos/           # detector_v1.pt (modelo treinado) + info
│   ├── storage/           # vídeos enviados e anotados (fora do Git)
│   ├── config.py
│   └── .env.example       # modelo do arquivo de configuração
├── database/
│   ├── migracoes/         # scripts que criam/alteram o banco (aplicados em ordem)
│   └── exemplos/          # consultas e revisões de exemplo
├── notebooks/             # treino do modelo no Google Colab
└── docs/                  # documentação (arquitetura, manual, banco, API, front) e métricas do modelo
```

## 🚀 Como executar (Windows)

Tudo roda na sua máquina: **MySQL** + **API** (que também entrega o front).
Abaixo está o resumo; o passo a passo completo, com as opções de configuração e a solução de problemas,
está no [**Manual de execução**](docs/02_MANUAL_DE_EXECUCAO.md).

### Pré-requisitos

- [Python 3.10 ou mais recente](https://www.python.org/downloads/) (marque *Add Python to PATH* na instalação)
- [MySQL Server 8.4 LTS](https://dev.mysql.com/downloads/mysql/) (*MSI Installer* para Windows). Anote a senha do usuário `root`.
- Git

Não é preciso GPU nem instalar FFmpeg (vem junto com as dependências).

### 1. Clonar e criar o ambiente Python

```bash
git clone https://github.com/libinayantonini-sketch/Integrative-Project-1.git
```
```bash
cd Integrative-Project-1
```
```bash
python -m venv venv
```
```bash
venv\Scripts\activate
```
```bash
pip install -r backend/api/requirements.txt
```

A primeira instalação baixa o PyTorch e demora alguns minutos.
(Linux/macOS: `source venv/bin/activate`.)

### 2. Configurar

Copie `backend/.env.example` para `backend/.env` e troque `SUA_SENHA` pela senha do seu MySQL:

```bash
copy backend\.env.example backend\.env
```

```
DB_URL=mysql+pymysql://root:SUA_SENHA@localhost:3306/projeto_sinalizacoes
```

### 3. Criar o banco (só na primeira vez)

Com o MySQL ligado:

```bash
python backend/db/criar_banco.py
```

### 4. Ligar a API

```bash
python backend/api/api.py
```

Deixe esse terminal aberto e acesse **http://127.0.0.1:8000** no navegador.
Em **Configurações**, o status deve aparecer como **Conectada**.

> Prefere editar o front com o Live Server do VS Code? Também funciona: com a API ligada,
> abra `frontend/index.html` pelo Live Server (porta 5500) — o front usa `http://127.0.0.1:8000/api` sozinho.

## 🖥️ Usando o sistema

| Tela | O que faz |
|---|---|
| **Vídeos → Nova análise** | Envia o vídeo com local, data, horário e observações e mostra o progresso do processamento |
| **Análises** | Lista as análises com busca e filtros por status e local |
| **Detalhe da análise** | Vídeo com as placas rotuladas (download do anotado e do original), resumo e lista de detecções com **Confirmar / Rejeitar / Corrigir** |
| ↳ **Consulta de frames** | Busca por **número do frame** ou **tempo** (ou pelas miniaturas) e mostra lado a lado o frame **original** e o **rotulado**, com as detecções daquele frame. O botão *Consultar frame deste instante* abre o frame do ponto em que o vídeo está |
| **Visão geral / Relatórios** | Totais, gráfico por período, detecções por classe e situação das revisões (exporta CSV) |

Só 1 frame por segundo fica guardado para consulta (configurável em `INTERVALO_EXTRACAO_S`);
se você pedir um frame que não foi guardado, o sistema mostra o mais próximo.

## 🧯 Problemas comuns

| Mensagem | Solução |
|---|---|
| `Não foi possível conectar ao MySQL` | Ligue o MySQL (Serviços do Windows → MySQL80 → Iniciar) e confira usuário/senha no `backend/.env` |
| `Unknown database 'projeto_sinalizacoes'` | Rode `python backend/db/criar_banco.py` |
| `Modelo não encontrado` | Confira se `backend/modelos/detector_v1.pt` existe |
| `ModuleNotFoundError` | Ative o venv (`venv\Scripts\activate`) antes de rodar |
| Front mostra *Desconectada* | A API não está rodando, ou o front foi aberto em outro endereço |

## 🛠️ Tecnologias

- **Visão computacional:** [Ultralytics YOLO26](https://docs.ultralytics.com/), OpenCV, FFmpeg (imageio-ffmpeg)
- **API:** Python, Flask
- **Banco de dados:** MySQL 8, SQLAlchemy, PyMySQL
- **Front-end:** HTML5, CSS3, JavaScript (sem frameworks)
- **Treino:** Google Colab (GPU T4)

## 👥 Equipe

| Integrante | GitHub |
|------------|--------|
| João Pedro Magri | [@Jpmagri-07](https://github.com/Jpmagri-07) |
| Libina | [@libinayantonini-sketch](https://github.com/libinayantonini-sketch) |
| Larissa | — |
| Vitória | — |
| Clara | — |
| Ana Clara | — |

Front-end desenvolvido originalmente em [luizfelipeyg-crypto/frontend_monitoramento_vias](https://github.com/luizfelipeyg-crypto/frontend_monitoramento_vias).
Banco de dados desenvolvido pela equipe de banco de dados (`database/`).

## 🤝 Como contribuir

1. Crie uma *branch* a partir da `main`:
   ```bash
   git checkout -b feature/nome-da-funcionalidade
   ```
2. Faça suas alterações e registre os *commits*:
   ```bash
   git commit -m "Descrição clara da alteração"
   ```
3. Envie para o repositório:
   ```bash
   git push origin feature/nome-da-funcionalidade
   ```
4. Abra um **Pull Request** descrevendo o que foi feito.

**Boas práticas do grupo:**
- Não suba o `backend/.env` (tem senha) nem vídeos (`backend/storage/`).
- Mudanças no banco: novo script numerado em `database/migracoes/`, nunca edite um já aplicado.
- Mudanças em rotas, tabelas ou telas: atualize o documento correspondente em `docs/` no mesmo PR.

---

<p align="center">Desenvolvido por estudantes para a cidade de Londrina – PR</p>
