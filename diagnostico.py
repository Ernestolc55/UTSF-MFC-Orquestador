import os
import sys
import requests

# ─── CONFIGURACIÓN ───
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT = os.getenv("TELEGRAM_CHAT_ID")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

def test_telegram():
    print("\n=== TEST 1: TELEGRAM ===")
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT:
        print("❌ Faltan secrets de Telegram")
        return False
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        r = requests.post(url, json={"chat_id": TELEGRAM_CHAT, "text": "🔧 Diagnóstico UTSF-MFC: Test 1 OK"}, timeout=10)
        print(f"Status: {r.status_code}")
        print(f"Respuesta: {r.text[:100]}")
        return r.status_code == 200
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_openrouter_modelo(nombre_modelo, modelo_id):
    print(f"\n=== TEST 2.{nombre_modelo}: OPENROUTER {modelo_id} ===")
    if not OPENROUTER_API_KEY:
        print("❌ Falta OPENROUTER_API_KEY")
        return False
    
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/UTSF-MFC",
        "X-Title": "UTSF-MFC Diagnóstico",
    }
    data = {
        "model": modelo_id,
        "messages": [{"role": "user", "content": "Responde solo: OK"}],
        "max_tokens": 10,
    }
    
    try:
        r = requests.post(url, headers=headers, json=data, timeout=30)
        print(f"Status: {r.status_code}")
        if r.status_code == 200:
            content = r.json()["choices"][0]["message"]["content"]
            print(f"✅ Respuesta: {content}")
            return True
        else:
            print(f"❌ Error: {r.text[:300]}")
            return False
    except Exception as e:
        print(f"❌ Excepción: {e}")
        return False

def test_estado_md():
    print("\n=== TEST 3: ESTADO.md ===")
    try:
        if os.path.exists("ESTADO.md"):
            with open("ESTADO.md", "r", encoding="utf-8") as f:
                contenido = f.read()
            print(f"✅ Existe, {len(contenido)} caracteres")
        else:
            print("ℹ️ No existe (se creará en primer ciclo)")
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    print("🔧 UTSF-MFC Diagnóstico de Infraestructura")
    print("Este script aísla cada punto de fallo.\n")
    
    resultados = {
        "telegram": test_telegram(),
        "openrouter_gpt4o": test_openrouter_modelo("GPT-4o", "openai/gpt-4o"),
        "openrouter_claude": test_openrouter_modelo("Claude", "anthropic/claude-3.5-sonnet"),
        "openrouter_deepseek": test_openrouter_modelo("DeepSeek", "deepseek/deepseek-chat"),
        "openrouter_gemini": test_openrouter_modelo("Gemini", "google/gemini-pro-1.5"),
        "estado_md": test_estado_md(),
    }
    
    print("\n=== RESUMEN ===")
    for nombre, ok in resultados.items():
        print(f"{'✅' if ok else '❌'} {nombre}")
    
    if all(resultados.values()):
        print("\n🎉 Todo OK. El orquestador debería funcionar.")
    else:
        print("\n⚠️ Hay fallos. Corrige antes de ejecutar orquestador.py.")

if __name__ == "__main__":
    main()
