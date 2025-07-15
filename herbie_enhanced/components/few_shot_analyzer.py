import json
import sqlite3
import numpy as np
from datetime import datetime
from typing import Dict, List
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import pickle
import os

from ..core_system import (
    ProjectAnalyzer, ProjectExecutor, LearningEngine, MetricsCollector,
    ProjectRequest, ProjectAnalysis, ExecutionResult, UserFeedback
)


# ============================================================================
# ANALIZADOR CON FEW-SHOT LEARNING
# ============================================================================

class FewShotProjectAnalyzer(ProjectAnalyzer):
    """
    Analizador que utiliza few-shot learning para mejorar predicciones
    """

    def __init__(self, examples_db_path: str = "few_shot_examples.db"):
        self.db_path = examples_db_path
        self.llm = self._init_llm()
        self.vectorizer = TfidfVectorizer(stop_words='english', max_features=1000)
        self.examples_cache = []
        self._init_database()
        self._load_examples()

    def _init_llm(self):
        """Inicializa el modelo de lenguaje"""
        from langchain_google_genai import ChatGoogleGenerativeAI
        from langchain.schema import HumanMessage

        return ChatGoogleGenerativeAI(
            model="gemini-1.5-flash",
            google_api_key=os.getenv('GOOGLE_API_KEY'),
            temperature=0.2
        )

    def _init_database(self):
        """Inicializa base de datos de ejemplos"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
                       CREATE TABLE IF NOT EXISTS examples
                       (
                           id
                           INTEGER
                           PRIMARY
                           KEY
                           AUTOINCREMENT,
                           description
                           TEXT,
                           framework
                           TEXT,
                           complexity_score
                           INTEGER,
                           success_rate
                           REAL,
                           tags
                           TEXT,
                           reasoning
                           TEXT,
                           timestamp
                           DATETIME
                       )
                       ''')

        # Insertar ejemplos semilla si no existen
        cursor.execute('SELECT COUNT(*) FROM examples')
        if cursor.fetchone()[0] == 0:
            self._insert_seed_examples(cursor)

        conn.commit()
        conn.close()

    def _insert_seed_examples(self, cursor):
        """Inserta ejemplos semilla de alta calidad"""
        seed_examples = [
            {
                'description': 'Create a React todo app with authentication and real-time updates',
                'framework': 'react',
                'complexity_score': 4,
                'success_rate': 0.9,
                'tags': '["react", "todo", "auth", "realtime"]',
                'reasoning': 'React is excellent for interactive UIs, well-documented auth solutions exist'
            },
            {
                'description': 'Build a simple blog with Django and user comments',
                'framework': 'django',
                'complexity_score': 3,
                'success_rate': 0.85,
                'tags': '["django", "blog", "comments", "crud"]',
                'reasoning': 'Django admin and ORM make blog creation straightforward'
            },
            {
                'description': 'Flutter mobile app for weather with location services',
                'framework': 'flutter',
                'complexity_score': 4,
                'success_rate': 0.75,
                'tags': '["flutter", "mobile", "weather", "location"]',
                'reasoning': 'Flutter good for cross-platform, but location services add complexity'
            },
            {
                'description': 'Vue.js e-commerce site with shopping cart',
                'framework': 'vue',
                'complexity_score': 4,
                'success_rate': 0.8,
                'tags': '["vue", "ecommerce", "cart", "payment"]',
                'reasoning': 'Vue is beginner-friendly, but e-commerce requires state management'
            },
            {
                'description': 'FastAPI REST API with database and authentication',
                'framework': 'fastapi',
                'complexity_score': 3,
                'success_rate': 0.82,
                'tags': '["fastapi", "api", "database", "auth"]',
                'reasoning': 'FastAPI has excellent documentation and built-in validation'
            }
        ]

        for example in seed_examples:
            cursor.execute('''
                           INSERT INTO examples
                           (description, framework, complexity_score, success_rate, tags, reasoning, timestamp)
                           VALUES (?, ?, ?, ?, ?, ?, ?)
                           ''', (
                               example['description'],
                               example['framework'],
                               example['complexity_score'],
                               example['success_rate'],
                               example['tags'],
                               example['reasoning'],
                               datetime.now()
                           ))

    def _load_examples(self):
        """Carga ejemplos desde la base de datos"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM examples ORDER BY success_rate DESC')
        rows = cursor.fetchall()

        self.examples_cache = []
        for row in rows:
            self.examples_cache.append({
                'id': row[0],
                'description': row[1],
                'framework': row[2],
                'complexity_score': row[3],
                'success_rate': row[4],
                'tags': json.loads(row[5]),
                'reasoning': row[6],
                'timestamp': row[7]
            })

        conn.close()

    def _find_similar_examples(self, description: str, top_k: int = 3) -> List[Dict]:
        """Encuentra ejemplos similares usando TF-IDF"""
        if not self.examples_cache:
            return []

        # Obtener descripciones de ejemplos
        example_descriptions = [ex['description'] for ex in self.examples_cache]
        all_descriptions = example_descriptions + [description]

        # Calcular similitud
        try:
            tfidf_matrix = self.vectorizer.fit_transform(all_descriptions)
            similarities = cosine_similarity(tfidf_matrix[-1:], tfidf_matrix[:-1]).flatten()

            # Obtener top K más similares
            similar_indices = np.argsort(similarities)[::-1][:top_k]

            return [self.examples_cache[i] for i in similar_indices if similarities[i] > 0.1]
        except:
            # Fallback: devolver ejemplos aleatorios
            return self.examples_cache[:top_k]

    def analyze_project(self, request: ProjectRequest) -> ProjectAnalysis:
        """
        Analiza proyecto usando few-shot learning
        """
        # Encontrar ejemplos similares
        similar_examples = self._find_similar_examples(request.user_input)

        # Construir prompt con ejemplos
        prompt = self._build_few_shot_prompt(request.user_input, similar_examples)

        # Obtener respuesta del LLM
        from langchain.schema import HumanMessage
        response = self.llm.invoke([HumanMessage(content=prompt)])

        # Parsear respuesta
        analysis_data = self._parse_llm_response(response.content)

        return ProjectAnalysis(
            repo_name=analysis_data['repo_name'],
            framework=analysis_data['framework'],
            description=analysis_data['description'],
            complexity_score=analysis_data['complexity_score'],
            predicted_success=analysis_data['predicted_success'],
            confidence=analysis_data['confidence'],
            reasoning=analysis_data['reasoning'],
            tags=analysis_data['tags'],
            is_private=analysis_data.get('is_private', False),
            init_command=analysis_data.get('init_command', ''),
            additional_setup=analysis_data.get('additional_setup')
        )

    def _build_few_shot_prompt(self, user_input: str, examples: List[Dict]) -> str:
        """Construye prompt con ejemplos few-shot"""
        prompt = """Como experto en desarrollo de software, analiza descripciones de proyectos y aprende de ejemplos exitosos.

EJEMPLOS DE PROYECTOS EXITOSOS:
"""

        for i, example in enumerate(examples, 1):
            prompt += f"""
Ejemplo {i}:
Descripción: "{example['description']}"
Framework: {example['framework']}
Complejidad: {example['complexity_score']}/5
Tasa de éxito: {example['success_rate']:.1%}
Razonamiento: {example['reasoning']}
Tags: {', '.join(example['tags'])}
"""

        prompt += f"""
NUEVA DESCRIPCIÓN A ANALIZAR:
"{user_input}"

Basándote en los ejemplos exitosos, responde con JSON válido:
{{
  "repo_name": "nombre-del-repositorio",
  "framework": "framework-elegido",
  "description": "descripción clara del proyecto",
  "complexity_score": 1-5,
  "predicted_success": 0.0-1.0,
  "confidence": 0.0-1.0,
  "reasoning": "justificación detallada",
  "tags": ["tag1", "tag2", "tag3"],
  "is_private": false,
  "init_command": "comando de inicialización",
  "additional_setup": ["cmd1", "cmd2"] o null
}}

Considera los patrones de éxito de los ejemplos para tomar decisiones.
"""

        return prompt

    def _parse_llm_response(self, response: str) -> Dict:
        """Parsea respuesta del LLM"""
        try:
            # Extraer JSON del contenido
            start = response.find('{')
            end = response.rfind('}') + 1

            if start == -1 or end == 0:
                raise ValueError("No JSON found in response")

            json_str = response[start:end]
            return json.loads(json_str)

        except (json.JSONDecodeError, ValueError) as e:
            # Fallback con valores por defecto
            return {
                'repo_name': 'generated-project',
                'framework': 'react',
                'description': 'Generated project',
                'complexity_score': 3,
                'predicted_success': 0.5,
                'confidence': 0.3,
                'reasoning': 'Error parsing LLM response',
                'tags': ['generated'],
                'is_private': False,
                'init_command': 'npx create-react-app generated-project',
                'additional_setup': None
            }