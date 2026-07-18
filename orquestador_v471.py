#!/usr/bin/env python3
"""
UTSF-MFC v4.7.1 — Orquestador Multi-IA Autónomo (Debug + Robustez)
Correcciones: logging exhaustivo, manejo de errores, verificación de secrets
"""

import os
import sys
import json
import asyncio
import aiohttp
import traceback
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict

DEBUG = os.getenv("DEBUG", "0") == "1"

def log(msg: str):
    print(msg, flush=True)

def debug(msg: str):
    if DEBUG:
        print(f"[DEBUG] {msg}", flush=True)

# ============================================
# CONFIGURACIÓN
# ============================================

PROMPT_NUCLEO = """UTSF-MFC v8.8.8 | Director: Ernesto Perfecto
MISIÓN: Correspondencia 19 sólidos (5 Platónicos + 13 Arquimedianos + Esfera) ↔ disciplinas científicas ↔ 5 regímenes temporales (δ₀ Estructura, δ₁ Interacción, δ₂ Emergencia, δ₃' Síntesis, δ₃ Totalidad)

RESULTADOS VALIDADOS:
• D₁₁₇: 117 disciplinas clasificadas
• TC1: δ₃ no ocupable establemente (0/117)
• κ inter-IA ≈ 0.78-0.84
• ρ=0.512 (p<0.0001) atemporal ↔ interdisciplinariedad

REGLAS: [DUDA]=incertidumbre | [HECHO]=dato | [HIPÓTESIS]=conjura
Español. ≤300 palabras. Sin referencias inventadas."""

PREGUNTA_ACTIVA = os.getenv("UTSF_PREGUNTA", 
    "Validar TC1: ¿Existe alguna disciplina que desafíe la imposibilidad de ocupar δ₃ establemente? Analizar evidencia contraria y fortaleza del teorema.")

@dataclass
class RespuestaIA:
    ia_id: str
    modelo: str
    contenido: str
    confianza: float
    latencia_ms: int
    tokens_entrada: int
    tokens_salida: int
    error: Optional[str] = None
    http_status: int = 0

class OrquestadorUTSF:
    def __init__(self):
        self.resultados = []
        self.timestamp = datetime.utcnow().isoformat()
        
        # Verificar qué secrets están presentes
        log("=== VERIFICACIÓN DE SECRETS EN PYTHON ===")
        secrets = {
            "GROQ_API_KEY": os.getenv("GROQ_API_KEY"),
            "MISTRAL_API_KEY": os.getenv("MISTRAL_API_KEY"),
            "COHERE_API_KEY": os.getenv("COHERE_API_KEY"),
            "GOOGLE_API_KEY": os.getenv("GOOGLE_API_KEY"),
            "QWEN_API_KEY": os.getenv("QWEN_API_KEY"),
            "OPENROUTER_API_KEY": os.getenv("OPENROUTER_API_KEY"),
        }
        for name, value in secrets.items():
            status = "✅" if value else "❌"
            debug(f"{status} {name}: {'presente' if value else 'AUSENTE'}")
        
        # Configuración de endpoints
        self.config = {
            "groq": {
                "url": "https://api.groq.com/openai/v1/chat/completions",
                "key": os.getenv("GROQ_API_KEY"),
                "modelo": "llama-3.1-70b-versatile",
                "peso": 1.0,
                "activo": bool(os.getenv("GROQ_API_KEY"))
            },
            "mistral": {
                "url": "https://api.mistral.ai/v1/chat/completions",
                "key": os.getenv("MISTRAL_API_KEY"),
                "modelo": "mistral-small-latest",
                "peso": 1.0,
                "activo": bool(os.getenv("MISTRAL_API_KEY"))
            },
            "cohere": {
                "url": "https://api.cohere.ai/v1/chat/completions",
                "key": os.getenv("COHERE_API_KEY"),
                "modelo": "command-r-plus",
                "peso": 0.9,
                "activo": bool(os.getenv("COHERE_API_KEY"))
            },
            "gemini": {
                "url": "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent",
                "key": os.getenv("GOOGLE_API_KEY"),
                "modelo": "gemini-1.5-flash",
                "peso": 1.0,
                "activo": bool(os.getenv("GOOGLE_API_KEY"))
            },
            "qwen": {
                "url": "https://dashscope-intl.aliyuncs.com/compatible-mode/v1/chat/completions",
                "key": os.getenv("QWEN_API_KEY"),
                "modelo": "qwen-3-72b",
                "peso": 1.0,
                "activo": bool(os.getenv("QWEN_API_KEY"))
            },
            "openrouter": {
                "url": "https://openrouter.ai/api/v1/chat/completions",
                "key": os.getenv("OPENROUTER_API_KEY"),
                "modelo": "meta-llama/llama-3.1-8b-instruct:free",
                "peso": 0.8,
                "activo": bool(os.getenv("OPENROUTER_API_KEY"))
            }
        }
        
        log(f"\nIAs configuradas: {sum(1 for c in self.config.values() if c['activo'])}/6")
    
    async def _llamar_api(self, ia_id: str, session: aiohttp.ClientSession, 
                         url: str, headers: dict, payload: dict, 
                         timeout_sec: int = 30) -> tuple:
        """Helper genérico para llamar APIs con logging completo."""
        cfg = self.config[ia_id]
        debug(f"{ia_id}: Enviando request a {url}")
        debug(f"{ia_id}: Modelo = {cfg['modelo']}")
        debug(f"{ia_id}: Headers = {list(headers.keys())}")
        
        inicio = asyncio.get_event_loop().time()
        try:
            async with session.post(
                url,
                headers=headers,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=timeout_sec)
            ) as resp:
                latencia = int((asyncio.get_event_loop().time() - inicio) * 1000)
                debug(f"{ia_id}: HTTP {resp.status} en {latencia}ms")
                
                text = await resp.text()
                debug(f"{ia_id}: Respuesta raw (primeros 200 chars): {text[:200]}")
                
                if resp.status == 200:
                    try:
                        data = json.loads(text)
                        return data, None, resp.status, latencia
                    except json.JSONDecodeError as e:
                        return None, f"JSON inválido: {e}", resp.status, latencia
                else:
                    return None, f"HTTP {resp.status}: {text[:200]}", resp.status, latencia
                    
        except asyncio.TimeoutError:
            latencia = int((asyncio.get_event_loop().time() - inicio) * 1000)
            return None, f"Timeout después de {timeout_sec}s", 0, latencia
        except Exception as e:
            latencia = int((asyncio.get_event_loop().time() - inicio) * 1000)
            return None, f"Excepción: {str(e)}\n{traceback.format_exc()}", 0, latencia
    
    async def consultar_groq(self, session: aiohttp.ClientSession) -> RespuestaIA:
        ia_id = "groq"
        cfg = self.config[ia_id]
        if not cfg["activo"]:
            debug(f"{ia_id}: No activa (sin API key)")
            return RespuestaIA(ia_id, cfg["modelo"], "", 0.0, 0, 0, 0, "No configurado", 0)
        
        data, error, status, latencia = await self._llamar_api(
            ia_id, session,
            cfg["url"],
            {"Authorization": f"Bearer {cfg['key']}", "Content-Type": "application/json"},
            {
                "model": cfg["modelo"],
                "messages": [
                    {"role": "system", "content": PROMPT_NUCLEO},
                    {"role": "user", "content": PREGUNTA_ACTIVA}
                ],
                "temperature": 0.3,
                "max_tokens": 1024
            }
        )
        
        if error:
            log(f"❌ {ia_id}: {error}")
            return RespuestaIA(ia_id, cfg["modelo"], "", 0.0, latencia, 0, 0, error, status)
        
        try:
            contenido = data["choices"][0]["message"]["content"]
            tokens_in = data.get("usage", {}).get("prompt_tokens", 0)
            tokens_out = data.get("usage", {}).get("completion_tokens", 0)
            log(f"✅ {ia_id}: Respuesta recibida ({len(contenido)} chars)")
            return RespuestaIA(ia_id, cfg["modelo"], contenido, 0.85, latencia, tokens_in, tokens_out, None, 200)
        except (KeyError, IndexError) as e:
            error = f"Formato inesperado: {e}"
            log(f"❌ {ia_id}: {error}")
            return RespuestaIA(ia_id, cfg["modelo"], "", 0.0, latencia, 0, 0, error, status)
    
    async def consultar_mistral(self, session: aiohttp.ClientSession) -> RespuestaIA:
        ia_id = "mistral"
        cfg = self.config[ia_id]
        if not cfg["activo"]:
            return RespuestaIA(ia_id, cfg["modelo"], "", 0.0, 0, 0, 0, "No configurado", 0)
        
        data, error, status, latencia = await self._llamar_api(
            ia_id, session,
            cfg["url"],
            {"Authorization": f"Bearer {cfg['key']}", "Content-Type": "application/json"},
            {
                "model": cfg["modelo"],
                "messages": [
                    {"role": "system", "content": PROMPT_NUCLEO},
                    {"role": "user", "content": PREGUNTA_ACTIVA}
                ],
                "temperature": 0.3,
                "max_tokens": 1024
            }
        )
        
        if error:
            log(f"❌ {ia_id}: {error}")
            return RespuestaIA(ia_id, cfg["modelo"], "", 0.0, latencia, 0, 0, error, status)
        
        try:
            contenido = data["choices"][0]["message"]["content"]
            tokens_in = data.get("usage", {}).get("prompt_tokens", 0)
            tokens_out = data.get("usage", {}).get("completion_tokens", 0)
            log(f"✅ {ia_id}: Respuesta recibida ({len(contenido)} chars)")
            return RespuestaIA(ia_id, cfg["modelo"], contenido, 0.82, latencia, tokens_in, tokens_out, None, 200)
        except (KeyError, IndexError) as e:
            error = f"Formato inesperado: {e}"
            log(f"❌ {ia_id}: {error}")
            return RespuestaIA(ia_id, cfg["modelo"], "", 0.0, latencia, 0, 0, error, status)
    
    async def consultar_cohere(self, session: aiohttp.ClientSession) -> RespuestaIA:
        ia_id = "cohere"
        cfg = self.config[ia_id]
        if not cfg["activo"]:
            return RespuestaIA(ia_id, cfg["modelo"], "", 0.0, 0, 0, 0, "No configurado", 0)
        
        # Cohere v1/chat/completions (OpenAI-compatible)
        data, error, status, latencia = await self._llamar_api(
            ia_id, session,
            cfg["url"],
            {"Authorization": f"Bearer {cfg['key']}", "Content-Type": "application/json"},
            {
                "model": cfg["modelo"],
                "messages": [
                    {"role": "system", "content": PROMPT_NUCLEO},
                    {"role": "user", "content": PREGUNTA_ACTIVA}
                ],
                "temperature": 0.3,
                "max_tokens": 1024
            }
        )
        
        if error:
            log(f"❌ {ia_id}: {error}")
            return RespuestaIA(ia_id, cfg["modelo"], "", 0.0, latencia, 0, 0, error, status)
        
        try:
            contenido = data["choices"][0]["message"]["content"]
            log(f"✅ {ia_id}: Respuesta recibida ({len(contenido)} chars)")
            return RespuestaIA(ia_id, cfg["modelo"], contenido, 0.80, latencia, 0, 0, None, 200)
        except (KeyError, IndexError) as e:
            error = f"Formato inesperado: {e}"
            log(f"❌ {ia_id}: {error}")
            return RespuestaIA(ia_id, cfg["modelo"], "", 0.0, latencia, 0, 0, error, status)
    
    async def consultar_gemini(self, session: aiohttp.ClientSession) -> RespuestaIA:
        ia_id = "gemini"
        cfg = self.config[ia_id]
        if not cfg["activo"]:
            return RespuestaIA(ia_id, cfg["modelo"], "", 0.0, 0, 0, 0, "No configurado", 0)
        
        url = f"{cfg['url']}?key={cfg['key']}"
        data, error, status, latencia = await self._llamar_api(
            ia_id, session,
            url,
            {"Content-Type": "application/json"},
            {
                "contents": [{
                    "parts": [{
                        "text": f"{PROMPT_NUCLEO}\n\nPregunta: {PREGUNTA_ACTIVA}"
                    }]
                }],
                "generationConfig": {
                    "temperature": 0.3,
                    "maxOutputTokens": 1024
                }
            }
        )
        
        if error:
            log(f"❌ {ia_id}: {error}")
            return RespuestaIA(ia_id, cfg["modelo"], "", 0.0, latencia, 0, 0, error, status)
        
        try:
            contenido = data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
            log(f"✅ {ia_id}: Respuesta recibida ({len(contenido)} chars)")
            return RespuestaIA(ia_id, cfg["modelo"], contenido, 0.83, latencia, 0, 0, None, 200)
        except (KeyError, IndexError) as e:
            error = f"Formato inesperado: {e}"
            log(f"❌ {ia_id}: {error}")
            return RespuestaIA(ia_id, cfg["modelo"], "", 0.0, latencia, 0, 0, error, status)
    
    async def consultar_qwen(self, session: aiohttp.ClientSession) -> RespuestaIA:
        ia_id = "qwen"
        cfg = self.config[ia_id]
        if not cfg["activo"]:
            return RespuestaIA(ia_id, cfg["modelo"], "", 0.0, 0, 0, 0, "No configurado", 0)
        
        data, error, status, latencia = await self._llamar_api(
            ia_id, session,
            cfg["url"],
            {"Authorization": f"Bearer {cfg['key']}", "Content-Type": "application/json"},
            {
                "model": cfg["modelo"],
                "messages": [
                    {"role": "system", "content": PROMPT_NUCLEO},
                    {"role": "user", "content": PREGUNTA_ACTIVA}
                ],
                "temperature": 0.3,
                "max_tokens": 1024
            }
        )
        
        if error:
            log(f"❌ {ia_id}: {error}")
            return RespuestaIA(ia_id, cfg["modelo"], "", 0.0, latencia, 0, 0, error, status)
        
        try:
            contenido = data["choices"][0]["message"]["content"]
            tokens_in = data.get("usage", {}).get("prompt_tokens", 0)
            tokens_out = data.get("usage", {}).get("completion_tokens", 0)
            log(f"✅ {ia_id}: Respuesta recibida ({len(contenido)} chars)")
            return RespuestaIA(ia_id, cfg["modelo"], contenido, 0.84, latencia, tokens_in, tokens_out, None, 200)
        except (KeyError, IndexError) as e:
            error = f"Formato inesperado: {e}"
            log(f"❌ {ia_id}: {error}")
            return RespuestaIA(ia_id, cfg["modelo"], "", 0.0, latencia, 0, 0, error, status)
    
    async def consultar_openrouter(self, session: aiohttp.ClientSession) -> RespuestaIA:
        ia_id = "openrouter"
        cfg = self.config[ia_id]
        if not cfg["activo"]:
            return RespuestaIA(ia_id, cfg["modelo"], "", 0.0, 0, 0, 0, "No configurado", 0)
        
        data, error, status, latencia = await self._llamar_api(
            ia_id, session,
            cfg["url"],
            {
                "Authorization": f"Bearer {cfg['key']}",
                "HTTP-Referer": "https://github.com/ernesto/utsf-mfc",
                "X-Title": "UTSF-MFC v4.7.1",
                "Content-Type": "application/json"
            },
            {
                "model": cfg["modelo"],
                "messages": [
                    {"role": "system", "content": PROMPT_NUCLEO},
                    {"role": "user", "content": PREGUNTA_ACTIVA}
                ],
                "temperature": 0.3,
                "max_tokens": 1024
            }
        )
        
        if error:
            log(f"❌ {ia_id}: {error}")
            return RespuestaIA(ia_id, cfg["modelo"], "", 0.0, latencia, 0, 0, error, status)
        
        try:
            contenido = data["choices"][0]["message"]["content"]
            log(f"✅ {ia_id}: Respuesta recibida ({len(contenido)} chars)")
            return RespuestaIA(ia_id, cfg["modelo"], contenido, 0.75, latencia, 0, 0, None, 200)
        except (KeyError, IndexError) as e:
            error = f"Formato inesperado: {e}"
            log(f"❌ {ia_id}: {error}")
            return RespuestaIA(ia_id, cfg["modelo"], "", 0.0, latencia, 0, 0, error, status)

    def calcular_consensus(self, respuestas: List[RespuestaIA]) -> Dict:
        """Algoritmo de consenso ponderado por confianza y latencia."""
        validas = [r for r in respuestas if r.error is None and r.http_status == 200]
        
        log(f"\n=== RESUMEN DE RESPUESTAS ===")
        for r in respuestas:
            status = "✅" if r.error is None and r.http_status == 200 else f"❌ {r.error[:50]}"
            log(f"   {r.ia_id:12} | HTTP {r.http_status:3} | {status}")
        log(f"Validas: {len(validas)}/{len(respuestas)}")
        
        if not validas:
            return {
                "estado": "FALLO_TOTAL",
                "consenso": None,
                "motivo": "Ninguna IA respondió correctamente",
                "ias_fallidas": len(respuestas)
            }
        
        pesos = []
        for r in validas:
            peso_conf = r.confianza * self.config[r.ia_id]["peso"]
            peso_lat = 1.0 / (1 + r.latencia_ms / 1000)
            peso_total = peso_conf * 0.7 + peso_lat * 0.3
            pesos.append(peso_total)
        
        total_pesos = sum(pesos)
        pesos_norm = [p / total_pesos for p in pesos]
        
        idx_ganador = pesos_norm.index(max(pesos_norm))
        ganador = validas[idx_ganador]
        
        confianzas = [r.confianza for r in validas]
        acuerdo = 1.0 - (max(confianzas) - min(confianzas)) / max(confianzas) if max(confianzas) > 0 else 0
        
        return {
            "estado": "CONSENSO" if acuerdo > 0.6 else "DIVERGENCIA",
            "consenso": ganador.contenido[:500],
            "ia_ganadora": ganador.ia_id,
            "modelo_ganador": ganador.modelo,
            "confianza_consensus": round(sum(confianzas) / len(confianzas), 3),
            "nivel_acuerdo": round(acuerdo, 3),
            "ias_participantes": len(validas),
            "ias_fallidas": len(respuestas) - len(validas),
            "distribucion_pesos": {r.ia_id: round(p, 3) for r, p in zip(validas, pesos_norm)},
            "latencia_promedio_ms": round(sum(r.latencia_ms for r in validas) / len(validas)),
            "timestamp": self.timestamp
        }
    
    async def ejecutar_ciclo(self):
        """Pipeline completo: consulta paralela → consenso → registro → notificación."""
        log(f"\n{'='*60}")
        log(f"🚀 UTSF-MFC v4.7.1 | Ciclo: {self.timestamp}")
        log(f"📝 Pregunta activa: {PREGUNTA_ACTIVA[:80]}...")
        log(f"{'='*60}")
        
        async with aiohttp.ClientSession() as session:
            tareas = [
                self.consultar_groq(session),
                self.consultar_mistral(session),
                self.consultar_cohere(session),
                self.consultar_gemini(session),
                self.consultar_qwen(session),
                self.consultar_openrouter(session)
            ]
            
            respuestas = await asyncio.gather(*tareas)
            
            resultado = self.calcular_consensus(respuestas)
            
            self.guardar_resultados(respuestas, resultado)
            
            await self.notificar_telegram(resultado)
            
            return resultado
    
    def guardar_resultados(self, respuestas: List[RespuestaIA], consenso: Dict):
        """Guardar en archivos JSON con timestamp."""
        import os
        os.makedirs("respuestas", exist_ok=True)
        
        fecha = datetime.utcnow().strftime("%Y-%m-%d-%H%M")
        
        for r in respuestas:
            filename = f"respuestas/{fecha}_{r.ia_id}.json"
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(asdict(r), f, ensure_ascii=False, indent=2)
            debug(f"Guardado: {filename}")
        
        consenso["pregunta"] = PREGUNTA_ACTIVA
        consenso["prompt_nucleo"] = PROMPT_NUCLEO[:200]
        consenso["version_orquestador"] = "v4.7.1"
        
        with open(f"respuestas/{fecha}_CONSENSO.json", "w", encoding="utf-8") as f:
            json.dump(consenso, f, ensure_ascii=False, indent=2)
        
        log(f"\n💾 Resultados guardados en respuestas/{fecha}_*.json")
        log(f"   - {len(respuestas)} respuestas individuales")
        log(f"   - 1 archivo de consenso")
    
    async def notificar_telegram(self, consenso: Dict):
        """Notificar vía Telegram si está configurado."""
        bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        chat_id = os.getenv("TELEGRAM_CHAT_ID")
        
        if not bot_token or not chat_id:
            log("⚠️ Telegram no configurado (sin TELEGRAM_BOT_TOKEN o TELEGRAM_CHAT_ID)")
            return
        
        estado_emoji = "✅" if consenso["estado"] == "CONSENSO" else "⚠️"
        ias_ok = consenso.get('ias_participantes', 0)
        ias_fail = consenso.get('ias_fallidas', 0)
        
        mensaje = f"""{estado_emoji} UTSF-MFC v4.7.1 — Ciclo completado

📊 Resumen de IAs:
   ✅ Participantes: {ias_ok}
   ❌ Fallidas: {ias_fail}

📈 Métricas:
   Estado: {consenso['estado']}
   Confianza: {consenso['confianza_consensus']}
   Acuerdo: {consenso['nivel_acuerdo']}
   Latencia promedio: {consenso['latencia_promedio_ms']}ms

🏆 IA ganadora: {consenso['ia_ganadora']}

📝 Consenso (extracto):
{consenso['consenso'][:300] if consenso['consenso'] else 'N/A'}...

📁 Revisa respuestas/ en GitHub para detalles completos."""
        
        try:
            async with aiohttp.ClientSession() as session:
                resp = await session.post(
                    f"https://api.telegram.org/bot{bot_token}/sendMessage",
                    json={"chat_id": chat_id, "text": mensaje, "parse_mode": "HTML"}
                )
                if resp.status == 200:
                    log("📱 Notificación Telegram enviada correctamente")
                else:
                    error_text = await resp.text()
                    log(f"⚠️ Telegram respondió HTTP {resp.status}: {error_text[:100]}")
        except Exception as e:
            log(f"⚠️ Error notificando Telegram: {str(e)}")

async def main():
    """Punto de entrada principal del orquestador."""
    log(f"\n{'='*60}")
    log("  UTSF-MFC v4.7.1 — ORQUESTADOR MULTI-IA AUTÓNOMO")
    log("  Ernesto Perfecto | Director Científico")
    log(f"{'='*60}")
    
    orquestador = OrquestadorUTSF()
    resultado = await orquestador.ejecutar_ciclo()
    
    log(f"\n{'='*60}")
    log("RESULTADO FINAL DEL CONSENSO:")
    log(f"{'='*60}")
    log(json.dumps(resultado, indent=2, ensure_ascii=False))
    
    # Código de salida: 0 si hay consenso, 1 si fallo total
    if resultado["estado"] == "FALLO_TOTAL":
        log("\n❌ Ciclo terminado con fallo total")
        sys.exit(1)
    else:
        log(f"\n✅ Ciclo terminado: {resultado['estado']}")
        sys.exit(0)

if __name__ == "__main__":
    asyncio.run(main())
