# ▶️ Manual de execução — rodando o projeto na sua máquina

Este manual leva você do zero até o sistema funcionando no navegador, em um computador **Windows**.
Leva cerca de **30 minutos na primeira vez** (a maior parte é download). Nas próximas vezes, **1 minuto**.

> Não precisa saber programar para seguir. Copie e cole os comandos exatamente como estão.
> Cada comando fica numa caixa cinza: rode **um de cada vez** e espere terminar.

---

## Sumário

1. [O que vamos instalar](#1-o-que-vamos-instalar)
2. [Instalar o Python](#2-instalar-o-python)
3. [Instalar o MySQL](#3-instalar-o-mysql)
4. [Instalar o Git e baixar o projeto](#4-instalar-o-git-e-baixar-o-projeto)
5. [Abrir o projeto no VS Code](#5-abrir-o-projeto-no-vs-code)
6. [Criar o ambiente Python e instalar as bibliotecas](#6-criar-o-ambiente-python-e-instalar-as-bibliotecas)
7. [Configurar a senha do banco (.env)](#7-configurar-a-senha-do-banco-env)
8. [Criar o banco de dados](#8-criar-o-banco-de-dados)
9. [Ligar o sistema](#9-ligar-o-sistema)
10. [Usando a página](#10-usando-a-página)
11. [Nas próximas vezes](#11-nas-próximas-vezes)
12. [Problemas comuns e soluções](#12-problemas-comuns-e-soluções)
13. [Perguntas frequentes](#13-perguntas-frequentes)

---

## 1. O que vamos instalar

| Programa | Para que serve | Obrigatório? |
|---|---|---|
| **Python 3.10 ou mais recente** | Roda a API e o modelo de detecção | ✅ Sim |
| **MySQL Server 8.4** | Banco de dados | ✅ Sim |
| **Git** | Baixar o projeto do GitHub | ✅ Sim |
| **VS Code** | Editor para abrir o projeto e o terminal | Recomendado |
| MySQL Workbench | Ver as tabelas com uma interface gráfica | Opcional |

**Você NÃO precisa instalar:** FFmpeg (vem junto com as bibliotecas), Node.js (o front é HTML/JS puro),
placa de vídeo / CUDA (o modelo roda no processador) nem servidor web (a própria API entrega as páginas).

**Espaço em disco:** reserve cerca de **3 GB** (a maior parte é o PyTorch, usado pelo modelo).

---

## 2. Instalar o Python

1. Acesse **https://www.python.org/downloads/** e baixe a versão mais recente para Windows.
2. Na primeira tela do instalador, **marque a caixa "Add python.exe to PATH"** (muito importante) e clique em *Install Now*.
3. Para conferir, abra o **PowerShell** (tecla Windows → digite *PowerShell*) e rode:

```bash
python --version
```

Deve aparecer algo como `Python 3.13.x`. Se aparecer *"python não é reconhecido"*, reinstale marcando a caixa do PATH.

---

## 3. Instalar o MySQL

1. Acesse **https://dev.mysql.com/downloads/mysql/**
2. Escolha **Version: 8.4.x LTS** e **Operating System: Microsoft Windows**.
3. Baixe o **Windows (x86, 64-bit), MSI Installer** e, na página seguinte, clique em **"No thanks, just start my download"** (não precisa criar conta).
4. Instale com o tipo **Typical**. No final, deixe marcado **"Run MySQL Configurator"**.

No **MySQL Configurator**, use estas opções:

| Tela | O que fazer |
|---|---|
| Data Directory | Deixe o padrão |
| Type and Networking | *Config Type*: **Development Computer** · TCP/IP marcado · porta **3306**. Pode **desmarcar** "Open Windows Firewall ports" (o banco só é usado no seu computador) |
| Accounts and Roles | **Crie a senha do usuário `root` e anote.** Dica: use só letras e números (ex.: `Vias2026`) |
| Windows Service | Deixe marcado *Start the MySQL Server at System Startup*. O serviço se chamará **MySQL84** |
| Server File Permissions | Deixe o padrão |
| Sample Databases | Deixe **desmarcado** (o projeto não usa) |
| Apply Configuration | Clique em **Execute** e espere todos os itens ficarem com ✔ verde → *Next* → *Finish* |

**Conferir se o MySQL está ligado:** tecla Windows → **Serviços** → procure **MySQL84** → *Status: Em execução*.

> Não crie nenhum banco ou tabela manualmente. O projeto faz isso sozinho no passo 8.

---

## 4. Instalar o Git e baixar o projeto

1. Instale o Git: **https://git-scm.com/download/win** (pode clicar *Next* em tudo).
2. Abra o PowerShell, vá até a pasta onde quer guardar o projeto (ex.: Documentos) e baixe:

```bash
cd $HOME\Documents
```
```bash
git clone https://github.com/libinayantonini-sketch/Integrative-Project-1.git
```

Isso cria a pasta `Documents\Integrative-Project-1`.

> Sem Git? No GitHub, clique em **Code → Download ZIP** e descompacte. Funciona igual,
> mas você não conseguirá enviar alterações depois.

---

## 5. Abrir o projeto no VS Code

1. Instale o VS Code: **https://code.visualstudio.com/** (opcional, mas facilita).
2. No VS Code: **File → Open Folder** → escolha a pasta **`Integrative-Project-1`**
   (a que contém `backend`, `frontend`, `database` e `docs`).
3. Abra o terminal integrado: **Ctrl + `** (a tecla acima do Tab) ou *Terminal → New Terminal*.

> **Todos os comandos a partir daqui são rodados nesse terminal, dentro da pasta `Integrative-Project-1`.**
> Confira: o terminal deve mostrar algo como `PS C:\Users\voce\Documents\Integrative-Project-1>`.

---

## 6. Criar o ambiente Python e instalar as bibliotecas

O **ambiente virtual** (`venv`) é uma pasta com as bibliotecas só deste projeto, sem bagunçar o resto do seu computador.

**6.1 Criar o ambiente** (só na primeira vez):

```bash
python -m venv venv
```

**6.2 Ativar o ambiente:**

```bash
venv\Scripts\activate
```

Deu certo quando aparece **`(venv)`** no começo da linha do terminal.

> **Erro "a execução de scripts foi desabilitada neste sistema"?** É uma proteção do PowerShell.
> Rode o comando abaixo, responda **S** (ou **A**) e ative de novo:
> ```bash
> Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
> ```

**6.3 Instalar as bibliotecas** (só na primeira vez; demora alguns minutos):

```bash
pip install -r backend/api/requirements.txt
```

O que é instalado:

| Biblioteca | Para quê |
|---|---|
| `Flask`, `flask-cors` | A API (servidor web) |
| `python-dotenv` | Lê as configurações do arquivo `backend/.env` |
| `SQLAlchemy`, `PyMySQL`, `cryptography` | Conversar com o MySQL |
| `imageio-ffmpeg` | FFmpeg, para gerar o vídeo com as placas rotuladas |
| `ultralytics` | O modelo YOLO26. Traz junto o **PyTorch**, o **OpenCV** e o `numpy` |

> Avisos amarelos como *"A new release of pip is available"* podem ser ignorados.

**6.4 Conferir:**

```bash
python -c "import ultralytics, flask, pymysql, cv2; print('ok')"
```

Deve aparecer `ok`.

> Se o VS Code perguntar *"We noticed a new environment… use it for the workspace?"*, clique **Yes**.

---

## 7. Configurar a senha do banco (.env)

O projeto precisa saber a senha do **seu** MySQL. Ela fica num arquivo chamado `backend/.env`,
que **nunca vai para o GitHub** (cada pessoa tem o seu).

**7.1 Criar o arquivo a partir do modelo:**

```bash
copy backend\.env.example backend\.env
```

> ⚠️ Use **copy** (copiar), não renomeie. O `.env.example` precisa continuar existindo, porque é o modelo que os colegas usam.

**7.2 Colocar a sua senha:** no VS Code, abra **`backend/.env`** e encontre a linha:

```
DB_URL=mysql+pymysql://root:SUA_SENHA@localhost:3306/projeto_sinalizacoes
```

Troque **somente** a palavra `SUA_SENHA` pela senha que você criou no MySQL. Exemplo com a senha `Vias2026`:

```
DB_URL=mysql+pymysql://root:Vias2026@localhost:3306/projeto_sinalizacoes
```

Salve com **Ctrl + S**.

| Parte da linha | Significado | Pode mudar? |
|---|---|---|
| `root` | usuário do MySQL | só se você usar outro usuário |
| `Vias2026` | **sua senha** | ✅ é o que você muda |
| `@localhost:3306` | o MySQL está no seu computador, porta 3306 | não |
| `/projeto_sinalizacoes` | nome do banco | **não** |

> **Sua senha tem `@`, `#`, `/`, `:` ou `%`?** Esses símbolos têm significado especial nessa linha.
> Escreva-os assim: `@` → `%40` · `#` → `%23` · `/` → `%2F` · `:` → `%3A` · `%` → `%25`.
> Exemplo: a senha `abc@123` fica `root:abc%40123@localhost`. Na linha deve existir **um único `@`** "de verdade": o que vem antes de `localhost`.

---

## 8. Criar o banco de dados

Com o MySQL ligado (passo 3) e o `.env` salvo (passo 7):

```bash
python backend/db/criar_banco.py
```

Resultado esperado:

```
  aplicando:   01_criar_banco.sql
  aplicando:   02_integracao.sql
Banco pronto: projeto_sinalizacoes
```

Esse comando cria o banco `projeto_sinalizacoes` com todas as tabelas. Ele é **seguro para rodar de novo**:
nunca apaga dados, só aplica o que ainda falta (veja [03_BANCO_DE_DADOS.md](03_BANCO_DE_DADOS.md)).

---

## 9. Ligar o sistema

```bash
python backend/api/api.py
```

Na primeira vez pode levar alguns segundos. Espere aparecer:

```
... INFO api: Modelo detector_v1 carregado (classes: ['placa'])

  Abra no navegador: http://127.0.0.1:8000
```

Abra **http://127.0.0.1:8000** no navegador (Chrome, Edge ou Firefox).

> ⚠️ **Deixe esse terminal aberto** enquanto usa o sistema. Fechar o terminal (ou apertar Ctrl + C) desliga o sistema.
> Mensagens que aparecem nele enquanto você usa a página são normais: é o registro do que a API está fazendo.

---

## 10. Usando a página

O menu lateral tem 5 telas. Comece por **Configurações** para conferir se está tudo ligado.

### 10.1 Configurações — conferir a conexão

Mostra **API: Conectada** (verde), o modelo carregado e o intervalo entre frames guardados.
Se aparecer **Desconectada**, o terminal do passo 9 foi fechado ou mostrou um erro.

Aqui você também escolhe quantas linhas aparecem por página nas listas e as **classes** disponíveis
para corrigir uma detecção (padrão: *Placa, Semáforo*; você pode adicionar outras, separadas por vírgula).

### 10.2 Vídeos → Nova análise — enviar um vídeo

1. Clique em **Selecionar arquivo** (ou arraste o vídeo para a área tracejada).
   - Formatos: **MP4, MOV ou WebM** · duração de **10 a 40 segundos** · até **200 MB**.
2. Confira a prévia do vídeo.
3. Preencha **Local** (obrigatório, ex.: *Av. Higienópolis, Centro*), **Data**, **Horário** e **Observações** (opcionais).
4. Clique em **Iniciar análise**.
5. Acompanhe: primeiro a barra de **envio**, depois o estado **Na fila → Processando (xx%)**.
6. Ao terminar aparece **"Análise concluída"** com o link **Ver vídeo anotado e frames**.

> Pode sair da página durante o processamento: ele continua no servidor. A análise aparece depois em **Análises**.
> Tempo aproximado: alguns minutos para um vídeo de 40 s num notebook comum.

### 10.3 Análises — encontrar uma análise

Lista todas as análises com vídeo, local, data, duração, número de detecções e status.
Use a **busca** (por número, nome do vídeo ou local) e os filtros de **status** e **local**. Clique em **Ver** para abrir.

### 10.4 Detalhe da análise — o resultado

| Bloco | O que mostra / permite |
|---|---|
| **Cabeçalho e dados** | Status, nome do vídeo, modelo usado, local, data, horário e duração |
| **Resumo da detecção** | Detecções, frames com placa, frames guardados e o intervalo entre eles |
| **Vídeo com as placas rotuladas** | Vídeo completo com as caixas verdes. Botões **Baixar vídeo anotado**, **Baixar original** e **Consultar frame deste instante** |
| **Detecções** | Lista com tempo, número do frame, classe e confiança. Filtros por classe e por revisão. Botões **Confirmar**, **Rejeitar** e **Corrigir**. Clicar numa detecção abre o frame dela |
| **Consulta de frames** | Ver abaixo |

Se a análise ainda estiver na fila ou processando, a página mostra uma barra de progresso e **se atualiza sozinha** ao terminar.

### 10.5 Consulta de frames — original × rotulado

No fim da página da análise. Há quatro jeitos de abrir um frame:

| Jeito | Como |
|---|---|
| Pelo **número** do frame | Digite em *Nº do frame* (ex.: `61`) e clique **Consultar** |
| Pelo **tempo** do vídeo | Digite em *ou tempo*: `00:12`, `12` ou `12.5` (segundos) e clique **Consultar** |
| Pelo **instante do vídeo** | Pause o vídeo no ponto desejado e clique **Consultar frame deste instante** |
| Pelas **miniaturas** | Clique numa miniatura da faixa no fim da página |

O frame aparece **lado a lado**: à esquerda o **Original** (como foi gravado) e à direita o **Rotulado** (com as caixas das placas).
Abaixo, a tabela com as detecções daquele frame (classe, confiança, posição da caixa em pixels e revisão).
Clique numa imagem para abri-la em tamanho real numa nova aba.

- **◀ Anterior / Próximo ▶** navegam entre os frames guardados.
- **Ver no vídeo** leva o vídeo até aquele instante.
- **Só frames com placa** mostra apenas os frames em que o modelo encontrou algo.
- O endereço da página muda para `…#/analise/7/frame/61`: dá para copiar e mandar para um colega abrir o mesmo frame (na máquina dele, se ele tiver a mesma análise).

> **Por que o frame 75 mostrou o frame 61?** Só 1 frame por segundo fica guardado (frames 1, 31, 61, 91… num vídeo a 30 fps).
> Se você pedir um frame que não foi guardado, o sistema mostra o mais próximo e avisa.

### 10.6 Revisar detecções

Na lista **Detecções**:

| Botão | Quando usar | O que acontece |
|---|---|---|
| **Confirmar** | A IA acertou | Revisão fica *Confirmada* |
| **Rejeitar** | Não era uma placa (falso positivo) | Revisão fica *Rejeitada* |
| **Corrigir** | Era outro objeto | Escolha a classe correta e escreva uma justificativa. Fica *Corrigida* e a lista mostra "IA previu: Placa" |

A resposta original da IA nunca é apagada: a revisão fica guardada à parte (tabela `revisoes`). Dá para mudar de ideia e revisar de novo.

### 10.7 Visão Geral e Relatórios

- **Visão Geral:** totais do período (7, 30 ou 90 dias), gráfico de detecções ao longo do tempo, distribuição por classe e as últimas análises.
- **Relatórios:** filtre por data e local para ver detecções por classe e a situação das revisões. **Exportar CSV** gera uma planilha.

---

## 11. Nas próximas vezes

O MySQL liga sozinho com o Windows. Basta:

1. Abrir a pasta `Integrative-Project-1` no VS Code e o terminal (**Ctrl + `**).
2. Ativar o ambiente e ligar o sistema:

```bash
venv\Scripts\activate
```
```bash
python backend/api/api.py
```

3. Abrir **http://127.0.0.1:8000**.

Para **desligar**: clique no terminal e aperte **Ctrl + C**.

**Quando alguém do grupo mandar atualizações para o GitHub:**

```bash
git pull
```
```bash
pip install -r backend/api/requirements.txt
```
```bash
python backend/db/criar_banco.py
```

Os dois últimos só fazem algo se houver bibliotecas ou mudanças de banco novas; nos outros casos terminam na hora.

---

## 12. Problemas comuns e soluções

| Mensagem ou sintoma | Causa | Solução |
|---|---|---|
| `'python' não é reconhecido` | Python sem PATH | Reinstale o Python marcando *Add python.exe to PATH* e reabra o VS Code |
| `a execução de scripts foi desabilitada` | Proteção do PowerShell | `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` |
| `No module named 'flask'` (ou outro) | Ambiente não ativado | `venv\Scripts\activate` (deve aparecer `(venv)`) |
| `Access denied ... (using password: NO)` | O `backend/.env` não existe ou está sem senha | Confira se o arquivo se chama exatamente `.env` (não `.env.txt`), está na pasta `backend` e foi salvo |
| `Access denied ... (using password: YES)` | Senha errada | Corrija a senha no `backend/.env` (maiúsculas e minúsculas importam) |
| `Can't connect to MySQL server on 'algo@localhost'` | Tem um `@` a mais na linha `DB_URL` | A senha deve ficar entre `root:` e `@localhost`. Se a senha tiver `@`, escreva `%40` |
| `Can't connect to MySQL server on 'localhost'` | MySQL desligado | Serviços do Windows → **MySQL84** → Iniciar |
| `Unknown database 'projeto_sinalizacoes'` | Banco não criado | `python backend/db/criar_banco.py` |
| `Duplicate column name` ao criar o banco | O `02_integracao.sql` já foi rodado à mão pelo Workbench | Veja [03_BANCO_DE_DADOS.md](03_BANCO_DE_DADOS.md#já-criei-o-banco-pelo-workbench) |
| `Modelo não encontrado` | Falta o arquivo do modelo | Confira se existe `backend/modelos/detector_v1.pt` |
| Erro de DLL do `torch` (`WinError 126`, `c10.dll`) | Falta uma biblioteca da Microsoft | Instale o **Microsoft Visual C++ Redistributable (x64)** |
| `Unable to copy ... venvlauncher.exe` | Tentou criar o venv com ele já ativo | Ignore: o ambiente já existe |
| Página não abre / "Desconectada" | Sistema desligado | Veja se o terminal do passo 9 está aberto e sem erro |
| "A duração deve estar entre 10s e 40s" | Limite do sistema | Corte o vídeo, ou mude o limite (veja a pergunta abaixo) |
| Página antiga mesmo depois de atualizar o código | Cache do navegador | **Ctrl + F5** |

Se nada resolver, copie as **últimas linhas do terminal** e mande no grupo (cuidado para não mandar a sua senha).

---

## 13. Perguntas frequentes

**Os meus dados aparecem para os colegas?**
Não. Cada pessoa tem o próprio MySQL e a própria pasta `backend/storage/`. O GitHub guarda o **código** e a
**estrutura** do banco, não os dados. Detalhes em [03_BANCO_DE_DADOS.md](03_BANCO_DE_DADOS.md#7-cada-pessoa-tem-o-seu-banco).

**Onde ficam os vídeos que eu enviei?**
Em `backend/storage/videos/` (original) e `backend/storage/processamentos/` (anotado). Essa pasta não vai para o GitHub.

**Preciso de placa de vídeo?**
Não. Com uma placa NVIDIA o processamento é mais rápido (é usada automaticamente se o PyTorch com CUDA estiver instalado).

**Como aceitar vídeos mais longos?**
Mude em **dois lugares** e reinicie o sistema:
- `backend/.env`: `VIDEO_MIN_S`, `VIDEO_MAX_S` (segundos) e `TAM_MAX_MB`;
- `frontend/api.js`, no início do arquivo: `VIDEO_MIN_S`, `VIDEO_MAX_S` e `TAM_MAX_MB`.

Vídeos mais longos demoram proporcionalmente mais (cada frame passa pelo modelo).

**Como guardar mais frames para consulta?**
No `backend/.env`, diminua `INTERVALO_EXTRACAO_S` (ex.: `0.5` = 2 frames por segundo). Vale para os próximos vídeos enviados.

**Posso usar o Live Server do VS Code para mexer no front?**
Pode. Com a API ligada (passo 9), abra `frontend/index.html` com o Live Server (porta 5500).
O front percebe isso e usa a API em `http://127.0.0.1:8000` automaticamente. Detalhes em [05_FRONTEND.md](05_FRONTEND.md).

**Como vejo os dados direto no banco?**
Pelo MySQL Workbench (conexão *Local instance*, usuário `root`) ou pelos scripts em `database/exemplos/`.
