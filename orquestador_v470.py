#!/usr/bin/env python3
"""
UTSF-MFC v4.7.0 — Orquestador Multi-IA Autónomo
5 motores: Groq, Mistral, Cohere, Gemini, Qwen
Fallback: OpenRouter
Ciclo: Consulta paralela → Consenso → Registro → Notificación
"""

import os
import json
import asyncio
import aiohttp
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
import random

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
    http_status: int = 200

class OrquestadorUTSF:
    def __init__(self):
        self.resultados = []
        self.timestamp = datetime.utcnow().isoformat()
        
        # Configuración de endpoints
        self.config = {
            "groq": {
                "url": "https://api.groq.com/openai/v1/chat/completions",
                "key": os.getenv("GROQ_API_KEY"),
                "modelo": "llama-4-70b-8192",
                "peso": 1.0,
                "activo": bool(os.getenv("GROQ_API_KEY"))
            },
            "mistral": {
                "url": "https://api.mistral.ai/v1/chat/completions",
                "key": os.getenv("MISTRAL_API_KEY"),
                "modelo": "mistral-large-latest",
                "peso": 1.0,
                "activo": bool(os.getenv("MISTRAL_API_KEY"))
            },
            "cohere": {
                "url": "https://api.cohere.ai/v1/generate",
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
                "modelo": "deepseek/deepseek-chat",
                "peso": 0.8,
                "activo": bool(os.getenv("OPENROUTER_API_KEY"))
            }
        }
    
    async def consultar_groq(self, session: aiohttp.ClientSession) -> RespuestaIA:
        cfg = self.config["groq"]
        if not cfg["activo"]:
            return RespuestaIA("groq", cfg["modelo"], "", 0.0, 0, 0, 0, "No configurado", 0)
        
        inicio = asyncio.get_event_loop().time()
        try:
            async with session.post(
                cfg["url"],
                headers={"Authorization": f"Bearer {cfg['key']}", "Content-Type": "application/json"},
                json={
                    "model": cfg["modelo"],
                    "messages": [
                        {"role": "system", "content": PROMPT_NUCLEO},
                        {"role": "user", "content": PREGUNTA_ACTIVA}
                    ],
                    "temperature": 0.3,
                    "max_tokens": 1024
                },
                timeout=aiohttp.ClientTimeout(total=30)
            ) as resp:
                latencia = int((asyncio.get_event_loop().time() - inicio) * 1000)
                if resp.status == 200:
                    data = await resp.json()
                    contenido = data["choices"][0]["message"]["content"]
                    tokens_in = data.get("usage", {}).get("prompt_tokens", 0)
                    tokens_out = data.get("usage", {}).get("completion_tokens", 0)
                    return RespuestaIA("groq", cfg["modelo"], contenido, 0.85, latencia, tokens_in, tokens_out, None, 200)
                else:
                    return RespuestaIA("groq", cfg["modelo"], "", 0.0, latencia, 0, 0, f"HTTP {resp.status}", resp.status)
        except Exception as e:
            return RespuestaIA("groq", cfg["modelo"], "", 0.0, 0, 0, 0, str(e), 0)
    
    async def consultar_mistral(self, session: aiohttp.ClientSession) -> RespuestaIA:
        cfg = self.config["mistral"]
        if not cfg["activo"]:
            return RespuestaIA("mistral", cfg["modelo"], "", 0.0, 0, 0, 0, "No configurado", 0)
        
        inicio = asyncio.get_event_loop().time()
        try:
            async with session.post(
                cfg["url"],
                headers={"Authorization": f"Bearer {cfg['key']}", "Content-Type": "application/json"},
                json={
                    "model": cfg["modelo"],
                    "messages": [
                        {"role": "system", "content": PROMPT_NUCLEO},
                        {"role": "user", "content": PREGUNTA_ACTIVA}
                    ],
                    "temperature": 0.3,
                    "max_tokens": 1024
                },
                timeout=aiohttp.ClientTimeout(total=30)
            ) as resp:
                latencia = int((asyncio.get_event_loop().time() - inicio) * 1000)
                if resp.status == 200:
                    data = await resp.json()
                    contenido = data["choices"][0]["message"]["content"]
                    tokens_in = data.get("usage", {}).get("prompt_tokens", 0)
                    tokens_out = data.get("usage", {}).get("completion_tokens", 0)
                    return RespuestaIA("mistral", cfg["modelo"], contenido, 0.82, latencia, tokens_in, tokens_out, None, 200)
                else:
                    return RespuestaIA("mistral", cfg["modelo"], "", 0.0, latencia, 0, 0, f"HTTP {resp.status}", resp.status)
        except Exception as e:
            return RespuestaIA("mistral", cfg["modelo"], "", 0.0, 0, 0, 0, str(e), 0)
    
    async def consultar_cohere(self, session: aiohttp.ClientSession) -> RespuestaIA:
        cfg = self.config["cohere"]
        if not cfg["activo"]:
            return RespuestaIA("cohere", cfg["modelo"], "", 0.0, 0, 0, 0, "No configurado", 0)
        
        inicio = asyncio.get_event_loop().time()
        try:
            async with session.post(
                cfg["url"],
                headers={"Authorization": f"Bearer {cfg['key']}", "Content-Type": "application/json"},
                json={
                    "model": cfg["modelo"],
                    "prompt": f"{PROMPT_NUCLEO}\n\nPregunta: {PREGUNTA_ACTIVA}\n\nRespuesta:",
                    "temperature": 0.3,
                    "max_tokens": 1024
                },
                timeout=aiohttp.ClientTimeout(total=30)
            ) as resp:
                latencia = int((asyncio.get_event_loop().time() - inicio) * 1000)
                if resp.status == 200:
                    data = await resp.json()
                    contenido = data.get("generations", [{}])[0].get("text", "")
                    return RespuestaIA("cohere", cfg["modelo"], contenido, 0.80, latencia, 0, 0, None, 200)
                else:
                    return RespuestaIA("cohere", cfg["modelo"], "", 0.0, latencia, 0, 0, f"HTTP {resp.status}", resp.status)
        except Exception as e:
            return RespuestaIA("cohere", cfg["modelo"], "", 0.0, 0, 0, 0, str(e), 0)
    
    async def consultar_gemini(self, session: aiohttp.ClientSession) -> RespuestaIA:
        cfg = self.config["gemini"]
        if not cfg["activo"]:
            return RespuestaIA("gemini", cfg["modelo"], "", 0.0, 0, 0, 0, "No configurado", 0)
        
        inicio = asyncio.get_event_loop().time()
        try:
            url = f"{cfg['url']}?key={cfg['key']}"
            async with session.post(
                url,
                headers={"Content-Type": "application/json"},
                json={
                    "contents": [{
                        "parts": [{
                            "text": f"{PROMPT_NUCLEO}\n\nPregunta: {PREGUNTA_ACTIVA}"
                        }]
                    }],
                    "generationConfig": {
                        "temperature": 0.3,
                        "maxOutputTokens": 1024
                    }
                },
                timeout=aiohttp.ClientTimeout(total=30)
            ) as resp:
                latencia = int((asyncio.get_event_loop().time() - inicio) * 1000)
                if resp.status == 200:
                    data = await resp.json()
                    contenido = data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                    return RespuestaIA("gemini", cfg["modelo"], contenido, 0.83, latencia, 0, 0, None, 200)
                else:
                    return RespuestaIA("gemini", cfg["modelo"], "", 0.0, latencia, 0, 0, f"HTTP {resp.status}", resp.status)
        except Exception as e:
            return RespuestaIA("gemini", cfg["modelo"], "", 0.0, 0, 0, 0, str(e), 0)
    
    async def consultar_qwen(self, session: aiohttp.ClientSession) -> RespuestaIA:
        cfg = self.config["qwen"]
        if not cfg["activo"]:
            return RespuestaIA("qwen", cfg["modelo"], "", 0.0, 0, 0, 0, "No configurado", 0)
        
        inicio = asyncio.get_event_loop().time()
        try:
            async with session.post(
                cfg["url"],
                headers={"Authorization": f"Bearer {cfg['key']}", "Content-Type": "application/json"},
                json={
                    "model": cfg["modelo"],
                    "messages": [
                        {"role": "system", "content": PROMPT_NUCLEO},
                        {"role": "user", "content": PREGUNTA_ACTIVA}
                    ],
                    "temperature": 0.3,
                    "max_tokens": 1024
                },
                timeout=aiohttp.ClientTimeout(total=30)
            ) as resp:
                latencia = int((asyncio.get_event_loop().time() - inicio) * 1000)
                if resp.status == 200:
                    data = await resp.json()
                    contenido = data["choices"][0]["message"]["content"]
                    tokens_in = data.get("usage", {}).get("prompt_tokens", 0)
                    tokens_out = data.get("usage", {}).get("completion_tokens", 0)
                    return RespuestaIA("qwen", cfg["modelo"], contenido, 0.84, latencia, tokens_in, tokens_out, None, 200)
                else:
                    return RespuestaIA("qwen", cfg["modelo"], "", 0.0, latencia, 0, 0, f"HTTP {resp.status}", resp.status)
        except Exception as e:
            return RespuestaIA("qwen", cfg["modelo"], "", 0.0, 0, 0, 0, str(e), 0)
    
    async def consultar_openrouter(self, session: aiohttp.ClientSession) -> RespuestaIA:
        cfg = self.config["openrouter"]
        if not cfg["activo"]:
            return RespuestaIA("openrouter", cfg["modelo"], "", 0.0, 0, 0, 0, "No configurado", 0)
        
        inicio = asyncio.get_event_loop().time()
        try:
            async with session.post(
                cfg["url"],
                headers={
                    "Authorization": f"Bearer {cfg['key']}",
                    "HTTP-Referer": "https://github.com/ernesto/utsf-mfc",
                    "X-Title": "UTSF-MFC v4.7.0"
                },
                json={
                    "model": cfg["modelo"],
                    "messages": [
                        {"role": "system", "content": PROMPT_NUCLEO},
                        {"role": "user", "content": PREGUNTA_ACTIVA}
                    ],
                    "temperature": 0.3,
                    "max_tokens": 1024
                },
                timeout=aiohttp.ClientTimeout(total=30)
            ) as resp:
                latencia = int((asyncio.get_event_loop().time() - inicio) * 1000)
                if resp.status == 200:
                    data = await resp.json()
                    contenido = data["choices"][0]["message"]["content"]
                    return RespuestaIA("openrouter", cfg["modelo"], contenido, 0.75, latencia, 0, 0, None, 200)
                else:
                    return RespuestaIA("openrouter", cfg["modelo"], "", 0.0, latencia, 0, 0, f"HTTP {resp.status}", resp.status)
        except Exception as e:
            return RespuestaIA("openrouter", cfg["modelo"], "", 0.0, 0, 0, 0, str(e), 0)
    
    def calcular_consensus(self, respuestas: List[RespuestaIA]) -> Dict:
        """Algoritmo de consenso ponderado por confianza y latencia."""
        validas = [r for r in respuestas if r.error is None and r.http_status == 200]
        
        if not validas:
            return {
                "estado": "FALLO_TOTAL",
                "consenso": None,
                "motivo": "Ninguna IA respondió correctamente",
                "ias_fallidas": len(respuestas)
            }
        
        # Ponderación: confianza * peso_config / latencia
        pesos = []
        for r in validas:
            peso_conf = r.confianza * self.config[r.ia_id]["peso"]
            peso_lat = 1.0 / (1 + r.latencia_ms / 1000)
            peso_total = peso_conf * 0.7 + peso_lat * 0.3
            pesos.append(peso_total)
        
        total_pesos = sum(pesos)
        pesos_norm = [p / total_pesos for p in pesos]
        
        # Seleccionar respuesta ganadora
        idx_ganador = pesos_norm.index(max(pesos_norm))
        ganador = validas[idx_ganador]
        
        # Calcular nivel de acuerdo (similitud de confianzas)
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
        print(f"🚀 UTSF-MFC v4.7.0 | Ciclo: {self.timestamp}")
        print(f"📝 Pregunta activa: {PREGUNTA_ACTIVA[:80]}...")
        
        async with aiohttp.ClientSession() as session:
            # Consultar todas las IAs en paralelo
            tareas = [
                self.consultar_groq(session),
                self.consultar_mistral(session),
                self.consultar_cohere(session),
                self.consultar_gemini(session),
                self.consultar_qwen(session),
                self.consultar_openrouter(session)
            ]
            
            respuestas = await asyncio.gather(*tareas)
            
            # Mostrar resultados individuales
            for r in respuestas:
                status = "✅" if r.error is None else f"❌ {r.error}"
                print(f"   {r.ia_id:12} | {r.modelo:20} | {status}")
            
            # Calcular consenso
            resultado = self.calcular_consensus(respuestas)
            
            # Guardar resultados
            self.guardar_resultados(respuestas, resultado)
            
            # Notificar si hay Telegram configurado
            await self.notificar_telegram(resultado)
            
            return resultado
    
    def guardar_resultados(self, respuestas: List[RespuestaIA], consenso: Dict):
        """Guardar en archivos JSON con timestamp."""
        import os
        os.makedirs("respuestas", exist_ok=True)
        
        fecha = datetime.utcnow().strftime("%Y-%m-%d-%H%M")
        
        # Guardar respuestas individuales
        for r in respuestas:
            filename = f"respuestas/{fecha}_{r.ia_id}.json"
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(asdict(r), f, ensure_ascii=False, indent=2)
        
        # Guardar consenso
        consenso["pregunta"] = PREGUNTA_ACTIVA
        consenso["prompt_nucleo"] = PROMPT_NUCLEO[:200]
        
        with open(f"respuestas/{fecha}_CONSENSO.json", "w", encoding="utf-8") as f:
            json.dump(consenso, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 Resultados guardados en respuestas/{fecha}_*.json")
    
    async def notificar_telegram(self, consenso: Dict):
        """Notificar vía Telegram si está configurado."""
        bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        chat_id = os.getenv("TELEGRAM_CHAT_ID")
        
        if not bot_token or not chat_id:
            return
        
        estado_emoji = "✅" if consenso["estado"] == "CONSENSO" else "⚠️"
        mensaje = f"""{estado_emoji} UTSF-MFC v4.7.0 — Ciclo completado

Estado: {consenso['estado']}
IAs participantes: {consenso['ias_participantes']}
IAs fallidas: {consenso['ias_fallidas']}
Confianza: {consenso['confianza_consensus']}
Acuerdo: {consenso['nivel_acuerdo']}
Latencia promedio: {consenso['latencia_promedio_ms']}ms

IA ganadora: {consenso['ia_ganadora']}

Consenso (extracto):
{consenso['consenso'][:300]}...

📁 Revisa respuestas/ en GitHub para detalles completos."""
        
        try:
            async with aiohttp.ClientSession() as session:
                await session.post(
                    f"https://api.telegram.org/bot{bot_token}/sendMessage",
                    json={"chat_id": chat_id, "text": mensaje, "parse_mode": "HTML"}
                )
            print("📱 Notificación Telegram enviada")
        except Exception as e:
            print(f"⚠️ Error notificando Telegram: {e}")

async def main():
    orquestador = OrquestadorUTSF()
    resultado = await orquestador.ejecutar_ciclo()
    
    print(f"\n{'='*60}")
    print("RESULTADO DEL CONSENSO:")
    print(f"{'='*60}")
    print(json.dumps(resultado, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    asyncio.run(main())
