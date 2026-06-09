import ast
import re
import random
import streamlit as st
import openai
import groq


def _build_client(provider: str, api_key: str):
    """Retorna (client, model_name) para o provedor escolhido."""
    if provider == "Groq":
        return groq.Groq(api_key=api_key), "llama-3.3-70b-versatile"
    return openai.OpenAI(api_key=api_key), "gpt-4o"

def generate_sql_with_rag_stream(user_query, collection, provider, api_key):
    """Gera SQL usando uma chamada de API com streaming e retorna o conteúdo."""
    if not api_key: 
        yield "❌ Erro: Configure sua chave de API na sidebar."
        return

    results = collection.query(query_texts=[user_query], n_results=8)
    context = "ESQUEMA E RELACIONAMENTOS DO BANCO DE DADOS:\n\n" + "\n---\n".join(results['documents'][0])
    
    prompt = f"""
Você é um assistente de IA especialista em PostgreSQL.

REGRA DE SEGURANÇA CRÍTICA:
1.  Sua única função é gerar consultas `SELECT` para ler dados. Comandos que modificam dados (INSERT, UPDATE, DELETE, etc.) são proibidos. Se o usuário pedir para modificar dados, responda na tag <descricao> que você só pode realizar consultas e deixe a tag <sql> vazia.
2.  Nunca use parâmetros (`:variavel` ou `?`). A consulta deve ser completa e executável.

{context}
### TAREFA:
Siga o processo de raciocínio abaixo para converter a solicitação do usuário. Gere três blocos de saída: `<raciocinio>`, `<descricao>` e `<sql>`.

### PROCESSO DE RACIOCÍNIO OBRIGATÓRIO:
1.  **Tabela Principal:** Qual tabela principal (`schema.tabela`) corresponde à solicitação?
2.  **Colunas e JOINs:** Quais colunas são necessárias? Se elas estiverem em tabelas diferentes, use os "Relacionamentos" para construir o `JOIN` correto.
3.  **Filtros (WHERE):** A solicitação implica algum filtro?
4.  **Colunas Duplicadas:** Se usar `JOIN`, liste as colunas explicitamente e use apelidos (`AS`) para renomear colunas com nomes iguais (ex: `f.id AS filme_id`).
5.  **VERIFICAÇÃO FINAL DE UNICIDADE (REGRA CRÍTICA):** Antes de finalizar, revise a lista de colunas no `SELECT`. É absolutamente proibido ter nomes de colunas duplicados no resultado final, mesmo após usar `AS`.
6.  **Seleção Mínima de Colunas (REGRA CRÍTICA):** Selecione APENAS as colunas que respondem diretamente à pergunta. Siga estas regras por tipo de pergunta:
    - "Quais X com [condição]?" → retorne apenas o nome/título de X e o campo da condição (ex: `titulo, duracao_em_minutos`). Nunca todos os campos.
    - "Liste todas as X" sem especificação → retorne os 2-3 atributos mais descritivos; nunca chaves estrangeiras internas, `created_at` ou campos técnicos.
    - "Qual X realizou o maior/menor [ação]?" → inclua SEMPRE o identificador/nome de X, os atributos descritivos das tabelas JOINadas que contextualizam X (ex: titulo do filme, nome da sala) E o valor do agregado.
    - "Qual X com [filtro] teve [métrica]?" → inclua o ID de X, campos descritivos de tabelas relacionadas (nome, titulo) e a métrica calculada.
    - Agregações com `GROUP BY` → inclua no SELECT apenas o campo de agrupamento descritivo (nunca IDs numéricos extras) + o agregado.
7.  **Nomes Descritivos vs IDs:** Em resultados, prefira `nome`, `titulo` em vez de IDs numéricos. Nunca adicione um campo `id` ou chave estrangeira ao SELECT a não ser que a pergunta peça explicitamente.
8.  **Tipo de JOIN:** Use `INNER JOIN` por padrão. Use `LEFT JOIN` apenas quando a pergunta pedir EXPLICITAMENTE registros sem correspondência (ex: "filmes sem sessões", "salas sem reservas", "inclua os que não têm"). Para "quantas X cada Y possui?" ou "para cada Y, qual o total de X?", use `INNER JOIN` — retorne apenas os Y que possuem ao menos um X.
9.  **ENUM — NUNCA traduza (REGRA CRÍTICA):** Use os valores de ENUM EXATAMENTE como aparecem no esquema. Se o esquema mostra `ENUM(CONFIRMED, CANCELLED, PENDING)`, use `'CONFIRMED'`, NUNCA `'confirmada'` ou variações em português.
10. **Formato de datas/meses:** Para perguntas sobre meses, use `TO_CHAR(coluna, 'YYYY-MM')` — retorna string legível como `'2025-01'`. Nunca use `EXTRACT(MONTH ...)` que retorna apenas o número do mês.
11. **Descrição:** Crie uma frase curta em português descrevendo o que a consulta SQL fará.

### APLICAÇÃO:
**SOLICITAÇÃO DO USUÁRIO:** "{user_query}"

**SAÍDA GERADA:**
<raciocinio>
* (Preencha seu raciocínio passo a passo aqui, usando bullet points)
</raciocinio>
<descricao>
(Preencha a descrição em português aqui)
</descricao>
<sql>
(Preencha APENAS o código SQL final aqui. Se não for possível, deixe este bloco vazio.)
</sql>
"""
    try:
        client, model_name = _build_client(provider, api_key)
        stream = client.chat.completions.create(
            model=model_name,
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            max_tokens=4096,
            stream=True,
        )
        
        for chunk in stream:
            content = chunk.choices[0].delta.content
            if content:
                yield content
    except Exception as e:
        yield f"❌ Erro ao gerar SQL com {provider}: {str(e)}"

def parse_ai_response(raw_response):
    """Analisa a resposta completa do stream para extrair raciocínio, descrição e SQL."""
    reasoning = re.search(r"<raciocinio>(.*?)</raciocinio>", raw_response, re.DOTALL)
    description = re.search(r"<descricao>(.*?)</descricao>", raw_response, re.DOTALL)
    sql = re.search(r"<sql>(.*?)</sql>", raw_response, re.DOTALL)

    sql_text = sql.group(1).strip() if sql else ""
    if not sql_text or sql_text.startswith("--"):
        sql_text = None
        
    return {
        "reasoning": reasoning.group(1).strip() if reasoning else "O modelo não forneceu um raciocínio.",
        "description": description.group(1).strip() if description else "O modelo não forneceu uma descrição.",
        "sql": sql_text
    }

def generate_dynamic_suggestions(_schema_info, provider, api_key):
    """Usa a IA para gerar sugestões de consultas dinâmicas com base no esquema."""
    default_suggestions = ["Contar usuários", "Listar vagas ativas", "Qual o currículo mais recente?"]
    if not api_key or not _schema_info:
        return default_suggestions
    
    sample_tables = random.sample(list(_schema_info.keys()), min(len(_schema_info), 5))
    schema_sample = ""
    for table_name in sample_tables:
        details = _schema_info[table_name]
        full_name = f"{details['schema']}.{table_name}"
        schema_sample += f"Tabela: {full_name}\nColunas: " + ", ".join([col['name'] for col in details['columns']]) + "\n\n"

    prompt = f"""Baseado na amostra de esquema de banco de dados abaixo, gere 3 perguntas simples e úteis que um usuário poderia fazer.
{schema_sample}
REGRAS:
- As perguntas devem ser em português.
- Retorne APENAS uma lista Python de strings. Exemplo: ["Pergunta 1", "Pergunta 2", "Pergunta 3"]
"""
    try:
        client, model_name = _build_client(provider, api_key)
        response = client.chat.completions.create(model=model_name, messages=[{"role": "user", "content": prompt}], temperature=0.5, max_tokens=200)
        response_text = response.choices[0].message.content.strip()
        suggestions_list = ast.literal_eval(response_text)
        if isinstance(suggestions_list, list) and all(isinstance(item, str) for item in suggestions_list):
            return suggestions_list[:3]
    except Exception:
        pass
    
    return default_suggestions