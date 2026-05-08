import os
import requests

# Leer secretos
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
NEON_DB_URL = os.getenv("NEON_DB_URL")

# Función para enviar mensaje a Telegram
def send_telegram(chat_id, text):
    if not TELEGRAM_TOKEN:
        print("ERROR: Token de Telegram no encontrado")
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    try:
        response = requests.post(url, json=payload, timeout=10)
        print("Telegram response:", response.status_code)
    except Exception as e:
        print("Error enviando mensaje:", e)

# Función para guardar en Neon (memoria)
def guardar_en_memoria(contenido):
    print("Guardando en Neon:", contenido[:100])

# Simular investigación
def investigar(pregunta):
    return f"[SIMULACIÓN] Respuesta a: {pregunta} (ejecutado en GitHub Actions)"

if __name__ == "__main__":
    pregunta = "¿Cuál es el siguiente paso en UTSF-MFC?"
    respuesta = investigar(pregunta)
    guardar_en_memoria(respuesta)
    
    # REEMPLAZA ESTE NÚMERO POR TU CHAT_ID REAL
    CHAT_ID = 123456789   # <--- CÁMBIALO
    send_telegram(CHAT_ID, f"Resultado:\n{respuesta}")
