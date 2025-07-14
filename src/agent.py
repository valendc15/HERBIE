
import time
from typing import Dict, Optional
from dataclasses import dataclass
from src.utils.logging_config import setup_logging
from src.framework_helper import FrameworkHelper
from src.github_client import GitHubClient
from src.training.few_shot_manager import FewShotManager

logger = setup_logging()


@dataclass
class AgentResponse:
    success: bool
    result: Optional[Dict] = None
    error: Optional[str] = None
    response_time: float = 0.0
    confidence: float = 0.0
    reasoning: Optional[str] = None


class HerbieAgent:
    def __init__(self, testing: bool = False):
        self.testing = testing
        self.framework_helper = FrameworkHelper()
        self.github_client = GitHubClient()
        self.few_shot_manager = FewShotManager()

        # Configuración de entrenamiento
        self.training_mode = "few_shot"  # few_shot, cot, hybrid
        self.confidence_threshold = 0.7

        logger.info("Herbie Agent inicializado")

    def process_request(self, user_input: str, user_id: str = "default") -> AgentResponse:
        """Procesa solicitud del usuario"""

        start_time = time.time()

        try:
            logger.info(f"Procesando solicitud: {user_input[:50]}...")

            # Validar entrada
            if not self.validate_input(user_input):
                return AgentResponse(
                    success=False,
                    error="Entrada inválida",
                    response_time=time.time() - start_time
                )

            # Procesar según modo de entrenamiento
            if self.training_mode == "few_shot":
                result = self.process_with_few_shot(user_input)
            elif self.training_mode == "cot":
                result = self.process_with_cot(user_input)
            else:
                result = self.process_with_hybrid(user_input)

            response_time = time.time() - start_time

            logger.info(f"Solicitud procesada exitosamente en {response_time:.2f}s")

            return AgentResponse(
                success=True,
                result=result,
                response_time=response_time,
                confidence=self.calculate_confidence(result),
                reasoning=self.generate_reasoning(user_input, result)
            )

        except Exception as e:
            logger.error(f"Error procesando solicitud: {str(e)}")

            return AgentResponse(
                success=False,
                error=str(e),
                response_time=time.time() - start_time
            )

    def validate_input(self, user_input: str) -> bool:
        """Valida entrada del usuario"""
        if not user_input or len(user_input.strip()) < 5:
            return False

        # Verificar palabras clave mínimas
        required_keywords = ['crear', 'app', 'aplicación', 'proyecto', 'api', 'web']
        return any(keyword in user_input.lower() for keyword in required_keywords)

    def calculate_confidence(self, result: Dict) -> float:
        """Calcula confianza en el resultado"""
        confidence = 0.5  # Base

        # Aumentar confianza si framework es reconocido
        if result.get('framework') in self.framework_helper.supported_frameworks:
            confidence += 0.3

        # Aumentar confianza si nombre es válido
        if result.get('repo_name') and len(result['repo_name']) > 3:
            confidence += 0.2

        return min(confidence, 1.0)

    def generate_reasoning(self, user_input: str, result: Dict) -> str:
        """Genera explicación del razonamiento"""
        reasoning = f"""
        Análisis del comando: "{user_input}"

        Framework detectado: {result.get('framework', 'No detectado')}
        Nombre sugerido: {result.get('repo_name', 'No generado')}
        Visibilidad: {'Privado' if result.get('is_private') else 'Público'}

        Factores considerados:
        - Palabras clave en el input
        - Patrones de naming estándar
        - Configuración por defecto del framework
        """

        return reasoning
