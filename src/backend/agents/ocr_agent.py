"""
OCR Agent for text extraction using GPT-5.1 (Improved with retry, timeout, caching, metrics).
"""
import logging
from typing import Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage

from ..config import (
    OPENAI_API_KEY, OPENAI_MODEL, OPENAI_MAX_TOKENS,
    AGENT_TIMEOUT_SECONDS, AGENT_RETRY_MAX_ATTEMPTS, AGENT_RETRY_MIN_WAIT, AGENT_RETRY_MAX_WAIT,
    CACHE_ENABLED, CACHE_TTL_SECONDS, CIRCUIT_BREAKER_ENABLED, METRICS_ENABLED
)
from ..utils.image_utils import verify_image_size
from ..utils.retry_utils import agent_retry
from ..utils.timeout_utils import with_timeout
from ..utils.cache_utils import get_cache_key, get_cached_result, set_cached_result
from ..utils.metrics_utils import track_agent_metrics, _noop_decorator
from ..utils.circuit_breaker import CircuitBreaker, CircuitBreakerOpenError
from ..models.agent_results import OCRResult

logger = logging.getLogger(__name__)


class OCRAgent:
    """Agent specialized in text extraction and OCR."""
    
    def __init__(self):
        """Initialize OCR Agent with GPT-5.1 model."""
        self.llm = ChatOpenAI(
            model=OPENAI_MODEL,
            api_key=OPENAI_API_KEY,
            max_tokens=OPENAI_MAX_TOKENS,
            temperature=0.1  # Lower temperature for OCR accuracy
        )
        logger.info("ℹ️ OCRAgent initialized")
    
    def _analyze_internal(self, image_base64: str, context: str = "") -> Dict[str, Any]:
        """Internal analysis method."""
        verify_image_size(image_base64, "OCR AGENT")
        logger.info("ℹ️ Starting OCR text extraction...")
        
        prompt = f"""Eres un experto en OCR y análisis de texto en imágenes para investigación OSINT.

{f'CONTEXTO: {context}' if context else ''}

Tu tarea es extraer y analizar TODO el texto visible en esta imagen con máxima precisión.

Proporciona:

1. TEXTO EXTRAÍDO:
   - Lista TODOS los textos visibles (carteles, letreros, matrículas, etiquetas, pantallas)
   - Mantén el formato y orden espacial cuando sea relevante
   - Indica el idioma de cada texto si es diferente

2. MATRÍCULAS Y IDENTIFICADORES:
   - Números de matrícula de vehículos (formato completo)
   - Códigos de identificación visibles
   - Números de serie o referencias

3. SEÑALIZACIÓN Y CARTELES:
   - Nombres de calles, edificios, negocios
   - Señales de tráfico con texto
   - Publicidad o anuncios

4. TEXTO EN PANTALLAS:
   - Información en monitores, televisores, dispositivos
   - URLs, nombres de usuario, mensajes

5. TEXTO PARCIAL O BORROSO:
   - Texto difícil de leer (indica incertidumbre)
   - Texto parcialmente visible

6. CONTEXTO DEL TEXTO:
   - Relación del texto con elementos visuales
   - Posible significado o importancia investigativa

Si no hay texto visible, indica claramente "No se detectó texto en la imagen".
Si el texto está en otro alfabeto, transcríbelo fielmente."""

        message = HumanMessage(
            content=[
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": image_base64}}
            ]
        )
        
        response = self.llm.invoke([message])
        ocr_text = response.content
        has_text = "no se detectó texto" not in ocr_text.lower()
        
        logger.info(f"✅ OCR extraction complete - Text found: {has_text}")
        
        return {
            "agent": "ocr",
            "status": "success",
            "analysis": ocr_text,
            "has_text": has_text,
            "confidence": "high" if has_text else "n/a"
        }
    
    @(track_agent_metrics("ocr") if METRICS_ENABLED else _noop_decorator)
    @with_timeout(AGENT_TIMEOUT_SECONDS)
    @agent_retry(max_attempts=AGENT_RETRY_MAX_ATTEMPTS, min_wait=AGENT_RETRY_MIN_WAIT, max_wait=AGENT_RETRY_MAX_WAIT)
    def _analyze_with_protection(self, image_base64: str, context: str = "") -> Dict[str, Any]:
        """Analyze with retry, timeout, and circuit breaker protection."""
        if CIRCUIT_BREAKER_ENABLED:
            breaker = CircuitBreaker(failure_threshold=5, recovery_timeout=60.0)
            try:
                return breaker.call(self._analyze_internal, image_base64, context)
            except CircuitBreakerOpenError as e:
                logger.error(f"❌ Circuit breaker OPEN: {e}")
                return {
                    "agent": "ocr",
                    "status": "error",
                    "error": "Circuit breaker is open - service temporarily unavailable",
                    "analysis": "OCR extraction unavailable",
                    "has_text": False
                }
        else:
            return self._analyze_internal(image_base64, context)
    
    def analyze(self, image_base64: str, context: str = "") -> Dict[str, Any]:
        """Extract all visible text from image."""
        try:
            if CACHE_ENABLED:
                cache_key = get_cache_key(image_base64, "ocr", context)
                cached = get_cached_result(cache_key, CACHE_TTL_SECONDS)
                if cached:
                    logger.info("💾 Using cached OCR result")
                    return cached
            
            result = self._analyze_with_protection(image_base64, context)
            
            if CACHE_ENABLED and result.get("status") == "success":
                cache_key = get_cache_key(image_base64, "ocr", context)
                set_cached_result(cache_key, result, CACHE_TTL_SECONDS)
            
            try:
                validated = OCRResult(**result)
                return validated.model_dump()
            except Exception as validation_error:
                logger.warning(f"⚠️ Result validation failed: {validation_error}")
                return result
            
        except TimeoutError as e:
            logger.error(f"⏱️ OCR analysis timeout: {e}")
            return {
                "agent": "ocr",
                "status": "timeout",
                "error": str(e),
                "analysis": "OCR extraction timed out",
                "has_text": False
            }
        except Exception as e:
            logger.error(f"❌ OCR extraction failed: {e}")
            return {
                "agent": "ocr",
                "status": "error",
                "error": str(e),
                "analysis": "OCR extraction failed",
                "has_text": False
            }

