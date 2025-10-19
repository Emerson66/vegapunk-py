# utils_db.py

import re;
import streamlit as st
import pandas as pd
from sqlalchemy import text, exc
import json

def get_database_schema(_conn, db_type='sqlite'):
    """Lê o esquema completo, usando 'schema.tabela' como chave única para evitar sobrescritas."""
    schema_info = {}
    table_map = {}
    if db_type == 'sqlite':
        cursor = _conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [table[0] for table in cursor.fetchall()]
        for table_name in tables:
            table_map[table_name] = table_name
            cursor.execute(f"PRAGMA table_info({table_name});")
            columns = cursor.fetchall()
            schema_info[table_name] = {"schema": "main", "table_name": table_name, "columns": [{"name": col[1], "type": col[2]} for col in columns], "relationships": []}
    else: # PostgreSQL
        tables_query = text("SELECT table_schema, table_name FROM information_schema.tables WHERE table_schema NOT IN ('pg_catalog', 'information_schema');")
        df_tables = pd.read_sql(tables_query, _conn)
        fk_query = text("""
            SELECT tc.table_schema, tc.table_name, kcu.column_name, 
                   ccu.table_schema AS foreign_table_schema, ccu.table_name AS foreign_table_name, ccu.column_name AS foreign_column_name 
            FROM information_schema.table_constraints AS tc 
            JOIN information_schema.key_column_usage AS kcu ON tc.constraint_name = kcu.constraint_name AND tc.table_schema = kcu.table_schema
            JOIN information_schema.constraint_column_usage AS ccu ON ccu.constraint_name = tc.constraint_name AND ccu.table_schema = tc.table_schema
            WHERE tc.constraint_type = 'FOREIGN KEY';
        """)
        df_fks = pd.read_sql(fk_query, _conn)
        for _, row in df_tables.iterrows():
            table_schema, table_name = row['table_schema'], row['table_name']
            full_table_name = f"{table_schema}.{table_name}"
            table_map[table_name] = full_table_name
            
            cols_query = text(f"SELECT column_name, data_type FROM information_schema.columns WHERE table_schema = '{table_schema}' AND table_name = '{table_name}';")
            df_columns = pd.read_sql(cols_query, _conn)
            
            relationships = []
            table_fks = df_fks[(df_fks['table_schema'] == table_schema) & (df_fks['table_name'] == table_name)]
            for _, fk_row in table_fks.iterrows():
                relationships.append({
                    "from_col": fk_row['column_name'],
                    "to_table": f"{fk_row['foreign_table_schema']}.{fk_row['foreign_table_name']}",
                    "to_col": fk_row['foreign_column_name']
                })

            schema_info[full_table_name] = {
                "schema": table_schema,
                "table_name": table_name,
                "columns": [{"name": col['column_name'], "type": col['data_type']} for _, col in df_columns.iterrows()],
                "relationships": relationships
            }
    return schema_info, table_map

def index_schema_in_chromadb(collection, schema_info, db_type='sqlite', validated_examples=None):
    documents, metadatas, ids = [], [], []
    for full_name, details in schema_info.items():
        doc = f"Tabela: {full_name}\nColunas:\n" + "".join(f"- {details['table_name']}.{col['name']} ({col['type']})\n" for col in details["columns"])
        if details.get("relationships"):
            doc += "Relacionamentos:\n" + "".join(f"- A coluna '{rel['from_col']}' referencia a tabela '{rel['to_table']}'\n" for rel in details["relationships"])
        documents.append(doc)
        metadatas.append({"full_table_name": full_name, "type": "schema"})
        ids.append(f"schema_{full_name}")
    if validated_examples:
        for i, example in enumerate(validated_examples):
            doc = f"Exemplo validado pelo usuário:\nPergunta: {example['query']}\nSQL Correto: {example['sql']}"
            documents.append(doc)
            metadatas.append({"type": "validated_example"})
            ids.append(f"example_{i}")
    try:
        collection.upsert(documents=documents, metadatas=metadatas, ids=ids)
    except Exception as e:
        st.error(f"Erro ao indexar esquema no ChromaDB: {e}")

def execute_sql(conn, sql_query, analyze_only=False, cost_limit=100000):
    clean_query = sql_query.strip().upper()
    if not clean_query.startswith("SELECT"):
        return None, "Operação não permitida. Este sistema é apenas para consultas (SELECT)."

    # Verificação de segurança aprimorada com expressões regulares
    forbidden_keywords = ["INSERT", "UPDATE", "DELETE", "DROP", "TRUNCATE", "ALTER", "CREATE"]
    # O padrão \b garante que estamos procurando por palavras inteiras e isoladas
    pattern = r"\b(" + "|".join(forbidden_keywords) + r")\b"
    
    if re.search(pattern, clean_query):
        return None, f"Operação não permitida. O comando contém uma palavra-chave proibida."
    try:
        if conn.dialect.name == 'postgresql':
            if analyze_only:
                explain_query = f"EXPLAIN (FORMAT JSON) {sql_query}"
                result = conn.execute(text(explain_query)).scalar_one()
                plan = result[0]['Plan']
                total_cost = plan.get('Total Cost', 0)
                if total_cost > cost_limit:
                    return None, f"COST_WARNING|{total_cost:.2f}"
                return pd.read_sql_query(text(sql_query), conn), None
            else:
                 with conn.begin() as trans:
                    conn.execute(text("SET statement_timeout = '15s';"))
                    df = pd.read_sql_query(text(sql_query), conn)
                    return df, None
        else:
            return pd.read_sql_query(text(sql_query), conn), None
    except exc.SQLAlchemyError as e:
        try:
            if conn.in_transaction(): conn.rollback()
        except Exception: pass
        return None, str(e)
    except Exception as e:
        return None, str(e)
