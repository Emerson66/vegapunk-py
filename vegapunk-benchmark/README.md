# vegapunk-benchmark

Ambiente PostgreSQL 16 isolado para avaliação do **Vegapunk** (TCC — IFRR 2026).
Espelha o esquema do projeto `cineminha` com dados determinísticos para o Capítulo 7.

## Pré-requisitos

- Docker + Docker Compose

## Subir o banco

```bash
docker compose up -d
```

Aguarde ~10 segundos para o PostgreSQL inicializar e executar os scripts em `init/`.

## Conectar

> As credenciais abaixo pertencem a um container local descartável, criado e destruído
> pelo próprio `docker compose`. Elas estão versionadas de propósito, para que a avaliação
> seja reproduzível por terceiros, e não têm qualquer valor fora deste ambiente.

| Usuário      | Senha           | Acesso      |
|--------------|-----------------|-------------|
| postgres     | postgres        | Total (admin) |
| vegapunk_ro  | somente_leitura | SELECT only   |

```bash
# Admin
psql postgresql://postgres:postgres@localhost:5432/cineminha_db

# Vegapunk (read-only)
psql postgresql://vegapunk_ro:somente_leitura@localhost:5432/cineminha_db
```

## Contagens esperadas

```sql
SELECT 'filmes'  , COUNT(*) FROM filmes   -- 56
UNION ALL
SELECT 'generos' , COUNT(DISTINCT genero) FROM filmes  -- 11
UNION ALL
SELECT 'salas'   , COUNT(*) FROM salas    -- 6
UNION ALL
SELECT 'sessoes' , COUNT(*) FROM sessoes  -- 101
UNION ALL
SELECT 'reservas', COUNT(*) FROM reservas; -- 658
```

## Líderes (benchmark determinístico)

```sql
-- Filme com mais sessões (deve retornar exatamente 1 linha: "O Último Combate", 15)
SELECT f.titulo, COUNT(*) AS total_sessoes
FROM sessoes s JOIN filmes f ON f.id = s.filme_id
GROUP BY f.titulo ORDER BY total_sessoes DESC LIMIT 1;

-- Usuário com mais reservas (deve retornar exatamente 1 linha: kc-user-001, 80)
SELECT usuario_id, COUNT(*) AS total_reservas
FROM reservas GROUP BY usuario_id ORDER BY total_reservas DESC LIMIT 1;
```

## Distribuição de status das reservas

```sql
SELECT status, COUNT(*), ROUND(COUNT(*)*100.0/658,1) AS pct
FROM reservas GROUP BY status;
-- CONFIRMED ~70%, CANCELLED ~20%, PENDING ~10%
```

## Testar restrição do usuário read-only

```bash
psql postgresql://vegapunk_ro:somente_leitura@localhost:5432/cineminha_db \
  -c "DELETE FROM reservas WHERE id=1;"
# Esperado: ERROR:  permission denied for table reservas
```

## Estrutura dos arquivos

```
vegapunk-benchmark/
├── docker-compose.yml          # PostgreSQL 16, porta 5432
├── init/
│   ├── 01_schema.sql           # DDL: tabelas, ENUM, índices, FKs
│   ├── 02_seed.sql             # 56 filmes / 6 salas / 101 sessões / 658 reservas
│   └── 03_readonly_user.sql    # vegapunk_ro com apenas SELECT
├── gerar_seed.py               # Script que gerou o 02_seed.sql
└── README.md
```

O `02_seed.sql` não foi escrito à mão: ele é a saída determinística de `gerar_seed.py`.
Rodar o script novamente produz exatamente o mesmo arquivo — é isso que garante que a
massa de dados usada na avaliação do Capítulo 7 possa ser reconstruída por terceiros.

```bash
python gerar_seed.py   # reescreve init/02_seed.sql (opcional; saída idêntica)
```

## Reproduzir a avaliação do Capítulo 7

O harness de avaliação (`benchmark_runner.py`) fica na raiz do projeto e importa o
pipeline real do Vegapunk (`utils_ai.py` + `utils_db.py`) — ou seja, mede exatamente o
mesmo fluxo dos botões "Gerar SQL" e "Executar SQL" da interface.

```bash
# 1. Suba o banco de benchmark (a partir desta pasta)
docker compose up -d
sleep 10                                  # aguarde o init/ ser executado

# 2. Volte à raiz do projeto e ative a venv do Vegapunk
cd ..
source .venv/bin/activate

# 3. Exporte a chave da API do provedor
export GROQ_API_KEY="sua_chave"           # padrão: Groq
# alternativa: export OPENAI_API_KEY="sua_chave" && export VEGAPUNK_PROVIDER=OpenAI

# 4. Execute a avaliação
python benchmark_runner.py
```

O runner conecta como `vegapunk_ro` (somente leitura), executa as 20 consultas de
`benchmark_dataset.json` mais os 5 testes de guardrails, e grava
`relatorio_benchmark_<data>_<hora>.md` e `.csv` na raiz do projeto.

### Variáveis de ambiente reconhecidas

| Variável | Padrão | Função |
|----------|--------|--------|
| `GROQ_API_KEY` / `OPENAI_API_KEY` | — | Chave do provedor (obrigatória) |
| `VEGAPUNK_PROVIDER` | `Groq` | `Groq` ou `OpenAI` |
| `VEGAPUNK_DB_URL` | `postgresql+psycopg2://vegapunk_ro:somente_leitura@localhost:5432/cineminha_db` | String de conexão |
| `VEGAPUNK_USE_FEEDBACK` | `1` | `0` para um baseline puro, sem os exemplos validados do feedback loop |

### Sobre a reprodutibilidade dos números

O relatório publicado (`RELATORIO_BENCHMARK_FINAL.md`) corresponde a **uma execução**,
de 10/06/2026 08:25. O ambiente do banco é determinístico, mas a geração de SQL depende
do LLM: mesmo com `temperature=0`, execuções distintas do mesmo código podem divergir.
Ao reproduzir a avaliação, espere resultados próximos — não necessariamente idênticos.

## Teardown

```bash
docker compose down -v   # remove container + volume de dados
```
