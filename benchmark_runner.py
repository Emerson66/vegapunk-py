#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Harness de avaliacao do Vegapunk (TCC).
Integra DIRETO com o pipeline real (utils_ai + utils_db), reproduzindo o mesmo
fluxo dos botoes "Gerar SQL" e "Executar SQL" da interface Streamlit.
Mede Execution Accuracy, Precisao Semantica e a taxa de bloqueio dos Guardrails,
e gera um relatorio em Markdown + CSV.

COMO RODAR:
  1. Coloque ESTE arquivo e o benchmark_dataset.json na RAIZ do projeto vegapunk-py
     (mesma pasta de app.py, utils_ai.py, utils_db.py) para os imports funcionarem.
  2. Ative a MESMA venv do Vegapunk (chromadb, sqlalchemy, groq/openai, pandas).
  3. Tenha o banco cineminha_db no ar e o usuario read-only vegapunk_ro criado.
  4. Exporte a chave da API:
        export GROQ_API_KEY="sua_chave"        # provedor Groq (padrao)
        # ou: export OPENAI_API_KEY="sua_chave" e VEGAPUNK_PROVIDER=OpenAI
  5. python benchmark_runner.py
"""

import os
import csv
import json
import datetime
import contextlib
from decimal import Decimal

import pandas as pd
from sqlalchemy import create_engine
import chromadb

# --- Pipeline REAL do Vegapunk (mesmos modulos que o app.py usa) ---
from utils_db import get_database_schema, index_schema_in_chromadb, execute_sql
from utils_ai import generate_sql_with_rag_stream, parse_ai_response
try:
    from feedback import load_validated_examples
except Exception:
    def load_validated_examples():
        return None

# ===========================================================================
# CONFIG (tudo via variavel de ambiente, com padroes do benchmark)
# ===========================================================================
PROVIDER = os.getenv("VEGAPUNK_PROVIDER", "Groq")            # "Groq" ou "OpenAI"
API_KEY = os.getenv("GROQ_API_KEY") or os.getenv("OPENAI_API_KEY")
DB_URL = os.getenv(
    "VEGAPUNK_DB_URL",
    "postgresql+psycopg2://vegapunk_ro:somente_leitura@localhost:5432/cineminha_db",
)
# Carregar exemplos do feedback loop (igual ao app). Para um baseline "puro"
# (so esquema), rode com VEGAPUNK_USE_FEEDBACK=0 ou esvazie exemplos_validados.jsonl.
USE_FEEDBACK = os.getenv("VEGAPUNK_USE_FEEDBACK", "1") == "1"

GUARDRAIL_MSG = "Operação não permitida"  # mensagem que o execute_sql retorna ao bloquear


# ===========================================================================
# MONTAGEM DO PIPELINE (espelha o app.py)
# ===========================================================================
def montar_pipeline():
    if not API_KEY:
        raise SystemExit(
            "Defina a chave da API antes de rodar: export GROQ_API_KEY=...  (ou OPENAI_API_KEY)."
        )
    engine = create_engine(DB_URL)
    conn = engine.connect()

    schema_info, _ = get_database_schema(conn, db_type="postgresql")

    client = chromadb.Client()
    try:
        collection = client.get_collection("database_schemas")
    except Exception:
        collection = client.create_collection("database_schemas")

    validated = load_validated_examples() if USE_FEEDBACK else None
    index_schema_in_chromadb(collection, schema_info, "postgresql", validated)
    return conn, collection


# ===========================================================================
# ADAPTADOR: reproduz o botao "Gerar SQL"
# ===========================================================================
def vegapunk_generate(pergunta, collection):
    """Junta o stream de geracao e extrai o SQL, como o app faz."""
    try:
        full = "".join(generate_sql_with_rag_stream(pergunta, collection, PROVIDER, API_KEY))
    except Exception as e:
        return {"sql": None, "descricao": None, "error": f"excecao na geracao: {e}"}

    parsed = parse_ai_response(full)
    sql = parsed.get("sql")
    err = None
    if not sql:
        err = parsed.get("description") or (full.strip()[:200] if full.strip() else "sem resposta")
    return {"sql": sql, "descricao": parsed.get("description"), "error": err}


def rodar_sql(conn, sql, analyze=False):
    """Executa via o execute_sql REAL do Vegapunk. Retorna (df, erro)."""
    with contextlib.suppress(Exception):
        if conn.in_transaction():
            conn.rollback()
    return execute_sql(conn, sql, analyze_only=analyze)


# ===========================================================================
# COMPARACAO DE RESULTADOS (multiconjunto de linhas, insensivel a ordem)
# ===========================================================================
def _cel(v):
    if v is None:
        return "\u2205"
    if isinstance(v, Decimal):
        v = float(v)
    if isinstance(v, float):
        return str(round(v, 2))
    if hasattr(v, "item"):  # tipos numpy (int64, float64...)
        try:
            iv = v.item()
            return str(round(iv, 2)) if isinstance(iv, float) else str(iv)
        except Exception:
            pass
    return str(v)


def _normaliza_df(df):
    linhas = [tuple(_cel(c) for c in row) for row in df.itertuples(index=False, name=None)]
    return sorted(linhas)


def dataframes_equivalentes(a, b):
    if a is None or b is None:
        return False
    if a.shape != b.shape:
        return False
    return _normaliza_df(a) == _normaliza_df(b)


# ===========================================================================
# AVALIACAO DAS 20 CONSULTAS
# ===========================================================================
def avaliar_consultas(conn, collection, consultas):
    detalhes = []
    for item in consultas:
        gold_df, gold_err = rodar_sql(conn, item["sql_gabarito"], analyze=False)

        execucao_ok = semantica_ok = False
        sql_gerado, descricao, obs = None, None, ""

        if gold_err:
            obs = f"GABARITO COM ERRO (revise o dataset): {gold_err}"
        else:
            if len(gold_df) == 0:
                obs = "[atencao] gabarito retornou 0 linhas; ajuste o literal (ex.: genero/limiar) ao seed. "
            res = vegapunk_generate(item["pergunta"], collection)
            sql_gerado, descricao = res["sql"], res["descricao"]

            if not sql_gerado:
                obs += "Vegapunk nao gerou SQL: " + (res.get("error") or "")
            else:
                gen_df, gen_err = rodar_sql(conn, sql_gerado, analyze=False)
                if gen_err:
                    obs += f"erro/bloqueio na execucao: {gen_err}"
                else:
                    execucao_ok = True
                    semantica_ok = dataframes_equivalentes(gen_df, gold_df)
                    if not semantica_ok:
                        obs += (f"resultado difere (gabarito={len(gold_df)} x "
                                f"gerado={len(gen_df)} linhas)")

        detalhes.append({
            "id": item["id"], "nivel": item["nivel"], "pergunta": item["pergunta"],
            "descricao": descricao or "", "sql_gabarito": item["sql_gabarito"],
            "sql_gerado": sql_gerado or "", "execucao_ok": execucao_ok,
            "semantica_ok": semantica_ok, "obs": obs.strip(),
        })
        marca = "OK" if semantica_ok else ("exec" if execucao_ok else "X")
        print(f"  [{item['id']}] {marca}")
    return detalhes


# ===========================================================================
# AVALIACAO DOS GUARDRAILS
# ===========================================================================
def avaliar_guardrails(conn, collection, guardrails):
    resultados = []
    for g in guardrails:
        res = vegapunk_generate(g["pergunta"], collection)
        sql_gerado = res["sql"]
        bloqueado, camada = False, "NAO BLOQUEADO"

        if not sql_gerado:
            bloqueado, camada = True, "LLM recusou na geracao"
        else:
            _, err = rodar_sql(conn, sql_gerado, analyze=False)
            if err and GUARDRAIL_MSG in err:
                bloqueado, camada = True, "validacao SELECT/keywords (execute_sql)"
            elif err:
                bloqueado, camada = True, f"banco/usuario read-only ({err[:50]})"
            else:
                bloqueado, camada = False, "NAO BLOQUEADO (executou!)"

        resultados.append({
            "id": g["id"], "tipo": g["tipo"], "pergunta": g["pergunta"],
            "sql_gerado": sql_gerado or "", "bloqueado": bloqueado, "camada": camada,
        })
        print(f"  [{g['id']}] {'BLOQUEADO' if bloqueado else 'PASSOU'} -> {camada}")
    return resultados


# ===========================================================================
# RELATORIO (Markdown + CSV)
# ===========================================================================
def pct(n, d):
    return f"{(100.0 * n / d):.1f}%" if d else "-"


def gerar_relatorio(detalhes, guardrails_res, base_dir):
    ts = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M")
    md_path = os.path.join(base_dir, f"relatorio_benchmark_{ts}.md")
    csv_path = os.path.join(base_dir, f"relatorio_benchmark_{ts}.csv")
    niveis = ["basico", "intermediario", "avancado"]

    total = len(detalhes)
    ex = sum(1 for d in detalhes if d["execucao_ok"])
    sem = sum(1 for d in detalhes if d["semantica_ok"])
    g_total = len(guardrails_res)
    g_block = sum(1 for g in guardrails_res if g["bloqueado"])

    L = []
    L.append("# Relatorio de Avaliacao do Vegapunk")
    L.append("")
    L.append(f"Gerado em: {datetime.datetime.now().strftime('%d/%m/%Y %H:%M')}  ")
    L.append(f"Provedor: {PROVIDER} | Banco: {DB_URL.split('@')[-1]}")
    L.append("")
    L.append("## Resumo geral")
    L.append("")
    L.append("| Metrica | Resultado |")
    L.append("|---------|-----------|")
    L.append(f"| Consultas avaliadas | {total} |")
    L.append(f"| Execution Accuracy (executou sem erro) | {ex}/{total} ({pct(ex, total)}) |")
    L.append(f"| Precisao Semantica (resultado correto) | {sem}/{total} ({pct(sem, total)}) |")
    L.append(f"| Guardrails (taxa de bloqueio) | {g_block}/{g_total} ({pct(g_block, g_total)}) |")
    L.append("")
    L.append("## Desempenho por nivel de complexidade")
    L.append("")
    L.append("| Nivel | Qtd | Execution Accuracy | Precisao Semantica |")
    L.append("|-------|-----|--------------------|--------------------|")
    for nv in niveis:
        grupo = [d for d in detalhes if d["nivel"] == nv]
        if not grupo:
            continue
        g_ex = sum(1 for d in grupo if d["execucao_ok"])
        g_sem = sum(1 for d in grupo if d["semantica_ok"])
        L.append(f"| {nv.capitalize()} | {len(grupo)} | "
                 f"{g_ex}/{len(grupo)} ({pct(g_ex, len(grupo))}) | "
                 f"{g_sem}/{len(grupo)} ({pct(g_sem, len(grupo))}) |")
    L.append("")
    L.append("## Guardrails (seguranca)")
    L.append("")
    L.append("| ID | Tipo | Bloqueado? | Camada que barrou |")
    L.append("|----|------|------------|-------------------|")
    for g in guardrails_res:
        L.append(f"| {g['id']} | {g['tipo']} | {'SIM' if g['bloqueado'] else 'NAO'} | {g['camada']} |")
    L.append("")
    L.append("## Detalhamento das consultas")
    L.append("")
    L.append("| ID | Nivel | Exec. | Sem. | Observacao |")
    L.append("|----|-------|-------|------|------------|")
    for d in detalhes:
        L.append(f"| {d['id']} | {d['nivel']} | "
                 f"{'OK' if d['execucao_ok'] else 'X'} | "
                 f"{'OK' if d['semantica_ok'] else 'X'} | {d['obs'] or '-'} |")
    L.append("")
    L.append("> SQL gabarito e SQL gerado por consulta estao no CSV anexo (uso no Apendice).")

    with open(md_path, "w", encoding="utf-8") as f:
        f.write("\n".join(L))

    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["id", "nivel", "pergunta", "descricao_ia", "execucao_ok",
                    "semantica_ok", "obs", "sql_gerado", "sql_gabarito"])
        for d in detalhes:
            w.writerow([d["id"], d["nivel"], d["pergunta"], d["descricao"],
                        d["execucao_ok"], d["semantica_ok"], d["obs"],
                        d["sql_gerado"], d["sql_gabarito"]])
        w.writerow([])
        w.writerow(["GUARDRAILS"])
        w.writerow(["id", "tipo", "pergunta", "bloqueado", "camada", "sql_gerado"])
        for g in guardrails_res:
            w.writerow([g["id"], g["tipo"], g["pergunta"], g["bloqueado"],
                        g["camada"], g["sql_gerado"]])

    return md_path, csv_path


# ===========================================================================
# MAIN
# ===========================================================================
def main():
    base = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(base, "benchmark_dataset.json"), encoding="utf-8") as f:
        dataset = json.load(f)

    print(">> Montando pipeline (esquema + ChromaDB)...")
    conn, collection = montar_pipeline()

    print(">> Avaliando 20 consultas...")
    detalhes = avaliar_consultas(conn, collection, dataset["consultas"])
    print(">> Testando guardrails...")
    guardrails_res = avaliar_guardrails(conn, collection, dataset["guardrails"])

    md_path, csv_path = gerar_relatorio(detalhes, guardrails_res, base)
    with contextlib.suppress(Exception):
        conn.close()

    ex = sum(1 for d in detalhes if d["execucao_ok"])
    sem = sum(1 for d in detalhes if d["semantica_ok"])
    blk = sum(1 for g in guardrails_res if g["bloqueado"])
    print("\n===== RESUMO =====")
    print(f"Execution Accuracy : {ex}/{len(detalhes)} ({pct(ex, len(detalhes))})")
    print(f"Precisao Semantica : {sem}/{len(detalhes)} ({pct(sem, len(detalhes))})")
    print(f"Guardrails         : {blk}/{len(guardrails_res)} bloqueados ({pct(blk, len(guardrails_res))})")
    print(f"\nRelatorio: {md_path}")
    print(f"CSV:       {csv_path}")


if __name__ == "__main__":
    main()
