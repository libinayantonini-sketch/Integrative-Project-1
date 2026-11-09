-- =============================================================
-- ARQUIVO 2: INTEGRAÇÃO COM A API E O MODELO
-- Acrescenta ao banco da equipe (01_criar_banco.sql) o que o fluxo
-- upload -> processamento -> consulta precisa. Nenhuma tabela é recriada.
-- =============================================================
USE projeto_sinalizacoes;

-- FRAMES: cada frame aparece uma única vez por vídeo.
-- (Só os frames amostrados, 1 a cada intervalo_extracao_segundos, são guardados,
--  sempre com a imagem ORIGINAL em frames.imagem.)
ALTER TABLE frames
    ADD UNIQUE KEY uq_frames_video_numero (id_video, numero_frame);

-- PROCESSAMENTOS: acompanhamento e resultado da análise.
ALTER TABLE processamentos
    ADD COLUMN progresso             DECIMAL(4,3) NOT NULL DEFAULT 0 AFTER status,  -- 0 a 1
    ADD COLUMN mensagem_erro         TEXT         NULL AFTER progresso,             -- preenchida se status = 'erro'
    ADD COLUMN caminho_video_anotado VARCHAR(500) NULL AFTER mensagem_erro,         -- vídeo com as caixas desenhadas
    ADD COLUMN total_deteccoes       INT          NULL AFTER caminho_video_anotado, -- detecções nos frames guardados
    ADD COLUMN frames_com_placa      INT          NULL AFTER total_deteccoes,       -- frames guardados com >= 1 placa
    ADD INDEX idx_processamentos_criado (criado_em);
