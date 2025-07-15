
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import pickle
import os

from ..core_system import (
    ProjectAnalyzer, ProjectExecutor, LearningEngine, MetricsCollector,
    ProjectRequest, ProjectAnalysis, ExecutionResult, UserFeedback
)

class RLHFLearningEngine(LearningEngine):
    """
    Motor de aprendizaje por refuerzo con feedback humano
    """


    def __init__(self, reward_model_path: str = "reward_model.pkl"):
        self.reward_model_path = reward_model_path
        self.reward_model = self._load_or_create_reward_model()
        self.learning_rate = 0.01
        self.feedback_history = []


    def _load_or_create_reward_model(self) -> Dict:
        """Carga o crea el modelo de recompensa"""
        if os.path.exists(self.reward_model_path):
            with open(self.reward_model_path, 'rb') as f:
                return pickle.load(f)

        # Modelo inicial
        return {
            'framework_weights': {
                'react': 0.9,
                'vue': 0.8,
                'angular': 0.7,
                'django': 0.85,
                'fastapi': 0.8,
                'nextjs': 0.95,
                'flutter': 0.75
            },
            'complexity_factors': {
                1: 1.0,  # Muy simple
                2: 0.95,  # Simple
                3: 0.9,  # Moderado
                4: 0.8,  # Complejo
                5: 0.7  # Muy complejo
            },
            'feature_weights': {
                'setup_success': 0.3,
                'user_satisfaction': 0.4,
                'code_quality': 0.2,
                'recommendation': 0.1
            }
        }


    def _save_reward_model(self):
        """Guarda el modelo de recompensa"""
        with open(self.reward_model_path, 'wb') as f:
            pickle.dump(self.reward_model, f)


    def _calculate_reward(self, analysis: ProjectAnalysis,
                          result: ExecutionResult,
                          feedback: UserFeedback) -> float:
        """Calcula recompensa basada en feedback"""

        # Recompensa base del feedback
        base_reward = (
                feedback.satisfaction * self.reward_model['feature_weights']['user_satisfaction'] +
                feedback.code_quality * self.reward_model['feature_weights']['code_quality'] +
                (1.0 if feedback.setup_success else 0.0) * self.reward_model['feature_weights']['setup_success'] +
                (1.0 if feedback.would_recommend else 0.0) * self.reward_model['feature_weights']['recommendation']
        )

        # Ajuste por framework
        framework_weight = self.reward_model['framework_weights'].get(analysis.framework, 0.5)

        # Ajuste por complejidad
        complexity_factor = self.reward_model['complexity_factors'].get(analysis.complexity_score, 0.5)

        # Bonus por éxito en ejecución
        execution_bonus = 0.1 if result.success else -0.1

        total_reward = base_reward * framework_weight * complexity_factor + execution_bonus

        return max(0.0, min(1.0, total_reward))


    def learn_from_feedback(self, analysis: ProjectAnalysis,
                            result: ExecutionResult,
                            feedback: UserFeedback) -> None:
        """Aprende del feedback y actualiza el modelo"""

        # Calcular recompensa
        reward = self._calculate_reward(analysis, result, feedback)

        # Actualizar pesos del framework
        framework = analysis.framework
        if framework in self.reward_model['framework_weights']:
            current_weight = self.reward_model['framework_weights'][framework]
            new_weight = current_weight + self.learning_rate * (reward - current_weight)
            self.reward_model['framework_weights'][framework] = max(0.1, min(1.0, new_weight))

        # Actualizar factor de complejidad
        complexity = analysis.complexity_score
        if complexity in self.reward_model['complexity_factors']:
            current_factor = self.reward_model['complexity_factors'][complexity]
            new_factor = current_factor + self.learning_rate * (reward - current_factor)
            self.reward_model['complexity_factors'][complexity] = max(0.1, min(1.0, new_factor))

        # Guardar feedback en historial
        self.feedback_history.append({
            'timestamp': datetime.now(),
            'framework': framework,
            'complexity': complexity,
            'reward': reward,
            'satisfaction': feedback.satisfaction,
            'setup_success': feedback.setup_success
        })

        # Mantener solo los últimos 1000 feedbacks
        if len(self.feedback_history) > 1000:
            self.feedback_history = self.feedback_history[-1000:]

        # Guardar modelo actualizado
        self._save_reward_model()

        print(f"Modelo RLHF actualizado. Recompensa: {reward:.3f}")


    def get_framework_recommendation(self, description: str) -> Tuple[str, float]:
        """Recomienda framework basado en el modelo entrenado"""

        # Análisis simple basado en palabras clave
        keywords = description.lower().split()
        scores = {}

        keyword_mapping = {
            'react': ['react', 'frontend', 'ui', 'interactive', 'spa'],
            'vue': ['vue', 'frontend', 'simple', 'beginner'],
            'angular': ['angular', 'enterprise', 'complex', 'typescript'],
            'django': ['python', 'web', 'admin', 'rapid'],
            'fastapi': ['api', 'fast', 'python', 'microservice'],
            'nextjs': ['next', 'ssr', 'seo', 'fullstack'],
            'flutter': ['mobile', 'app', 'cross-platform', 'dart']
        }

        for framework, framework_keywords in keyword_mapping.items():
            score = sum(1 for kw in framework_keywords if kw in keywords)
            scores[framework] = score * self.reward_model['framework_weights'].get(framework, 0.5)

        # Recomendar el framework con mayor score
        best_framework = max(scores, key=scores.get)
        confidence = min(1.0, scores[best_framework] / 5.0)  # Normalizar

        return best_framework, confidence