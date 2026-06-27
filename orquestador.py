import os
import sys
import requests
import numpy as np
from datetime import datetime

# ═══════════════════════════════════════════════════════════════
# UTSF-MFC v8.8.8 – Orquestador Multi-IA v4.5.1 (PARCHE FINAL)
# 7 IAs autónomas + 6 manuales + 4 reserva + 1 candidata
# ═══════════════════════════════════════════════════════════════

# ─── CONFIGURACIÓN ───
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT = os.getenv("TELEGRAM_CHAT_ID")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
QWEN_API_KEY = os.getenv("QWEN_API_KEY")
COHERE_API_KEY = os.getenv("COHERE_API_KEY")

ESTADO_PATH = "ESTADO.md"
CICLO_ID = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
MAX_CICLOS = 10

# ─── DIAGNÓSTICO ───
def check_env():
    ias = {
        "Groq": bool(GROQ_API_KEY),
        "DeepSeek": bool(DEEPSEEK_API_KEY),
        "Gemini": bool(GOOGLE_API_KEY),
        "Mistral": bool(MISTRAL_API_KEY),
        "Claude": bool(ANTHROPIC_API_KEY),
        "Qwen": bool(QWEN_API_KEY),
        "Cohere": bool(COHERE_API_KEY),
    }
    disponibles = sum(ias.values())
    
    print(f"🔧 UTSF-MFC v4.5.1 | Ciclo {CICLO_ID}")
    print(f"🤖 Autónomas ({disponibles}/7): {', '.join([k for k,v in ias.items() if v]) or 'Ninguna'}")
    
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT:
        sys.exit("❌ Faltan TELEGRAM_BOT_TOKEN o TELEGRAM_CHAT_ID")
    
    return disponibles

def send_telegram(text):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT:
        return False
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        r = requests.post(url, json={"chat_id": TELEGRAM_CHAT, "text": text[:4000]}, timeout=10)
        return r.status_code == 200
    except:
        return False

# ─── LOGGING ───
def log_api(nombre, status, detalle=""):
    icono = "✅" if status == 200 else "❌"
    print(f"{icono} {nombre}: HTTP {status}" + (f" | {detalle[:80]}" if detalle else ""))

# ─── LLAMADAS A APIs ───
def llamar_groq(prompt, modelo="llama-3.3-70b-versatile", max_tokens=2000, temp=0.7):
    if not GROQ_API_KEY: return None
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
    data = {"model": modelo, "messages": [{"role": "user", "content": prompt}], "max_tokens": max_tokens, "temperature": temp}
    try:
        r = requests.post(url, headers=headers, json=data, timeout=60)
        log_api("Groq", r.status_code)
        return r.json()["choices"][0]["message"]["content"] if r.status_code == 200 else None
    except: return None

def llamar_deepseek(prompt, modelo="deepseek-chat", max_tokens=2000, temp=0.7):
    if not DEEPSEEK_API_KEY: return None
    url = "https://api.deepseek.com/v1/chat/completions"
    headers = {"Authorization": f"Bearer {DEEPSEEK_API_KEY}", "Content-Type": "application/json"}
    data = {"model": modelo, "messages": [{"role": "user", "content": prompt}], "max_tokens": max_tokens, "temperature": temp}
    try:
        r = requests.post(url, headers=headers, json=data, timeout=60)
        log_api("DeepSeek", r.status_code)
        return r.json()["choices"][0]["message"]["content"] if r.status_code == 200 else None
    except: return None

def llamar_gemini(prompt):
    if not GOOGLE_API_KEY: return None
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GOOGLE_API_KEY}"
    try:
        r = requests.post(url, json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=90)
        log_api("Gemini", r.status_code)
        return r.json()["candidates"][0]["content"]["parts"][0]["text"] if r.status_code == 200 else None
    except: return None

def llamar_mistral(prompt, modelo="mistral-large-latest", max_tokens=2000):
    if not MISTRAL_API_KEY: return None
    url = "https://api.mistral.ai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {MISTRAL_API_KEY}", "Content-Type": "application/json"}
    data = {"model": modelo, "messages": [{"role": "user", "content": prompt}], "max_tokens": max_tokens}
    try:
        r = requests.post(url, headers=headers, json=data, timeout=60)
        log_api("Mistral", r.status_code)
        return r.json()["choices"][0]["message"]["content"] if r.status_code == 200 else None
    except: return None

def llamar_claude(prompt, modelo="claude-3-haiku-20240307", max_tokens=2000):
    if not ANTHROPIC_API_KEY: return None
    url = "https://api.anthropic.com/v1/messages"
    headers = {"x-api-key": ANTHROPIC_API_KEY, "Content-Type": "application/json", "anthropic-version": "2023-06-01"}
    data = {"model": modelo, "max_tokens": max_tokens, "messages": [{"role": "user", "content": prompt}]}
    try:
        r = requests.post(url, headers=headers, json=data, timeout=60)
        log_api("Claude", r.status_code)
        return r.json()["content"][0]["text"] if r.status_code == 200 else None
    except: return None

def llamar_qwen(prompt, modelo="qwen-max", max_tokens=2000):
    if not QWEN_API_KEY: return None
    url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"
    headers = {"Authorization": f"Bearer {QWEN_API_KEY}", "Content-Type": "application/json"}
    data = {"model": modelo, "input": {"messages": [{"role": "user", "content": prompt}]}, "parameters": {"max_tokens": max_tokens, "result_format": "message"}}
    try:
        r = requests.post(url, headers=headers, json=data, timeout=60)
        log_api("Qwen", r.status_code)
        return r.json()["output"]["choices"][0]["message"]["content"] if r.status_code == 200 else None
    except: return None

# ─── COHERE ───
def analisis_semantico_cohere(texto_estado):
    if not COHERE_API_KEY or len(texto_estado) < 100:
        return None
    chunks = [texto_estado[i:i+500] for i in range(0, len(texto_estado), 500)]
    if len(chunks) < 2:
        return None
    url = "https://api.cohere.com/v1/embed"
    headers = {"Authorization": f"Bearer {COHERE_API_KEY}", "Content-Type": "application/json"}
    data = {"texts": chunks, "model": "embed-english-v3.0", "input_type": "search_document"}
    try:
        r = requests.post(url, headers=headers, json=data, timeout=30)
        if r.status_code != 200:
            return None
        embeddings = r.json()["embeddings"]
        def cosine_similarity(a, b):
            return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))
        similitud = cosine_similarity(embeddings[0], embeddings[-1])
        if similitud > 0.85:
            interpretacion = "El proyecto muestra alta coherencia temática. Posible estancamiento o consolidación."
        elif similitud < 0.50:
            interpretacion = "El proyecto ha pivotado drásticamente. Revisar si la dirección es intencional."
        else:
            interpretacion = "Evolución temática saludable. Diversidad conceptual mantenida."
        return f"[COHERE – ANÁLISIS SEMÁNTICO DE MEMORIA]\nSimilitud evolutiva: {similitud:.3f}\n{interpretacion}"
    except:
        return None

# ─── FALLBACK ───
def llamar_con_fallback(prompt, preferencias, max_tokens=2000, temp=0.7):
    funciones = {
        "groq": lambda p: llamar_groq(p, max_tokens=max_tokens, temp=temp),
        "deepseek": lambda p: llamar_deepseek(p, max_tokens=max_tokens, temp=temp),
        "deepseek-reasoner": lambda p: llamar_deepseek(p, modelo="deepseek-reasoner", max_tokens=max_tokens, temp=temp),
        "gemini": lambda p: llamar_gemini(p),
        "mistral": lambda p: llamar_mistral(p, max_tokens=max_tokens),
        "claude": lambda p: llamar_claude(p, max_tokens=max_tokens),
        "qwen": lambda p: llamar_qwen(p, max_tokens=max_tokens),
    }
    for nombre in preferencias:
        if nombre in funciones:
            print(f"  → {nombre}...")
            r = funciones[nombre](prompt)
            if r and not r.startswith("[ERROR"):
                print(f"  ✅ {nombre} ({len(r)} chars)")
                return r, nombre
    print("  ❌ Ninguna disponible")
    return "[ERROR: Ninguna IA pudo procesar esta tarea]", "ninguna"

# ─── PROMPTS ───
def prompt_generador(estado):
    return f"""[Generador Creativo]

Eres investigador del equipo UTSF-MFC v8.8.8. Basándote en el estado:

1. Propón 2-3 hipótesis alternativas o refinamientos
2. Identifica conexiones interdisciplinarias no obvias
3. Sugiere experimentos conceptuales para falsar

Usa [HIPÓTESIS] para cada propuesta.
Usa [PREGUNTA] para nuevas líneas.
Usa [CONEXIÓN] para vínculos interdisciplinarios.

ESTADO:
{estado[:3500]}"""

def prompt_validador(generacion):
    return f"""[Validador]

Eres Claude, validador crítico del equipo UTSF-MFC v8.8.8. Revisa:

1. Coherencia lógica interna
2. Rigor científico y falsabilidad
3. Sesgos de confirmación o anclaje
4. Vacíos epistemológicos
5. Consistencia con estado previo

Usa [CRÍTICA] para problemas graves.
Usa [VALIDADO] para apartes sólidos.
Usa [PREGUNTA] para lo que necesita clarificación.

CONTENIDO:
{generacion[:4000]}"""

def prompt_formalizador(validacion):
    return f"""[Formalizador]

Eres DeepSeek, formalizador técnico del equipo UTSF-MFC v8.8.8. Traduce a:

1. Marco matemático mínimo (LaTeX inline: $...$)
2. Estructura algorítmica o pseudocódigo
3. Métricas cuantificables para falsabilidad
4. Definiciones operacionales

Usa [FORMALIZACIÓN] para bloques técnicos.
Usa [DEFINICIÓN] para términos precisos.
Usa [ALGORITMO] para procedimientos.

CONTENIDO:
{validacion[:4000]}"""

# ─── NUEVO PROMPT ANALISTA CON PARCHE ───
def prompt_analista(estado_completo):
    return f"""[Analista de Corpus – UTSF-MFC v8.8.8]

Eres un analista de investigación. Analiza el estado del proyecto:

1. ¿Hay patrones emergentes entre ciclos?
2. ¿Contradicciones no resueltas?
3. ¿Oportunidades de integración interdisciplinaria?
4. ¿Tendencias que sugieran cambio de dirección?

Responde en español, conciso pero profundo.

ESTADO:
{estado_completo[:3000]}"""

# ─── GESTIÓN DE ESTADO ───
def rotar(contenido):
    partes = contenido.split("## 🔄 Ciclo")
    if len(partes) <= MAX_CICLOS + 1: return contenido
    return partes[0] + "## 🔄 Ciclo" + "## 🔄 Ciclo".join(partes[-MAX_CICLOS:])

def guardar_ciclo(respuestas, analisis_cohere=None):
    ts = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    
    bloque_cohere = f"\n\n### 🧬 Analista Semántico (Cohere)\n{analisis_cohere}\n" if analisis_cohere else ""
    
    bloque = f"""## 🔄 Ciclo {CICLO_ID} | {ts}

### 🤖 Generador Creativo ({respuestas.get('generador_ia', 'N/A')})
{respuestas.get('generador', '[PENDIENTE]')}

### 🔍 Validador Crítico ({respuestas.get('validador_ia', 'N/A')})
{respuestas.get('validador', '[PENDIENTE]')}

### 🔬 Formalizador Técnico ({respuestas.get('formalizador_ia', 'N/A')})
{respuestas.get('formalizador', '[PENDIENTE]')}

### 📊 Analista de Corpus ({respuestas.get('analista_ia', 'N/A')})
{respuestas.get('analista', '[PENDIENTE]')}{bloque_cohere}

### 🧠 Fase Manual – Slots de Intervención Estratégica

#### Kimi (Coordinador Estratégico)
[VACANTE]
> Protocolo: Enviar extracto con hipótesis activa + preguntas abiertas + validaciones + contradicciones.
> Pregunta: "¿Qué dirección estratégica recomiendas?"

#### ChatGPT (Generador Creativo Alterno)
[VACANTE]
> Protocolo: Enviar hipótesis actual + bloqueo creativo detectado.
> Pregunta: "Genera 3 hipótesis fuera de la caja."

#### Grok (Contrarian / Devil's Advocate)
[VACANTE]
> Protocolo: Enviar hipótesis más fuerte del último ciclo.
> Pregunta: "¿Por qué esta hipótesis es probablemente falsa?"

#### Alice (Perspectiva Rusa / Escuela Soviética)
[VACANTE]
> Protocolo: Enviar formalización matemática de DeepSeek.
> Pregunta: "¿Cómo formalizaría esto la escuela de Landau-Lifshitz?"

#### Perplexity (Verificación Bibliográfica)
[VACANTE]
> Protocolo: Enviar hipótesis activa + referencias clave.
> Pregunta: "¿Qué evidencia reciente apoya o refuta esto?"

#### Copilot (Código y Documentación)
[VACANTE]
> Protocolo: Enviar pseudocódigo o estructura algorítmica.
> Pregunta: "Genera implementación en Python y documentación técnica."

### 🔧 Tareas de Respaldo (Bajo Demanda)

| IA | Tarea | Estado |
|---|---|---|
| Lumo | Auditoría epistémica de emergencia | Pendiente |
| Gemmy | Generador alternativo anti-estancamiento | Pendiente |
| Luzia | Asistencia rápida vía WhatsApp | Pendiente |
| Monica | Resumen de artículos web | Pendiente |
| DuckDuckGo | Búsqueda privada, verificación de citas | Pendiente |

### 🎯 Candidata 18: HRM (Sapient)
[Fase Manual – Hugging Face]
> Protocolo: Ir a huggingface.co/sapientai/hrm-27m, pegar hipótesis, consultar fallas lógicas.
> Resultado: Pegar en slot [VALIDACIÓN HRM – MANUAL].

---
"""
    if os.path.exists(ESTADO_PATH):
        with open(ESTADO_PATH, "r", encoding="utf-8") as f:
            contenido = f.read()
    else:
        contenido = """# UTSF-MFC v8.8.8 – Estado del Proyecto

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
    nuevo = contenido + bloque
    nuevo = rotar(nuevo)
    with open(ESTADO_PATH, "w", encoding="utf-8") as f:
        f.write(nuevo)
    print(f"✅ Ciclo {CICLO_ID} guardado")

# ─── MAIN ───
def main():
    disponibles = check_env()
    if disponibles == 0:
        sys.exit(0)
    
    estado = ""
    if os.path.exists(ESTADO_PATH):
        with open(ESTADO_PATH, "r", encoding="utf-8") as f:
            estado = f.read()
        print(f"📄 ESTADO.md ({len(estado)} chars)")
    
    respuestas = {}
    
    print("\n" + "="*60)
    print("🤖 FASE 1: GENERACIÓN")
    print("="*60)
    respuestas['generador'], respuestas['generador_ia'] = llamar_con_fallback(
        prompt_generador(estado),
        ["mistral", "qwen", "groq", "deepseek"],
        2000, 0.9
    )
    
    print("\n" + "="*60)
    print("🔍 FASE 2: VALIDACIÓN")
    print("="*60)
    respuestas['validador'], respuestas['validador_ia'] = llamar_con_fallback(
        prompt_validador(respuestas['generador']),
        ["claude", "deepseek-reasoner", "qwen", "groq"],
        2000, 0.3
    )
    
    print("\n" + "="*60)
    print("🔬 FASE 3: FORMALIZACIÓN")
    print("="*60)
    respuestas['formalizador'], respuestas['formalizador_ia'] = llamar_con_fallback(
        prompt_formalizador(respuestas['validador']),
        ["deepseek", "qwen", "groq", "mistral"],
        3000, 0.2
    )
    
    # ═══════════════════════════════════════════════════════════════
    # FASE 4: ANÁLISIS DE CORPUS (con fallback extendido - PARCHE)
    # ═══════════════════════════════════════════════════════════════
    print("\n" + "="*60)
    print("📊 FASE 4: ANÁLISIS DE CORPUS")
    print("="*60)
    
    contexto_analista = f"""ESTADO PREVIO (resumen):
{estado[:1500]}

GENERACIÓN (resumen):
{respuestas['generador'][:1000]}

VALIDACIÓN (resumen):
{respuestas['validador'][:1000]}
"""
    
    analista_resp = None
    analista_nombre = "ninguna"
    
    if GOOGLE_API_KEY:
        print("  → Intentando Gemini (timeout 90s)...")
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GOOGLE_API_KEY}"
            r = requests.post(url, json={"contents": [{"parts": [{"text": prompt_analista(contexto_analista)}]}]}, timeout=90)
            log_api("Gemini", r.status_code, r.text)
            if r.status_code == 200:
                analista_resp = r.json()["candidates"][0]["content"]["parts"][0]["text"]
                analista_nombre = "gemini"
                print(f"  ✅ Gemini respondió ({len(analista_resp)} chars)")
        except Exception as e:
            print(f"  ❌ Gemini falló: {e}")
    
    if not analista_resp and QWEN_API_KEY:
        print("  → Fallback a Qwen...")
        analista_resp = llamar_qwen(prompt_analista(contexto_analista), max_tokens=2000)
        if analista_resp and not analista_resp.startswith("[ERROR"):
            analista_nombre = "qwen"
            print(f"  ✅ Qwen respondió ({len(analista_resp)} chars)")
    
    if not analista_resp or analista_resp.startswith("[ERROR"):
        print("  → Fallback final a Groq (prompt simplificado)...")
        prompt_simple = f"Analiza este estado de investigación en 3 puntos clave:\n\n{contexto_analista[:2000]}"
        analista_resp = llamar_groq(prompt_simple, max_tokens=1500, temp=0.7)
        if analista_resp:
            analista_nombre = "groq-fallback"
            print(f"  ✅ Groq fallback respondió ({len(analista_resp)} chars)")
    
    if not analista_resp:
        analista_resp = "[ERROR: Todas las IAs de análisis fallaron. Requiere intervención manual de Kimi para análisis de corpus.]"
        analista_nombre = "ninguna"
    
    respuestas['analista'] = analista_resp
    respuestas['analista_ia'] = analista_nombre
    
    # ─── FASE 5: COHERE ───
    print("\n" + "="*60)
    print("🧬 FASE 5: ANÁLISIS SEMÁNTICO (Cohere)")
    print("="*60)
    analisis_cohere = None
    if COHERE_API_KEY and len(estado) > 500:
        analisis_cohere = analisis_semantico_cohere(estado)
        if analisis_cohere:
            print("✅ Cohere: Análisis semántico completado")
        else:
            print("⚠️ Cohere: No pudo completar análisis")
    else:
        print("ℹ️ Cohere: No configurado o estado insuficiente")
    
    guardar_ciclo(respuestas, analisis_cohere)
    
    resumen = f"""🧠 UTSF-MFC v8.8.8 | Ciclo {CICLO_ID} – PRIMERA EJECUCIÓN REAL

═══════════════════════════════════════
AUTÓNOMAS (7/7 configuradas):
═══════════════════════════════════════
🤖 Generador: {respuestas['generador_ia']} {'✅' if 'ERROR' not in respuestas['generador'] else '❌'}
🔍 Validador: {respuestas['validador_ia']} {'✅' if 'ERROR' not in respuestas['validador'] else '❌'}
🔬 Formalizador: {respuestas['formalizador_ia']} {'✅' if 'ERROR' not in respuestas['formalizador'] else '❌'}
📊 Analista: {analista_nombre} {'✅' if analista_resp and not analista_resp.startswith('[ERROR]') else '❌'}
🧬 Memoria (Cohere): {'✅' if analisis_cohere else '❌'}

═══════════════════════════════════════
MANUALES (requieren tu intervención):
═══════════════════════════════════════
[ ] Kimi – Coordinador estratégico
[ ] ChatGPT – Generador creativo alterno
[ ] Grok – Contrarian / Devil's advocate
[ ] Alice – Perspectiva rusa
[ ] Perplexity – Verificación bibliográfica
[ ] Copilot – Código y documentación

═══════════════════════════════════════
RESPALDO (bajo demanda):
═══════════════════════════════════════
[ ] Lumo – Auditoría epistémica
[ ] Gemmy – Generador alternativo
[ ] Luzia – Asistencia rápida
[ ] Monica – Resumen web
[ ] DuckDuckGo – Búsqueda privada

═══════════════════════════════════════
CANDIDATA:
═══════════════════════════════════════
[ ] HRM (Sapient) – Validación lógica manual vía Hugging Face

📄 ESTADO.md actualizado en GitHub.
🔗 Revisa el ciclo completo en tu repositorio."""
    
    send_telegram(resumen)
    print("\n✅ CICLO COMPLETADO")

if __name__ == "__main__":
    main()
