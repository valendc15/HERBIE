import os
import json
import time
import sqlite3
import hashlib
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict, deque

# Importar solo las clases necesarias del Enhanced Herbie original
# SIN crear dependencias circulares

logger = logging.getLogger(__name__)


class FeedbackType(Enum):
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"
    CORRECTION = "correction"


class InteractionType(Enum):
    GREETING = "greeting"
    PROJECT_CREATION = "project_creation"
    TECHNICAL_HELP = "technical_help"
    ERROR_HANDLING = "error_handling"
    CONVERSATION = "conversation"


@dataclass
class HumanFeedback:
    interaction_id: str
    user_input: str
    agent_response: str
    feedback_type: FeedbackType
    feedback_text: str
    rating: int  # 1-5 scale
    timestamp: datetime
    context: Dict[str, Any] = field(default_factory=dict)
    suggestions: List[str] = field(default_factory=list)
    interaction_type: InteractionType = InteractionType.CONVERSATION


@dataclass
class ConversationState:
    user_id: str
    session_id: str
    conversation_history: List[Dict] = field(default_factory=list)
    current_mood: str = "neutral"
    user_preferences: Dict = field(default_factory=dict)
    satisfaction_score: float = 0.5
    interaction_count: int = 0


class SimpleRLHFDatabase:
    """Base de datos simple para RLHF - sin dependencias complejas"""

    def __init__(self, db_path: str = "herbie_rlhf.db"):
        self.db_path = db_path
        self.init_database()

        # Cache en memoria para evitar acceso frecuente a BD
        self.feedback_cache = []
        self.style_preferences = defaultdict(lambda: defaultdict(float))
        self.load_cache()

    def init_database(self):
        """Inicializa BD con esquema simple"""
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
                           interaction_id
                           TEXT,
                           user_input
                           TEXT,
                           agent_response
                           TEXT,
                           rating
                           INTEGER,
                           feedback_text
                           TEXT,
                           timestamp
                           DATETIME
                           DEFAULT
                           CURRENT_TIMESTAMP
                       )
                       ''')

        cursor.execute('''
                       CREATE TABLE IF NOT EXISTS style_preferences
                       (
                           context
                           TEXT,
                           style
                           TEXT,
                           score
                           REAL,
                           updated
                           DATETIME
                           DEFAULT
                           CURRENT_TIMESTAMP,
                           PRIMARY
                           KEY
                       (
                           context,
                           style
                       )
                           )
                       ''')

        conn.commit()
        conn.close()

    def store_feedback(self, feedback: HumanFeedback):
        """Almacena feedback de forma simple"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
                       INSERT INTO feedback (interaction_id, user_input, agent_response, rating, feedback_text)
                       VALUES (?, ?, ?, ?, ?)
                       ''', (
                           feedback.interaction_id,
                           feedback.user_input,
                           feedback.agent_response,
                           feedback.rating,
                           feedback.feedback_text
                       ))

        conn.commit()
        conn.close()

        # Actualizar cache
        self.feedback_cache.append(feedback)
        if len(self.feedback_cache) > 100:
            self.feedback_cache.pop(0)  # Mantener solo los últimos 100

    def update_style_preference(self, context: str, style: str, score_delta: float):
        """Actualiza preferencia de estilo"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT OR REPLACE INTO style_preferences (context, style, score)
            VALUES (?, ?, COALESCE((SELECT score FROM style_preferences WHERE context=? AND style=?), 0) + ?)
        ''', (context, style, context, style, score_delta))

        conn.commit()
        conn.close()

        # Actualizar cache
        self.style_preferences[context][style] += score_delta

    def get_best_style(self, context: str) -> str:
        """Obtiene el mejor estilo para un contexto"""
        if context in self.style_preferences:
            preferences = self.style_preferences[context]
            if preferences:
                return max(preferences.items(), key=lambda x: x[1])[0]

        # Default styles por contexto
        defaults = {
            "greeting": "casual",
            "project_creation": "enthusiastic",
            "error_handling": "supportive",
            "technical_help": "technical",
            "conversation": "casual"
        }

        return defaults.get(context, "casual")

    def load_cache(self):
        """Carga cache desde BD"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Cargar preferencias de estilo
        cursor.execute('SELECT context, style, score FROM style_preferences')
        for row in cursor.fetchall():
            self.style_preferences[row[0]][row[1]] = row[2]

        conn.close()

    def get_statistics(self) -> Dict:
        """Obtiene estadísticas simples"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('SELECT COUNT(*), AVG(rating) FROM feedback')
        count, avg_rating = cursor.fetchone()

        cursor.execute('SELECT rating, COUNT(*) FROM feedback GROUP BY rating')
        rating_dist = dict(cursor.fetchall())

        conn.close()

        return {
            "total_feedback": count or 0,
            "average_rating": avg_rating or 0,
            "rating_distribution": rating_dist,
            "learned_styles": dict(self.style_preferences)
        }


class ConversationStyleManager:
    """Gestor de estilos de conversación - SEPARADO del agente principal"""

    def __init__(self, db: SimpleRLHFDatabase):
        self.db = db

        # Patrones de estilo simples
        self.style_patterns = {
            "casual": {
                "greeting": "¡Hola! ¿Cómo estás?",
                "positive": "¡Genial!",
                "question": "¿Qué necesitas?"
            },
            "enthusiastic": {
                "greeting": "¡Hola! 🎉 ¡Qué emocionante!",
                "positive": "¡Increíble! 🚀",
                "question": "¿Qué proyecto increíble vamos a crear?"
            },
            "supportive": {
                "greeting": "Hola, estoy aquí para ayudarte",
                "positive": "¡Perfecto! Lo estás haciendo bien",
                "question": "¿Cómo puedo ayudarte mejor?"
            },
            "technical": {
                "greeting": "Saludos. Sistema listo.",
                "positive": "Comando ejecutado exitosamente",
                "question": "¿Qué framework necesitas?"
            }
        }

    def classify_interaction(self, user_input: str) -> str:
        """Clasifica el tipo de interacción"""
        user_lower = user_input.lower()

        if any(word in user_lower for word in ["hola", "buenos días", "hey"]):
            return "greeting"
        elif any(word in user_lower for word in ["crear", "proyecto", "nuevo"]):
            return "project_creation"
        elif any(word in user_lower for word in ["error", "problema", "falla"]):
            return "error_handling"
        elif any(word in user_lower for word in ["ayuda", "como", "explicar"]):
            return "technical_help"
        else:
            return "conversation"

    def apply_style_to_response(self, response: str, style: str, interaction_type: str) -> str:
        """Aplica estilo a una respuesta - SIN modificar el agente original"""

        # Obtener patrones del estilo
        patterns = self.style_patterns.get(style, self.style_patterns["casual"])

        # Aplicar modificaciones según el estilo
        if style == "enthusiastic":
            # Añadir emojis si no los tiene
            if not any(emoji in response for emoji in ["🎉", "🚀", "✨", "💡"]):
                response = "🚀 " + response

        elif style == "supportive":
            # Añadir elementos de apoyo
            if interaction_type == "error_handling":
                if not response.startswith("💪"):
                    response = "💪 " + response

        elif style == "technical":
            # Formato más técnico
            if not response.startswith("📋"):
                response = "📋 " + response

        return response

    def learn_from_feedback(self, feedback: HumanFeedback, style_used: str):
        """Aprende de feedback - actualiza preferencias"""

        interaction_type = self.classify_interaction(feedback.user_input)

        # Convertir rating a score delta
        score_delta = (feedback.rating - 3) * 0.5  # -1 a 1

        # Actualizar preferencia
        self.db.update_style_preference(interaction_type, style_used, score_delta)

        print(f"📊 Aprendizaje: {interaction_type} + {style_used} → {score_delta:+.1f}")


class RLHFWrapper:
    """Wrapper RLHF que NO hereda del agente original - evita recursión"""

    def __init__(self, agent_instance):
        # Referencia al agente original SIN herencia
        self.agent = agent_instance
        self.db = SimpleRLHFDatabase()
        self.style_manager = ConversationStyleManager(self.db)

        # Estado de la sesión
        self.session_id = self._generate_session_id()
        self.conversation_history = []
        self.learning_enabled = True
        self.last_interaction_id = None
        self.last_style_used = "casual"

    def _generate_session_id(self) -> str:
        """Genera ID único para la sesión"""
        return hashlib.md5(f"{datetime.now()}{os.getpid()}".encode()).hexdigest()[:8]

    def chat_with_learning(self, user_input: str) -> str:
        """Chat que aprende - SIN recursión"""

        # Generar ID para la interacción
        interaction_id = hashlib.md5(f"{user_input}{time.time()}".encode()).hexdigest()[:12]

        # Clasificar interacción
        interaction_type = self.style_manager.classify_interaction(user_input)

        # Obtener mejor estilo aprendido
        best_style = self.db.get_best_style(interaction_type)

        # Llamar al agente original DIRECTAMENTE - sin herencia
        base_response = self.agent.chat(user_input)

        # Aplicar estilo aprendido
        styled_response = self.style_manager.apply_style_to_response(
            base_response, best_style, interaction_type
        )

        # Almacenar información para feedback
        self.last_interaction_id = interaction_id
        self.last_style_used = best_style

        # Guardar en historial
        self.conversation_history.append({
            "id": interaction_id,
            "user_input": user_input,
            "agent_response": styled_response,
            "style_used": best_style,
            "interaction_type": interaction_type,
            "timestamp": datetime.now()
        })

        return styled_response

    def give_feedback(self, rating: int, comment: str = ""):
        """Dar feedback sobre la última interacción"""

        if not self.last_interaction_id:
            print("❌ No hay interacción reciente para dar feedback")
            return

        # Buscar la interacción
        interaction = None
        for item in reversed(self.conversation_history):
            if item["id"] == self.last_interaction_id:
                interaction = item
                break

        if not interaction:
            print("❌ No se encontró la interacción")
            return

        # Crear feedback
        feedback = HumanFeedback(
            interaction_id=self.last_interaction_id,
            user_input=interaction["user_input"],
            agent_response=interaction["agent_response"],
            feedback_type=FeedbackType.POSITIVE if rating >= 4 else FeedbackType.NEGATIVE if rating <= 2 else FeedbackType.NEUTRAL,
            feedback_text=comment,
            rating=rating,
            timestamp=datetime.now()
        )

        # Almacenar feedback
        self.db.store_feedback(feedback)

        # Aprender del feedback
        if self.learning_enabled:
            self.style_manager.learn_from_feedback(feedback, self.last_style_used)

        print(f"✅ Feedback registrado: {rating}/5 - {comment}")

    def get_statistics(self) -> Dict:
        """Obtiene estadísticas de aprendizaje"""
        return self.db.get_statistics()

    def enable_learning(self, enabled: bool = True):
        """Habilita/deshabilita aprendizaje"""
        self.learning_enabled = enabled
        print(f"🧠 Aprendizaje {'habilitado' if enabled else 'deshabilitado'}")


def create_simple_rlhf_session():
    """Crea sesión RLHF simple - SIN dependencias complejas"""

    print("🧠 Sesión RLHF Simple para Enhanced Herbie")
    print("=" * 50)

    # Crear agente mock para pruebas
    class MockEnhancedHerbie:
        def __init__(self):
            self.frameworks = ["react", "vue", "django", "angular"]

        def chat(self, user_input: str) -> str:
            """Simulación simple del Enhanced Herbie"""
            user_lower = user_input.lower()

            if any(word in user_lower for word in ["hola", "buenos días", "hey"]):
                return "¡Hola! ¿En qué puedo ayudarte hoy?"
            elif "react" in user_lower:
                return "¡Excelente elección! React es perfecto para crear interfaces interactivas. ¿Cómo quieres llamar tu proyecto?"
            elif "error" in user_lower or "problema" in user_lower:
                return "Veo que tienes un problema. Vamos a solucionarlo paso a paso."
            elif "crear" in user_lower and "proyecto" in user_lower:
                return "¡Genial! Vamos a crear un proyecto nuevo. ¿Qué framework prefieres?"
            else:
                return f"Entiendo que preguntas sobre: {user_input}. Te puedo ayudar con React, Vue, Django y Angular."

    # Crear agente y wrapper RLHF
    base_agent = MockEnhancedHerbie()
    rlhf_wrapper = RLHFWrapper(base_agent)

    print("\n📋 Comandos disponibles:")
    print("   /feedback <rating> [comentario] - Dar feedback (1-5)")
    print("   /stats - Ver estadísticas de aprendizaje")
    print("   /toggle-learning - Habilitar/deshabilitar aprendizaje")
    print("   /quit - Salir")

    print("\n🎯 Ejemplos de uso:")
    print("   Tú: Hola")
    print("   Herbie: ¡Hola! ¿En qué puedo ayudarte hoy?")
    print("   Tú: /feedback 3 Muy genérico")
    print("   [Herbie aprende y adapta su estilo]")

    while True:
        try:
            user_input = input("\n💬 Tú: ").strip()

            if not user_input:
                continue

            # Comandos especiales
            if user_input.startswith('/feedback'):
                parts = user_input.split(maxsplit=2)
                if len(parts) >= 2:
                    try:
                        rating = int(parts[1])
                        comment = parts[2] if len(parts) > 2 else ""
                        rlhf_wrapper.give_feedback(rating, comment)
                    except ValueError:
                        print("❌ Rating debe ser un número del 1 al 5")
                else:
                    print("❌ Formato: /feedback <rating> [comentario]")
                continue

            if user_input == '/stats':
                stats = rlhf_wrapper.get_statistics()
                print("\n📊 Estadísticas de Aprendizaje:")
                print(f"   Total feedback: {stats['total_feedback']}")
                print(f"   Rating promedio: {stats['average_rating']:.2f}")
                print(f"   Distribución de ratings: {stats['rating_distribution']}")
                if stats['learned_styles']:
                    print("   Estilos aprendidos:")
                    for context, styles in stats['learned_styles'].items():
                        print(f"     {context}: {dict(styles)}")
                continue

            if user_input == '/toggle-learning':
                rlhf_wrapper.enable_learning(not rlhf_wrapper.learning_enabled)
                continue

            if user_input in ['/quit', 'exit', 'salir']:
                print("\n👋 ¡Hasta luego! Gracias por ayudar a Herbie a aprender.")
                break

            # Procesar entrada normal
            response = rlhf_wrapper.chat_with_learning(user_input)
            print(f"\n🤖 Herbie: {response}")
            print(f"💡 Usa '/feedback <1-5>' para ayudarme a mejorar")

        except KeyboardInterrupt:
            print("\n\n👋 Sesión terminada")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")
            continue


def integrate_rlhf_with_existing_agent(existing_agent):
    """Integra RLHF con agente existente - SIN recursión"""

    print("🔗 Integrando RLHF con Enhanced Herbie existente...")

    # Crear wrapper sin herencia
    rlhf_wrapper = RLHFWrapper(existing_agent)

    # Función para alternar entre modo normal y RLHF
    def enhanced_chat_with_rlhf(user_input: str, use_rlhf: bool = True) -> str:
        if use_rlhf:
            return rlhf_wrapper.chat_with_learning(user_input)
        else:
            return existing_agent.chat(user_input)

    # Añadir métodos al agente existente SIN herencia
    existing_agent.rlhf_chat = enhanced_chat_with_rlhf
    existing_agent.give_feedback = rlhf_wrapper.give_feedback
    existing_agent.get_rlhf_stats = rlhf_wrapper.get_statistics
    existing_agent.toggle_rlhf_learning = rlhf_wrapper.enable_learning

    print("✅ RLHF integrado exitosamente")
    print("📋 Nuevos métodos disponibles:")
    print("   - agent.rlhf_chat(input, use_rlhf=True)")
    print("   - agent.give_feedback(rating, comment)")
    print("   - agent.get_rlhf_stats()")
    print("   - agent.toggle_rlhf_learning(enabled)")

    return existing_agent


# Ejemplo de uso sin recursión
if __name__ == "__main__":
    create_simple_rlhf_session()
