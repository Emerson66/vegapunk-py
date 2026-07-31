-- =============================================================================
-- VEGAPUNK BENCHMARK — SCHEMA
-- Espelha fielmente o esquema real do projeto cineminha (db/init.sql).
--
-- DEVIAÇÃO PROPOSITAL (documentada):
--   Foram adicionadas DUAS chaves estrangeiras explícitas que NÃO existem no
--   projeto real (lá são referências lógicas entre fronteiras de microsserviço):
--     1. fk_sessoes_filme:   sessoes.filme_id  → filmes.id
--     2. fk_reservas_sessao: reservas.sessao_id → sessoes.id
--   Motivo: permitir que o RAG do Vegapunk indexe os relacionamentos entre tabelas.
--   A FK sessoes.sala_id → salas.id já existe no real e foi mantida.
-- =============================================================================

-- ---------------------------------------------------------------------------
-- FILME-SERVICE
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS filmes (
    id                  BIGSERIAL       PRIMARY KEY,
    titulo              VARCHAR(255)    NOT NULL,
    sinopse             TEXT,
    diretor             VARCHAR(255),
    genero              VARCHAR(100),
    duracao_em_minutos  INTEGER
);

-- ---------------------------------------------------------------------------
-- AGENDAMENTO-SERVICE
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS salas (
    id          BIGSERIAL       PRIMARY KEY,
    nome        VARCHAR(255)    NOT NULL UNIQUE,
    capacidade  INTEGER         NOT NULL
);

CREATE TABLE IF NOT EXISTS sessoes (
    id              BIGSERIAL           PRIMARY KEY,
    filme_id        BIGINT              NOT NULL,
    sala_id         BIGINT              NOT NULL,
    start_time      TIMESTAMP           NOT NULL,
    end_time        TIMESTAMP           NOT NULL,
    ticket_price    NUMERIC(10, 2)      NOT NULL,

    CONSTRAINT fk_sessoes_sala
        FOREIGN KEY (sala_id) REFERENCES salas (id) ON DELETE CASCADE,

    -- DEVIAÇÃO: FK explícita adicionada para o RAG do Vegapunk
    CONSTRAINT fk_sessoes_filme
        FOREIGN KEY (filme_id) REFERENCES filmes (id) ON DELETE CASCADE
);

-- ---------------------------------------------------------------------------
-- RESERVA-SERVICE
-- ---------------------------------------------------------------------------

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'reserva_status') THEN
        CREATE TYPE reserva_status AS ENUM (
            'CONFIRMED',
            'CANCELLED',
            'PENDING'
        );
    END IF;
END$$;

CREATE TABLE IF NOT EXISTS reservas (
    id                  BIGSERIAL           PRIMARY KEY,
    usuario_id          VARCHAR(255)        NOT NULL,
    sessao_id           BIGINT              NOT NULL,
    numero_de_ingressos INTEGER             NOT NULL,
    preco_total         NUMERIC(10, 2)      NOT NULL,
    status              reserva_status      NOT NULL,
    created_at          TIMESTAMP           NOT NULL DEFAULT NOW(),

    -- DEVIAÇÃO: FK explícita adicionada para o RAG do Vegapunk
    CONSTRAINT fk_reservas_sessao
        FOREIGN KEY (sessao_id) REFERENCES sessoes (id) ON DELETE CASCADE
);

-- ---------------------------------------------------------------------------
-- ÍNDICES (iguais ao real)
-- ---------------------------------------------------------------------------

CREATE INDEX IF NOT EXISTS idx_sessoes_filme_id   ON sessoes  (filme_id);
CREATE INDEX IF NOT EXISTS idx_sessoes_sala_id    ON sessoes  (sala_id);
CREATE INDEX IF NOT EXISTS idx_sessoes_start_time ON sessoes  (start_time);

CREATE INDEX IF NOT EXISTS idx_reservas_usuario_id ON reservas (usuario_id);
CREATE INDEX IF NOT EXISTS idx_reservas_sessao_id  ON reservas (sessao_id);
CREATE INDEX IF NOT EXISTS idx_reservas_status     ON reservas (status);
