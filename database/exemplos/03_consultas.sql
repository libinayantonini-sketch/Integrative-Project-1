USE projeto_sinalizacoes;

-- 1. Mostre os vídeos
SELECT * FROM videos;

-- 2. Mostre o que a IA encontrou
SELECT * FROM deteccoes;

-- 3. Mostre as revisões feitas pelas pessoas
SELECT * FROM revisoes;

-- 4. Só os semáforos com 70% de certeza ou mais
SELECT * FROM deteccoes
WHERE classe_prevista = 'semaforo' AND confianca >= 0.70;

-- 5. Só as revisões que ainda estão pendentes
SELECT * FROM revisoes
WHERE status = 'pendente';


-- Tamanho dos bytes armazenados, sem carregar as imagens na listagem.
SELECT id_frame, id_video, numero_frame, tipo_imagem,
       OCTET_LENGTH(imagem) AS tamanho_bytes
FROM frames;


-- =============================================================
-- Consultas usadas pela API (backend/db/repositorio.py)
-- =============================================================

-- 6. Lista de análises (tela "Análises" do front)
SELECT p.id_processamento AS id, v.nome_arquivo AS video, m.local_gravacao AS local,
       m.data_gravacao AS data, m.horario_gravacao AS horario, v.duracao_segundos AS duracao,
       p.status, p.progresso, COALESCE(p.total_deteccoes, 0) AS deteccoes
FROM processamentos p
JOIN videos v               ON v.id_video = p.id_video
LEFT JOIN video_metadados m ON m.id_video = p.id_video
ORDER BY p.criado_em DESC;

-- 7. Detecções de uma análise, com a revisão (sem linha em revisoes = pendente)
SELECT d.id_deteccao, f.numero_frame, f.tempo_segundos, d.classe_prevista, d.confianca,
       d.x_min, d.y_min, d.x_max, d.y_max,
       COALESCE(r.status, 'pendente') AS revisao, r.classe_corrigida, r.comentario
FROM deteccoes d
JOIN frames f        ON f.id_frame = d.id_frame
LEFT JOIN revisoes r ON r.id_deteccao = d.id_deteccao
WHERE d.id_processamento = 1
ORDER BY f.numero_frame, d.id_deteccao;

-- 8. Frames guardados de uma análise e quantas placas cada um tem (sem carregar as imagens)
SELECT f.numero_frame, f.tempo_segundos, COUNT(d.id_deteccao) AS qtd_placas
FROM processamentos p
JOIN frames f         ON f.id_video = p.id_video
LEFT JOIN deteccoes d ON d.id_frame = f.id_frame AND d.id_processamento = p.id_processamento
WHERE p.id_processamento = 1
GROUP BY f.id_frame, f.numero_frame, f.tempo_segundos
ORDER BY f.numero_frame;
