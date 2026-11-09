# 📚 Documentação do projeto

Comece por aqui. Cada documento foi escrito para ser entendido por **qualquer integrante**,
de qualquer equipe (front-end, back-end/visão computacional ou banco de dados).

| # | Documento | Leia se você quer… |
|---|---|---|
| 1 | [🗺️ Arquitetura visual](01_ARQUITETURA_VISUAL.md) | Entender **como as partes se encaixam**, com diagramas (comece por este) |
| 2 | [▶️ Manual de execução](02_MANUAL_DE_EXECUCAO.md) | **Rodar o sistema na sua máquina** e aprender a usar a página |
| 3 | [🐬 Banco de dados](03_BANCO_DE_DADOS.md) | Saber o que cada tabela guarda e **o que acontece no banco** durante o uso |
| 4 | [🔌 API](04_API.md) | Conhecer **todas as rotas**, os formatos JSON, o modelo e o pipeline |
| 5 | [🖥️ Front-end](05_FRONTEND.md) | Entender **as telas** e como elas conversam com a API |

**Sugestão de leitura por equipe:**

| Equipe | Ordem |
|---|---|
| Todos | 1 → 2 |
| Front-end | 1 → 2 → 5 → 4 (seções 5 e 6) |
| Back-end / visão computacional | 1 → 2 → 4 → 3 |
| Banco de dados | 1 → 2 → 3 → 4 (seção 6) |

**Outros materiais**

- [`modelo/`](modelo/) — gráficos de desempenho do modelo (curva precisão × recall, F1, matriz de confusão, exemplo de predição).
- [`../backend/modelos/README.md`](../backend/modelos/README.md) — sobre o modelo treinado e como trocá-lo.
- [`../database/README.md`](../database/README.md) — resumo da pasta de scripts SQL.
- [`../notebooks/`](../notebooks/) — notebook de treino do modelo (Google Colab).

> **Mantendo a documentação viva:** quem mudar uma rota, uma tabela ou uma tela atualiza o documento
> correspondente **no mesmo Pull Request**.
