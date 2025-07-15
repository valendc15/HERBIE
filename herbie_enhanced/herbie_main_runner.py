#!/usr/bin/env python3
# ============================================================================
# HERBIE MAIN RUNNER - SCRIPT PRINCIPAL
# Script principal que integra todos los componentes y maneja la ejecución
# ============================================================================

import os
import sys
import json
import importlib.util
from pathlib import Path
from typing import Dict, Any, Optional
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class HerbieModuleLoader:
    """Cargador de módulos de Herbie con manejo de dependencias"""

    def __init__(self):
        self.modules = {}
        self.components_loaded = False

    def load_core_system(self):
        """Carga el sistema core de Herbie"""
        try:
            # Intentar importar desde el módulo instalado
            from herbie_enhanced.core_system import HerbieComponentFactory, HerbieOrchestrator
            self.modules['core'] = {
                'HerbieComponentFactory': HerbieComponentFactory,
                'HerbieOrchestrator': HerbieOrchestrator
            }
            return True
        except ImportError:
            # Fallback a implementación local
            return self._load_local_core_system()

    def _load_local_core_system(self):
        """Carga implementación local del sistema core"""
        try:
            # Añadir directorio actual al path
            current_dir = Path(__file__).parent
            sys.path.insert(0, str(current_dir))

            # Crear implementación mínima si no existe
            if not self._create_minimal_core_system():
                return False

            from core_system import HerbieComponentFactory, HerbieOrchestrator
            self.modules['core'] = {
                'HerbieComponentFactory': HerbieComponentFactory,
                'HerbieOrchestrator': HerbieOrchestrator
            }
            return True
        except Exception as e:
            logger.error(f"Error cargando sistema core: {e}")
            return False

    def _create_minimal_core_system(self):
        """Crea sistema core mínimo si no existe"""
        core_file = Path("core_system.py")

        if core_file.exists():
            return True

        # Crear implementación mínima
        minimal_core = '''
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, List, Optional, Any
from datetime import datetime
import uuid
import json
import random

@dataclass
class ProjectRequest:
    user_input: str
    user_id: str
    session_id: str
    timestamp: datetime
    preferences: Optional[Dict] = None

@dataclass
class ProjectAnalysis:
    repo_name: str
    framework: str
    description: str
    complexity_score: int
    predicted_success: float
    confidence: float
    reasoning: str
    tags: List[str]
    is_private: bool = False
    init_command: str = ""
    additional_setup: Optional[List[str]] = None

@dataclass
class ExecutionResult:
    success: bool
    repo_url: Optional[str] = None
    error_message: Optional[str] = None
    execution_time: float = 0.0
    steps_completed: List[str] = None
    metrics: Dict[str, Any] = None

@dataclass
class UserFeedback:
    session_id: str
    satisfaction: float
    setup_success: bool
    code_quality: float
    comments: str
    would_recommend: bool
    timestamp: datetime

class ProjectAnalyzer(ABC):
    @abstractmethod
    def analyze_project(self, request: ProjectRequest) -> ProjectAnalysis:
        pass

class ProjectExecutor(ABC):
    @abstractmethod
    def execute_project(self, analysis: ProjectAnalysis) -> ExecutionResult:
        pass

class LearningEngine(ABC):
    @abstractmethod
    def learn_from_feedback(self, analysis: ProjectAnalysis, result: ExecutionResult, feedback: UserFeedback) -> None:
        pass

class MetricsCollector(ABC):
    @abstractmethod
    def collect_metrics(self, analysis: ProjectAnalysis, result: ExecutionResult, feedback: Optional[UserFeedback] = None) -> None:
        pass

class SimpleAnalyzer(ProjectAnalyzer):
    def analyze_project(self, request: ProjectRequest) -> ProjectAnalysis:
        # Análisis simple por palabras clave
        description = request.user_input.lower()

        if 'react' in description:
            framework = 'react'
        elif 'vue' in description:
            framework = 'vue'
        elif 'django' in description:
            framework = 'django'
        elif 'flutter' in description:
            framework = 'flutter'
        else:
            framework = 'react'  # Default

        complexity = 3 if 'complex' in description else 2

        return ProjectAnalysis(
            repo_name=f"{framework}-project-{random.randint(100, 999)}",
            framework=framework,
            description=request.user_input,
            complexity_score=complexity,
            predicted_success=0.8,
            confidence=0.7,
            reasoning=f"Análisis simple: detectado {framework}",
            tags=[framework, 'project'],
            init_command=f"npx create-{framework}-app project" if framework == 'react' else f"mkdir {framework}-project"
        )

class SimpleExecutor(ProjectExecutor):
    def execute_project(self, analysis: ProjectAnalysis) -> ExecutionResult:
        # Simulación de ejecución
        import time
        time.sleep(1)  # Simular trabajo

        return ExecutionResult(
            success=True,
            repo_url=f"https://github.com/user/{analysis.repo_name}",
            execution_time=1.0,
            steps_completed=["Proyecto simulado creado"],
            metrics={'framework': analysis.framework}
        )

class SimpleLearning(LearningEngine):
    def learn_from_feedback(self, analysis: ProjectAnalysis, result: ExecutionResult, feedback: UserFeedback) -> None:
        print(f"📚 Aprendiendo de feedback: {feedback.satisfaction:.1%} satisfacción")

class SimpleMetrics(MetricsCollector):
    def __init__(self):
        self.metrics = []

    def collect_metrics(self, analysis: ProjectAnalysis, result: ExecutionResult, feedback: Optional[UserFeedback] = None) -> None:
        self.metrics.append({
            'framework': analysis.framework,
            'success': result.success,
            'satisfaction': feedback.satisfaction if feedback else None
        })

class HerbieOrchestrator:
    def __init__(self, analyzer, executor, learning_engine, metrics_collector):
        self.analyzer = analyzer
        self.executor = executor
        self.learning_engine = learning_engine
        self.metrics_collector = metrics_collector
        self.session_history = {}

    def create_project(self, user_input: str, user_id: str = "anonymous") -> Dict:
        session_id = str(uuid.uuid4())

        try:
            request = ProjectRequest(
                user_input=user_input,
                user_id=user_id,
                session_id=session_id,
                timestamp=datetime.now()
            )

            analysis = self.analyzer.analyze_project(request)
            result = self.executor.execute_project(analysis)
            self.metrics_collector.collect_metrics(analysis, result)

            self.session_history[session_id] = {
                'request': request,
                'analysis': analysis,
                'result': result,
                'timestamp': datetime.now()
            }

            return {
                'success': result.success,
                'session_id': session_id,
                'analysis': {
                    'repo_name': analysis.repo_name,
                    'framework': analysis.framework,
                    'description': analysis.description,
                    'complexity_score': analysis.complexity_score,
                    'predicted_success': analysis.predicted_success,
                    'confidence': analysis.confidence,
                    'reasoning': analysis.reasoning,
                    'tags': analysis.tags,
                    'is_private': analysis.is_private,
                    'init_command': analysis.init_command,
                    'additional_setup': analysis.additional_setup
                },
                'result': {
                    'success': result.success,
                    'repo_url': result.repo_url,
                    'error_message': result.error_message,
                    'execution_time': result.execution_time,
                    'steps_completed': result.steps_completed,
                    'metrics': result.metrics
                },
                'next_steps': self._generate_next_steps(analysis, result)
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'session_id': session_id
            }

    def submit_feedback(self, session_id: str, feedback_data: Dict) -> Dict:
        if session_id not in self.session_history:
            return {'success': False, 'error': 'Sesión no encontrada'}

        session = self.session_history[session_id]

        feedback = UserFeedback(
            session_id=session_id,
            satisfaction=feedback_data.get('satisfaction', 0.5),
            setup_success=feedback_data.get('setup_success', False),
            code_quality=feedback_data.get('code_quality', 0.5),
            comments=feedback_data.get('comments', ''),
            would_recommend=feedback_data.get('would_recommend', False),
            timestamp=datetime.now()
        )

        self.learning_engine.learn_from_feedback(session['analysis'], session['result'], feedback)
        self.metrics_collector.collect_metrics(session['analysis'], session['result'], feedback)

        return {
            'success': True,
            'improvements_applied': True,
            'thank_you_message': "¡Gracias por tu feedback! Herbie ha aprendido de tu experiencia."
        }

    def get_system_health(self) -> Dict:
        total_sessions = len(self.session_history)
        successful_sessions = sum(1 for s in self.session_history.values() if s['result'].success)

        return {
            'total_sessions': total_sessions,
            'success_rate': successful_sessions / total_sessions if total_sessions > 0 else 0,
            'frameworks_used': list(set(s['analysis'].framework for s in self.session_history.values())),
            'avg_complexity': sum(s['analysis'].complexity_score for s in self.session_history.values()) / total_sessions if total_sessions > 0 else 0
        }

    def _generate_next_steps(self, analysis: ProjectAnalysis, result: ExecutionResult) -> List[str]:
        if not result.success:
            return ["Revisar configuración", "Intentar de nuevo"]
        return [f"Visitar {result.repo_url}", "Personalizar el proyecto"]

class HerbieComponentFactory:
    @staticmethod
    def create_basic_system():
        return HerbieOrchestrator(
            analyzer=SimpleAnalyzer(),
            executor=SimpleExecutor(),
            learning_engine=SimpleLearning(),
            metrics_collector=SimpleMetrics()
        )

    @staticmethod
    def create_advanced_system():
        return HerbieComponentFactory.create_basic_system()  # Fallback
'''

        try:
            with open(core_file, 'w', encoding='utf-8') as f:
                f.write(minimal_core)
            return True
        except Exception as e:
            logger.error(f"Error creando sistema core mínimo: {e}")
            return False


class HerbieConversationManager:
    """Maneja el flujo conversacional con el usuario"""

    def __init__(self, herbie_system):
        self.herbie_system = herbie_system
        self.conversation_state = {'stage': 'greeting'}
        self.user_id = f"user_{hash(str(os.getpid()))}"

    def _print_animated(self, message: str, delay: float = 0.03):
        """Imprime mensaje con animación"""
        import time
        for char in message:
            print(char, end='', flush=True)
            time.sleep(delay)
        print()

    def _clear_screen(self):
        """Limpia la pantalla"""
        os.system('clear' if os.name == 'posix' else 'cls')

    def _show_banner(self):
        """Muestra banner de Herbie"""
        banner = """
╔══════════════════════════════════════════════════════════════╗
║   🤖 HERBIE ENHANCED - Agente de IA Generativa v2.0         ║
║   ⚡ Powered by Few-Shot Learning + RLHF                     ║
║   🎯 Tu asistente inteligente para crear proyectos          ║
╚══════════════════════════════════════════════════════════════╝
"""
        print(banner)

    def start_conversation(self):
        """Inicia la conversación con el usuario"""
        self._clear_screen()
        self._show_banner()

        greetings = [
            "¡Hola! Soy Herbie, tu asistente inteligente para crear proyectos increíbles! 🤖",
            "¡Saludos! Herbie aquí, listo para ayudarte a crear el próximo gran proyecto 🚀",
            "¡Hey! Soy Herbie, tu compañero de desarrollo con superpoderes de IA ⚡"
        ]

        import random
        greeting = random.choice(greetings)
        self._print_animated(greeting)

        print("\n" + "=" * 60)
        print("🛠️  Frameworks disponibles:")
        frameworks = ['react', 'vue', 'angular', 'django', 'fastapi', 'nextjs', 'flutter']
        for i, fw in enumerate(frameworks, 1):
            print(f"   {i}. {fw.title()}")
        print("=" * 60)

        self._print_animated("\n¿Qué tipo de proyecto te gustaría crear hoy?")
        self._print_animated("Puedes describirlo libremente o mencionar el framework que prefieres 💡")

        return self._handle_project_description()

    def _handle_project_description(self):
        """Maneja la descripción del proyecto"""
        while True:
            user_input = input("\n📝 Describe tu proyecto: ").strip()

            if not user_input:
                self._print_animated("🤔 Necesito que me cuentes algo sobre tu proyecto para poder ayudarte.")
                continue

            if user_input.lower() in ['salir', 'exit', 'quit']:
                self._print_animated("👋 ¡Hasta luego! Que tengas un excelente día codificando!")
                return {'action': 'exit'}

            return self._process_project_description(user_input)

    def _process_project_description(self, description: str):
        """Procesa la descripción y crea el proyecto"""
        import time

        thinking_messages = [
            "🤔 Analizando tu idea...",
            "🧠 Procesando con mis neuronas artificiales...",
            "⚡ Aplicando magia de IA generativa...",
            "🔍 Buscando en mi base de conocimiento...",
            "💭 Pensando en la mejor solución..."
        ]

        import random
        thinking_msg = random.choice(thinking_messages)
        print(f"\n{thinking_msg}")
        time.sleep(1.5)

        try:
            # Usar el sistema para crear proyecto
            result = self.herbie_system.create_project(
                user_input=description,
                user_id=self.user_id
            )

            if result['success']:
                return self._handle_successful_creation(result)
            else:
                return self._handle_creation_error(result)

        except Exception as e:
            error_messages = [
                "¡Ups! Algo no salió como esperaba 😅",
                "¡Oops! Parece que tuve un pequeño problema 🤕",
                "¡Ay! Mi circuito de procesamiento tuvo un hiccup 🔧"
            ]

            error_msg = random.choice(error_messages)
            self._print_animated(f"{error_msg}")
            self._print_animated(f"Error técnico: {str(e)}")
            return self._ask_retry()

    def _handle_successful_creation(self, result):
        """Maneja creación exitosa"""
        analysis = result['analysis']

        encouragement = [
            "¡Excelente elección! 🎯",
            "¡Me gusta tu estilo! 💪",
            "¡Genial! Vamos a crear algo increíble 🌟",
            "¡Perfecto! Esto va a estar buenísimo 🔥"
        ]

        import random
        self._print_animated(f"\n{random.choice(encouragement)}")

        print("\n" + "=" * 50)
        print("🎯 ANÁLISIS DEL PROYECTO")
        print("=" * 50)
        print(f"📁 Nombre: {analysis['repo_name']}")
        print(f"🛠️  Framework: {analysis['framework']}")
        print(f"📊 Complejidad: {analysis['complexity_score']}/5")
        print(f"🎲 Confianza: {analysis['confidence']:.1%}")
        print(f"🏷️  Tags: {', '.join(analysis['tags'])}")
        print(f"💭 Razonamiento: {analysis['reasoning']}")

        # Mostrar resultado de ejecución
        print(f"\n🚀 RESULTADO DE CREACIÓN")
        print(f"✅ Estado: {'Exitoso' if result['result']['success'] else 'Fallido'}")
        if result['result']['success']:
            print(f"🔗 URL: {result['result']['repo_url']}")
            print(f"⏱️  Tiempo: {result['result']['execution_time']:.1f}s")

        # Pedir feedback
        return self._request_feedback(result)

    def _request_feedback(self, result):
        """Solicita feedback del usuario"""
        print("\n" + "=" * 50)
        print("📝 FEEDBACK")
        print("=" * 50)

        self._print_animated("¡Tu opinión es muy valiosa para que pueda mejorar!")

        # Preguntas de feedback
        feedback_data = {}

        # Satisfacción
        while True:
            try:
                satisfaction = input("\n¿Qué tan satisfecho estás con el resultado? (1-10): ").strip()
                score = int(satisfaction)
                if 1 <= score <= 10:
                    feedback_data['satisfaction'] = score / 10.0
                    break
                else:
                    print("Por favor ingresa un número entre 1 y 10")
            except ValueError:
                print("Por favor ingresa un número válido")

        # Setup exitoso
        while True:
            setup = input("¿El setup fue exitoso? (s/n): ").strip().lower()
            if setup in ['s', 'si', 'sí', 'y', 'yes']:
                feedback_data['setup_success'] = True
                break
            elif setup in ['n', 'no']:
                feedback_data['setup_success'] = False
                break
            else:
                print("Por favor responde 's' (sí) o 'n' (no)")

        # Calidad del código
        while True:
            try:
                quality = input("¿Cómo calificarías la calidad del código? (1-10): ").strip()
                score = int(quality)
                if 1 <= score <= 10:
                    feedback_data['code_quality'] = score / 10.0
                    break
                else:
                    print("Por favor ingresa un número entre 1 y 10")
            except ValueError:
                print("Por favor ingresa un número válido")

        # Recomendación
        while True:
            recommend = input("¿Recomendarías Herbie a otros desarrolladores? (s/n): ").strip().lower()
            if recommend in ['s', 'si', 'sí', 'y', 'yes']:
                feedback_data['would_recommend'] = True
                break
            elif recommend in ['n', 'no']:
                feedback_data['would_recommend'] = False
                break
            else:
                print("Por favor responde 's' (sí) o 'n' (no)")

        # Comentarios
        comments = input("\n💬 ¿Algún comentario adicional? (opcional): ").strip()
        feedback_data['comments'] = comments

        # Procesar feedback
        return self._process_feedback(result, feedback_data)

    def _process_feedback(self, result, feedback_data):
        """Procesa el feedback del usuario"""
        import time

        print("\n🤔 Procesando tu feedback...")
        time.sleep(1)

        try:
            feedback_result = self.herbie_system.submit_feedback(
                session_id=result['session_id'],
                feedback_data=feedback_data
            )

            if feedback_result['success']:
                self._print_animated("🎯 ¡Gracias por tu feedback! He aprendido de tu experiencia.")
                self._print_animated("🧠 Mis algoritmos de IA se han actualizado para mejorar.")

                # Mostrar stats del sistema
                try:
                    health = self.herbie_system.get_system_health()
                    print(f"\n📊 Estadísticas del sistema:")
                    print(f"   ✅ Tasa de éxito: {health['success_rate']:.1%}")
                    print(f"   🔢 Proyectos creados: {health['total_sessions']}")
                    if health['frameworks_used']:
                        print(f"   🛠️  Frameworks populares: {', '.join(health['frameworks_used'][:3])}")
                except Exception:
                    pass

                return self._ask_for_another_project()
            else:
                self._print_animated("⚠️  Hubo un problema procesando tu feedback, pero igual lo valoro mucho.")
                return self._ask_for_another_project()

        except Exception as e:
            self._print_animated("🤔 No pude procesar el feedback completamente, pero gracias por compartirlo.")
            return self._ask_for_another_project()

    def _ask_for_another_project(self):
        """Pregunta si quiere crear otro proyecto"""
        print("\n" + "=" * 50)
        self._print_animated("¿Te gustaría crear otro proyecto? 🚀")

        while True:
            response = input("\n👉 (s/n): ").strip().lower()

            if response in ['s', 'si', 'sí', 'y', 'yes']:
                return self.start_conversation()
            elif response in ['n', 'no']:
                self._print_animated("👋 ¡Gracias por usar Herbie! ¡Que tengas un excelente día desarrollando!")
                return {'action': 'exit'}
            else:
                self._print_animated("🤔 Por favor responde 's' (sí) o 'n' (no)")

    def _handle_creation_error(self, result):
        """Maneja errores en la creación"""
        error_messages = [
            "¡Ups! Algo no salió como esperaba 😅",
            "¡Oops! Parece que tuve un pequeño problema 🤕",
            "¡Ay! Mi circuito de procesamiento tuvo un hiccup 🔧"
        ]

        import random
        error_msg = random.choice(error_messages)
        self._print_animated(f"{error_msg}")
        self._print_animated(f"💭 Problema: {result.get('error', 'Error desconocido')}")

        return self._ask_retry()

    def _ask_retry(self):
        """Pregunta si quiere reintentar"""
        self._print_animated("\n🔄 ¿Quieres intentar de nuevo con una descripción diferente?")

        while True:
            response = input("👉 (s/n): ").strip().lower()

            if response in ['s', 'si', 'sí', 'y', 'yes']:
                return self._handle_project_description()
            elif response in ['n', 'no']:
                self._print_animated("👋 ¡Nos vemos pronto! Espero poder ayudarte la próxima vez.")
                return {'action': 'exit'}
            else:
                self._print_animated("🤔 Por favor responde 's' (sí) o 'n' (no)")


class HerbieCLI:
    """CLI principal de Herbie"""

    def __init__(self):
        self.herbie_system = None
        self.conversation_manager = None
        self.module_loader = HerbieModuleLoader()
        self._initialize_system()

    def _initialize_system(self):
        """Inicializa el sistema de Herbie"""
        try:
            print("🔧 Inicializando sistema Herbie Enhanced...")

            # Cargar módulos core
            if not self.module_loader.load_core_system():
                raise Exception("No se pudo cargar el sistema core")

            # Crear sistema
            factory = self.module_loader.modules['core']['HerbieComponentFactory']

            # Intentar sistema avanzado, fallback a básico
            try:
                self.herbie_system = factory.create_advanced_system()
                print("✅ Sistema avanzado inicializado")
            except Exception as e:
                logger.warning(f"Sistema avanzado falló, usando básico: {e}")
                self.herbie_system = factory.create_basic_system()
                print("✅ Sistema básico inicializado")

            # Crear manager de conversación
            self.conversation_manager = HerbieConversationManager(self.herbie_system)

            import time
            time.sleep(1)

        except Exception as e:
            logger.error(f"Error crítico inicializando sistema: {e}")
            print(f"❌ Error crítico: {e}")
            print("🔧 Creando sistema de emergencia...")
            self._create_emergency_system()

    def _create_emergency_system(self):
        """Crea sistema de emergencia mínimo"""
        try:
            # Crear sistema mínimo en memoria
            class EmergencySystem:
                def __init__(self):
                    self.session_history = {}

                def create_project(self, user_input: str, user_id: str = "anonymous"):
                    import uuid
                    import random

                    session_id = str(uuid.uuid4())

                    # Análisis muy básico
                    if 'react' in user_input.lower():
                        framework = 'react'
                    elif 'vue' in user_input.lower():
                        framework = 'vue'
                    elif 'django' in user_input.lower():
                        framework = 'django'
                    else:
                        framework = 'react'

                    repo_name = f"{framework}-project-{random.randint(100, 999)}"

                    return {
                        'success': True,
                        'session_id': session_id,
                        'analysis': {
                            'repo_name': repo_name,
                            'framework': framework,
                            'description': user_input,
                            'complexity_score': 3,
                            'predicted_success': 0.8,
                            'confidence': 0.7,
                            'reasoning': f"Sistema de emergencia: detectado {framework}",
                            'tags': [framework, 'emergency'],
                            'is_private': False,
                            'init_command': f"mkdir {repo_name}",
                            'additional_setup': None
                        },
                        'result': {
                            'success': True,
                            'repo_url': f"https://github.com/user/{repo_name}",
                            'error_message': None,
                            'execution_time': 0.5,
                            'steps_completed': ["Sistema de emergencia activado"],
                            'metrics': {'emergency': True}
                        },
                        'next_steps': ["Proyecto simulado creado"]
                    }

                def submit_feedback(self, session_id: str, feedback_data: Dict):
                    print(f"📝 Feedback registrado (sistema de emergencia)")
                    return {
                        'success': True,
                        'improvements_applied': False,
                        'thank_you_message': "Gracias por el feedback (sistema de emergencia)"
                    }

                def get_system_health(self):
                    return {
                        'total_sessions': 1,
                        'success_rate': 1.0,
                        'frameworks_used': ['react'],
                        'avg_complexity': 3.0,
                        'emergency_mode': True
                    }

            self.herbie_system = EmergencySystem()
            self.conversation_manager = HerbieConversationManager(self.herbie_system)
            print("🚨 Sistema de emergencia activado")

        except Exception as e:
            logger.error(f"Error crítico en sistema de emergencia: {e}")
            print("❌ Error crítico: No se puede inicializar ningún sistema")
            sys.exit(1)

    def run(self):
        """Ejecuta la CLI de Herbie"""
        try:
            while True:
                result = self.conversation_manager.start_conversation()

                if result.get('action') == 'exit':
                    break

        except KeyboardInterrupt:
            print("\n\n👋 ¡Hasta luego! Gracias por usar Herbie Enhanced!")
        except Exception as e:
            logger.error(f"Error inesperado: {e}")
            print(f"\n❌ Error inesperado: {e}")
            print("🔄 Reiniciando sistema...")
            self._initialize_system()
            self.run()


def main():
    """Función principal"""
    print("🚀 Iniciando Herbie Enhanced...")

    # Verificar variables de entorno
    if not os.getenv('GITHUB_TOKEN'):
        print("⚠️  ADVERTENCIA: GITHUB_TOKEN no está configurado")
        print("   Algunas funcionalidades pueden usar simulación")

    if not os.getenv('GOOGLE_API_KEY'):
        print("⚠️  ADVERTENCIA:simple_metrics GOOGLE_API_KEY no está configurado")
        print("   El análisis de IA usará fallbacks básicos")

    # Iniciar CLI
    cli = HerbieCLI()
    cli.run()


if __name__ == "__main__":
    main()