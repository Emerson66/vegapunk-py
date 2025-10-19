# feedback.py

import json
from datetime import datetime
import streamlit as st
import os

def save_feedback(query, sql, reasoning, description, is_good):
    """Salva o feedback do usuário em um arquivo JSONL (JSON Lines)."""
    feedback_entry = {
        "timestamp": datetime.now().isoformat(),
        "query": query,
        "sql": sql,
        "reasoning": reasoning,
        "description": description,
        "is_good": is_good
    }
    
    filename = "exemplos_validados.jsonl" if is_good else "erros_para_analise.jsonl"
    
    try:
        with open(filename, 'a', encoding='utf-8') as f:
            f.write(json.dumps(feedback_entry, ensure_ascii=False) + "\n")
        st.toast("Obrigado pelo seu feedback!", icon="✅" if is_good else "📉")
    except Exception as e:
        st.error(f"Não foi possível salvar o feedback: {e}")

# Função para carregar os exemplos validados
def load_validated_examples(filename="exemplos_validados.jsonl"):
    """Carrega exemplos de alta qualidade do arquivo de feedback positivo."""
    examples = []
    if not os.path.exists(filename):
        return examples
    
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    examples.append(json.loads(line))
                except json.JSONDecodeError:
                    # Ignora linhas mal formatadas
                    continue
    except Exception as e:
        st.warning(f"Não foi possível carregar exemplos validados: {e}")
        
    return examples