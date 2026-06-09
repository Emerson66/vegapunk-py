# app.py

import streamlit as st
import pandas as pd
import sqlite3
from sqlalchemy import create_engine
import io
import chromadb

from utils_db import get_database_schema, execute_sql, index_schema_in_chromadb
from utils_ai import generate_sql_with_rag_stream, parse_ai_response, generate_dynamic_suggestions
from feedback import save_feedback, load_validated_examples

st.set_page_config(page_title="Sistema Text-to-SQL", layout="wide")

if 'history' not in st.session_state:
    st.session_state.history = []
if 'user_query' not in st.session_state:
    st.session_state.user_query = ""

def set_query_from_history(query):
    st.session_state.user_query = query

@st.cache_resource
def init_demo_database():
    conn = sqlite3.connect(":memory:", check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE funcionarios (id INTEGER PRIMARY KEY, nome TEXT, cargo TEXT, salario REAL)")
    cursor.execute("INSERT INTO funcionarios (nome, cargo, salario) VALUES ('João', 'Engenheiro', 7500)")
    conn.commit()
    return conn

@st.cache_resource
def init_chromadb():
    client = chromadb.Client()
    try:
        collection = client.get_collection("database_schemas")
    except Exception:
        collection = client.create_collection("database_schemas")
    return collection

def main():
    st.title("🗄️ Sistema de Relatórios Personalizados")
    st.markdown("**Gere relatórios SQL a partir de linguagem natural (SOMENTE CONSULTAS)**")

    with st.sidebar:
        st.header("⚙️ Configurações")
        api_provider = st.selectbox("Provedor de API", ["Groq", "OpenAI"])

        if api_provider == "Groq":
            model_in_use = "llama-3.3-70b-versatile"
        else:
            model_in_use = "gpt-4o"
        st.caption(f"🤖 Modelo em uso: {model_in_use}")

        api_key = st.text_input(f"{api_provider} API Key", type="password")
        
        st.subheader("🗃️ Banco de Dados")
        db_option = st.selectbox("Tipo de Banco", ["SQLite (Demo)", "PostgreSQL"])
        
        db_connection_params = {}
        if db_option == "PostgreSQL":
            st.info("Insira os dados de conexão do seu banco PostgreSQL.")
            db_connection_params['host'] = st.text_input("Host", value="localhost")
            db_connection_params['port'] = st.text_input("Porta", value="5432")
            db_connection_params['name'] = st.text_input("Nome do Banco", value="buritiscript")
            db_connection_params['user'] = st.text_input("Usuário")
            db_connection_params['password'] = st.text_input("Senha", type="password")
        
        if st.button("Conectar ao Banco de Dados", type="primary"):
            for key in ['db_connection', 'connection_active', 'schema_info', 'table_map', 'schema_indexed']:
                st.session_state.pop(key, None)
            
            if db_option == "PostgreSQL":
                if all(db_connection_params.values()):
                    try:
                        conn_url = f"postgresql+psycopg2://{db_connection_params['user']}:{db_connection_params['password']}@{db_connection_params['host']}:{db_connection_params['port']}/{db_connection_params['name']}"
                        st.session_state.db_connection = create_engine(conn_url).connect()
                        st.session_state.db_type = 'postgresql'
                        st.session_state.connection_active = True
                        st.sidebar.success("✅ Conectado ao PostgreSQL!")
                        st.rerun()
                    except Exception as e:
                        st.sidebar.error(f"Falha na conexão: {e}")
                else:
                    st.sidebar.warning("Preencha todos os campos de conexão.")
            else:
                st.session_state.db_connection = init_demo_database()
                st.session_state.db_type = 'sqlite'
                st.session_state.connection_active = True
                st.sidebar.success("✅ Conectado ao banco de demonstração!")
                st.rerun()

        if st.session_state.get('connection_active'):
            if st.button("🔄 Atualizar Esquema do Banco"):
                for key in ('schema_info', 'table_map', 'schema_indexed', 'suggestions'):
                    st.session_state.pop(key, None)
                st.toast("Esquema do banco de dados será atualizado.")
                st.rerun()

        st.subheader("📜 Histórico de Consultas")
        if st.session_state.history:
            for item in st.session_state.history:
                st.button(item, key=f"hist_{item}", on_click=set_query_from_history, args=(item,), use_container_width=True)
        else:
            st.caption("Nenhuma consulta ainda.")

    if not st.session_state.get('connection_active', False):
        st.info("Por favor, conecte-se a um banco de dados na barra lateral para começar.")
        return

    conn = st.session_state.db_connection
    db_type = st.session_state.db_type

    if 'schema_info' not in st.session_state or 'table_map' not in st.session_state:
        with st.spinner("Lendo esquema do banco de dados..."):
            st.session_state.schema_info, st.session_state.table_map = get_database_schema(conn, db_type)
    
    if 'schema_indexed' not in st.session_state:
        with st.spinner("Indexando esquema e exemplos validados..."):
            collection = init_chromadb()
            validated_examples = load_validated_examples()
            index_schema_in_chromadb(collection, st.session_state.schema_info, db_type, validated_examples)
            st.session_state.schema_indexed = True
    
    schema_info = st.session_state.schema_info
    table_map = st.session_state.table_map
    collection = init_chromadb()

    main_col, schema_col = st.columns([2, 1])
    
    with main_col:
        st.subheader("💬 Consulta em Linguagem Natural")
        st.text_area("Digite sua consulta:", height=100, key="user_query", label_visibility="collapsed")
        
        if 'suggestions' not in st.session_state:
            with st.spinner("Gerando sugestões inteligentes..."):
                st.session_state.suggestions = generate_dynamic_suggestions(schema_info, api_provider, api_key)
        suggestions = st.session_state.suggestions
        st.caption("Sugestões:")
        s_cols = st.columns(len(suggestions) if suggestions else 1)
        if suggestions:
            for i, suggestion in enumerate(suggestions):
                with s_cols[i]:
                    st.button(suggestion, use_container_width=True, on_click=set_query_from_history, args=(suggestion,))

        if st.button("🚀 Gerar SQL", type="primary"):
            st.session_state.pop('result_df', None); st.session_state.pop('ai_response', None)
            user_query_text = st.session_state.user_query
            if user_query_text and api_key:
                st.subheader("🤖 Resposta da IA (em tempo real)")
                placeholder = st.empty()
                with placeholder.container():
                    stream_generator = generate_sql_with_rag_stream(user_query_text, collection, api_provider, api_key)
                    full_response_text = st.write_stream(stream_generator)
                
                ai_response = parse_ai_response(full_response_text)
                placeholder.empty()
                st.session_state.ai_response = ai_response

                if ai_response.get("sql"):
                    if user_query_text not in st.session_state.history:
                        st.session_state.history.insert(0, user_query_text)
                        st.session_state.history = st.session_state.history[:10]
            elif user_query_text and not api_key:
                st.warning("🔑 Por favor, insira sua chave de API na barra lateral.")
        
        if 'ai_response' in st.session_state:
            response = st.session_state.ai_response
            if not response.get("sql"):
                st.info(response.get("description", "A IA se recusou a gerar um SQL para esta solicitação."))
            else:
                st.subheader("📝 SQL Gerado")
                st.markdown(f"**Descrição:** *{response['description']}*")
                with st.expander("Ver o Raciocínio da IA"):
                    st.markdown(response['reasoning'], unsafe_allow_html=False)
                st.code(response['sql'], language="sql")
                if st.session_state.get('edit_mode', False):
                    st.info("✏️ Modo de Edição.")
                    edited_sql = st.text_area("Edite a consulta:", value=response['sql'], height=200, key="sql_editor")
                    edit_cols = st.columns(2)
                    if edit_cols[0].button("💾 Salvar", type="primary"):
                        st.session_state.ai_response['sql'] = edited_sql; st.session_state.edit_mode = False; st.rerun()
                    if edit_cols[1].button("❌ Cancelar"):
                        st.session_state.edit_mode = False; st.rerun()
                else:
                    exec_cols = st.columns([0.8, 0.2])
                    if exec_cols[0].button("✅ Executar SQL", type="primary"):
                        st.session_state.pop('confirm_slow_query', None)
                        with st.spinner("Analisando performance da consulta..."):
                            df, error = execute_sql(conn, response['sql'], analyze_only=True)
                        if error and error.startswith("COST_WARNING"):
                            cost = error.split("|")[1]
                            st.warning(f"⚠️ **Consulta Lenta Detectada!**\n\nO custo estimado é de **{cost}**, o que pode demorar. Deseja continuar?")
                            st.session_state.confirm_slow_query = True
                        elif error:
                            st.error(f"❌ Erro na análise: {error}")
                        else:
                            st.session_state.result_df = df; st.success("✅ Executado!")
                    if exec_cols[1].button("✏️ Editar", key="edit_sql_btn"):
                        st.session_state.edit_mode = True; st.rerun()
                if st.session_state.get('confirm_slow_query'):
                    if st.button("Executar Mesmo Assim"):
                        with st.spinner("Executando consulta lenta..."):
                            df, error = execute_sql(conn, response['sql'])
                        if error:
                            st.error(f"❌ Erro: {error}")
                        else:
                            st.session_state.result_df = df; st.success("✅ Executado!")
                        st.session_state.pop('confirm_slow_query', None)

        if 'result_df' in st.session_state:
            df = st.session_state.result_df
            res_cols = st.columns([0.8, 0.1, 0.1])
            with res_cols[0]: st.subheader("📊 Resultados")
            with res_cols[1]:
                if st.button("👍", key="feedback_good", help="Marcar como bom resultado"):
                    save_feedback(st.session_state.user_query, response['sql'], response['reasoning'], response['description'], True)
            with res_cols[2]:
                if st.button("👎", key="feedback_bad", help="Marcar como mau resultado"):
                    save_feedback(st.session_state.user_query, response['sql'], response['reasoning'], response['description'], False)
            st.dataframe(df, use_container_width=True)
            if len(df.columns) == 2 and pd.api.types.is_numeric_dtype(df.iloc[:, 1]):
                try:
                    st.subheader("📈 Visualização"); st.bar_chart(df.set_index(df.columns[0]))
                except Exception: pass
            st.subheader("📥 Exportar Dados")
            export_cols = st.columns(3)
            with export_cols[0]:
                st.download_button(label="Baixar como CSV", data=df.to_csv(index=False).encode('utf-8'), file_name='dados.csv', mime='text/csv')
            with export_cols[1]:
                st.download_button(label="Baixar como JSON", data=df.to_json(orient='records').encode('utf-8'), file_name='dados.json', mime='application/json')
            with export_cols[2]:
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df.to_excel(writer, index=False, sheet_name='Resultados')
                st.download_button(label="Baixar como Excel", data=output.getvalue(), file_name='dados.xlsx', mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')


    with schema_col:
        st.subheader("🗃️ Esquema do Banco")

        search_term = st.text_input("Buscar tabela...", key="schema_search", label_visibility="collapsed", placeholder="🔎 Buscar tabela...")
        
        for full_table_name, details in schema_info.items():
            if search_term.lower() in full_table_name.lower():
                with st.expander(f"📋 {full_table_name}"):
                    st.markdown("**Colunas:**")
                    for col in details["columns"]:
                        st.markdown(f"- `{col['name']}` ({col['type']})")
                    if details.get("relationships"):
                        st.markdown("**Relacionamentos:**")
                        for rel in details["relationships"]:
                            st.markdown(f"- A coluna `{rel['from_col']}` referencia `{rel['to_table']}`")

if __name__ == "__main__":
    main()
