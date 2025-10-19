# 🤖 Pipeline do Sistema Text-to-SQL

Este documento descreve o fluxo completo do sistema, desde a entrada do usuário até a visualização dos resultados, detalhando as fases de preparação, geração de IA e execução.

---

### **Fase 1: ⚙️ Inicialização e Preparação de Contexto**
[cite_start]Esta fase inicial ocorre uma vez por sessão e prepara todo o ambiente e o conhecimento que a IA utilizará[cite: 4].

* [cite_start]**🔌 Conexão com o Banco de Dados:** O sistema estabelece uma conexão ativa com a fonte de dados selecionada, seja SQLite ou PostgreSQL[cite: 5].
* [cite_start]**🗺️ Extração do Esquema:** Uma leitura completa é realizada para extrair todas as tabelas, colunas e, fundamentalmente, os **relacionamentos** (chaves estrangeiras) do banco[cite: 6].
* [cite_start]**⚡ Cache de Performance:** Para garantir alta velocidade nas interações subsequentes, o resultado da extração do esquema é armazenado em cache[cite: 7].
* [cite_start]**🧠 Carregamento de Feedback:** O sistema lê o arquivo `exemplos_validados.jsonl` para aprender com as consultas que foram previamente aprovadas pelo usuário (👍)[cite: 7].
* **📚 Indexação RAG Aprimorada:** O esquema estrutural do banco e os exemplos práticos validados são combinados e indexados no ChromaDB. [cite_start]Isso cria um contexto rico que une conhecimento teórico e prático para a IA[cite: 8].
* [cite_start]**💡 Geração de Sugestões Dinâmicas:** A IA analisa o esquema do banco de dados conectado e gera, de forma inteligente, sugestões de perguntas relevantes, que são exibidas como botões interativos para o usuário[cite: 9].

---

### **Fase 2: ✍️ Geração da Resposta da IA**
[cite_start]Este é o ciclo principal, ativado sempre que o usuário solicita a tradução de uma pergunta para SQL[cite: 10].

* [cite_start]**🗣️ Entrada do Usuário:** O usuário digita sua consulta em linguagem natural na caixa de texto[cite: 11].
* [cite_start]**🔍 Recuperação (RAG):** O ChromaDB realiza uma busca vetorial para encontrar os trechos mais relevantes do esquema e dos exemplos validados que correspondem à pergunta do usuário[cite: 12].
* [cite_start]**📝 Construção do Prompt:** As informações recuperadas são combinadas com a pergunta do usuário e um conjunto de instruções de "processo de raciocínio"[cite: 13]. [cite_start]O prompt guia a IA a gerar uma resposta estruturada que inclui o raciocínio, uma descrição em português e o código SQL[cite: 13, 14].
* [cite_start]**🚀 Chamada LLM com Streaming:** O prompt final é enviado para o modelo de IA selecionado (Groq ou OpenAI)[cite: 15]. [cite_start]A resposta é recebida em tempo real (streaming), palavra por palavra, proporcionando uma experiência de usuário mais dinâmica[cite: 15, 16].
* [cite_start]**🧹 Parsing da Resposta:** Ao final do streaming, o texto completo é analisado para extrair e separar o raciocínio, a descrição e o SQL em campos distintos[cite: 17].

---

### **Fase 3: ✅ Validação, Execução e Visualização**
[cite_start]A etapa final, focada na interação do usuário, segurança e apresentação dos dados[cite: 18].

* [cite_start]**📄 Exibição da Resposta:** O sistema apresenta a resposta da IA de forma organizada, exibindo a descrição em linguagem natural, o raciocínio (em uma seção expansível) e o código SQL gerado[cite: 19].
* [cite_start]**🧑‍💻 Ação do Usuário:** O usuário tem duas opções principais[cite: 20]:
    * [cite_start]**✏️ Editar:** Clicar no botão de edição para ajustar manualmente o SQL gerado antes da execução[cite: 20].
    * [cite_start]**▶️ Executar:** Clicar para prosseguir com a consulta[cite: 21].
* [cite_start]**🚦 Análise de Performance (EXPLAIN):** Ao clicar em "Executar", um comando `EXPLAIN` é enviado primeiro ao PostgreSQL[cite: 21]. [cite_start]Se a consulta for estimada como muito "cara" ou lenta, um aviso é exibido, solicitando a confirmação do usuário antes de continuar[cite: 21, 22].
* [cite_start]**🛡️ Execução Segura:** Somente após ser considerada segura e rápida (ou confirmada pelo usuário), a consulta SQL é executada no banco de dados[cite: 23].
* [cite_start]**📊 Visualização Aprimorada:** Os resultados são exibidos de múltiplas formas[cite: 24]:
    * [cite_start]Uma tabela de dados interativa[cite: 24].
    * [cite_start]Um **gráfico de barras** gerado automaticamente, se os dados forem compatíveis[cite: 25].
    * [cite_start]Botões para exportar os dados nos formatos **CSV, JSON e Excel**[cite: 26].
* [cite_start]**👍 Ciclo de Feedback:** Após ver os resultados, o usuário pode clicar nos botões 👍 ou 👎[cite: 27]. [cite_start]Esse feedback é salvo em arquivos `.jsonl` e será utilizado para aprimorar o contexto da IA em sessões futuras[cite: 28].
