# Modelo de detecção de placas

| Arquivo | O que é |
|---|---|
| `detector_v1.pt` | Pesos do modelo **YOLO26n** treinado para a classe `placa` (≈5 MB) |
| `detector_v1_info.json` | Versão, classes, `imgsz`, `conf`, `iou` e métricas de teste. A API lê este arquivo |

Gerado pelo notebook [`notebooks/treino_detector_placas_yolo26.ipynb`](../../notebooks/treino_detector_placas_yolo26.ipynb)
(seções 5 e 6), treinado no Google Colab (GPU T4) com o dataset `placas_unificado`
(imagens repetidas removidas e split refeito por grupos de imagens parecidas).

## Métricas no split de teste

| mAP50 | mAP50-95 | Precisão | Recall |
|---|---|---|---|
| 0,957 | 0,765 | 0,957 | 0,931 |

Curvas e matriz de confusão: [`docs/modelo/`](../../docs/modelo/).

> Essas métricas usam imagens do mesmo tipo das de treino (Roboflow). O desempenho real precisa
> ser conferido em vídeos de Londrina (dia, noite, chuva).

## Como a API usa o modelo

`backend/visao/detector.py` carrega o `.pt` uma vez quando a API liga e chama
`detectar(frame)` para cada frame do vídeo. O caminho vem de `MODELO_PESOS` no `backend/.env`.

## Como trocar por um modelo novo

1. Treine com o notebook mudando `MODEL_VERSION` (ex.: `detector_v2`).
2. Copie `detector_v2.pt` e `detector_v2_info.json` para esta pasta.
3. No `backend/.env`: `MODELO_PESOS=modelos/detector_v2.pt` e reinicie a API.

Cada análise registra em `processamentos.nome_modelo` / `versao_modelo` qual modelo foi usado,
então dá para comparar versões depois. Se um modelo futuro passar de 100 MB, publique-o em
*GitHub Releases* em vez de versionar o arquivo.
