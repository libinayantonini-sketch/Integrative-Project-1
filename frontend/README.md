# Monitoramento de Vias Públicas

**Front-End do sistema de Detecção Inteligente de Sinalizações Viárias**

Projeto Integrador desenvolvido no contexto acadêmico da UTFPR, com o objetivo de fornecer uma interface para monitoramento de vias públicas, visualização de análises de vídeos e acompanhamento de detecções de sinalizações viárias.

## Sobre o projeto

O sistema propõe uma plataforma de monitoramento que permite acompanhar análises de vídeos de vias públicas, visualizar sinalizações detectadas e consultar informações relacionadas aos resultados do processamento.

O Front-End foi desenvolvido para oferecer uma interface administrativa intuitiva, organizada e responsiva, facilitando o acesso às informações e a interação com os recursos do sistema.

## Objetivos

- Desenvolver uma interface para monitoramento e análise de vídeos de vias públicas.
- Facilitar a visualização de sinalizações viárias detectadas.
- Apresentar indicadores, gráficos e relatórios relacionados às análises.
- Permitir a revisão e classificação das detecções.
- Integrar a interface com a API responsável pelo processamento e armazenamento dos dados.

## Tecnologias utilizadas

- **HTML5** — estrutura das páginas.
- **CSS3** — estilização, layout e responsividade.
- **JavaScript** — interatividade, navegação e manipulação dos dados.
- **Fetch API** — comunicação com o back-end.
- **XMLHttpRequest** — envio de vídeos com acompanhamento do progresso.
- **Google Fonts — IBM Plex Sans** — tipografia da interface.
- **Git e GitHub** — versionamento e hospedagem do código-fonte.

##  Funcionalidades

###  Visão geral
- Indicadores resumidos das análises e detecções.
- Visualização de gráficos e distribuição por classe.
- Listagem de análises recentes.

###  Análises
- Consulta das análises registradas.
- Pesquisa por vídeo, identificação ou localização.
- Filtros por status e localização.
- Paginação dos resultados.

### Envio de vídeos
- Seleção de arquivos e suporte a arrastar e soltar.
- Validação de formato, tamanho e duração.
- Informações sobre a localização do vídeo.
- Acompanhamento do progresso real do envio.
- Acesso aos detalhes da análise após o envio, conforme a resposta da API.

###  Detalhes e revisão
- Visualização dos metadados da análise.
- Exibição das detecções e dos respectivos níveis de confiança.
- Reprodução do vídeo, quando disponível.
- Visualização de caixas delimitadoras sobre o vídeo, quando os dados necessários são fornecidos.
- Recursos para confirmar, rejeitar ou corrigir detecções, conforme suporte do back-end.
- Consulta de ocorrências e prioridades.

###  Relatórios
- Consulta de indicadores e resultados agregados.
- Filtros para consulta dos dados.
- Exportação de informações em formato CSV.

### Configurações
- Preferências de paginação.
- Configuração de classes utilizadas pela interface.
- Verificação do estado de conexão com a API.

> **Observação:** a disponibilidade efetiva de cada funcionalidade depende da implementação correspondente e da integração com o back-end.

##  Estrutura do projeto

```text
frontend/
├── index.html   estrutura principal da aplicação
├── style.css    estilos e responsividade
├── api.js       configuração e comunicação com a API (única parte que fala com o back-end)
├── app.js       navegação, páginas e interações
└── README.md
```

##  Como executar

O front faz parte do repositório **Integrative-Project-1** e é entregue pela própria API.
Siga o passo a passo do README principal e acesse **http://127.0.0.1:8000**.

Para desenvolver o front com o **Live Server** do VS Code: deixe a API ligada e abra
`frontend/index.html` pelo Live Server (porta 5500). O `api.js` detecta isso e usa
`http://127.0.0.1:8000/api` automaticamente.

##  Integração com o back-end

- Rotas e formatos: [`docs/04_API.md`](../docs/04_API.md). Detalhes das telas: [`docs/05_FRONTEND.md`](../docs/05_FRONTEND.md).
- A URL base é escolhida em `CONFIG.API_URL` (`api.js`): `/api` quando o front é servido pela API,
  `http://127.0.0.1:8000/api` no Live Server, ou o valor de `window.API_URL` se for definido antes de `api.js`.
- Vídeos e imagens de frames vêm da API (`/api/analises/<id>/video` e `/api/analises/<id>/frames/<n>/imagem`).

### Alterações da versão integrada (v0.2.0)

- Acompanhamento do processamento (progresso) após o envio e na página da análise.
- Página da análise com o **vídeo com as placas rotuladas** e download do anotado e do original.
- **Consulta de frames**: por número, por tempo, pelo instante atual do vídeo ou pelas miniaturas,
  com o frame **original** e o **rotulado** lado a lado e as detecções daquele frame.
- Detecções com o número do frame; clicar numa detecção abre o frame correspondente.
- Indicadores ajustados ao modelo atual (placas): análises, detecções, frames com placa, revisões pendentes.
- Seção de ocorrências e prioridades removida (o modelo atual não detecta ocorrências).

##  Desenvolvimento

Este repositório concentra o código-fonte do **Front-End** do sistema.

## Contexto acadêmico

**Projeto Integrador — UTFPR**

**Tema:** Monitoramento de Vias Públicas e Detecção Inteligente de Sinalizações Viárias.

