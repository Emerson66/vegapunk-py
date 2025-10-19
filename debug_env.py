# debug_env.py
print("--- INICIANDO SCRIPT DE DEBUG ---")
try:
    import google.genai
    print("✅ Módulo 'google.genai' importado com sucesso.")

    # 1. Verificar o caminho do arquivo do módulo
    print("\n🔍 O módulo está sendo carregado de:")
    print(f"   {google.genai.__file__}")

    # 2. Listar todos os atributos disponíveis no módulo
    print("\n📜 Atributos disponíveis em 'google.genai':")
    attributes = dir(google.genai)
    for attr in attributes:
        print(f"   - {attr}")

    # 3. Verificar especificamente a presença de 'configure'
    print("\n🔎 Verificando a presença de 'configure'...")
    if 'configure' in attributes:
        print("   ✅ O atributo 'configure' FOI ENCONTRADO. O problema pode ser outro.")
    else:
        print("   ❌ O atributo 'configure' NÃO FOI ENCONTRADO na biblioteca carregada.")
        print("      Isso confirma que uma versão antiga ou incorreta está em uso.")

except ImportError:
    print("❌ Falha ao importar 'google.genai'. A biblioteca não está instalada neste ambiente.")
except Exception as e:
    print(f"❌ Ocorreu um erro inesperado: {e}")

print("\n--- FIM DO SCRIPT DE DEBUG ---")