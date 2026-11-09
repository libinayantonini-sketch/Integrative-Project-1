# Banco de dados (MySQL 8) — `projeto_sinalizacoes`

Desenvolvido pela equipe de banco de dados. Esta pasta tem dois tipos de script:

| Pasta | Conteúdo | Quem roda |
|---|---|---|
| `migracoes/` | Criam e alteram a estrutura. Aplicados **em ordem, uma vez** | `python backend/db/criar_banco.py` (ou o Workbench) |
| `exemplos/` | Consultas e revisões de exemplo para estudo/teste | Você, no Workbench |

## Criar o banco

Com o MySQL ligado e o `backend/.env` preenchido (veja o README principal):

```bash
python backend/db/criar_banco.py
```

O comando cria o banco, aplica `01_criar_banco.sql` e `02_integracao.sql` e registra o que já foi
aplicado na tabela `schema_versao`. Pode rodar de novo sem problema.

**Já tinha criado o banco pelo Workbench com o `01`?** Tudo bem: o `01` usa `IF NOT EXISTS`, então o
comando só aplica o `02`. Se você também já tinha rodado o `02` manualmente, registre-o para não ser
aplicado duas vezes:

```sql
USE projeto_sinalizacoes;
CREATE TABLE IF NOT EXISTS schema_versao (arquivo VARCHAR(255) PRIMARY KEY, aplicado_em DATETIME DEFAULT CURRENT_TIMESTAMP);
INSERT IGNORE INTO schema_versao (arquivo) VALUES ('01_criar_banco.sql'), ('02_integracao.sql');
```

## Mudar o banco no futuro

Nunca edite um script já aplicado. Crie um **novo arquivo numerado** em `migracoes/`
(ex.: `03_tabela_ocorrencias.sql`) e rode `python backend/db/criar_banco.py` de novo.

## Tabelas

```
videos 1───1 video_metadados          (local, data, horário e observações digitados no front)
   │1
   ├──n frames                        (só os frames guardados: 1 a cada intervalo_extracao_segundos,
   │      │1                           com a imagem ORIGINAL em frames.imagem)
   │1     └──n deteccoes n───1 processamentos   (caixas em pixels: x_min, y_min, x_max, y_max)
   └──n processamentos                (modelo, status, progresso, vídeo anotado, métricas)
deteccoes 1───1 revisoes              (confirmada / rejeitada / corrigida; sem linha = pendente)
```

### O que o `02_integracao.sql` acrescentou

| Tabela | Alteração | Por quê |
|---|---|---|
| `frames` | `UNIQUE (id_video, numero_frame)` | um frame só aparece uma vez por vídeo |
| `processamentos` | `progresso`, `mensagem_erro` | o front mostra o andamento e o erro |
| `processamentos` | `caminho_video_anotado` | o vídeo com as caixas fica em disco; o banco guarda o caminho |
| `processamentos` | `total_deteccoes`, `frames_com_placa` | métricas exibidas no front |

### Regras de uso combinadas com a API

- Uma **análise** do front = uma linha de `processamentos`.
- Os **vídeos** (original e anotado) ficam em disco (`backend/storage/`); o banco guarda o caminho
  relativo a essa pasta. As **imagens dos frames** ficam no banco (`frames.imagem`), só a original;
  a versão rotulada é desenhada pela API a partir das caixas de `deteccoes`.
- `revisoes`: **não** criar linhas `pendente` antecipadamente. A revisão é gravada quando o usuário
  confirma, rejeita ou corrige (uma por detecção; ver `exemplos/04_revisar_deteccoes.sql`).
- Status: o banco usa `aguardando / processando / concluido / erro`; a API traduz para o front
  (`na_fila / processando / concluida / falhou`).
