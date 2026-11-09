
CREATE DATABASE IF NOT EXISTS projeto_sinalizacoes;
USE projeto_sinalizacoes;


-- -------------------------------------------------------------
-- TABELA 1: videos
-- Cada linha é um vídeo enviado para o sistema.
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS videos (
    id_video         INT AUTO_INCREMENT PRIMARY KEY,     -- número único, criado sozinho
    nome_arquivo     VARCHAR(255) NOT NULL,              -- ex.: via_exemplo.mp4
    origem           VARCHAR(150) DEFAULT 'upload',      -- de onde veio o vídeo
    caminho_arquivo  VARCHAR(500) NOT NULL,              -- onde o arquivo está salvo
    duracao_segundos DECIMAL(10,3) NOT NULL,             -- duração do vídeo
    fps              DECIMAL(8,3) NOT NULL,              -- quadros por segundo
    largura          INT NOT NULL,                       -- em pixels
    altura           INT NOT NULL,                       -- em pixels
    data_envio       DATETIME DEFAULT CURRENT_TIMESTAMP  -- preenchida sozinha
);


-- -------------------------------------------------------------
-- TABELA 2: video_metadados
-- Informações extras de cada vídeo, preenchidas pela tela do sistema.
-- Cada vídeo tem no máximo UMA linha aqui (relação 1 para 1).
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS video_metadados (
    id_video         INT PRIMARY KEY,                    -- mesmo número do vídeo
    local_gravacao   VARCHAR(150) NOT NULL,
    data_gravacao    DATE,
    horario_gravacao TIME,
    observacoes      TEXT,
    FOREIGN KEY (id_video) REFERENCES videos(id_video) ON DELETE CASCADE
);


-- -------------------------------------------------------------
-- TABELA 3: frames
-- "Fotos" tiradas do vídeo. Um vídeo tem várias fotos.
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS frames (
    id_frame         INT AUTO_INCREMENT PRIMARY KEY,
    id_video         INT NOT NULL,                       -- de qual vídeo é esta foto
    numero_frame     INT NOT NULL,                       -- posição da foto no vídeo
    tempo_segundos   DECIMAL(10,3) NOT NULL,             -- em que segundo do vídeo
    caminho_imagem   VARCHAR(500) NULL,                  -- opcional, não guarda a foto
    imagem           LONGBLOB NOT NULL,                 -- bytes completos da imagem
    tipo_imagem      VARCHAR(50) NOT NULL,               -- image/jpeg ou image/png
    FOREIGN KEY (id_video) REFERENCES videos(id_video) ON DELETE CASCADE
);


-- -------------------------------------------------------------
-- TABELA 4: processamentos
-- Cada vez que a Inteligência Artificial analisa um vídeo.
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS processamentos (
    id_processamento INT AUTO_INCREMENT PRIMARY KEY,
    id_video         INT NOT NULL,                       -- qual vídeo foi analisado
    nome_modelo      VARCHAR(100) NOT NULL,              -- nome da IA usada
    versao_modelo    VARCHAR(50) NOT NULL,               -- versão da IA
    intervalo_extracao_segundos DECIMAL(8,3) DEFAULT 1,  -- tira 1 foto a cada X segundos
    limiar_confianca DECIMAL(5,4) DEFAULT 0.5,           -- certeza mínima para aceitar
    status ENUM('aguardando', 'processando', 'concluido', 'erro') DEFAULT 'aguardando',
    criado_em        DATETIME DEFAULT CURRENT_TIMESTAMP,
    iniciado_em      DATETIME,
    finalizado_em    DATETIME,
    FOREIGN KEY (id_video) REFERENCES videos(id_video) ON DELETE CASCADE
);


-- -------------------------------------------------------------
-- TABELA 5: deteccoes
-- O que a IA encontrou em cada foto (placa, semáforo...).
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS deteccoes (
    id_deteccao      INT AUTO_INCREMENT PRIMARY KEY,
    id_processamento INT NOT NULL,                       -- em qual análise foi achado
    id_frame         INT NOT NULL,                       -- em qual foto foi achado
    classe_prevista  VARCHAR(100) NOT NULL,              -- o que a IA acha que é
    confianca        DECIMAL(5,4) NOT NULL,              -- de 0 a 1 (0.91 = 91% de certeza)
    x_min INT NOT NULL,                                  -- x_min, y_min, x_max, y_max:
    y_min INT NOT NULL,                                  -- o retângulo em volta do
    x_max INT NOT NULL,                                  -- objeto na imagem
    y_max INT NOT NULL,                                  -- (em pixels)
    FOREIGN KEY (id_processamento) REFERENCES processamentos(id_processamento) ON DELETE CASCADE,
    FOREIGN KEY (id_frame) REFERENCES frames(id_frame) ON DELETE CASCADE
);


-- -------------------------------------------------------------
-- TABELA 6: revisoes
-- Uma pessoa confere o que a IA encontrou.
-- A resposta da IA NUNCA é alterada: a correção fica guardada aqui.
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS revisoes (
    id_revisao       INT AUTO_INCREMENT PRIMARY KEY,
    id_deteccao      INT NOT NULL UNIQUE,                -- UNIQUE: 1 revisão por detecção
    status ENUM('pendente', 'confirmada', 'rejeitada', 'corrigida') DEFAULT 'pendente',
    classe_corrigida VARCHAR(100),                       -- preenchida só quando corrigida
    comentario       TEXT,
    data_revisao     DATETIME,
    FOREIGN KEY (id_deteccao) REFERENCES deteccoes(id_deteccao) ON DELETE CASCADE
);


-- Mostra as tabelas criadas
SHOW TABLES;
