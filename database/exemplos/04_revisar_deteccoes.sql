-- =============================================================
-- ARQUIVO 4: REVISÃO HUMANA
-- Simula uma pessoa conferindo o trabalho da IA.
--
-- Mudança em relação à versão anterior: as linhas de revisão NÃO são criadas
-- antecipadamente como 'pendente'. Detecção sem linha em revisoes = pendente.
-- Por isso a revisão é gravada com INSERT ... ON DUPLICATE KEY UPDATE
-- (cria a revisão ou altera a existente; revisoes.id_deteccao é UNIQUE).
-- A API faz exatamente isso quando o usuário clica em Confirmar/Rejeitar/Corrigir.
-- =============================================================
USE projeto_sinalizacoes;

-- Detecção 1: a IA acertou
INSERT INTO revisoes (id_deteccao, status, data_revisao)
VALUES (1, 'confirmada', NOW())
ON DUPLICATE KEY UPDATE status = VALUES(status), data_revisao = VALUES(data_revisao);

-- Detecção 2: a IA errou, não havia placa
INSERT INTO revisoes (id_deteccao, status, comentario, data_revisao)
VALUES (2, 'rejeitada', 'era um outdoor', NOW())
ON DUPLICATE KEY UPDATE status = VALUES(status), comentario = VALUES(comentario),
                        data_revisao = VALUES(data_revisao);

-- Detecção 3: era outro tipo de objeto
INSERT INTO revisoes (id_deteccao, status, classe_corrigida, data_revisao)
VALUES (3, 'corrigida', 'Semáforo', NOW())
ON DUPLICATE KEY UPDATE status = VALUES(status), classe_corrigida = VALUES(classe_corrigida),
                        data_revisao = VALUES(data_revisao);

-- Ver o resultado: todas as detecções com o status da revisão (sem linha = pendente)
SELECT d.id_deteccao, d.classe_prevista, d.confianca,
       COALESCE(r.status, 'pendente') AS revisao, r.classe_corrigida, r.comentario
FROM deteccoes d
LEFT JOIN revisoes r ON r.id_deteccao = d.id_deteccao
ORDER BY d.id_deteccao;
