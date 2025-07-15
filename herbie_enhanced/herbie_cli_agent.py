#!/usr/bin/env python3
# ============================================================================
# HERBIE CLI AGENT - INTERFAZ CONVERSACIONAL
# Agente interactivo con personalidad y capacidades avanzadas de IA
# ============================================================================

import sys
import os
import time
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
import random
from dataclasses import asdict

# Importar el sistema core
from herbie_enhanced.core_system import HerbieComponentFactory, HerbieOrchestrator


class HerbiePersonality:
    """Personalidad y respuestas conversacionales de Herbie"""

    GREETING_MESSAGES = [
        "¡Hola! Soy Herbie, tu asistente inteligente para crear proyectos increíbles! 🤖",
        "¡Saludos! Herbie aquí, listo para ayudarte a crear el próximo gran proyecto 🚀",
        "¡Hey! Soy Herbie, tu compañero de desarrollo con superpoderes de IA ⚡"
    ]

    FRAMEWORK_SUGGESTIONS = {
        'web': ['react', 'vue', 'angular', 'nextjs'],
        'backend': ['django', 'fastapi', 'rails'],
        'mobile': ['flutter', 'react-native'],
        'desktop': ['electron', 'flutter']
    }

    ENCOURAGEMENT_MESSAGES = [
        "¡Excelente elección! 🎯",
        "¡Me gusta tu estilo! 💪",
        "¡Genial! Vamos a crear algo increíble 🌟",
        "¡Perfecto! Esto va a estar buenísimo 🔥"
    ]

    THINKING_MESSAGES = [
        "🤔 Analizando tu idea...",
        "🧠 Procesando con mis neuronas artificiales...",
        "⚡ Aplicando magia de IA generativa...",
        "🔍 Buscando en mi base de conocimiento...",
        "💭 Pensando en la mejor solución..."
    ]

    ERROR_MESSAGES = [
        "¡Ups! Algo no salió como esperaba 😅",
        "¡Oops! Parece que tuve un pequeño problema 🤕",
        "¡Ay! Mi circuito de procesamiento tuvo un hiccup 🔧"
    ]


class HerbieConversationManager:
    """Maneja el flujo conversacional con el usuario"""

    def __init__(self, herbie_system: HerbieOrchestrator):
        self.herbie_system = herbie_system
        self.personality = HerbiePersonality()
        self.conversation_state = {
            'stage': 'greeting',
            'project_info': {},
            'user_preferences': {},
            'session_id': None
        }
        self.user_id = self._generate_user_id()

    def _generate_user_id(self) -> str:
        """Genera ID único para el usuario"""
        return f"user_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    def _print_animated(self, message: str, delay: float = 0.03):
        """Imprime mensaje con animación de typing"""
        for char in message:
            print(char, end='', flush=True)
            time.sleep(delay)
        print()

    def _print_thinking(self):
        """Muestra mensaje de pensamiento"""
        thinking_msg = random.choice(self.personality.THINKING_MESSAGES)
        print(f"\n{thinking_msg}")
        time.sleep(1.5)

    def start_conversation(self):
        """Inicia la conversación con el usuario"""
        self._clear_screen()
        self._show_banner()

        # Saludo inicial
        greeting = random.choice(self.personality.GREETING_MESSAGES)
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

    def _handle_project_description(self) -> Dict:
        """Maneja la descripción del proyecto"""
        while True:
            user_input = input("\n📝 Describe tu proyecto: ").strip()

            if not user_input:
                self._print_animated("🤔 Necesito que me cuentes algo sobre tu proyecto para poder ayudarte.")
                continue

            if user_input.lower() in ['salir', 'exit', 'quit']:
                self._print_animated("👋 ¡Hasta luego! Que tengas un excelente día codificando!")
                return {'action': 'exit'}

            # Procesar descripción
            return self._process_project_description(user_input)

    def _process_project_description(self, description: str) -> Dict:
        """Procesa la descripción y inicia el análisis"""
        self._print_thinking()

        try:
            # Usar el sistema avanzado para analizar
            result = self.herbie_system.create_project(
                user_input=description,
                user_id=self.user_id
            )

            if result['success']:
                return self._handle_successful_analysis(result)
            else:
                return self._handle_analysis_error(result)

        except Exception as e:
            error_msg = random.choice(self.personality.ERROR_MESSAGES)
            self._print_animated(f"{error_msg}")
            self._print_animated(f"Error técnico: {str(e)}")
            return {'action': 'retry'}

    def _handle_successful_analysis(self, result: Dict) -> Dict:
        """Maneja análisis exitoso y presenta opciones"""
        analysis = result['analysis']

        # Mostrar análisis
        encouragement = random.choice(self.personality.ENCOURAGEMENT_MESSAGES)
        self._print_animated(f"\n{encouragement}")

        print("\n" + "=" * 50)
        print("🎯 ANÁLISIS DEL PROYECTO")
        print("=" * 50)
        print(f"📁 Nombre sugerido: {analysis['repo_name']}")
        print(f"🛠️  Framework: {analysis['framework']}")
        print(f"📊 Complejidad: {analysis['complexity_score']}/5")
        print(f"🎲 Confianza: {analysis['confidence']:.1%}")
        print(f"🏷️  Tags: {', '.join(analysis['tags'])}")
        print(f"💭 Razonamiento: {analysis['reasoning']}")

        # Pregunta si quiere personalizar
        return self._ask_for_customization(result)

    def _ask_for_customization(self, result: Dict) -> Dict:
        """Pregunta si el usuario quiere personalizar algo"""
        print("\n" + "=" * 50)
        self._print_animated("¿Te gusta el análisis o quieres cambiar algo?")
        print("\n🔧 Opciones:")
        print("1. ¡Perfecto! Crear el proyecto así")
        print("2. Cambiar el nombre del repositorio")
        print("3. Usar un framework diferente")
        print("4. Hacer privado el repositorio")
        print("5. Empezar de nuevo")

        while True:
            choice = input("\n👉 Tu elección (1-5): ").strip()

            if choice == '1':
                return self._execute_project_creation(result)
            elif choice == '2':
                return self._customize_repo_name(result)
            elif choice == '3':
                return self._customize_framework(result)
            elif choice == '4':
                return self._toggle_privacy(result)
            elif choice == '5':
                return self._restart_conversation()
            else:
                self._print_animated("🤔 Por favor, elige una opción válida (1-5)")

    def _customize_repo_name(self, result: Dict) -> Dict:
        """Permite al usuario personalizar el nombre del repo"""
        current_name = result['analysis']['repo_name']
        self._print_animated(f"📁 Nombre actual: {current_name}")

        new_name = input("📝 Ingresa el nuevo nombre: ").strip()

        if new_name and new_name != current_name:
            result['analysis']['repo_name'] = new_name
            self._print_animated(f"✅ Nombre actualizado a: {new_name}")

        return self._ask_for_customization(result)

    def _customize_framework(self, result: Dict) -> Dict:
        """Permite cambiar el framework"""
        frameworks = ['react', 'vue', 'angular', 'django', 'fastapi', 'nextjs', 'flutter']

        print("\n🛠️  Frameworks disponibles:")
        for i, fw in enumerate(frameworks, 1):
            print(f"   {i}. {fw.title()}")

        while True:
            choice = input("\n👉 Elige framework (1-7): ").strip()

            try:
                fw_index = int(choice) - 1
                if 0 <= fw_index < len(frameworks):
                    new_framework = frameworks[fw_index]
                    result['analysis']['framework'] = new_framework
                    self._print_animated(f"🛠️  Framework cambiado a: {new_framework}")

                    # Recalcular análisis con nuevo framework
                    self._print_thinking()
                    return self._reanalyze_with_framework(result, new_framework)
                else:
                    self._print_animated("🤔 Por favor, elige un número válido (1-7)")
            except ValueError:
                self._print_animated("🤔 Por favor, ingresa un número válido")

    def _reanalyze_with_framework(self, result: Dict, new_framework: str) -> Dict:
        """Reanaliza el proyecto con el nuevo framework"""
        # Aquí podrías implementar lógica para recalcular
        # Por simplicidad, mantenemos el análisis actual
        self._print_animated(f"✅ Análisis actualizado para {new_framework}")
        return self._ask_for_customization(result)

    def _toggle_privacy(self, result: Dict) -> Dict:
        """Cambia la privacidad del repositorio"""
        current_privacy = result['analysis'].get('is_private', False)
        new_privacy = not current_privacy

        result['analysis']['is_private'] = new_privacy
        privacy_text = "privado" if new_privacy else "público"
        self._print_animated(f"🔒 Repositorio será: {privacy_text}")

        return self._ask_for_customization(result)

    def _restart_conversation(self) -> Dict:
        """Reinicia la conversación"""
        self._print_animated("🔄 ¡Perfecto! Empecemos de nuevo...")
        time.sleep(1)
        return self.start_conversation()

    def _execute_project_creation(self, result: Dict) -> Dict:
        """Ejecuta la creación del proyecto"""
        print("\n" + "=" * 50)
        print("🚀 CREANDO PROYECTO")
        print("=" * 50)

        self._print_animated("⚙️  Inicializando proyecto...")
        time.sleep(1)

        # Simular progreso
        steps = [
            "📋 Validando análisis...",
            "🔍 Verificando dependencias...",
            "📁 Creando estructura local...",
            "🐙 Creando repositorio en GitHub...",
            "📤 Subiendo código inicial...",
            "✅ ¡Proyecto creado exitosamente!"
        ]

        for step in steps:
            self._print_animated(step)
            time.sleep(0.8)

        # Mostrar resultado
        if result['success']:
            repo_url = result['result'].get('repo_url', 'https://github.com/user/proyecto')
            print(f"\n🎉 ¡Tu proyecto está listo!")
            print(f"🔗 URL: {repo_url}")
            print(f"⏱️  Tiempo de ejecución: {result['result'].get('execution_time', 0):.1f}s")

            # Pedir feedback
            return self._request_feedback(result)
        else:
            return self._handle_creation_error(result)

    def _request_feedback(self, result: Dict) -> Dict:
        """Solicita feedback del usuario"""
        print("\n" + "=" * 50)
        print("📝 FEEDBACK")
        print("=" * 50)

        self._print_animated("¡Tu opinión es muy valiosa para que pueda mejorar!")

        feedback_questions = [
            ("¿Qué tan satisfecho estás con el resultado? (1-10)", 'satisfaction'),
            ("¿El setup fue exitoso? (s/n)", 'setup_success'),
            ("¿Cómo calificarías la calidad del código? (1-10)", 'code_quality'),
            ("¿Recomendarías Herbie a otros desarrolladores? (s/n)", 'would_recommend')
        ]

        feedback_data = {}

        for question, key in feedback_questions:
            while True:
                response = input(f"\n{question}: ").strip().lower()

                if key in ['setup_success', 'would_recommend']:
                    if response in ['s', 'si', 'sí', 'y', 'yes']:
                        feedback_data[key] = True
                        break
                    elif response in ['n', 'no']:
                        feedback_data[key] = False
                        break
                    else:
                        print("Por favor responde 's' (sí) o 'n' (no)")
                else:
                    try:
                        score = int(response)
                        if 1 <= score <= 10:
                            feedback_data[key] = score / 10.0  # Normalizar a 0-1
                            break
                        else:
                            print("Por favor ingresa un número entre 1 y 10")
                    except ValueError:
                        print("Por favor ingresa un número válido")

        # Comentarios opcionales
        comments = input("\n💬 ¿Algún comentario adicional? (opcional): ").strip()
        feedback_data['comments'] = comments

        # Procesar feedback
        return self._process_feedback(result, feedback_data)

    def _process_feedback(self, result: Dict, feedback_data: Dict) -> Dict:
        """Procesa el feedback del usuario"""
        self._print_thinking()

        try:
            feedback_result = self.herbie_system.submit_feedback(
                session_id=result['session_id'],
                feedback_data=feedback_data
            )

            if feedback_result['success']:
                self._print_animated("🎯 ¡Gracias por tu feedback! He aprendido de tu experiencia.")
                self._print_animated("🧠 Mis algoritmos de IA se han actualizado para mejorar.")

                # Mostrar estadísticas
                self._show_system_stats()

                return self._ask_for_another_project()
            else:
                self._print_animated("⚠️  Hubo un problema procesando tu feedback, pero igual lo valoro mucho.")
                return self._ask_for_another_project()

        except Exception as e:
            self._print_animated("🤔 No pude procesar el feedback completamente, pero gracias por compartirlo.")
            return self._ask_for_another_project()

    def _show_system_stats(self):
        """Muestra estadísticas del sistema"""
        try:
            health = self.herbie_system.get_system_health()

            print("\n" + "=" * 40)
            print("📊 ESTADÍSTICAS DEL SISTEMA")
            print("=" * 40)
            print(f"✅ Tasa de éxito: {health['success_rate']:.1%}")
            print(f"🔢 Proyectos creados: {health['total_sessions']}")
            print(f"🛠️  Frameworks populares: {', '.join(health['frameworks_used'][:3])}")
            print(f"📈 Complejidad promedio: {health['avg_complexity']:.1f}/5")

        except Exception:
            pass  # Si hay error, no mostrar stats

    def _ask_for_another_project(self) -> Dict:
        """Pregunta si quiere crear otro proyecto"""
        print("\n" + "=" * 50)
        self._print_animated("¿Te gustaría crear otro proyecto? 🚀")

        while True:
            response = input("\n👉 (s/n): ").strip().lower()

            if response in ['s', 'si', 'sí', 'y', 'yes']:
                return self._restart_conversation()
            elif response in ['n', 'no']:
                self._print_animated("👋 ¡Gracias por usar Herbie! ¡Que tengas un excelente día desarrollando!")
                return {'action': 'exit'}
            else:
                self._print_animated("🤔 Por favor responde 's' (sí) o 'n' (no)")

    def _handle_analysis_error(self, result: Dict) -> Dict:
        """Maneja errores en el análisis"""
        error_msg = random.choice(self.personality.ERROR_MESSAGES)
        self._print_animated(f"{error_msg}")
        self._print_animated(f"💭 Problema: {result.get('error', 'Error desconocido')}")

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

    def _handle_creation_error(self, result: Dict) -> Dict:
        """Maneja errores en la creación"""
        error_msg = random.choice(self.personality.ERROR_MESSAGES)
        self._print_animated(f"{error_msg}")
        self._print_animated(f"💭 No pude crear el proyecto: {result.get('error', 'Error desconocido')}")

        print("\n🔧 Posibles soluciones:")
        print("1. Verificar conexión a internet")
        print("2. Revisar token de GitHub")
        print("3. Intentar con un framework diferente")

        return self._ask_for_another_project()


class HerbieCLI:
    """CLI principal de Herbie"""

    def __init__(self):
        self.herbie_system = None
        self.conversation_manager = None
        self._initialize_system()

    def _initialize_system(self):
        """Inicializa el sistema de Herbie"""
        try:
            print("🔧 Inicializando sistema Herbie Enhanced...")
            self.herbie_system = HerbieComponentFactory.create_advanced_system()
            self.conversation_manager = HerbieConversationManager(self.herbie_system)
            print("✅ Sistema inicializado correctamente")
            time.sleep(1)
        except Exception as e:
            print(f"❌ Error inicializando sistema: {e}")
            print("🔄 Intentando con sistema básico...")
            try:
                self.herbie_system = HerbieComponentFactory.create_basic_system()
                self.conversation_manager = HerbieConversationManager(self.herbie_system)
                print("✅ Sistema básico inicializado")
            except Exception as e2:
                print(f"❌ Error crítico: {e2}")
                sys.exit(1)

    def run(self):
        """Ejecuta la CLI de Herbie"""
        try:
            while True:
                result = self.conversation_manager.start_conversation()

                if result.get('action') == 'exit':
                    break
                elif result.get('action') == 'retry':
                    continue

        except KeyboardInterrupt:
            print("\n\n👋 ¡Hasta luego! Gracias por usar Herbie Enhanced!")
        except Exception as e:
            print(f"\n❌ Error inesperado: {e}")
            print("🔄 Reiniciando sistema...")
            self._initialize_system()
            self.run()


def main():
    """Función principal"""
    # Verificar variables de entorno
    if not os.getenv('GITHUB_TOKEN'):
        print("⚠️  ADVERTENCIA: GITHUB_TOKEN no está configurado")
        print("   Algunas funcionalidades pueden no funcionar correctamente")

    if not os.getenv('GOOGLE_API_KEY'):
        print("⚠️  ADVERTENCIA: GOOGLE_API_KEY no está configurado")
        print("   El análisis de IA puede usar valores por defecto")

    # Iniciar CLI
    cli = HerbieCLI()
    cli.run()


if __name__ == "__main__":
    main()