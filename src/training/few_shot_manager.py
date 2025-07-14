# src/herbie/training/few_shot_manager.py
import json
import random
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict
from pathlib import Path
from ..utils.logging_config import setup_logging

logger = setup_logging()


@dataclass
class TrainingExample:
    id: str
    input: str
    output: Dict
    context: str
    difficulty: str
    framework: str
    success_rate: float = 0.0
    usage_count: int = 0
    created_at: str = ""
    updated_at: str = ""


class FewShotManager:
    def __init__(self, examples_path: str = "data/training/few_shot_examples.json"):
        self.examples_path = Path(examples_path)
        self.examples_path.parent.mkdir(parents=True, exist_ok=True)

        self.examples = self.load_examples()
        self.performance_tracker = {}

        logger.info(f"FewShotManager inicializado con {len(self.examples)} ejemplos")

    def load_examples(self) -> List[TrainingExample]:
        """Carga ejemplos de entrenamiento"""

        if not self.examples_path.exists():
            logger.info("Archivo de ejemplos no existe, creando ejemplos por defecto")
            return self.create_default_examples()

        try:
            with open(self.examples_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            examples = []
            for example_data in data:
                examples.append(TrainingExample(**example_data))

            logger.info(f"Cargados {len(examples)} ejemplos desde {self.examples_path}")
            return examples

        except Exception as e:
            logger.error(f"Error cargando ejemplos: {e}")
            return self.create_default_examples()

    def create_default_examples(self) -> List[TrainingExample]:
        """Crea ejemplos por defecto"""

        default_examples = [
            TrainingExample(
                id="react_task_manager",
                input="crea una aplicación React privada para gestión de tareas",
                output={
                    "repo_name": "task-manager-app",
                    "framework": "react",
                    "is_private": True,
                    "description": "Aplicación React para gestión de tareas personales",
                    "init_command": "npx create-react-app task-manager-app"
                },
                context="aplicación de productividad personal",
                difficulty="easy",
                framework="react"
            ),
            TrainingExample(
                id="django_users_api",
                input="necesito un API REST con Django público para gestión de usuarios",
                output={
                    "repo_name": "users-api",
                    "framework": "django",
                    "is_private": False,
                    "description": "API REST Django para gestión de usuarios",
                    "init_command": "django-admin startproject users_api"
                },
                context="backend web service",
                difficulty="medium",
                framework="django"
            ),
            TrainingExample(
                id="flutter_fitness_private",
                input="app móvil Flutter privada para fitness tracking con autenticación",
                output={
                    "repo_name": "fitness-tracker",
                    "framework": "flutter",
                    "is_private": True,
                    "description": "App móvil Flutter para seguimiento de fitness con autenticación",
                    "init_command": "flutter create fitness_tracker",
                    "additional_setup": ["flutter pub add firebase_auth", "flutter pub add firebase_core"]
                },
                context="aplicación móvil con servicios cloud",
                difficulty="hard",
                framework="flutter"
            ),
            TrainingExample(
                id="vue_ecommerce_public",
                input="crear tienda online con Vue.js pública",
                output={
                    "repo_name": "ecommerce-vue",
                    "framework": "vue",
                    "is_private": False,
                    "description": "Tienda online desarrollada con Vue.js",
                    "init_command": "npm create vue@latest ecommerce-vue"
                },
                context="comercio electrónico",
                difficulty="medium",
                framework="vue"
            ),
            TrainingExample(
                id="fastapi_blog_api",
                input="API para blog con FastAPI privado",
                output={
                    "repo_name": "blog-api",
                    "framework": "fastapi",
                    "is_private": True,
                    "description": "API para sistema de blog desarrollada con FastAPI",
                    "init_command": "fastapi-cli new blog-api"
                },
                context="sistema de contenido",
                difficulty="medium",
                framework="fastapi"
            )
        ]

        # Guardar ejemplos por defecto
        self.save_examples(default_examples)
        return default_examples

    def select_examples(self, user_input: str, num_examples: int = 3) -> List[TrainingExample]:
        """Selecciona ejemplos más relevantes"""

        # Estrategia de selección inteligente
        scored_examples = []

        for example in self.examples:
            score = self.calculate_relevance_score(user_input, example)
            scored_examples.append((example, score))

        # Ordenar por relevancia
        scored_examples.sort(key=lambda x: x[1], reverse=True)

        # Seleccionar top ejemplos asegurando diversidad
        selected = self.ensure_diversity(scored_examples, num_examples)

        # Actualizar contador de uso
        for example in selected:
            example.usage_count += 1

        return selected

    def calculate_relevance_score(self, user_input: str, example: TrainingExample) -> float:
        """Calcula score de relevancia"""

        score = 0.0
        user_input_lower = user_input.lower()

        # Similitud de framework
        if example.framework in user_input_lower:
            score += 0.4

        # Similitud de palabras clave
        input_words = set(user_input_lower.split())
        example_words = set(example.input.lower().split())

        common_words = input_words.intersection(example_words)
        if common_words:
            score += 0.3 * (len(common_words) / len(input_words))

        # Contexto similar
        if example.context:
            context_words = set(example.context.lower().split())
            context_overlap = input_words.intersection(context_words)
            if context_overlap:
                score += 0.2 * (len(context_overlap) / len(context_words))

        # Penalizar ejemplos sobre-utilizados
        if example.usage_count > 10:
            score *= 0.8

        # Bonus por alta tasa de éxito
        if example.success_rate > 0.8:
            score += 0.1

        return score

    def ensure_diversity(self, scored_examples: List[tuple], num_examples: int) -> List[TrainingExample]:
        """Asegura diversidad en ejemplos seleccionados"""

        selected = []
        used_frameworks = set()
        used_difficulties = set()

        for example, score in scored_examples:
            if len(selected) >= num_examples:
                break

            # Priorizar diversidad de frameworks
            if example.framework not in used_frameworks:
                selected.append(example)
                used_frameworks.add(example.framework)
                used_difficulties.add(example.difficulty)
                continue

            # Priorizar diversidad de dificultad
            if example.difficulty not in used_difficulties and len(selected) < num_examples:
                selected.append(example)
                used_difficulties.add(example.difficulty)
                continue

            # Agregar si aún necesitamos más ejemplos
            if len(selected) < num_examples:
                selected.append(example)

        return selected

    def create_few_shot_prompt(self, user_input: str, num_examples: int = 3) -> str:
        """Crea prompt con ejemplos few-shot"""

        selected_examples = self.select_examples(user_input, num_examples)

        # Crear ejemplos formateados
        examples_text = []
        for i, example in enumerate(selected_examples):
            examples_text.append(f"""
Ejemplo {i + 1}:
Input: {example.input}
Output: {json.dumps(example.output, indent=2, ensure_ascii=False)}
""")

        prompt = f"""
Eres un experto en desarrollo de software que ayuda a crear repositorios de GitHub.
Analiza el input del usuario y genera un JSON con la configuración del proyecto.

Aprende de estos ejemplos exitosos:
{''.join(examples_text)}

Reglas importantes:
1. El repo_name debe ser kebab-case (minúsculas con guiones)
2. La descripción debe ser clara y técnica
3. El framework debe ser uno de: react, vue, angular, django, fastapi, flask, rails, flutter
4. El init_command debe ser el comando estándar para el framework
5. Si no se especifica privacidad, usar false (público)

Ahora analiza este nuevo input:
Input: {user_input}
Output: """

        return prompt

    def add_example(self, example: TrainingExample):
        """Agrega nuevo ejemplo"""

        # Verificar que no existe
        existing_ids = {ex.id for ex in self.examples}
        if example.id in existing_ids:
            logger.warning(f"Ejemplo con ID {example.id} ya existe")
            return False

        self.examples.append(example)
        self.save_examples()

        logger.info(f"Ejemplo {example.id} agregado exitosamente")
        return True

    def update_example_performance(self, example_id: str, success: bool):
        """Actualiza performance del ejemplo"""

        for example in self.examples:
            if example.id == example_id:
                # Actualizar tasa de éxito usando promedio móvil
                if success:
                    example.success_rate = (example.success_rate * 0.9) + (1.0 * 0.1)
                else:
                    example.success_rate = (example.success_rate * 0.9) + (0.0 * 0.1)

                break

        self.save_examples()

    def save_examples(self, examples: Optional[List[TrainingExample]] = None):
        """Guarda ejemplos en archivo"""

        if examples is None:
            examples = self.examples

        try:
            data = [asdict(example) for example in examples]

            with open(self.examples_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            logger.info(f"Ejemplos guardados en {self.examples_path}")

        except Exception as e:
            logger.error(f"Error guardando ejemplos: {e}")

    def get_statistics(self) -> Dict:
        """Obtiene estadísticas de ejemplos"""

        if not self.examples:
            return {}

        frameworks = [ex.framework for ex in self.examples]
        difficulties = [ex.difficulty for ex in self.examples]

        from collections import Counter

        stats = {
            "total_examples": len(self.examples),
            "frameworks": dict(Counter(frameworks)),
            "difficulties": dict(Counter(difficulties)),
            "avg_success_rate": sum(ex.success_rate for ex in self.examples) / len(self.examples),
            "most_used": max(self.examples, key=lambda x: x.usage_count).id if self.examples else None
        }

        return stats