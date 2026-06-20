import os
import sys
import requests

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT = os.getenv("TELEGRAM_CHAT_ID")
ESTADO_PATH = "ESTADO.md"

def check_env():
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT:
        sys.exit("❌ Faltan secrets TELEGRAM_BOT_TOKEN o TELEGRAM_CHAT_ID")
    print("✅ Variables de entorno OK")

def send_telegram(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        r = requests.post(url, json={"chat_id": TELEGRAM_CHAT, "text": text}, timeout=10)
        ok = r.status_code == 200
        if not ok:
            print(f"❌ Telegram HTTP {r.status_code}")
        return ok
    except requests.exceptions.RequestException:
        print("❌ Error de conexión con Telegram")
        return False

SEMILLA = """# UTSF-MFC v8.8.8 – Estado del Proyecto

📌 Hipótesis activa
Los sólidos fundamentales son estados topológicos donde la simetría de 
traslación temporal está explícitamente rota, generando fases no unitarias 
clasificables por invariantes de Berry generalizados.

❓ Preguntas abiertas
1. ¿Qué álgebra describe la ruptura de simetría temporal en sólidos con interacciones de largo alcance?
2. ¿Existe límite termodinámico bien definido cuando el tiempo es parámetro de deformación?

✅ Decisiones tomadas
- v8.8.8 = iteración sobre clasificación no unitaria
- Dominio: materia condensada fuera del equilibrio

🧠 Último resultado validado por Claude
[Pendiente]

📎 Próxima pregunta para el equipo
¿Cuál es el grupo de simetría mínimo que preserva estabilidad bajo fluctuaciones cuánticas temporales?
"""

def init_estado():
    if not os.path.exists(ESTADO_PATH):
        with open(ESTADO_PATH, "w", encoding="utf-8") as f:
            f.write(SEMILLA)
        print("✅ ESTADO.md semilla creado")
        return True
    print("ℹ️ ESTADO.md ya existe, no se sobrescribe")
    return False

def validar_semilla():
    with open(ESTADO_PATH, "r", encoding="utf-8") as f:
        contenido = f.read()
    checks = [
        ("Hipótesis presente", "📌 Hipótesis activa" in contenido),
        ("Preguntas abiertas", "❓ Preguntas abiertas" in contenido),
        ("No vacío", len(contenido) > 500),
    ]
    for nombre, ok in checks:
        print(f"{'✅' if ok else '❌'} {nombre}")
    return all(c[1] for c in checks)

def main():
    print("🔧 UTSF-MFC Orquestador v0.2\n")
    check_env()
    init_estado()
    valido = validar_semilla()
    if valido:
        ok = send_telegram("🔧 UTSF-MFC: Orquestador activo. ESTADO.md inicializado y validado.")
        if ok:
            print("\n✅ Pipeline listo. Próximo paso: integrar APIs de IAs")
        else:
            print("\n⚠️ Estado validado pero notificación Telegram falló")
    else:
        send_telegram("❌ UTSF-MFC: Validación de ESTADO.md falló.")
        sys.exit(1)

if __name__ == "__main__":
    main()
