# src/herbie/evaluation/evaluator.py
import json
from datetime import datetime

import numpy as np
import pandas as pd
from typing import Dict, List, Any
from dataclasses import dataclass
from sklearn.metrics import accuracy_score, precision_recall_fscore_support
from ..utils.logging_config import setup_logging

logger = setup_logging()


@dataclass
class EvaluationResult:
    metric_name: str
    value: float
    details: Dict
    timestamp: str


class HerbieEvaluator:
    def __init__(self, agent):
        self.agent = agent
        self.evaluation_history = []

    def run_comprehensive_evaluation(self, test_cases: List[Dict]) -> Dict:
        """Ejecuta evaluación completa del agente"""

        logger.info(f"Iniciando evaluación con {len(test_cases)} casos de prueba")

        results = {
            'parsing_accuracy': self.evaluate_parsing_accuracy(test_cases),
            'response_quality': self.evaluate_response_quality(test_cases),
            'performance_metrics': self.evaluate_performance(test_cases),
            'user_experience': self.evaluate_user_experience(test_cases),
            'technical_accuracy': self.evaluate_technical_accuracy(test_cases)
        }

        # Calcular score general
        overall_score = self.calculate_overall_score(results)
        results['overall_score'] = overall_score

        # Guardar en historial
        self.evaluation_history.append({
            'timestamp': datetime.now().isoformat(),
            'results': results,
            'test_cases_count': len(test_cases)
        })

        return results

    def evaluate_parsing_accuracy(self, test_cases: List[Dict]) -> Dict:
        """Evalúa precisión del parsing"""

        correct_framework = 0
        correct_privacy = 0
        correct_naming = 0
        parsing_errors = 0

        for test_case in test_cases:
            try:
                response = self.agent.process_request(test_case['input'])

                if response.success:
                    result = response.result
                    expected = test_case['expected']

                    # Verificar framework
                    if result.get('framework') == expected.get('framework'):
                        correct_framework += 1

                    # Verificar privacidad
                    if result.get('is_private') == expected.get('is_private'):
                        correct_privacy += 1

                    # Verificar naming (más flexible)
                    if self.is_reasonable_name(result.get('repo_name', ''), test_case['input']):
                        correct_naming += 1
                else:
                    parsing_errors += 1

            except Exception as e:
                parsing_errors += 1
                logger.error(f"Error evaluando caso: {e}")

        total = len(test_cases)

        return {
            'framework_accuracy': correct_framework / total,
            'privacy_accuracy': correct_privacy / total,
            'naming_accuracy': correct_naming / total,
            'parsing_success_rate': (total - parsing_errors) / total,
            'details': {
                'total_cases': total,
                'correct_framework': correct_framework,
                'correct_privacy': correct_privacy,
                'correct_naming': correct_naming,
                'parsing_errors': parsing_errors
            }
        }

    def evaluate_response_quality(self, test_cases: List[Dict]) -> Dict:
        """Evalúa calidad de respuestas"""

        clarity_scores = []
        completeness_scores = []
        consistency_scores = []

        for test_case in test_cases:
            try:
                response = self.agent.process_request(test_case['input'])

                if response.success:
                    result = response.result

                    # Evaluar claridad
                    clarity = self.evaluate_clarity(result)
                    clarity_scores.append(clarity)

                    # Evaluar completitud
                    completeness = self.evaluate_completeness(result)
                    completeness_scores.append(completeness)

                    # Evaluar consistencia
                    consistency = self.evaluate_consistency(test_case['input'], result)
                    consistency_scores.append(consistency)

            except Exception as e:
                logger.error(f"Error evaluando calidad: {e}")

        return {
            'avg_clarity': np.mean(clarity_scores) if clarity_scores else 0,
            'avg_completeness': np.mean(completeness_scores) if completeness_scores else 0,
            'avg_consistency': np.mean(consistency_scores) if consistency_scores else 0,
            'details': {
                'clarity_scores': clarity_scores,
                'completeness_scores': completeness_scores,
                'consistency_scores': consistency_scores
            }
        }

    def evaluate_performance(self, test_cases: List[Dict]) -> Dict:
        """Evalúa métricas de rendimiento"""

        response_times = []
        confidence_scores = []

        for test_case in test_cases:
            try:
                response = self.agent.process_request(test_case['input'])

                response_times.append(response.response_time)
                confidence_scores.append(response.confidence)

            except Exception as e:
                logger.error(f"Error evaluando rendimiento: {e}")

        return {
            'avg_response_time': np.mean(response_times) if response_times else 0,
            'max_response_time': np.max(response_times) if response_times else 0,
            'min_response_time': np.min(response_times) if response_times else 0,
            'avg_confidence': np.mean(confidence_scores) if confidence_scores else 0,
            'details': {
                'response_times': response_times,
                'confidence_scores': confidence_scores
            }
        }

    def is_reasonable_name(self, repo_name: str, original_input: str) -> bool:
        """Evalúa si el nombre del repositorio es razonable"""

        if not repo_name or len(repo_name) < 3:
            return False

        # Verificar formato
        if ' ' in repo_name or any(c in repo_name for c in "!@#$%^&*()"):
            return False

        # Verificar relación con input
        input_words = set(original_input.lower().split())
        name_words = set(repo_name.lower().replace('-', ' ').replace('_', ' ').split())

        return len(input_words.intersection(name_words)) > 0

    def evaluate_clarity(self, result: Dict) -> float:
        """Evalúa claridad del resultado"""

        score = 0.0

        # Descripción clara
        description = result.get('description', '')
        if description and len(description) > 10:
            score += 0.3

        # Nombre descriptivo
        repo_name = result.get('repo_name', '')
        if repo_name and len(repo_name) > 3:
            score += 0.2

        # Comando válido
        init_command = result.get('init_command', '')
        if init_command and len(init_command) > 5:
            score += 0.2

        # Framework reconocido
        framework = result.get('framework', '')
        if framework in self.agent.framework_helper.supported_frameworks:
            score += 0.3

        return score

    def evaluate_completeness(self, result: Dict) -> float:
        """Evalúa completitud del resultado"""

        required_fields = ['repo_name', 'framework', 'is_private', 'description', 'init_command']
        present_fields = sum(1 for field in required_fields if field in result and result[field])

        return present_fields / len(required_fields)

    def evaluate_consistency(self, user_input: str, result: Dict) -> float:
        """Evalúa consistencia entre input y resultado"""

        score = 1.0

        # Framework mencionado en input vs resultado
        frameworks = ['react', 'vue', 'django', 'flask', 'fastapi', 'rails', 'flutter']
        input_framework = None

        for fw in frameworks:
            if fw in user_input.lower():
                input_framework = fw
                break

        if input_framework and result.get('framework') != input_framework:
            score -= 0.5

        # Privacidad mencionada
        if 'privad' in user_input.lower() and not result.get('is_private'):
            score -= 0.3
        elif 'públic' in user_input.lower() and result.get('is_private'):
            score -= 0.3

        return max(score, 0.0)

    def calculate_overall_score(self, results: Dict) -> float:
        """Calcula score general"""

        weights = {
            'parsing_accuracy': 0.3,
            'response_quality': 0.25,
            'performance_metrics': 0.15,
            'user_experience': 0.2,
            'technical_accuracy': 0.1
        }

        overall_score = 0.0

        for category, weight in weights.items():
            if category in results:
                category_score = self.extract_category_score(results[category])
                overall_score += category_score * weight

        return overall_score

    def extract_category_score(self, category_results: Dict) -> float:
        """Extrae score de una categoría"""

        if 'avg_clarity' in category_results:
            # Response quality
            return (category_results['avg_clarity'] +
                    category_results['avg_completeness'] +
                    category_results['avg_consistency']) / 3

        elif 'framework_accuracy' in category_results:
            # Parsing accuracy
            return (category_results['framework_accuracy'] +
                    category_results['privacy_accuracy'] +
                    category_results['naming_accuracy']) / 3

        elif 'avg_response_time' in category_results:
            # Performance (invertir tiempo de respuesta)
            time_score = max(0, 1 - (category_results['avg_response_time'] / 10))
            confidence_score = category_results['avg_confidence']
            return (time_score + confidence_score) / 2

        else:
            return 0.5  # Score por defecto

    def generate_evaluation_report(self, results: Dict) -> str:
        """Genera reporte de evaluación"""

        report = f"""
# 📊 REPORTE DE EVALUACIÓN - HERBIE AGENT

## Resumen Ejecutivo
- **Score General**: {results['overall_score']:.2%}
- **Fecha**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Métricas Detalladas

### 🎯 Precisión de Parsing
- Framework: {results['parsing_accuracy']['framework_accuracy']:.2%}
- Privacidad: {results['parsing_accuracy']['privacy_accuracy']:.2%}
- Naming: {results['parsing_accuracy']['naming_accuracy']:.2%}
- Éxito de Parsing: {results['parsing_accuracy']['parsing_success_rate']:.2%}

### 🌟 Calidad de Respuestas
- Claridad: {results['response_quality']['avg_clarity']:.2%}
- Completitud: {results['response_quality']['avg_completeness']:.2%}
- Consistencia: {results['response_quality']['avg_consistency']:.2%}

### ⚡ Rendimiento
- Tiempo Promedio: {results['performance_metrics']['avg_response_time']:.2f}s
- Confianza Promedio: {results['performance_metrics']['avg_confidence']:.2%}

## Recomendaciones
{self.generate_recommendations(results)}

## Casos de Prueba
- Total evaluados: {results['parsing_accuracy']['details']['total_cases']}
- Errores de parsing: {results['parsing_accuracy']['details']['parsing_errors']}
"""

        return report

    def generate_recommendations(self, results: Dict) -> str:
        """Genera recomendaciones basadas en resultados"""

        recommendations = []

        # Parsing accuracy
        if results['parsing_accuracy']['framework_accuracy'] < 0.8:
            recommendations.append("- Mejorar detección de frameworks con más ejemplos de entrenamiento")

        if results['parsing_accuracy']['naming_accuracy'] < 0.7:
            recommendations.append("- Refinar algoritmo de generación de nombres de repositorios")

        # Response quality
        if results['response_quality']['avg_clarity'] < 0.7:
            recommendations.append("- Mejorar claridad de respuestas con prompts más específicos")

        # Performance
        if results['performance_metrics']['avg_response_time'] > 3.0:
            recommendations.append("- Optimizar tiempo de respuesta, considerar caching")

        if results['performance_metrics']['avg_confidence'] < 0.6:
            recommendations.append("- Mejorar sistema de confianza con más features")

        if not recommendations:
            recommendations.append("- El agente está funcionando dentro de parámetros aceptables")

        return "\n".join(recommendations)