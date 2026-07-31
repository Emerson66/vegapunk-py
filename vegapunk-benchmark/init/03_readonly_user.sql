-- =============================================================================
-- VEGAPUNK BENCHMARK — USUÁRIO SOMENTE-LEITURA
-- Princípio do privilégio mínimo (Guardrails do TCC Vegapunk)
-- =============================================================================

-- Cria o usuário se ainda não existir
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'vegapunk_ro') THEN
        CREATE ROLE vegapunk_ro WITH LOGIN PASSWORD 'somente_leitura';
    END IF;
END$$;

-- Garante que não há permissões de escrita
REVOKE ALL ON ALL TABLES IN SCHEMA public FROM vegapunk_ro;
REVOKE ALL ON SCHEMA public FROM vegapunk_ro;

-- Concede apenas uso do schema e SELECT nas tabelas
GRANT USAGE ON SCHEMA public TO vegapunk_ro;
GRANT SELECT ON filmes   TO vegapunk_ro;
GRANT SELECT ON salas    TO vegapunk_ro;
GRANT SELECT ON sessoes  TO vegapunk_ro;
GRANT SELECT ON reservas TO vegapunk_ro;

-- Garante que futuras tabelas criadas pelo owner também sejam acessíveis (read-only)
ALTER DEFAULT PRIVILEGES IN SCHEMA public
    GRANT SELECT ON TABLES TO vegapunk_ro;

-- Connection string para o Vegapunk:
-- postgresql://vegapunk_ro:somente_leitura@localhost:5432/cineminha_db
