# src/herbie/training/feedback_system.py
import sqlite3
import json
import pandas as pd
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from pathlib import Path
from ..utils.logging_config import setup_logging

logger = setup_logging()


@dataclass
class FeedbackEntry:
    id: Optional[int] = None
    timestamp: str = ""
    user_id: str = ""
    user_input: str = ""
    agent_response: str = ""
    user_rating: int = 0
    specific_feedback: str = ""
    task_success: bool = False
    response_time: float = 0.0
    framework: str = ""
    difficulty: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()


class FeedbackDatabase:
    def __init__(self, db_path: str = "data/feedback.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.init_database()

        logger.info(f"FeedbackDatabase inicializada en {self.db_path}")

    def init_database(self):
        """Inicializa la base de datos"""

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
                       CREATE TABLE IF NOT EXISTS feedback
                       (
                           id
                           INTEGER
                           PRIMARY
                           KEY
                           AUTOINCREMENT,
                           timestamp
                           TEXT
                           NOT
                           NULL,
                           user_id
                           TEXT
                           NOT
                           NULL,
                           user_input
                           TEXT
                           NOT
                           NULL,
                           agent_response
                           TEXT
                           NOT
                           NULL,
                           user_rating
                           INTEGER
                           NOT
                           NULL
                           CHECK
                       (
                           user_rating
                           >=
                           1
                           AND
                           user_rating
                           <=
                           5
                       ),
                           specific_feedback TEXT,
                           task_success BOOLEAN NOT NULL,
                           response_time REAL NOT NULL,
                           framework TEXT,
                           difficulty TEXT
                           )
                       ''')

        cursor.execute('''
                       CREATE INDEX IF NOT EXISTS idx_timestamp ON feedback(timestamp);
                       ''')

        cursor.execute('''
                       CREATE INDEX IF NOT EXISTS idx_user_rating ON feedback(user_rating);
                       ''')

        cursor.execute('''
                       CREATE INDEX IF NOT EXISTS idx_framework ON feedback(framework);
                       ''')

        conn.commit()
        conn.close()

        logger.info("Base de datos de feedback inicializada")

    def add_feedback(self, feedback: FeedbackEntry) -> int:
        """Agrega feedback a la base de datos"""

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
                       INSERT INTO feedback (timestamp, user_id, user_input, agent_response,
                                             user_rating, specific_feedback, task_success,
                                             response_time, framework, difficulty)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                       ''', (
                           feedback.timestamp,
                           feedback.user_id,
                           feedback.user_input,
                           feedback.agent_response,
                           feedback.user_rating,
                           feedback.specific_feedback,
                           feedback.task_success,
                           feedback.response_time,
                           feedback.framework,
                           feedback.difficulty
                       ))

        feedback_id = cursor.lastrowid
        conn.commit()
        conn.close()

        logger.info(f"Feedback agregado con ID {feedback_id}")
        return feedback_id

    def get_feedback_data(self, limit: Optional[int] = None,
                          min_rating: Optional[int] = None) -> pd.DataFrame:
        """Obtiene datos de feedback"""

        conn = sqlite3.connect(self.db_path)

        query = "SELECT * FROM feedback"
        params = []

        if min_rating:
            query += " WHERE user_rating >= ?"
            params.append(min_rating)

        query += " ORDER BY timestamp DESC"

        if limit:
            query += " LIMIT ?"
            params.append(limit)

        df = pd.read_sql_query(query, conn, params=params)
        conn.close()

        return df

    def get_statistics(self) -> Dict:
        """Obtiene estadísticas del feedback"""

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Estadísticas básicas
        cursor.execute("SELECT COUNT(*) FROM feedback")
        total_feedback = cursor.fetchone()[0]

        cursor.execute("SELECT AVG(user_rating) FROM feedback")
        avg_rating = cursor.fetchone()[0] or 0

        cursor.execute("SELECT AVG(response_time) FROM feedback")
        avg_response_time = cursor.fetchone()[0] or 0

        cursor.execute("SELECT COUNT(*) FROM feedback WHERE task_success = 1")
        success_count = cursor.fetchone()[0]

        # Distribución por rating
        cursor.execute("SELECT user_rating, COUNT(*) FROM feedback GROUP BY user_rating")
        rating_distribution = dict(cursor.fetchall())

        # Distribución por framework
        cursor.execute("SELECT framework, COUNT(*) FROM feedback WHERE framework IS NOT NULL GROUP BY framework")
        framework_distribution = dict(cursor.fetchall())

        conn.close()

        stats = {
            "total_feedback": total_feedback,
            "avg_rating": round(avg_rating, 2),
            "avg_response_time": round(avg_response_time, 2),
            "success_rate": round(success_count / total_feedback * 100, 2) if total_feedback > 0 else 0,
            "rating_distribution": rating_distribution,
            "framework_distribution": framework_distribution
        }

        return stats


class InteractiveFeedbackCollector:
    def __init__(self, db: FeedbackDatabase):
        self.db = db

    def collect_feedback(self, user_id: str, user_input: str,
                         agent_response: str, response_time: float,
                         framework: str = "", difficulty: str = "medium") -> FeedbackEntry:
        """Recolecta feedback de forma interactiva"""

        print("\n" + "=" * 60)
        print("📊 EVALUACIÓN DE RESPUESTA DEL AGENTE")
        print("=" * 60)
        print(f"📝 Tu comando: {user_input}")
        print(f"🤖 Respuesta: {agent_response}")
        print(f"⏱️  Tiempo: {response_time:.2f}s")
        print(f"🔧 Framework: {framework}")
        print()

        # Recopilar rating
        rating = self.get_rating()

        # Recopilar feedback específico
        specific_feedback = input("💬 Comentarios específicos (opcional): ").strip()

        # Verificar éxito de la tarea
        task_success = self.get_task_success()

        # Crear entrada de feedback
        feedback = FeedbackEntry(
            timestamp=datetime.now().isoformat(),
            user_id=user_id,
            user_input=user_input,
            agent_response=agent_response,
            user_rating=rating,
            specific_feedback=specific_feedback,
            task_success=task_success,
            response_time=response_time,
            framework=framework,
            difficulty=difficulty
        )

        # Guardar en base de datos
        feedback_id = self.db.add_feedback(feedback)
        feedback.id = feedback_id

        print(f"✅ Feedback guardado con ID {feedback_id}")
        print("¡Gracias por tu evaluación!")

        return feedback

    def get_rating(self) -> int:
        """Obtiene rating del usuario"""

        while True:
            try:
                print("⭐ Califica esta respuesta:")
                print("  1 - Muy mala")
                print("  2 - Mala")
                print("  3 - Regular")
                print("  4 - Buena")
                print("  5 - Excelente")

                rating = int(input("Tu calificación (1-5): "))

                if 1 <= rating <= 5:
                    return rating
                else:
                    print("❌ Por favor, ingresa un número entre 1 y 5")

            except ValueError:
                print("❌ Por favor, ingresa un número válido")

    def get_task_success(self) -> bool:
        """Verifica si la tarea fue exitosa"""

        while True:
            response = input("✅ ¿La tarea se completó exitosamente? (s/n): ").lower().strip()

            if response in ['s', 'si', 'sí', 'y', 'yes']:
                return True
            elif response in ['n', 'no']:
                return False
            else:
                print("❌ Por favor, responde 's' para sí o 'n' para no")

    def collect_batch_feedback(self, test_cases: List[Dict]) -> List[FeedbackEntry]:
        """Recolecta feedback para múltiples casos"""

        feedback_entries = []

        print(f"\n🔄 Evaluando {len(test_cases)} casos de prueba...")

        for i, test_case in enumerate(test_cases, 1):
            print(f"\n📋 Caso {i}/{len(test_cases)}")

            feedback = self.collect_feedback(
                user_id=test_case.get('user_id', 'batch_tester'),
                user_input=test_case['input'],
                agent_response=test_case['response'],
                response_time=test_case.get('response_time', 1.0),
                framework=test_case.get('framework', ''),
                difficulty=test_case.get('difficulty', 'medium')
            )

            feedback_entries.append(feedback)

            # Mostrar progreso
            if i % 5 == 0:
                print(f"✨ Progreso: {i}/{len(test_cases)} casos evaluados")

        return feedback_entries


class RewardModelTrainer:
    def __init__(self, feedback_db: FeedbackDatabase):
        self.feedback_db = feedback_db
        self.model = None
        self.feature_columns = []

    def prepare_training_data(self) -> pd.DataFrame:
        """Prepara datos para entrenamiento"""

        df = self.feedback_db.get_feedback_data()

        if df.empty:
            raise ValueError("No hay datos de feedback disponibles")

        # Feature engineering
        df['input_length'] = df['user_input'].str.len()
        df['response_length'] = df['agent_response'].str.len()
        df['has_feedback'] = df['specific_feedback'].notna() & (df['specific_feedback'] != '')

        # Features de complejidad
        df['complexity_score'] = df['user_input'].apply(self.calculate_complexity)
        df['clarity_score'] = df['agent_response'].apply(self.calculate_clarity)

        # Features categóricas
        df['framework_encoded'] = pd.Categorical(df['framework']).codes
        df['difficulty_encoded'] = pd.Categorical(df['difficulty']).codes

        # Features de tiempo
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df['hour'] = df['timestamp'].dt.hour
        df['day_of_week'] = df['timestamp'].dt.dayofweek

        return df

    def calculate_complexity(self, text: str) -> float:
        """Calcula score de complejidad del input"""

        if not text:
            return 0.0

        complexity_keywords = [
            'autenticación', 'base de datos', 'api', 'privado',
            'microservicio', 'docker', 'deployment', 'ci/cd',
            'testing', 'seguridad', 'performance', 'escalabilidad'
        ]

        score = 0.0
        text_lower = text.lower()

        # Palabras clave de complejidad
        for keyword in complexity_keywords:
            if keyword in text_lower:
                score += 0.1

        # Longitud del texto
        if len(text) > 100:
            score += 0.2
        elif len(text) > 50:
            score += 0.1

        # Múltiples frameworks mencionados
        frameworks = ['react', 'vue', 'django', 'flask', 'fastapi', 'rails', 'flutter']
        framework_count = sum(1 for fw in frameworks if fw in text_lower)
        if framework_count > 1:
            score += 0.2

        return min(score, 1.0)

    def calculate_clarity(self, response: str) -> float:
        """Calcula score de claridad de la respuesta"""

        if not response:
            return 0.0

        score = 0.0

        # Estructura JSON válida
        try:
            json.loads(response)
            score += 0.4
        except:
            # Buscar JSON parcial
            if '{' in response and '}' in response:
                score += 0.2

        # Longitud apropiada
        if 50 <= len(response) <= 500:
            score += 0.3
        elif 20 <= len(response) <= 1000:
            score += 0.1

        # Campos requeridos
        required_fields = ['repo_name', 'framework', 'description', 'init_command']
        for field in required_fields:
            if field in response:
                score += 0.075  # 0.3 / 4

        return min(score, 1.0)

    def train_model(self) -> Dict:
        """Entrena modelo de reward"""

        from sklearn.ensemble import RandomForestRegressor
        from sklearn.model_selection import train_test_split, cross_val_score
        from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error

        # Preparar datos
        df = self.prepare_training_data()

        # Seleccionar features
        self.feature_columns = [
            'input_length', 'response_length', 'has_feedback',
            'complexity_score', 'clarity_score', 'framework_encoded',
            'difficulty_encoded', 'task_success', 'response_time',
            'hour', 'day_of_week'
        ]

        X = df[self.feature_columns]
        y = df['user_rating']

        # Dividir datos
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )

        # Entrenar modelo
        self.model = RandomForestRegressor(
            n_estimators=100,
            max_depth=10,
            min_samples_split=5,
            min_samples_leaf=2,
            random_state=42
        )

        self.model.fit(X_train, y_train)

        # Evaluar modelo
        y_pred = self.model.predict(X_test)

        # Métricas
        mse = mean_squared_error(y_test, y_pred)
        mae = mean_absolute_error(y_test, y_pred)
        r2 = r2_score(y_test, y_pred)

        # Validación cruzada
        cv_scores = cross_val_score(self.model, X_train, y_train, cv=5, scoring='r2')

        # Feature importance
        feature_importance = dict(zip(self.feature_columns, self.model.feature_importances_))

        results = {
            'model': self.model,
            'mse': mse,
            'mae': mae,
            'r2': r2,
            'cv_mean': cv_scores.mean(),
            'cv_std': cv_scores.std(),
            'feature_importance': feature_importance,
            'training_size': len(X_train),
            'test_size': len(X_test)
        }

        # Log results
        logger.info(f"Modelo entrenado - R²: {r2:.3f}, MSE: {mse:.3f}, MAE: {mae:.3f}")
        logger.info(f"Validación cruzada - Media: {cv_scores.mean():.3f}, Std: {cv_scores.std():.3f}")

        return results

    def predict_reward(self, features: Dict) -> float:
        """Predice reward para nuevas features"""

        if not self.model:
            raise ValueError("Modelo no entrenado")

        # Crear DataFrame con features
        feature_df = pd.DataFrame([features])

        # Asegurar que tenga todas las columnas necesarias
        for col in self.feature_columns:
            if col not in feature_df.columns:
                feature_df[col] = 0

        # Predecir
        prediction = self.model.predict(feature_df[self.feature_columns])[0]

        # Clamp entre 1-5
        return max(1.0, min(5.0, prediction))

    def save_model(self, model_path: str):
        """Guarda modelo entrenado"""

        import joblib

        if not self.model:
            raise ValueError("No hay modelo para guardar")

        model_data = {
            'model': self.model,
            'feature_columns': self.feature_columns,
            'timestamp': datetime.now().isoformat()
        }

        joblib.dump(model_data, model_path)
        logger.info(f"Modelo guardado en {model_path}")

    def load_model(self, model_path: str):
        """Carga modelo guardado"""

        import joblib

        model_data = joblib.load(model_path)
        self.model = model_data['model']
        self.feature_columns = model_data['feature_columns']

        logger.info(f"Modelo cargado desde {model_path}")