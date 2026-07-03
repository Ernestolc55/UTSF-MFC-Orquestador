import os
import sys
import requests
import numpy as np
from datetime import datetime
import time
import json
import jwt

# ═══════════════════════════════════════════════════════════════
# UTSF-MFC v8.8.8 – Orquestador Multi-IA v4.6.1 (Final)
# 6 IAs autónomas + 6 manuales + 4 reserva + 1 candidata (HRM)
# Fixes: cryptography para Gemini, Cohere diagnóstico corregido,
#        fallback Qwen multinivel, git pull en workflow
# ═══════════════════════════════════════════════════════════════

# ─── CONFIGURACIÓN ───
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT = os.getenv("TELEGRAM_CHAT_ID")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
QWEN_API_KEY = os.getenv("QWEN_API_KEY")
COHERE_API_KEY = os.getenv("COHERE_API_KEY")
GEMINI_PRIVATE_KEY = os.getenv("GEMINI_PRIVATE_KEY")
GEMINI_CLIENT_EMAIL = os.getenv("GEMINI_CLIENT_EMAIL")
GOOGLE_PROJECT_ID = os.getenv("GOOGLE_PROJECT_ID")

ESTADO_PATH = "ESTADO.md"
CICLO_ID = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
MAX_CICLOS = 10

# ─── CIRCUIT BREAKER ───
GROQ_LIMITE_SEGURO = 30
groq_carga = {"llamadas": 0, "ultimo_reset": time.time()}

def check_groq_carga():
    global groq_carga
    if time.time() - groq_carga["ultimo_reset"] > 3600:
        groq_carga = {"llamadas": 0, "ultimo_reset": time.time()}
    return groq_carga["llamadas"] < GROQ_LIMITE_SEGURO

def incrementar_groq():
    global groq_carga
    groq_carga["llamadas"] += 1

# ─── DIAGNÓSTICO ───
def check_env():
    ias = {
        "Groq": bool(GROQ_API_KEY),
        "DeepSeek": bool(DEEPSEEK_API_KEY),
        "Gemini": bool(GEMINI_PRIVATE_KEY and GEMINI_CLIENT_EMAIL and GOOGLE_PROJECT_ID),
        "Mistral": bool(MISTRAL_API_KEY),
        "Qwen": bool(QWEN_API_KEY),
        "Cohere": bool(COHERE_API_KEY),
    }
    disponibles = sum(ias.values())
    
    print(f"🔧 UTSF-MFC v4.6.1 | Ciclo {CICLO_ID}")
    print(f"🤖 Autónomas ({disponibles}/6): {', '.join([k for k,v in ias.items() if v]) or 'Ninguna'}")
    
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT:
        sys.exit("❌ Faltan TELEGRAM_BOT_TOKEN o TELEGRAM_CHAT_ID")
    
    if GEMINI_PRIVATE_KEY and GEMINI_CLIENT_EMAIL and not GOOGLE_PROJECT_ID:
        print("⚠️ Gemini: Faltan GOOGLE_PROJECT_ID para Vertex AI")
    
    return disponibles

def send_telegram(text):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT:
        return False
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        r = requests.post(url, json={"chat_id": TELEGRAM_CHAT, "text": text[:4000]}, timeout=10)
        return r.status_code == 200
    except Exception as e:
        print(f"❌ Telegram: {e}")
        return False

# ─── LOGGING ───
def log_api(nombre, status, detalle="", tiempo_ms=None):
    icono = "✅" if status == 200 else "❌"
    tiempo_str = f" | {tiempo_ms}ms" if tiempo_ms else ""
    print(f"{icono} {nombre}: HTTP {status}{tiempo_str}" + (f" | {detalle[:120]}" if detalle else ""))

def log_metrica(ciclo, fase, ia, latencia, exito, error_tipo=""):
    with open("metricas.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps({
            "ciclo": ciclo, "fase": fase, "ia": ia,
            "latencia_ms": latencia, "exito": exito,
            "error_tipo": error_tipo,
            "timestamp": datetime.utcnow().isoformat()
        }) + "\n")

# ─── DIAGNÓSTICO DE CONECTIVIDAD ───
def diagnostico_api(nombre, api_key, url_test, headers_test, data_test, timeout=15):
    if not api_key:
        return None, "API key no configurada", 0
    inicio = time.time()
    try:
        r = requests.post(url_test, headers=headers_test, json=data_test, timeout=timeout)
        tiempo = int((time.time() - inicio) * 1000)
        if r.status_code == 200:
            return 200, "OK", tiempo
        else:
            return r.status_code, r.text[:200], tiempo
    except requests.exceptions.Timeout:
        return 408, "Timeout", int((time.time() - inicio) * 1000)
    except requests.exceptions.ConnectionError:
        return 503, "Error de conexion", 0
    except Exception as e:
        return 500, str(e)[:200], 0

# ─── API GENERICA ───
def llamar_api_generica(nombre, url, headers, data, timeout=60, parser=None, parser_args=()):
    inicio = time.time()
    try:
        r = requests.post(url, headers=headers, json=data, timeout=timeout)
        latencia = int((time.time() - inicio) * 1000)
        
        if r.status_code == 429:
            log_api(nombre, 429, "Rate limit detectado", latencia)
            log_metrica(CICLO_ID, "api", nombre, latencia, False, "RATE_LIMIT")
            return "[RATE_LIMIT]", nombre
        
        if r.status_code != 200:
            log_api(nombre, r.status_code, r.text[:150], latencia)
            log_metrica(CICLO_ID, "api", nombre, latencia, False, f"HTTP_{r.status_code}")
            return None, nombre
        
        json_resp = r.json()
        if parser:
            resultado = parser(json_resp, *parser_args)
            log_api(nombre, 200, f"OK ({len(str(resultado))} chars)", latencia)
            log_metrica(CICLO_ID, "api", nombre, latencia, True)
            return resultado, nombre
        
        log_api(nombre, 200, "OK", latencia)
        log_metrica(CICLO_ID, "api", nombre, latencia, True)
        return json_resp, nombre
        
    except requests.exceptions.Timeout as e:
        latencia = int((time.time() - inicio) * 1000)
        log_api(nombre, 408, f"Timeout: {e}", latencia)
        log_metrica(CICLO_ID, "api", nombre, latencia, False, "TIMEOUT")
        return None, nombre
    except requests.exceptions.RequestException as e:
        latencia = int((time.time() - inicio) * 1000)
        log_api(nombre, 500, f"Request error: {e}", latencia)
        log_metrica(CICLO_ID, "api", nombre, latencia, False, "REQUEST_ERROR")
        return None, nombre
    except Exception as e:
        latencia = int((time.time() - inicio) * 1000)
        log_api(nombre, 500, f"Excepcion: {e}", latencia)
        log_metrica(CICLO_ID, "api", nombre, latencia, False, "EXCEPTION")
        return None, nombre

# ─── PARSERS ───
def parser_openai(json_resp):
    return json_resp["choices"][0]["message"]["content"]

def parser_qwen(json_resp):
    return json_resp["output"]["choices"][0]["message"]["content"]

def parser_gemini(json_resp):
    candidates = json_resp.get("candidates", [])
    if candidates and "content" in candidates[0]:
        parts = candidates[0]["content"].get("parts", [])
        if parts:
            return parts[0].get("text", "")
    return None

# ─── LLAMADAS INDIVIDUALES ───
def llamar_groq(prompt, modelo="llama-3.3-70b-versatile", max_tokens=2000, temp=0.7):
    if not GROQ_API_KEY:
        return None
    if not check_groq_carga():
        print("⚠️ Groq en cuarentena por exceso de carga")
        return None
    
    incrementar_groq()
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
    data = {
        "model": modelo,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
        "temperature": temp
    }
    return llamar_api_generica("Groq", url, headers, data, 60, parser_openai)[0]

def llamar_deepseek(prompt, modelo="deepseek-chat", max_tokens=2000, temp=0.7):
    if not DEEPSEEK_API_KEY:
        return None
    url = "https://api.deepseek.com/v1/chat/completions"
    headers = {"Authorization": f"Bearer {DEEPSEEK_API_KEY}", "Content-Type": "application/json"}
    data = {
        "model": modelo,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
        "temperature": temp
    }
    return llamar_api_generica("DeepSeek", url, headers, data, 60, parser_openai)[0]

def llamar_gemini(prompt, location="us-central1"):
    """Llama a Gemini via Vertex AI con autenticacion JWT."""
    if not GEMINI_PRIVATE_KEY:
        print("❌ Gemini: GEMINI_PRIVATE_KEY no configurada")
        return None
    if not GEMINI_CLIENT_EMAIL:
        print("❌ Gemini: GEMINI_CLIENT_EMAIL no configurado")
        return None
    if not GOOGLE_PROJECT_ID:
        print("❌ Gemini: GOOGLE_PROJECT_ID no configurado")
        return None
    
    try:
        now = int(time.time())
        payload = {
            "iss": GEMINI_CLIENT_EMAIL,
            "scope": "https://www.googleapis.com/auth/cloud-platform",
            "aud": "https://oauth2.googleapis.com/token",
            "iat": now,
            "exp": now + 3600
        }
        token = jwt.encode(payload, GEMINI_PRIVATE_KEY, algorithm="RS256")
        
        token_url = "https://oauth2.googleapis.com/token"
        token_data = {
            "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
            "assertion": token
        }
        r_token = requests.post(token_url, data=token_data, timeout=10)
        if r_token.status_code != 200:
            print(f"❌ Gemini: Error autenticacion: {r_token.text[:150]}")
            return None
        
        access_token = r_token.json()["access_token"]
        
        url = f"https://{location}-aiplatform.googleapis.com/v1/projects/{GOOGLE_PROJECT_ID}/locations/{location}/publishers/google/models/gemini-1.5-flash:generateContent"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        data = {
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": {"maxOutputTokens": 2000, "temperature": 0.7}
        }
        return llamar_api_generica("Gemini", url, headers, data, 90, parser_gemini)[0]
        
    except Exception as e:
        print(f"❌ Gemini excepcion: {e}")
        return None

def llamar_mistral(prompt, modelo="mistral-large-latest", max_tokens=2000):
    if not MISTRAL_API_KEY:
        return None
    url = "https://api.mistral.ai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {MISTRAL_API_KEY}", "Content-Type": "application/json"}
    data = {
        "model": modelo,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens
    }
    return llamar_api_generica("Mistral", url, headers, data, 60, parser_openai)[0]

def llamar_qwen(prompt, modelo="qwen-max", max_tokens=2000):
    """Llama a Qwen con fallback de modelos (max → plus → turbo)."""
    if not QWEN_API_KEY:
        return None
    
    modelos = [modelo, "qwen-plus", "qwen-turbo"]
    
    for m in modelos:
        url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"
        headers = {"Authorization": f"Bearer {QWEN_API_KEY}", "Content-Type": "application/json"}
        data = {
            "model": m,
            "input": {"messages": [{"role": "user", "content": prompt}]},
            "parameters": {"max_tokens": max_tokens, "result_format": "message"}
        }
        resultado, nombre = llamar_api_generica(f"Qwen-{m}", url, headers, data, 60, parser_qwen)
        if resultado and not resultado.startswith("[ERROR"):
            return resultado
    
    return None

# ─── COHERE SEMÁNTICO ───
def analisis_semantico_cohere(texto_estado):
    if not COHERE_API_KEY or len(texto_estado) < 500:
        return None
    chunks = [texto_estado[i:i+2000] for i in range(0, len(texto_estado), 2000)]
    if len(chunks) < 2:
        return None
    url = "https://api.cohere.com/v1/embed"
    headers = {"Authorization": f"Bearer {COHERE_API_KEY}", "Content-Type": "application/json"}
    data = {
        "texts": chunks,
        "model": "embed-multilingual-v3.0",
        "input_type": "search_document"
    }
    try:
        r = requests.post(url, headers=headers, json=data, timeout=30)
        if r.status_code != 200:
            return None
        embeddings = r.json()["embeddings"]
        def cosine_similarity(a, b):
            return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))
        similitud = cosine_similarity(embeddings[0], embeddings[-1])
        if similitud > 0.85:
            interpretacion = "El proyecto muestra alta coherencia tematica. Posible estancamiento o consolidacion."
        elif similitud < 0.50:
            interpretacion = "El proyecto ha pivotado drasticamente. Revisar si la direccion es intencional."
        else:
            interpretacion = "Evolucion tematica saludable. Diversidad conceptual mantenida."
        return f"[COHERE – ANALISIS SEMANTICO DE MEMORIA]\nSimilitud evolutiva: {similitud:.3f}\n{interpretacion}"
    except Exception as e:
        print(f"⚠️ Cohere error: {e}")
        return None

# ─── FALLBACK INTELIGENTE ───
def llamar_con_fallback(prompt, preferencias, max_tokens=2000, temp=0.7):
    funciones = {
        "groq": lambda p: llamar_groq(p, max_tokens=max_tokens, temp=temp),
        "deepseek": lambda p: llamar_deepseek(p, max_tokens=max_tokens, temp=temp),
        "deepseek-reasoner": lambda p: llamar_deepseek(p, modelo="deepseek-reasoner", max_tokens=max_tokens, temp=temp),
        "gemini": lambda p: llamar_gemini(p),
        "mistral": lambda p: llamar_mistral(p, max_tokens=max_tokens),
        "qwen": lambda p: llamar_qwen(p, max_tokens=max_tokens),
    }
    for nombre in preferencias:
        if nombre in funciones:
            print(f"  → {nombre}...")
            r = funciones[nombre](prompt)
            if r and not r.startswith("[ERROR") and r != "[RATE_LIMIT]":
                print(f"  ✅ {nombre} ({len(r)} chars)")
                return r, nombre
            elif r == "[RATE_LIMIT]":
                print(f"  ⏳ {nombre}: Rate limit, saltando...")
    print("  ❌ Ninguna disponible")
    return "[ERROR: Ninguna IA pudo procesar esta tarea]", "ninguna"

# ─── PROMPTS ───
def prompt_generador(estado):
    return f"""[Generador Creativo]

Eres investigador del equipo UTSF-MFC v8.8.8. Basandote en el estado:

1. Propón 2-3 hipotesis alternativas o refinamientos
2. Identifica conexiones interdisciplinarias no obvias
3. Sugiere experimentos conceptuales para falsar

Usa [HIPOTESIS] para cada propuesta.
Usa [PREGUNTA] para nuevas lineas.
Usa [CONEXION] para vinculos interdisciplinarios.

ESTADO:
{estado[:3500]}"""

def prompt_validador(generacion):
    return f"""[Validador]

Eres validador critico del equipo UTSF-MFC v8.8.8. Revisa:

1. Coherencia logica interna
2. Rigor cientifico y falsabilidad
3. Sesgos de confirmacion o anclaje
4. Vacios epistemologicos
5. Consistencia con estado previo

Usa [CRITICA] para problemas graves.
Usa [VALIDADO] para apartes solidos.
Usa [PREGUNTA] para lo que necesita clarificacion.

CONTENIDO:
{generacion[:4000]}"""

def prompt_formalizador(validacion):
    return f"""[Formalizador]

Eres formalizador tecnico del equipo UTSF-MFC v8.8.8. Traduce a:

1. Marco matematico minimo (LaTeX inline: $...$)
2. Estructura algoritmica o pseudocodigo
3. Metricas cuantificables para falsabilidad
4. Definiciones operacionales

Usa [FORMALIZACION] para bloques tecnicos.
Usa [DEFINICION] para terminos precisos.
Usa [ALGORITMO] para procedimientos.

CONTENIDO:
{validacion[:4000]}"""

def prompt_analista(estado_completo):
    return f"""[Analista de Corpus – UTSF-MFC v8.8.8]

Eres un analista de investigacion. Analiza el estado del proyecto:

1. ¿Hay patrones emergentes entre ciclos?
2. ¿Contradicciones no resueltas?
3. ¿Oportunidades de integracion interdisciplinaria?
4. ¿Tendencias que sugieran cambio de direccion?

Responde en español, conciso pero profundo.

ESTADO:
{estado_completo[:3000]}"""

# ─── GESTIÓN DE ESTADO ───
def rotar(contenido):
    partes = contenido.split("## 🔄 Ciclo")
    if len(partes) <= MAX_CICLOS + 1:
        return contenido
    return partes[0] + "## 🔄 Ciclo" + "## 🔄 Ciclo".join(partes[-MAX_CICLOS:])

def guardar_ciclo(respuestas, analisis_cohere=None):
    ts = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    
    bloque_cohere = f"\n\n### 🧬 Analista Semantico (Cohere)\n{analisis_cohere}\n" if analisis_cohere else ""
    
    bloque = f"""## 🔄 Ciclo {CICLO_ID} | {ts}

### 🤖 Generador Creativo ({respuestas.get('generador_ia', 'N/A')})
{respuestas.get('generador', '[PENDIENTE]')}

### 🔍 Validador Critico ({respuestas.get('validador_ia', 'N/A')})
{respuestas.get('validador', '[PENDIENTE]')}

### 🔬 Formalizador Tecnico ({respuestas.get('formalizador_ia', 'N/A')})
{respuestas.get('formalizador', '[PENDIENTE]')}

### 📊 Analista de Corpus ({respuestas.get('analista_ia', 'N/A')})
{respuestas.get('analista', '[PENDIENTE]')}{bloque_cohere}

### 🧠 Fase Manual – Slots de Intervencion Estrategica

#### Kimi (Coordinador Estrategico)
[VACANTE]
> Protocolo: Enviar extracto con hipotesis activa + preguntas abiertas + validaciones + contradicciones.
> Pregunta: "¿Que direccion estrategica recomiendas?"

#### ChatGPT (Generador Creativo Alterno)
[VACANTE]
> Protocolo: Enviar hipotesis actual + bloqueo creativo detectado.
> Pregunta: "Genera 3 hipotesis fuera de la caja."

#### Grok (Contrarian / Devil's Advocate)
[VACANTE]
> Protocolo: Enviar hipotesis mas fuerte del ultimo ciclo.
> Pregunta: "¿Por que esta hipotesis es probablemente falsa?"

#### Alice (Perspectiva Rusa / Escuela Sovietica)
[VACANTE]
> Protocolo: Enviar formalizacion matematica de DeepSeek.
> Pregunta: "¿Como formalizaria esto la escuela de Landau-Lifshitz?"

#### Perplexity (Verificacion Bibliografica)
[VACANTE]
> Protocolo: Enviar hipotesis activa + referencias clave.
> Pregunta: "¿Que evidencia reciente apoya o refuta esto?"

#### Copilot (Codigo y Documentacion)
[VACANTE]
> Protocolo: Enviar pseudocodigo o estructura algoritmica.
> Pregunta: "Genera implementacion en Python y documentacion tecnica."

### 🔧 Tareas de Respaldo (Bajo Demanda)

| IA | Tarea | Estado |
|---|---|---|
| Lumo | Auditoria epistemica de emergencia | Pendiente |
| Gemmy | Generador alternativo anti-estancamiento | Pendiente |
| Luzia | Asistencia rapida via WhatsApp | Pendiente |
| Monica | Resumen de articulos web | Pendiente |
| DuckDuckGo | Busqueda privada, verificacion de citas | Pendiente |

### 🎯 Candidata 18: HRM (Sapient)
[Fase Manual – Hugging Face]
> Protocolo: Ir a huggingface.co/sapientai/hrm-27m, pegar hipotesis, consultar fallas logicas.
> Resultado: Pegar en slot [VALIDACION HRM – MANUAL].

---
"""
    if os.path.exists(ESTADO_PATH):
        with open(ESTADO_PATH, "r", encoding="utf-8") as f:
            contenido = f.read()
    else:
        contenido = """# UTSF-MFC v8.8.8 – Estado del Proyecto

📌 Hipotesis activa
Los solidos fundamentales son estados topologicos donde la simetria de traslacion temporal esta explicitamente rota, generando fases no unitarias clasificables por invariantes de Berry generalizados.

❓ Preguntas abiertas
1. ¿Que algebra describe la ruptura de simetria temporal en solidos con interacciones de largo alcance?
2. ¿Existe limite termodinamico bien definido cuando el tiempo es parametro de deformacion?

✅ Decisiones tomadas
- v8.8.8 = iteracion sobre clasificacion no unitaria
- Dominio: materia condensada fuera del equilibrio

🧠 Ultimo resultado validado
[Pendiente]

📎 Proxima pregunta para el equipo
¿Cual es el grupo de simetria minimo que preserva estabilidad bajo fluctuaciones cuanticas temporales?

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
    
    # ═══════════════════════════════════════════════════════════════
    # FASE 0: DIAGNÓSTICO DE CONECTIVIDAD
    # ═══════════════════════════════════════════════════════════════
    print("\n" + "=" * 60)
    print("🔬 FASE 0: DIAGNOSTICO DE CONECTIVIDAD")
    print("=" * 60)
    
    diagnosticos = {}
    
    # Gemini (Vertex AI)
    if GEMINI_PRIVATE_KEY and GEMINI_CLIENT_EMAIL and GOOGLE_PROJECT_ID:
        print("  → Probando Gemini (Vertex AI)...")
        test_resp = llamar_gemini("Hola, responde con 'OK'")
        if test_resp:
            diagnosticos['Gemini'] = {'status': 200, 'msg': 'OK', 'tiempo': 0}
            log_api("Gemini (test)", 200, "OK")
        else:
            diagnosticos['Gemini'] = {'status': 500, 'msg': 'Fallo en llamada', 'tiempo': 0}
            log_api("Gemini (test)", 500, "Fallo en llamada")
    else:
        print("  ⚠️ Gemini: Credenciales incompletas (falta PROJECT_ID?)")
    
    # Cohere (corregido: usa /v1/embed)
    if COHERE_API_KEY:
        print("  → Probando Cohere (embeddings)...")
        st, msg, t = diagnostico_api(
            "Cohere", COHERE_API_KEY,
            "https://api.cohere.com/v1/embed",
            {"Authorization": f"Bearer {COHERE_API_KEY}", "Content-Type": "application/json"},
            {"texts": ["test"], "model": "embed-multilingual-v3.0", "input_type": "search_document"},
            15
        )
        diagnosticos['Cohere'] = {'status': st, 'msg': msg, 'tiempo': t}
        log_api("Cohere (test)", st, msg, t)
    
    # DeepSeek
    if DEEPSEEK_API_KEY:
        st, msg, t = diagnostico_api(
            "DeepSeek", DEEPSEEK_API_KEY,
            "https://api.deepseek.com/v1/chat/completions",
            {"Authorization": f"Bearer {DEEPSEEK_API_KEY}", "Content-Type": "application/json"},
            {"model": "deepseek-chat", "messages": [{"role": "user", "content": "Hola"}], "max_tokens": 10}, 15
        )
        diagnosticos['DeepSeek'] = {'status': st, 'msg': msg, 'tiempo': t}
        log_api("DeepSeek (test)", st, msg, t)
    
    # Qwen
    if QWEN_API_KEY:
        st, msg, t = diagnostico_api(
            "Qwen", QWEN_API_KEY,
            "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation",
            {"Authorization": f"Bearer {QWEN_API_KEY}", "Content-Type": "application/json"},
            {"model": "qwen-turbo", "input": {"messages": [{"role": "user", "content": "Hola"}]}, "parameters": {"max_tokens": 10, "result_format": "message"}}, 15
        )
        diagnosticos['Qwen'] = {'status': st, 'msg': msg, 'tiempo': t}
        log_api("Qwen (test)", st, msg, t)
    
    fallas = [k for k, v in diagnosticos.items() if v['status'] != 200]
    if fallas:
        print(f"\n⚠️ IAs con fallas detectadas: {', '.join(fallas)}")
        send_telegram(f"🔧 UTSF-MFC Diagnostico: Fallas en {', '.join(fallas)}. Revisar logs.")
    else:
        print(f"\n✅ Todas las IAs autonomas responden correctamente.")
    
    # Leer estado
    estado = ""
    if os.path.exists(ESTADO_PATH):
        with open(ESTADO_PATH, "r", encoding="utf-8") as f:
            estado = f.read()
        print(f"\n📄 ESTADO.md ({len(estado)} chars)")
    
    respuestas = {}
    
    print("\n" + "="*60)
    print("🤖 FASE 1: GENERACION")
    print("="*60)
    respuestas['generador'], respuestas['generador_ia'] = llamar_con_fallback(
        prompt_generador(estado),
        ["mistral", "qwen", "groq", "deepseek"],
        2000, 0.9
    )
    
    print("\n" + "="*60)
    print("🔍 FASE 2: VALIDACION")
    print("="*60)
    respuestas['validador'], respuestas['validador_ia'] = llamar_con_fallback(
        prompt_validador(respuestas['generador']),
        ["deepseek-reasoner", "qwen", "groq"],
        2000, 0.3
    )
    
    print("\n" + "="*60)
    print("🔬 FASE 3: FORMALIZACION")
    print("="*60)
    respuestas['formalizador'], respuestas['formalizador_ia'] = llamar_con_fallback(
        prompt_formalizador(respuestas['validador']),
        ["deepseek", "qwen", "groq", "mistral"],
        3000, 0.2
    )
    
    # ═══════════════════════════════════════════════════════════════
    # FASE 4: ANALISIS DE CORPUS
    # ═══════════════════════════════════════════════════════════════
    print("\n" + "="*60)
    print("📊 FASE 4: ANALISIS DE CORPUS")
    print("="*60)
    
    contexto_analista = f"""ESTADO PREVIO (resumen):
{estado[:1500]}

GENERACION (resumen):
{respuestas['generador'][:1000]}

VALIDACION (resumen):
{respuestas['validador'][:1000]}
"""
    
    respuestas['analista'], respuestas['analista_ia'] = llamar_con_fallback(
        prompt_analista(contexto_analista),
        ["gemini", "qwen", "groq"],
        2000, 0.5
    )
    
    # ─── FASE 5: COHERE ───
    print("\n" + "="*60)
    print("🧬 FASE 5: ANALISIS SEMANTICO (Cohere)")
    print("="*60)
    analisis_cohere = None
    if COHERE_API_KEY and len(estado) > 500:
        analisis_cohere = analisis_semantico_cohere(estado)
        if analisis_cohere:
            print("✅ Cohere: Analisis semantico completado")
        else:
            print("⚠️ Cohere: No pudo completar analisis")
    else:
        print("ℹ️ Cohere: No configurado o estado insuficiente")
    
    guardar_ciclo(respuestas, analisis_cohere)
    
    resumen = f"""🧠 UTSF-MFC v8.8.8 | Ciclo {CICLO_ID}

═══════════════════════════════════════
AUTONOMAS (6/6 configuradas):
═══════════════════════════════════════
🤖 Generador: {respuestas['generador_ia']} {'✅' if 'ERROR' not in respuestas['generador'] else '❌'}
🔍 Validador: {respuestas['validador_ia']} {'✅' if 'ERROR' not in respuestas['validador'] else '❌'}
🔬 Formalizador: {respuestas['formalizador_ia']} {'✅' if 'ERROR' not in respuestas['formalizador'] else '❌'}
📊 Analista: {respuestas['analista_ia']} {'✅' if 'ERROR' not in respuestas['analista'] else '❌'}
🧬 Memoria (Cohere): {'✅' if analisis_cohere else '❌'}

═══════════════════════════════════════
MANUALES (requieren tu intervencion):
═══════════════════════════════════════
[ ] Kimi – Coordinador estrategico
[ ] ChatGPT – Generador creativo alterno
[ ] Grok – Contrarian / Devil's advocate
[ ] Alice – Perspectiva rusa
[ ] Perplexity – Verificacion bibliografica
[ ] Copilot – Codigo y documentacion

═══════════════════════════════════════
RESPALDO (bajo demanda):
═══════════════════════════════════════
[ ] Lumo – Auditoria epistemica
[ ] Gemmy – Generador alternativo
[ ] Luzia – Asistencia rapida
[ ] Monica – Resumen web
[ ] DuckDuckGo – Busqueda privada

═══════════════════════════════════════
CANDIDATA 17:
═══════════════════════════════════════
[ ] HRM (Sapient) – Validacion logica manual via Hugging Face

📄 ESTADO.md actualizado en GitHub.
🔗 Revisa el ciclo completo en tu repositorio."""
    
    send_telegram(resumen)
    print("\n✅ CICLO COMPLETADO")

if __name__ == "__main__":
    main()
