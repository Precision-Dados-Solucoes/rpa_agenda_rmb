-- Script para criar a tabela relatorios_rmb no Supabase
-- Execute este script no SQL Editor do Supabase

CREATE TABLE IF NOT EXISTS relatorios_rmb (
    id SERIAL PRIMARY KEY,
    id_legalone BIGINT,
    compromisso_tarefa TEXT,
    tipo TEXT,
    subtipo TEXT,
    etiqueta TEXT,
    inicio_data DATE,
    inicio_hora TIME,
    conclusao_prevista_data DATE,
    conclusao_prevista_hora TIME,
    conclusao_efetiva_data DATE,
    pasta_proc TEXT,
    numero_cnj TEXT,
    executante TEXT,
    executante_sim TEXT,
    descricao TEXT,
    link TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Criar índices para melhor performance
CREATE INDEX IF NOT EXISTS idx_relatorios_rmb_id_legalone ON relatorios_rmb(id_legalone);
CREATE INDEX IF NOT EXISTS idx_relatorios_rmb_executante_sim ON relatorios_rmb(executante_sim);
CREATE INDEX IF NOT EXISTS idx_relatorios_rmb_created_at ON relatorios_rmb(created_at);
