import os
import sys
import requests
import numpy as np
from datetime import datetime

# ═══════════════════════════════════════════════════════════════
# UTSF-MFC v8.8.8 – Orquestador Multi-IA v4.5 (Final Consolidado)
# 7 IAs autónomas + 6 manuales + 5 reserva + 1 candidata
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

# ─── EQUIPO UTSF-MFC v8.8.8 ───
EQUIPO_AUTONOMO = ["Groq", "DeepSeek", "Gemini", "Mistral", "Claude", "Qwen", "Cohere"]
EQUIPO_MANUAL = ["Kimi", "ChatGPT", "Grok", "Alice", "Perplexity", "Copilot"]
EQUIPO_RESERVA = ["Lumo", "Gemmy", "Luzia", "Monica", "DuckDuckGo"]
CANDIDATA = "HRM (Sapient) – Fase Manual Hugging Face"

# ─── DIAGNÓSTICO INICIAL ───
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
    
    print("=" * 60)
    print(f"🔧 UTSF-MFC Orquestador v4.5")
    print(f"🕐 Ciclo: {CICLO_ID}")
    print(f"🤖 IAs Autónomas activas: {disponibles}/7")
    for nombre, activa in ias.items():
        print(f"   {'✅' if activa else '❌'} {nombre}")
    print(f"🧠 IAs Manuales: {len(EQUIPO_MANUAL)}")
    print(f"💡 IAs Reserva: {len(EQUIPO_RESERVA)}")
    print(f"🎯 Candidata: {CANDIDATA}")
    print("=" * 60)
    
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT:
        print("❌ CRÍTICO: Faltan secrets de Telegram")
        sys.exit(1)
    
    if disponibles == 0:
        send_telegram("⚠️ UTSF-MFC v8.8.8: Ninguna IA autónoma configurada. Modo manual total.")
        print("⚠️ Modo manual total. Pipeline detenido.")
        sys.exit(0)
    
    print(f"✅ Pipeline listo. {disponibles} IAs autónomas operativas.")
    return disponibles

def send_telegram(text):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT:
        return False
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        r = requests.post(url, json={"chat_id": TELEGRAM_CHAT, "text": text[:4000]}, timeout=10)
        return r.status_code == 200
    except Exception as e:
        print(f"❌ Telegram error: {e}")
        return False

# ─── APIs CON LOGGING DETALLADO ───
def log_api(nombre, status, detalle=""):
    icono = "✅" if status == 200 else "❌"
    print(f"{icono} {nombre}: HTTP {status}" + (f" | {detalle[:100]}" if detalle else ""))

def llamar_groq(prompt, modelo="llama-3.3-70b-versatile", max_tokens=2000, temp=0.7):
    if not GROQ_API_KEY:
        return None
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": modelo,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
        "temperature": temp
    }
    try:
        r = requests.post(url, headers=headers, json=data, timeout=60)
        log_api("Groq", r.status_code, r.text)
        if r.status_code == 200:
            return r.json()["choices"][0]["message"]["content"]
        elif r.status_code == 429:
            return "[ERROR GROQ] Rate limit excedido. Esperar 60 segundos."
        return None
    except Exception as e:
        print(f"❌ Groq excepción: {e}")
        return None

def llamar_deepseek(prompt, modelo="deepseek-chat", max_tokens=2000, temp=0.7):
    if not DEEPSEEK_API_KEY:
        return None
    url = "https://api.deepseek.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": modelo,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
        "temperature": temp
    }
    try:
        r = requests.post(url, headers=headers, json=data, timeout=60)
        log_api("DeepSeek", r.status_code, r.text)
        if r.status_code == 200:
            return r.json()["choices"][0]["message"]["content"]
        return None
    except Exception as e:
        print(f"❌ DeepSeek excepción: {e}")
        return None

def llamar_gemini(prompt):
    if not GOOGLE_API_KEY:
        return None
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GOOGLE_API_KEY}"
    try:
        r = requests.post(url, json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=60)
        log_api("Gemini", r.status_code, r.text)
        if r.status_code == 200:
            return r.json()["candidates"][0]["content"]["parts"][0]["text"]
        return None
    except Exception as e:
        print(f"❌ Gemini excepción: {e}")
        return None

def llamar_mistral(prompt, modelo="mistral-large-latest", max_tokens=2000):
    if not MISTRAL_API_KEY:
        return None
    url = "https://api.mistral.ai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {MISTRAL_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": modelo,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens
    }
    try:
        r = requests.post(url, headers=headers, json=data, timeout=60)
        log_api("Mistral", r.status_code, r.text)
        if r.status_code == 200:
            return r.json()["choices"][0]["message"]["content"]
        return None
    except Exception as e:
        print(f"❌ Mistral excepción: {e}")
        return None

def llamar_claude(prompt, modelo="claude-3-haiku-20240307", max_tokens=2000):
    if not ANTHROPIC_API_KEY:
        return None
    url = "https://api.anthropic.com/v1/messages"
    headers = {
        "x-api-key": ANTHROPIC_API_KEY,
        "Content-Type": "application/json",
        "anthropic-version": "2023-06-01"
    }
    data = {
        "model": modelo,
        "max_tokens": max_tokens,
        "messages": [{"role": "user", "content": prompt}]
    }
    try:
        r = requests.post(url, headers=headers, json=data, timeout=60)
        log_api("Claude", r.status_code, r.text)
        if r.status_code == 200:
            return r.json()["content"][0]["text"]
        return None
    except Exception as e:
        print(f"❌ Claude excepción: {e}")
        return None

def llamar_qwen(prompt, modelo="qwen-max", max_tokens=2000):
    if not QWEN_API_KEY:
        return None
    url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"
    headers = {
        "Authorization": f"Bearer {QWEN_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": modelo,
        "input": {"messages": [{"role": "user", "content": prompt}]},
        "parameters": {"max_tokens": max_tokens, "result_format": "message"}
    }
    try:
        r = requests.post(url, headers=headers, json=data, timeout=60)
        log_api("Qwen", r.status_code, r.text)
        if r.status_code == 200:
            return r.json()["output"]["choices"][0]["message"]["content"]
        return None
    except Exception as e:
        print(f"❌ Qwen excepción: {e}")
        return None

# ─── COHERE: ANALISTA SEMÁNTICO ───
def llamar_cohere(prompt, max_tokens=500):
    if not COHERE_API_KEY:
        return None
    url = "https://api.cohere.com/v1/generate"
    headers = {
        "Authorization": f"Bearer {COHERE_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "command-r",
        "prompt": prompt,
        "max_tokens": max_tokens,
        "temperature": 0.3
    }
    try:
        r = requests.post(url, headers=headers, json=data, timeout=30)
        log_api("Cohere", r.status_code, r.text)
        if r.status_code == 200:
            return r.json()["generations"][0]["text"]
        return None
    except Exception as e:
        print(f"❌ Cohere excepción: {e}")
        return None

def analisis_semantico_cohere(texto_estado):
    if not COHERE_API_KEY or len(texto_estado) < 500:
        return None
    
    chunks = [texto_estado[i:i+500] for i in range(0, len(texto_estado), 500)]
    if len(chunks) < 2:
        return None
    
    url = "https://api.cohere.com/v1/embed"
    headers = {
        "Authorization": f"Bearer {COHERE_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "texts": chunks,
        "model": "embed-english-v3.0",
        "input_type": "search_document"
    }
    
    try:
        r = requests.post(url, headers=headers, json=data, timeout=30)
        log_api("Cohere Embed", r.status_code)
        if r.status_code != 200:
            return None
        
        embeddings = r.json()["embeddings"]
        
        def cosine_similarity(a, b):
            return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))
        
        similitud = cosine_similarity(embeddings[0], embeddings[-1])
        
        if similitud > 0.85:
            interpretacion = "Alta coherencia temática. Posible estancamiento o consolidación madura."
        elif similitud < 0.50:
            interpretacion = "Pivot drástico detectado. Verificar intencionalidad de la dirección."
        else:
            interpretacion = "Evolución temática saludable. Diversidad conceptual mantenida."
        
        return f"[COHERE – ANÁLISIS SEMÁNTICO]\nSimilitud evolutiva: {similitud:.3f}\n{interpretacion}"
    except Exception as e:
        print(f"❌ Cohere Embed excepción: {e}")
        return None

# ─── FALLBACK INTELIGENTE ───
def llamar_con_fallback(prompt, preferencias, max_tokens=2000, temp=0.7):
    funciones = {
        "groq": lambda p: llamar_groq(p, max_tokens=max_tokens, temp=temp),
        "deepseek": lambda p: llamar_deepseek(p, max_tokens=max_tokens, temp=temp),
        "deepseek-reasoner": lambda p: llamar_deepseek(p, modelo="deepseek-reasoner", max_tokens=max_tokens, temp=temp),
        "gemini": lambda p: llamar_gemini(p),
        "mistral": lambda p: llamar_mistral(p, max_tokens=max_tokens),
        "claude": lambda p: llamar_claude(p, max_tokens=max_tokens),
        "qwen": lambda p: llamar_qwen(p, max_tokens=max_tokens),
        "cohere": lambda p: llamar_cohere(p, max_tokens=max_tokens),
    }
    
    for nombre in preferencias:
        if nombre in funciones:
            print(f"\n  → Intentando {nombre}...")
            r = funciones[nombre](prompt)
            if r and not r.startswith("[ERROR"):
                print(f"  ✅ {nombre} respondió ({len(r)} caracteres)")
                return r, nombre
            elif r and r.startswith("[ERROR"):
                print(f"  ⚠️ {nombre} error: {r[:100]}")
    
    print("  ❌ Ninguna IA del equipo autónomo pudo procesar esta tarea.")
    return "[ERROR: Pipeline autónomo falló. Requiere intervención manual de Kimi o Ernesto.]", "ninguna"

# ─── PROMPTS PROTOCOLARIOS UTSF-MFC ───
def prompt_generador(estado):
    return f"""[Generador Creativo – UTSF-MFC v8.8.8]

Eres un investigador creativo del equipo UTSF-MFC. Tu misión: expandir el espacio de hipótesis.

INSTRUCCIONES:
1. Propón 2-3 hipótesis alternativas o refinamientos a la hipótesis activa
2. Identifica conexiones interdisciplinarias no obvias (física, matemáticas, computación, biología, filosofía)
3. Sugiere experimentos conceptuales para falsar cada hipótesis
4. Evalúa qué tan "lejos" de la ortodoxia está cada propuesta (1-10)

FORMATO:
[HIPÓTESIS 1] Título conciso
- Descripción: 2-3 oraciones
- Fundamento: ¿Por qué podría ser cierta?
- Falsificación: ¿Qué resultado la invalidaría?
- Riesgo ortodoxia: X/10

[PREGUNTA] Cada hipótesis debe generar al menos una pregunta abierta nueva.

[CONEXIÓN] Identifica al menos un vínculo interdisciplinario no obvio.

ESTADO ACTUAL:
{estado[:3500]}"""

def prompt_validador(generacion):
    return f"""[Validador Crítico – UTSF-MFC v8.8.8]

Eres Claude, validador crítico del equipo UTSF-MFC. Tu misión: elevar la calidad epistemológica.

INSTRUCCIONES:
1. Evalúa coherencia lógica interna
2. Evalúa rigor científico y falsabilidad
3. Detecta sesgos de confirmación o anclaje
4. Identifica vacíos epistemológicos
5. Verifica consistencia con estado previo

FORMATO:
[VALIDADO] Para apartes sólidos. Justifica en 1 línea.

[CRÍTICA] Severidad: LEVE / MODERADA / GRAVE.
- Problema: Descripción
- Impacto: ¿Qué invalida?
- Recomendación: Cómo corregir

[PREGUNTA] Para lo que necesita clarificación.

CONTENIDO A VALIDAR:
{generacion[:4000]}"""

def prompt_formalizador(validacion):
    return f"""[Formalizador Técnico – UTSF-MFC v8.8.8]

Eres DeepSeek, formalizador técnico del equipo UTSF-MFC. Tu misión: traducir intuición a rigor.

INSTRUCCIONES:
1. Traduce a marco matemático mínimo (LaTeX inline: $...$)
2. Propón estructura algorítmica o pseudocódigo
3. Define métricas cuantificables para falsabilidad
4. Operacionaliza términos ambiguos

FORMATO:
[FORMALIZACIÓN] Bloque técnico principal. Incluye ecuaciones.

[DEFINICIÓN] Términos que necesitan precisión.

[ALGORITMO] Pseudocódigo o procedimiento computacional.

[MÉTRICA] Valor numérico o condición que invalidaría la hipótesis.

Si algo no se puede formalizar, decláralo. No inventes referencias.

CONTENIDO VALIDADO:
{validacion[:4000]}"""

def prompt_analista(estado_completo):
    return f"""[Analista de Corpus – UTSF-MFC v8.8.8]

Eres Gemini, analista multimodal del equipo UTSF-MFC. Tu misión: ver patrones que otros no ven.

INSTRUCCIONES:
1. Detecta patrones emergentes entre ciclos
2. Identifica contradicciones acumulativas no resueltas
3. Explora oportunidades de integración (ML, teoría información, topología datos)
4. Evalúa si hay tendencias para pivot de hipótesis
5. Calcula métricas de progreso

FORMATO:
[ANÁLISIS] Hallazgo principal con evidencia.

[CONTRADICCIÓN] Inconsistencia entre ciclos.

[PIVOT] Si recomiendas cambiar dirección. Justifica riesgo/beneficio.

[TENDENCIA] ¿Convergencia, divergencia o estancamiento?

ESTADO COMPLETO:
{estado_completo[:4000]}"""
  # ─── GESTIÓN DE ESTADO CON ROTACIÓN ───
def rotar_estado(contenido):
    partes = contenido.split("## 🔄 Ciclo")
    if len(partes) <= MAX_CICLOS + 1:
        return contenido
    header = partes[0]
    ciclos = partes[-MAX_CICLOS:]
    return header + "## 🔄 Ciclo" + "## 🔄 Ciclo".join(ciclos)

def guardar_ciclo(respuestas, analisis_cohere=None):
    ts = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    
    bloque_cohere = f"\n\n### 🧬 Analista Semántico – Memoria Colectiva (Cohere)\n{analisis_cohere}\n" if analisis_cohere else ""
    
    bloque = f"""## 🔄 Ciclo {CICLO_ID} | {ts}

### 🤖 Generador Creativo ({respuestas.get('generador_ia', 'N/A')})
{respuestas.get('generador', '[PENDIENTE – Fallo del pipeline autónomo]')}

### 🔍 Validador Crítico ({respuestas.get('validador_ia', 'N/A')})
{respuestas.get('validador', '[PENDIENTE – Fallo del pipeline autónomo]')}

### 🔬 Formalizador Técnico ({respuestas.get('formalizador_ia', 'N/A')})
{respuestas.get('formalizador', '[PENDIENTE – Fallo del pipeline autónomo]')}

### 📊 Analista de Corpus ({respuestas.get('analista_ia', 'N/A')})
{respuestas.get('analista', '[PENDIENTE – Fallo del pipeline autónomo]')}{bloque_cohere}

---

### 🧠 FASE MANUAL – Slots de Intervención Estratégica

#### Kimi (Coordinador Estratégico)
[VACANTE]
> PROTOCOLO: Enviar a Kimi extracto con:
>   - Hipótesis activa del último ciclo
>   - Preguntas abiertas acumuladas
>   - Validaciones de Claude (último ciclo)
>   - Contradicciones señaladas por Gemini
> PREGUNTA: "¿Qué dirección estratégica recomiendas? ¿Continuar, pivotar o profundizar?"

#### ChatGPT (Generador Creativo Alterno)
[VACANTE]
> PROTOCOLO: Enviar hipótesis actual + señal de bloqueo creativo (3 ciclos sin hipótesis novedosas).
> PREGUNTA: "Genera 3 hipótesis fuera de la caja que ningún físico convencional consideraría."

#### Grok (Contrarian / Devil's Advocate)
[VACANTE]
> PROTOCOLO: Enviar hipótesis más fuerte del último ciclo.
> PREGUNTA: "¿Por qué esta hipótesis es probablemente falsa? Destruye los argumentos a favor."

#### Alice (Perspectiva Rusa / Escuela Soviética)
[VACANTE]
> PROTOCOLO: Enviar formalización matemática de DeepSeek.
> PREGUNTA: "¿Cómo formalizaría esto la escuela de Landau-Lifshitz? ¿Qué simplificaciones harían?"

#### Perplexity (Verificación Bibliográfica)
[VACANTE]
> PROTOCOLO: Enviar hipótesis activa + referencias clave mencionadas por el pipeline.
> PREGUNTA: "¿Qué evidencia experimental reciente (2024-2026) apoya o refuta esto?"

#### Copilot (Código y Documentación Técnica)
[VACANTE]
> PROTOCOLO: Enviar pseudocódigo o estructura algorítmica del Formalizador.
> PREGUNTA: "Genera implementación Python ejecutable y documentación técnica del repo."

---

### 🔧 TAREAS DE RESPALDO (Activación por Ernesto según necesidad)

| IA | Tarea asignada | Protocolo de activación |
|---|---|---|
| **Lumo** | Auditoría epistémica de emergencia | Activar cuando: 2+ IAs autónomas generan respuestas idénticas; o Claude valida sin crítica en 3 ciclos consecutivos; o Kimi detecta inconsistencia no capturada. |
| **Gemmy** | Generador alternativo anti-estancamiento | Activar cuando: Generador autónomo produce hipótesis conservadoras por 2 ciclos consecutivos; o Kimi recomienda "perspectiva fresca". |
| **Luzia** | Asistencia rápida vía WhatsApp | Consulta puntual para Ernesto sin interrumpir flujo principal. |
| **Monica** | Resumen de artículos web relevantes | Enviar URL de paper/blog. Monica resume en 3 puntos clave. |
| **DuckDuckGo** | Búsqueda privada, verificación de citas | Verificar si referencias mencionadas por pipeline existen realmente. |

---

### 🎯 CANDIDATA 18: HRM (Sapient) – Auditor de Razonamiento Lógico

**ESTADO:** Fase Manual (Hugging Face)
**URL:** https://huggingface.co/sapientai/hrm-27m

PROTOCOLO DE ACTIVACIÓN:
1. Ir a URL de Hugging Face
2. En widget de demo, pegar hipótesis a validar
3. Pregunta: "¿Esta hipótesis contiene fallas lógicas, sesgos de confirmación o contradicciones internas no evidentes?"
4. Copiar respuesta y pegar en slot [VALIDACIÓN HRM – MANUAL]
5. Si HRM detecta falla GRAVE: detener pipeline, notificar a Kimi, reiniciar ciclo con nueva semilla.

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
- Arquitectura: 7 IAs autónomas + 6 manuales + 5 reserva + 1 candidata

🧠 Último resultado validado por Claude
[Pendiente]

📎 Próxima pregunta para el equipo
¿Cuál es el grupo de simetría mínimo que preserva estabilidad bajo fluctuaciones cuánticas temporales?

---
"""
    
    nuevo = contenido + bloque
    nuevo = rotar_estado(nuevo)
    
    with open(ESTADO_PATH, "w", encoding="utf-8") as f:
        f.write(nuevo)
    
    print(f"\n✅ Ciclo {CICLO_ID} guardado en ESTADO.md ({len(nuevo)} caracteres totales)")

# ─── MAIN ───
def main():
    disponibles = check_env()
    
    # Leer estado actual
    estado = ""
    if os.path.exists(ESTADO_PATH):
        with open(ESTADO_PATH, "r", encoding="utf-8") as f:
            estado = f.read()
        print(f"📄 ESTADO.md cargado: {len(estado)} caracteres")
    else:
        print("⚠️ ESTADO.md no existe. Se creará con semilla inicial.")
    
    respuestas = {}
    
    # ═══════════════════════════════════════════════════════════════
    # FASE 1: GENERACIÓN CREATIVA
    # ═══════════════════════════════════════════════════════════════
    print("\n" + "=" * 60)
    print("🤖 FASE 1: GENERACIÓN CREATIVA")
    print("=" * 60)
    respuestas['generador'], respuestas['generador_ia'] = llamar_con_fallback(
        prompt_generador(estado),
        ["mistral", "qwen", "groq", "deepseek"],
        max_tokens=2500,
        temp=0.9
    )
    
    # ═══════════════════════════════════════════════════════════════
    # FASE 2: VALIDACIÓN CRÍTICA
    # ═══════════════════════════════════════════════════════════════
    print("\n" + "=" * 60)
    print("🔍 FASE 2: VALIDACIÓN CRÍTICA")
    print("=" * 60)
    respuestas['validador'], respuestas['validador_ia'] = llamar_con_fallback(
        prompt_validador(respuestas['generador']),
        ["claude", "deepseek-reasoner", "qwen", "groq"],
        max_tokens=2500,
        temp=0.3
    )
    
    # ═══════════════════════════════════════════════════════════════
    # FASE 3: FORMALIZACIÓN TÉCNICA
    # ═══════════════════════════════════════════════════════════════
    print("\n" + "=" * 60)
    print("🔬 FASE 3: FORMALIZACIÓN TÉCNICA")
    print("=" * 60)
    respuestas['formalizador'], respuestas['formalizador_ia'] = llamar_con_fallback(
        prompt_formalizador(respuestas['validador']),
        ["deepseek", "qwen", "groq", "mistral"],
        max_tokens=3500,
        temp=0.2
    )
    
    # ═══════════════════════════════════════════════════════════════
    # FASE 4: ANÁLISIS DE CORPUS
    # ═══════════════════════════════════════════════════════════════
    print("\n" + "=" * 60)
    print("📊 FASE 4: ANÁLISIS DE CORPUS")
    print("=" * 60)
    contexto_analista = f"""=== ESTADO PREVIO ===
{estado[:2000]}

=== GENERACIÓN DEL CICLO ===
{respuestas['generador'][:1500]}

=== VALIDACIÓN DEL CICLO ===
{respuestas['validador'][:1500]}
"""
    respuestas['analista'], respuestas['analista_ia'] = llamar_con_fallback(
        prompt_analista(contexto_analista),
        ["gemini", "qwen", "groq", "deepseek"],
        max_tokens=2500,
        temp=0.7
    )
    
    # ═══════════════════════════════════════════════════════════════
    # FASE 5: ANÁLISIS SEMÁNTICO (COHERE)
    # ═══════════════════════════════════════════════════════════════
    print("\n" + "=" * 60)
    print("🧬 FASE 5: ANÁLISIS SEMÁNTICO DE MEMORIA")
    print("=" * 60)
    analisis_cohere = None
    if COHERE_API_KEY and len(estado) > 1000:
        analisis_cohere = analisis_semantico_cohere(estado)
        if analisis_cohere:
            print("✅ Cohere: Análisis semántico completado")
        else:
            print("⚠️ Cohere: No pudo completar análisis (seguirá en próximo ciclo)")
    else:
        print("ℹ️ Cohere: No configurado o estado insuficiente para análisis semántico")
    
    # Guardar ciclo
    guardar_ciclo(respuestas, analisis_cohere)
    
    # Notificar
    resumen = f"""🧠 UTSF-MFC v8.8.8 | Ciclo {CICLO_ID} – PRIMERA EJECUCIÓN REAL

═══════════════════════════════════════
AUTÓNOMAS ({disponibles}/7 configuradas):
═══════════════════════════════════════
🤖 Generador: {respuestas['generador_ia']} {'✅' if 'ERROR' not in respuestas['generador'] else '❌'}
🔍 Validador: {respuestas['validador_ia']} {'✅' if 'ERROR' not in respuestas['validador'] else '❌'}
🔬 Formalizador: {respuestas['formalizador_ia']} {'✅' if 'ERROR' not in respuestas['formalizador'] else '❌'}
📊 Analista: {respuestas['analista_ia']} {'✅' if 'ERROR' not in respuestas['analista'] else '❌'}
🧬 Memoria (Cohere): {'✅' if analisis_cohere else '⏭️'}

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
    
    print("\n" + "=" * 60)
    print("✅ CICLO COMPLETADO – UTSF-MFC v8.8.8")
    print("=" * 60)
    print("🎯 Próximo paso: Ernesto revisa ESTADO.md y activa slots manuales según necesidad.")

if __name__ == "__main__":
    main()
