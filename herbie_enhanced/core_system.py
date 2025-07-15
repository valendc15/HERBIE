
from abc import ABC, abstractmethod
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
import json
import uuid
import logging

# ============================================================================
# CONFIGURACIÓN DE LOGGING
# ============================================================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================================
# MODELOS DE DATOS
# ============================================================================

@dataclass
class ProjectRequest:
    """Solicitud de proyecto del usuario"""
    user_input: str
    user_id: str
    session_id: str
    timestamp: datetime
    preferences: Optional[Dict] = None


@dataclass
class ProjectAnalysis:
    """Análisis procesado del proyecto"""
    repo_name: str
    framework: str
    description: str
    complexity_score: int  # 1-5
    predicted_success: float  # 0-1
    confidence: float  # 0-1
    reasoning: str
    tags: List[str]
    is_private: bool = False
    init_command: str = ""
    additional_setup: Optional[List[str]] = None


@dataclass
class ExecutionResult:
    """Resultado de la ejecución"""
    success: bool
    repo_url: Optional[str] = None
    error_message: Optional[str] = None
    execution_time: float = 0.0
    steps_completed: List[str] = None
    metrics: Dict[str, Any] = None


@dataclass
class UserFeedback:
    """Feedback del usuario"""
    session_id: str
    satisfaction: float  # 0-1
    setup_success: bool
    code_quality: float  # 0-1
    comments: str
    would_recommend: bool
    timestamp: datetime


# ============================================================================
# INTERFACES ABSTRACTAS
# ============================================================================

class ProjectAnalyzer(ABC):
    """Interfaz para analizadores de proyectos"""

    @abstractmethod
    def analyze_project(self, request: ProjectRequest) -> ProjectAnalysis:
        """Analiza una solicitud de proyecto"""
        pass


class ProjectExecutor(ABC):
    """Interfaz para ejecutores de proyectos"""

    @abstractmethod
    def execute_project(self, analysis: ProjectAnalysis) -> ExecutionResult:
        """Ejecuta la creación del proyecto"""
        pass


class LearningEngine(ABC):
    """Interfaz para motores de aprendizaje"""

    @abstractmethod
    def learn_from_feedback(self, analysis: ProjectAnalysis,
                            result: ExecutionResult,
                            feedback: UserFeedback) -> None:
        """Aprende del feedback del usuario"""
        pass


class MetricsCollector(ABC):
    """Interfaz para recolección de métricas"""

    @abstractmethod
    def collect_metrics(self, analysis: ProjectAnalysis,
                        result: ExecutionResult,
                        feedback: Optional[UserFeedback] = None) -> None:
        """Recolecta métricas del proceso"""
        pass


# ============================================================================
# SISTEMA CENTRAL - ORCHESTRATOR
# ============================================================================

class HerbieOrchestrator:
    """
    Orchestrador principal que coordina todos los componentes
    """

    def __init__(self,
                 analyzer: ProjectAnalyzer,
                 executor: ProjectExecutor,
                 learning_engine: LearningEngine,
                 metrics_collector: MetricsCollector):
        self.analyzer = analyzer
        self.executor = executor
        self.learning_engine = learning_engine
        self.metrics_collector = metrics_collector
        self.session_history = {}

    def create_project(self, user_input: str, user_id: str = "anonymous") -> Dict:
        """
        Proceso principal de creación de proyecto

        Args:
            user_input: Descripción del proyecto del usuario
            user_id: ID del usuario

        Returns:
            Dict con resultado completo del proceso
        """
        session_id = str(uuid.uuid4())

        try:
            # 1. Crear solicitud
            request = ProjectRequest(
                user_input=user_input,
                user_id=user_id,
                session_id=session_id,
                timestamp=datetime.now()
            )

            logger.info(f"Procesando solicitud: {session_id}")

            # 2. Analizar proyecto con IA
            analysis = self.analyzer.analyze_project(request)
            logger.info(f"Análisis completado: {analysis.framework} - {analysis.complexity_score}/5")

            # 3. Ejecutar creación
            result = self.executor.execute_project(analysis)
            logger.info(f"Ejecución {'exitosa' if result.success else 'fallida'}")

            # 4. Recolectar métricas
            self.metrics_collector.collect_metrics(analysis, result)

            # 5. Guardar en historial
            self.session_history[session_id] = {
                'request': request,
                'analysis': analysis,
                'result': result,
                'timestamp': datetime.now()
            }

            return {
                'success': result.success,
                'session_id': session_id,
                'analysis': asdict(analysis),
                'result': asdict(result),
                'next_steps': self._generate_next_steps(analysis, result)
            }

        except Exception as e:
            logger.error(f"Error en creación de proyecto: {e}")
            return {
                'success': False,
                'error': str(e),
                'session_id': session_id
            }

    def submit_feedback(self, session_id: str, feedback_data: Dict) -> Dict:
        """
        Procesa feedback del usuario

        Args:
            session_id: ID de la sesión
            feedback_data: Datos del feedback

        Returns:
            Dict con resultado del procesamiento
        """
        if session_id not in self.session_history:
            return {'success': False, 'error': 'Sesión no encontrada'}

        session = self.session_history[session_id]

        # Crear objeto feedback
        feedback = UserFeedback(
            session_id=session_id,
            satisfaction=feedback_data.get('satisfaction', 0.5),
            setup_success=feedback_data.get('setup_success', False),
            code_quality=feedback_data.get('code_quality', 0.5),
            comments=feedback_data.get('comments', ''),
            would_recommend=feedback_data.get('would_recommend', False),
            timestamp=datetime.now()
        )

        # Procesar aprendizaje
        self.learning_engine.learn_from_feedback(
            session['analysis'],
            session['result'],
            feedback
        )

        # Actualizar métricas
        self.metrics_collector.collect_metrics(
            session['analysis'],
            session['result'],
            feedback
        )

        logger.info(f"Feedback procesado para sesión: {session_id}")

        return {
            'success': True,
            'improvements_applied': True,
            'thank_you_message': "¡Gracias por tu feedback! Herbie ha aprendido de tu experiencia."
        }

    def get_system_health(self) -> Dict:
        """
        Obtiene estado de salud del sistema

        Returns:
            Dict con métricas de salud
        """
        total_sessions = len(self.session_history)
        successful_sessions = sum(1 for s in self.session_history.values() if s['result'].success)

        return {
            'total_sessions': total_sessions,
            'success_rate': successful_sessions / total_sessions if total_sessions > 0 else 0,
            'active_since': min(
                s['timestamp'] for s in self.session_history.values()) if self.session_history else None,
            'frameworks_used': list(set(s['analysis'].framework for s in self.session_history.values())),
            'avg_complexity': sum(s['analysis'].complexity_score for s in
                                  self.session_history.values()) / total_sessions if total_sessions > 0 else 0
        }

    def _generate_next_steps(self, analysis: ProjectAnalysis, result: ExecutionResult) -> List[str]:
        """Genera pasos siguientes recomendados"""
        if not result.success:
            return [
                "Revisar los requisitos del sistema",
                "Consultar la documentación de instalación",
                "Intentar con un framework diferente"
            ]

        return [
            f"Explorar el código generado en: {result.repo_url}",
            "Personalizar la configuración según tus necesidades",
            "Ejecutar tests y validar funcionalidad",
            "Desplegar en tu entorno preferido"
        ]


# ============================================================================
# FACTORY PATTERN PARA COMPONENTES
# ============================================================================

class HerbieComponentFactory:
    """Factory para crear componentes de Herbie"""

    @staticmethod
    def create_basic_system() -> HerbieOrchestrator:
        """Crea un sistema básico de Herbie"""
        from .components.basic_components import BasicProjectAnalyzer
        from .components.basic_components import BasicProjectExecutor
        from .components.basic_components import SimpleLearningEngine
        from .components.basic_components import SimpleMetricsCollector

        return HerbieOrchestrator(
            analyzer=BasicProjectAnalyzer(),
            executor=BasicProjectExecutor(),
            learning_engine=SimpleLearningEngine(),
            metrics_collector=SimpleMetricsCollector()
        )

    @staticmethod
    def create_advanced_system() -> HerbieOrchestrator:
        """Crea un sistema avanzado de Herbie"""
        from .components.few_shot_analyzer import FewShotProjectAnalyzer
        from .components.ehanced_executor import EnhancedProjectExecutor
        from .components.rlhf_learning import RLHFLearningEngine
        from .components.advanced_metrics import AdvancedMetricsCollector

        return HerbieOrchestrator(
            analyzer=FewShotProjectAnalyzer(),
            executor=EnhancedProjectExecutor(),
            learning_engine=RLHFLearningEngine(),
            metrics_collector=AdvancedMetricsCollector()
        )


# ============================================================================
# EJEMPLO DE USO
# ============================================================================

def main():
    """Ejemplo de uso del sistema"""

    # Crear sistema avanzado
    herbie = HerbieComponentFactory.create_advanced_system()

    # Crear proyecto
    result = herbie.create_project(
        user_input="Quiero crear una aplicación React para gestionar tareas con autenticación",
        user_id="user123"
    )

    print("=== RESULTADO DE CREACIÓN ===")
    print(f"Éxito: {result['success']}")
    print(f"Framework: {result['analysis']['framework']}")
    print(f"Complejidad: {result['analysis']['complexity_score']}/5")
    print(f"Confianza: {result['analysis']['confidence']:.2f}")

    if result['success']:
        print(f"Repositorio: {result['result']['repo_url']}")

        # Simular feedback
        feedback = herbie.submit_feedback(
            session_id=result['session_id'],
            feedback_data={
                'satisfaction': 0.9,
                'setup_success': True,
                'code_quality': 0.8,
                'comments': 'Excelente trabajo, muy intuitivo',
                'would_recommend': True
            }
        )

        print("=== FEEDBACK PROCESADO ===")
        print(f"Aprendizaje aplicado: {feedback['improvements_applied']}")

    # Estado del sistema
    health = herbie.get_system_health()
    print("=== SALUD DEL SISTEMA ===")
    print(f"Tasa de éxito: {health['success_rate']:.1%}")
    print(f"Sesiones totales: {health['total_sessions']}")


if __name__ == "__main__":
    main()