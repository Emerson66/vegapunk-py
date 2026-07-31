# 🚀 Sistema Text-to-SQL Inteligente com Streamlit

🗄️ Uma aplicação completa e robusta que traduz linguagem natural em consultas SQL seguras, com suporte a múltiplos provedores de IA, aprendizado contínuo e análise de performance.

---

## ✨ Funcionalidades Avançadas

-   **🧠 Suporte a Múltiplos LLMs:** Escolha entre **Groq** (para velocidade) e **OpenAI** (para poder de raciocínio) diretamente na interface.
-   **🤖 RAG com Consciência de Relacionamentos:** Utiliza **ChromaDB** para criar um contexto rico que inclui não apenas tabelas e colunas, mas também os **relacionamentos (chaves estrangeiras)** entre elas, permitindo a geração de `JOINs` complexos e precisos.
-   **⚡ Respostas em Tempo Real:** A resposta da IA, incluindo o raciocínio, é exibida palavra por palavra (**streaming**), criando uma experiência de usuário dinâmica e interativa.
-   **💡 Sugestões Dinâmicas:** A IA analisa o esquema do banco de dados conectado e gera sugestões de consulta inteligentes e relevantes, adaptando-se a diferentes bancos.
-   **📜 Histórico de Consultas:** Suas últimas consultas são salvas na barra lateral para fácil reutilização.
-   **🧑‍💻 Edição de SQL para Power Users:** Permite que usuários com conhecimento técnico ajustem o SQL gerado pela IA antes da execução.
-   **🚦 Análise de Performance (`EXPLAIN`):** Antes de executar uma consulta, o sistema a analisa e **alerta o usuário** se ela for potencialmente lenta, pedindo confirmação antes de prosseguir.
-   **👍 Ciclo de Feedback e Aprendizado Contínuo:**
    -   Avalie as respostas da IA com botões 👍 / 👎.
    -   Respostas positivas (`👍`) são salvas no arquivo `exemplos_validados.jsonl` e usadas para **reforçar o contexto da IA** em sessões futuras, tornando o sistema progressivamente mais inteligente.
-   **📊 Visualização Aprimorada:**
    -   Exibição dos resultados em uma tabela interativa.
    -   Geração automática de **gráficos de barras** para resultados compatíveis.
-   **📥 Exportação Múltipla:** Exporte os resultados das suas consultas para **CSV, JSON e Excel**.
-   **🛡️ Segurança Robusta:**
    -   Validação estrita para permitir **apenas comandos `SELECT`**.
    -   Bloqueio de palavras-chave perigosas (`DELETE`, `UPDATE`, `DROP`, etc.).

---

## 🛠️ Instalação e Execução

Siga os passos abaixo para configurar e executar o projeto em seu ambiente local.

### 1. Pré-requisitos

-   **Python:** `3.13.5` ou superior.
-   **pip:** O gerenciador de pacotes do Python.
-   Um ambiente virtual (recomendado para isolar as dependências do projeto).

### 2. Instalação

Clone o repositório, crie um ambiente virtual e instale as dependências.


#### 1. Clone o projeto para sua máquina local

    git clone <URL_DO_SEU_REPOSITORIO>
    cd <NOME_DA_PASTA_DO_PROJETO>

#### 2. Crie e ative um ambiente virtual
##### Em Linux/macOS

    python3 -m venv .venv
    source .venv/bin/activate

##### Em Windows

    python -m venv .venv
    .venv\Scripts\activate

### 3. Instale todas as bibliotecas necessárias

    pip install -r requirements.txt

### 4. Com o ambiente virtual ativado, inicie o servidor do Streamlit.

    streamlit run app.py

---

## 🧪 Reprodução da Avaliação (Capítulo 7 do TCC)

O repositório inclui o ambiente completo usado na avaliação do sistema, para que os
resultados do Capítulo 7 possam ser reproduzidos por terceiros:

| Artefato | O que é |
|----------|---------|
| `vegapunk-benchmark/` | Ambiente Docker com PostgreSQL 16 e massa de dados sintética determinística (56 filmes, 6 salas, 101 sessões, 658 reservas) |
| `benchmark_dataset.json` | As 20 consultas avaliadas (5 básicas, 10 intermediárias, 5 avançadas) com SQL-gabarito, mais 5 testes de guardrails |
| `benchmark_runner.py` | Harness que executa a avaliação usando o pipeline real (`utils_ai.py` + `utils_db.py`) |
| `RELATORIO_BENCHMARK_FINAL.md` / `.csv` | Relatório da execução reportada no TCC |

```bash
cd vegapunk-benchmark && docker compose up -d && sleep 10 && cd ..
export GROQ_API_KEY="sua_chave"
python benchmark_runner.py
```

As instruções detalhadas — credenciais, variáveis de ambiente, consultas de validação
do seed e teardown — estão em [`vegapunk-benchmark/README.md`](vegapunk-benchmark/README.md).

**Resultado reportado** (execução de 10/06/2026, Groq `llama-3.3-70b-versatile`):

| Métrica | Resultado |
|---------|-----------|
| Execution Accuracy | 19/20 (95%) |
| Precisão Semântica | 17/20 (85%) |
| Guardrails (taxa de bloqueio) | 5/5 (100%) |

Os números correspondem a uma execução específica. O banco é determinístico, mas a
geração de SQL depende do LLM: mesmo com `temperature=0`, execuções distintas do mesmo
código podem produzir resultados ligeiramente diferentes.

