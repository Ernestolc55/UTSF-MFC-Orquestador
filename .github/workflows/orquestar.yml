# UTSF-MFC Orquestador v2.0 (Kimi + DeepSeek)
# Arquitectura híbrida: 4 IAs autónomas + slot manual para Kimi/Ernesto

import os
import sys
import requests
from datetime import datetime

# ─── CONFIGURACIÓN ───
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT = os.getenv("TELEGRAM_CHAT_ID")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
ESTADO_PATH = "ESTADO.md"
CICLO_ID = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
MAX_CICLOS_EN_ESTADO = 10

# ─── DIAGNÓSTICO ───
def check_env():
    faltantes = []
    if not TELEGRAM_TOKEN: faltantes.append("TELEGRAM_BOT_TOKEN")
    if not TELEGRAM_CHAT: faltantes.append("TELEGRAM_CHAT_ID")
    if not OPENROUTER_API_KEY: faltantes.append("OPENROUTER_API_KEY")
    if faltantes:
        sys.exit(f"❌ Faltan secrets: {', '.join(faltantes)}")
    print("✅ Variables de entorno OK")

def send_telegram(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        r = requests.post(url, json={"chat_id": TELEGRAM_CHAT, "text": text[:4000]}, timeout=10)
        return r.status_code == 200
    except:
        return False

# ─── LLAMADA A OPENROUTER ───
def llamar_ia(prompt, modelo, max_tokens=2000, temperature=0.7):
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/UTSF-MFC",
        "X-Title": "UTSF-MFC Orquestador",
    }
    data = {
        "model": modelo,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
        "temperature": temperature,
    }
    try:
        r = requests.post(url, headers=headers, json=data, timeout=60)
        if r.status_code == 200:
            return r.json()["choices"][0]["message"]["content"]
        elif r.status_code == 429:
            return "[ERROR] Rate limit excedido. Requiere espera o recarga de créditos."
        else:
            return f"[ERROR] HTTP {r.status_code}: {r.text[:200]}"
    except Exception as e:
        return f"[ERROR] {str(e)[:200]}"

# ─── PROMPTS UTSF-MFC ───
def prompt_generador(estado):
    return f"""[Generador Creativo]

Eres ChatGPT del equipo UTSF-MFC v8.8.8. Genera hipótesis creativas y redacción clara.

Basándote en el siguiente estado del proyecto:
1. Propón 2-3 hipótesis alternativas o refinamientos
2. Redacta explicaciones accesibles pero rigurosas
3. Identifica conexiones interdisciplinarias no obvias

Usa [HIPÓTESIS] para cada propuesta.
Usa [PREGUNTA] para abrir nuevas líneas.
Sé creativo pero fundamentado.

ESTADO ACTUAL:
{estado}
"""

def prompt_validador(generacion):
    return f"""[Validador]

Eres Claude, validador crítico del equipo UTSF-MFC v8.8.8.

Revisa las siguientes hipótesis/generación y evalúa:
1. Coherencia lógica interna
2. Rigor científico y falsabilidad
3. Sesgos de confirmación o anclaje
4. Vacíos epistemológicos

Usa [CRÍTICA] para problemas graves.
Usa [VALIDADO] para apartes sólidos.
Sé implacable pero constructivo.

CONTENIDO A VALIDAR:
{generacion}
"""

def prompt_formalizador(validacion):
    return f"""[Formalizador]

Eres DeepSeek, formalizador técnico del equipo UTSF-MFC v8.8.8.

Toma el contenido validado y tradúcelo a:
1. Marco matemático mínimo (LaTeX inline: $...$)
2. Estructura algorítmica o pseudocódigo si aplica
3. Métricas cuantificables para falsabilidad

Usa [FORMALIZACIÓN] para bloques técnicos.
No inventes referencias. Sé riguroso.

CONTENIDO VALIDADO:
{validacion}
"""

def prompt_analista(estado_completo):
    return f"""[Analista de Corpus]

Eres Gemini, analista multimodal del equipo UTSF-MFC v8.8.8.

Analiza el siguiente estado completo del proyecto. Busca:
1. Patrones emergentes entre ciclos
2. Contradicciones acumulativas no resueltas
3. Oportunidades de integración con campos adyacentes (ML, teoría de información, etc.)
4. Tendencias que sugieren pivot de hipótesis

ESTADO COMPLETO:
{estado_completo}
"""

# ─── GESTIÓN DE ESTADO ───
def rotar_estado(contenido_completo):
    partes = contenido_completo.split("## 🔄 Ciclo")
    if len(partes) <= MAX_CICLOS_EN_ESTADO + 1:
        return contenido_completo
    header = partes[0]
    ciclos = partes[1:]
    ciclos_recientes = ciclos[-MAX_CICLOS_EN_ESTADO:]
    return header + "## 🔄 Ciclo" + "## 🔄 Ciclo".join(ciclos_recientes)

def guardar_ciclo(generacion, validacion, formalizacion, analisis):
    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    bloque = f"""## 🔄 Ciclo {CICLO_ID} | {timestamp}

### 🤖 ChatGPT (Generador)
{generacion}

### 🔍 Claude (Validador)
{validacion}

### 🔬 DeepSeek (Formalizador)
{formalizacion}

### 📊 Gemini (Analista)
{analisis}

### 🧠 Kimi + Ernesto (Supervisores)
[VACANTE - Pendiente de revisión manual]
> Copia este bloque y reemplázalo con la aportación de Kimi cuando la tengas.
> Formato esperado: [Coordinador] + [HIPÓTESIS]/[CRÍTICA] + sugerencia de próximo paso.

---
"""
    if os.path.exists(ESTADO_PATH):
        with open(ESTADO_PATH, "r", encoding="utf-8") as f:
            contenido = f.read()
    else:
        contenido = f"""# UTSF-MFC v8.8.8 – Estado del Proyecto

📌 Hipótesis activa
Los sólidos fundamentales son estados topológicos donde la simetría de traslación temporal está explícitamente rota, generando fases no unitarias clasificables por invariantes de Berry generalizados.

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

---

"""
    nuevo_contenido = contenido + bloque
    nuevo_contenido = rotar_estado(nuevo_contenido)
    with open(ESTADO_PATH, "w", encoding="utf-8") as f:
        f.write(nuevo_contenido)
    print(f"✅ Ciclo {CICLO_ID} guardado. Rotación aplicada si era necesaria.")

# ─── MAIN ───
def main():
    print(f"🔧 UTSF-MFC Orquestador v2.0 | Ciclo {CICLO_ID}\n")
    check_env()
    estado = ""
    if os.path.exists(ESTADO_PATH):
        with open(ESTADO_PATH, "r", encoding="utf-8") as f:
            estado = f.read()
        print(f"📄 ESTADO.md cargado ({len(estado)} caracteres)")
    else:
        print("⚠️ ESTADO.md no existe. Creando semilla...")
    print("\n🤖 Llamando a ChatGPT (Generador)...")
    generacion = llamar_ia(prompt_generador(estado), "openai/gpt-4o", temperature=0.9)
    print("✅ ChatGPT respondió")
    print("\n🔍 Llamando a Claude (Validador)...")
    validacion = llamar_ia(prompt_validador(generacion), "anthropic/claude-3.5-sonnet")
    print("✅ Claude respondió")
    print("\n🔬 Llamando a DeepSeek (Formalizador)...")
    formalizacion = llamar_ia(prompt_formalizador(validacion), "deepseek/deepseek-chat", max_tokens=3000)
    print("✅ DeepSeek respondió")
    print("\n📊 Llamando a Gemini (Analista)...")
    analisis = llamar_ia(prompt_analista(estado + generacion + validacion), "google/gemini-pro-1.5")
    print("✅ Gemini respondió")
    guardar_ciclo(generacion, validacion, formalizacion, analisis)
    resumen = f"""🧠 UTSF-MFC v8.8.8 | Ciclo {CICLO_ID} completado

🤖 ChatGPT: Generó hipótesis
🔍 Claude: Validó rigor
🔬 DeepSeek: Formalizó técnicamente
📊 Gemini: Analizó patrones

🧠 [VACANTE] Kimi + Ernesto: Pendiente revisión manual

📄 Revisa ESTADO.md en GitHub.
✉️ Para activar revisión de Kimi: copia ESTADO.md y envíalo aquí."""
    send_telegram(resumen)
    print("\n✅ Ciclo autónomo completado. Slot reservado para supervisión humana.")

if __name__ == "__main__":
    main()
