-- Criar tabelas no MySQL da Hostinger (execute no phpMyAdmin ou cliente MySQL)
-- Banco: u438744025_advromas

-- 1) agenda_base
CREATE TABLE IF NOT EXISTS agenda_base (
    id INT AUTO_INCREMENT PRIMARY KEY,
    id_legalone BIGINT,
    compromisso_tarefa TEXT,
    tipo VARCHAR(255),
    subtipo VARCHAR(255),
    etiqueta VARCHAR(255),
    inicio_data DATE,
    inicio_hora TIME,
    conclusao_prevista_data DATE,
    conclusao_prevista_hora TIME,
    conclusao_efetiva_data DATE,
    prazo_fatal_data DATE,
    pasta_proc VARCHAR(255),
    numero_cnj VARCHAR(255),
    executante VARCHAR(255),
    executante_sim VARCHAR(50),
    descricao TEXT,
    status VARCHAR(255),
    link TEXT,
    cadastro DATE,
    `cliente-processo` TEXT,
    `contrario-processo` TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_id_legalone (id_legalone),
    INDEX idx_executante_sim (executante_sim)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 2) andamento_base
CREATE TABLE IF NOT EXISTS andamento_base (
    id INT AUTO_INCREMENT PRIMARY KEY,
    id_andamento_legalone BIGINT,
    id_agenda_legalone BIGINT,
    tipo_andamento VARCHAR(255),
    subtipo_andamento VARCHAR(255),
    descricao_andamento TEXT,
    cadastro_andamento DATETIME,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_id_agenda (id_agenda_legalone),
    INDEX idx_tipo (tipo_andamento)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 3) processos_base (id = id do processo no Legal One, usado no link)
CREATE TABLE IF NOT EXISTS processos_base (
    id BIGINT PRIMARY KEY COMMENT 'Id do processo no Legal One',
    link TEXT,
    data_cadastro DATETIME NULL,
    data_sentenca DATETIME NULL,
    data_encerramento_resultado_tipo_resultado DATETIME NULL,
    status VARCHAR(255) NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Se já existir com mais colunas, adicione a coluna link se faltar:
-- ALTER TABLE processos_base ADD COLUMN link TEXT NULL;

-- Colunas para processos encerrados (relatório id=680):
-- ALTER TABLE processos_base ADD COLUMN data_sentenca DATETIME NULL;
-- ALTER TABLE processos_base ADD COLUMN data_encerramento_resultado_tipo_resultado DATETIME NULL;
-- ALTER TABLE processos_base ADD COLUMN status VARCHAR(255) NULL;
