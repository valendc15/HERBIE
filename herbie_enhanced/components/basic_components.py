# ============================================================================
# COMPONENTES BÁSICOS DE HERBIE
# Implementaciones simples para sistema básico
# ============================================================================

import json
import random
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import asdict

from herbie_enhanced.core_system import (
    ProjectAnalyzer, ProjectExecutor, LearningEngine, MetricsCollector,
    ProjectRequest, ProjectAnalysis, ExecutionResult, UserFeedback
)


# ============================================================================
# ANALIZADOR BÁSICO
# ============================================================================

class BasicProjectAnalyzer(ProjectAnalyzer):
    """Analizador básico sin capacidades avanzadas de IA"""

    def __init__(self):
        self.framework_keywords = {
            'react': ['react', 'frontend', 'ui', 'component', 'jsx', 'spa'],
            'vue': ['vue', 'frontend', 'simple', 'template', 'vuejs'],
            'angular': ['angular', 'typescript', 'enterprise', 'framework'],
            'django': ['django', 'python', 'web', 'backend', 'admin', 'orm'],
            'fastapi': ['fastapi', 'api', 'fast', 'python', 'async', 'rest'],
            'nextjs': ['next', 'nextjs', 'ssr', 'react', 'fullstack'],
            'flutter': ['flutter', 'mobile', 'app', 'dart', 'cross-platform']
        }

        self.complexity_keywords = {
            1: ['simple', 'basic', 'easy', 'minimal'],
            2: ['todo', 'calculator', 'counter', 'hello'],
            3: ['blog', 'crud', 'form', 'auth'],
            4: ['ecommerce', 'chat', 'realtime', 'dashboard'],
            5: ['complex', 'enterprise', 'microservice', 'ai', 'ml']
        }

    def analyze_project(self, request: ProjectRequest) -> ProjectAnalysis:
        """Análisis básico basado en palabras clave"""
        description = request.user_input.lower()

        # Detectar framework
        framework = self._detect_framework(description)

        # Detectar complejidad
        complexity = self._detect_complexity(description)

        # Generar nombre de repo
        repo_name = self._generate_repo_name(description, framework)

        # Generar tags
        tags = self._generate_tags(description, framework)

        # Comando de inicialización
        init_command = self._get_init_command(framework, repo_name)

        return ProjectAnalysis(
            repo_name=repo_name,
            framework=framework,
            description=request.user_input,
            complexity_score=complexity,
            predicted_success=0.7,  # Valor fijo para versión básica
            confidence=0.6,  # Valor fijo para versión básica
            reasoning=f"Análisis básico: detectado framework {framework} con complejidad {complexity}",
            tags=tags,
            is_private=False,
            init_command=init_command,
            additional_setup=None
        )

    def _detect_framework(self, description: str) -> str:
        """Detecta framework basado en palabras clave"""
        scores = {}

        for framework, keywords in self.framework_keywords.items():
            score = sum(1 for keyword in keywords if keyword in description)
            scores[framework] = score

        # Retornar el framework con mayor score, o 'react' por defecto
        return max(scores, key=scores.get) if max(scores.values()) > 0 else 'react'

    def _detect_complexity(self, description: str) -> int:
        """Detecta complejidad basada en palabras clave"""
        for complexity, keywords in self.complexity_keywords.items():
            if any(keyword in description for keyword in keywords):
                return complexity

        return 3  # Complejidad por defecto

    def _generate_repo_name(self, description: str, framework: str) -> str:
        """Genera nombre de repositorio"""
        # Extraer palabras clave del description
        words = description.split()
        relevant_words = [word for word in words if len(word) > 3 and word.isalpha()]

        if relevant_words:
            base_name = relevant_words[0][:8]  # Tomar primera palabra relevante
        else:
            base_name = "project"

        return f"{framework}-{base_name}-{random.randint(100, 999)}"

    def _generate_tags(self, description: str, framework: str) -> List[str]:
        """Genera tags básicos"""
        tags = [framework]

        # Agregar tags comunes
        if 'api' in description:
            tags.append('api')
        if 'auth' in description:
            tags.append('auth')
        if 'database' in description:
            tags.append('database')
        if 'mobile' in description:
            tags.append('mobile')
        if 'web' in description:
            tags.append('web')

        return tags

    def _get_init_command(self, framework: str, repo_name: str) -> str:
        """Obtiene comando de inicialización"""
        commands = {
            'react': f'npx create-react-app {repo_name}',
            'vue': f'npm create vue@latest {repo_name}',
            'angular': f'ng new {repo_name}',
            'django': f'django-admin startproject {repo_name}',
            'fastapi': f'fastapi-cli new {repo_name}',
            'nextjs': f'npx create-next-app@latest {repo_name}',
            'flutter': f'flutter create {repo_name}'
        }

        return commands.get(framework, f'mkdir {repo_name}')


# ============================================================================
# EJECUTOR BÁSICO
# ============================================================================

class BasicProjectExecutor(ProjectExecutor):
    """Ejecutor básico con simulación de creación"""

    def __init__(self):
        self.simulation_mode = True  # Para evitar llamadas reales sin configuración

    def execute_project(self, analysis: ProjectAnalysis) -> ExecutionResult:
        """Ejecuta creación del proyecto (simulada)"""
        import time

        start_time = time.time()

        # Simular diferentes pasos
        steps = [
            "Validando análisis",
            "Verificando dependencias",
            "Creando estructura local",
            "Configurando repositorio",
            "Generando archivos iniciales"
        ]

        try:
            # Simular éxito/fallo basado en complejidad
            success_probability = 0.9 - (analysis.complexity_score - 1) * 0.1
            success = random.random() < success_probability

            if success:
                repo_url = f"https://github.com/user/{analysis.repo_name}"
                execution_time = time.time() - start_time

                return ExecutionResult(
                    success=True,
                    repo_url=repo_url,
                    execution_time=execution_time,
                    steps_completed=steps,
                    metrics={
                        'framework': analysis.framework,
                        'complexity': analysis.complexity_score,
                        'simulation': True
                    }
                )
            else:
                return ExecutionResult(
                    success=False,
                    error_message=f"Fallo simulado para framework {analysis.framework}",
                    execution_time=time.time() - start_time,
                    steps_completed=steps[:3]  # Solo algunos pasos completados
                )

        except Exception as e:
            return ExecutionResult(
                success=False,
                error_message=f"Error en ejecución: {str(e)}",
                execution_time=time.time() - start_time,
                steps_completed=[]
            )


# ============================================================================
# MOTOR DE APRENDIZAJE SIMPLE
# ============================================================================

class SimpleLearningEngine(LearningEngine):
    """Motor de aprendizaje simple sin RLHF"""

    def __init__(self):
        self.feedback_count = 0
        self.total_satisfaction = 0.0
        self.framework_feedback = {}

    def learn_from_feedback(self, analysis: ProjectAnalysis,
                            result: ExecutionResult,
                            feedback: UserFeedback) -> None:
        """Aprendizaje simple basado en promedio de feedback"""

        # Actualizar estadísticas generales
        self.feedback_count += 1
        self.total_satisfaction += feedback.satisfaction

        # Registrar feedback por framework
        framework = analysis.framework
        if framework not in self.framework_feedback:
            self.framework_feedback[framework] = {
                'count': 0,
                'total_satisfaction': 0.0,
                'success_count': 0
            }

        self.framework_feedback[framework]['count'] += 1
        self.framework_feedback[framework]['total_satisfaction'] += feedback.satisfaction

        if feedback.setup_success:
            self.framework_feedback[framework]['success_count'] += 1

        # Log simple del aprendizaje
        print(f"📚 Aprendizaje simple: Framework {framework}, Satisfacción: {feedback.satisfaction:.2f}")

    def get_framework_satisfaction(self, framework: str) -> float:
        """Obtiene satisfacción promedio para un framework"""
        if framework in self.framework_feedback:
            data = self.framework_feedback[framework]
            return data['total_satisfaction'] / data['count']
        return 0.5  # Valor neutral por defecto

    def get_learning_stats(self) -> Dict:
        """Obtiene estadísticas de aprendizaje"""
        return {
            'total_feedback': self.feedback_count,
            'avg_satisfaction': self.total_satisfaction / self.feedback_count if self.feedback_count > 0 else 0,
            'framework_stats': {
                framework: {
                    'count': data['count'],
                    'avg_satisfaction': data['total_satisfaction'] / data['count'],
                    'success_rate': data['success_count'] / data['count']
                }
                for framework, data in self.framework_feedback.items()
            }
        }


# ============================================================================
# RECOLECTOR DE MÉTRICAS SIMPLE
# ============================================================================

class SimpleMetricsCollector(MetricsCollector):
    """Recolector simple de métricas en memoria"""

    def __init__(self):
        self.metrics_history = []
        self.session_count = 0
        self.success_count = 0

    def collect_metrics(self, analysis: ProjectAnalysis,
                        result: ExecutionResult,
                        feedback: Optional[UserFeedback] = None) -> None:
        """Recolecta métricas básicas"""

        self.session_count += 1

        if result.success:
            self.success_count += 1

        # Crear registro de métricas
        metrics_record = {
            'timestamp': datetime.now().isoformat(),
            'framework': analysis.framework,
            'complexity': analysis.complexity_score,
            'predicted_success': analysis.predicted_success,
            'actual_success': result.success,
            'execution_time': result.execution_time,
            'confidence': analysis.confidence,
            'user_satisfaction': feedback.satisfaction if feedback else None,
            'setup_success': feedback.setup_success if feedback else None
        }

        self.metrics_history.append(metrics_record)

        # Mantener solo las últimas 100 métricas
        if len(self.metrics_history) > 100:
            self.metrics_history = self.metrics_history[-100:]

    def get_basic_stats(self) -> Dict:
        """Obtiene estadísticas básicas"""
        return {
            'total_sessions': self.session_count,
            'success_rate': self.success_count / self.session_count if self.session_count > 0 else 0,
            'recent_metrics_count': len(self.metrics_history),
            'frameworks_used': list(set(m['framework'] for m in self.metrics_history))
        }

    def get_framework_performance(self) -> Dict:
        """Obtiene rendimiento por framework"""
        framework_stats = {}

        for metric in self.metrics_history:
            framework = metric['framework']
            if framework not in framework_stats:
                framework_stats[framework] = {
                    'count': 0,
                    'success_count': 0,
                    'total_satisfaction': 0.0,
                    'satisfaction_count': 0
                }

            framework_stats[framework]['count'] += 1

            if metric['actual_success']:
                framework_stats[framework]['success_count'] += 1

            if metric['user_satisfaction'] is not None:
                framework_stats[framework]['total_satisfaction'] += metric['user_satisfaction']
                framework_stats[framework]['satisfaction_count'] += 1

        # Calcular promedios
        result = {}
        for framework, stats in framework_stats.items():
            result[framework] = {
                'count': stats['count'],
                'success_rate': stats['success_count'] / stats['count'],
                'avg_satisfaction': (stats['total_satisfaction'] / stats['satisfaction_count']
                                     if stats['satisfaction_count'] > 0 else 0)
            }

        return result


# ============================================================================
# FUNCIONES DE UTILIDAD
# ============================================================================

def create_mock_system_for_testing():
    """Crea sistema mock para testing"""
    return {
        'analyzer': BasicProjectAnalyzer(),
        'executor': BasicProjectExecutor(),
        'learning_engine': SimpleLearningEngine(),
        'metrics_collector': SimpleMetricsCollector()
    }


# ============================================================================
# EJEMPLO DE USO DE COMPONENTES BÁSICOS
# ============================================================================

if __name__ == "__main__":
    # Crear componentes básicos
    analyzer = BasicProjectAnalyzer()
    executor = BasicProjectExecutor()
    learning_engine = SimpleLearningEngine()
    metrics_collector = SimpleMetricsCollector()

    # Crear request de prueba
    request = ProjectRequest(
        user_input="Crear una aplicación React para gestionar tareas",
        user_id="test_user",
        session_id="test_session",
        timestamp=datetime.now()
    )

    # Probar análisis
    analysis = analyzer.analyze_project(request)
    print("=== ANÁLISIS BÁSICO ===")
    print(f"Framework: {analysis.framework}")
    print(f"Complejidad: {analysis.complexity_score}")
    print(f"Comando: {analysis.init_command}")
    print(f"Tags: {analysis.tags}")

    # Probar ejecución
    result = executor.execute_project(analysis)
    print("\n=== EJECUCIÓN BÁSICA ===")
    print(f"Éxito: {result.success}")
    if result.success:
        print(f"URL: {result.repo_url}")
    else:
        print(f"Error: {result.error_message}")

    # Simular feedback
    feedback = UserFeedback(
        session_id="test_session",
        satisfaction=0.8,
        setup_success=True,
        code_quality=0.7,
        comments="Buen trabajo básico",
        would_recommend=True,
        timestamp=datetime.now()
    )

    # Probar aprendizaje
    learning_engine.learn_from_feedback(analysis, result, feedback)
    metrics_collector.collect_metrics(analysis, result, feedback)

    print("\n=== ESTADÍSTICAS ===")
    print(f"Stats aprendizaje: {learning_engine.get_learning_stats()}")
    print(f"Stats métricas: {metrics_collector.get_basic_stats()}")