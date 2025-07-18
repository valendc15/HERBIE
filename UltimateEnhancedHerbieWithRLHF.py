#!/usr/bin/env python3
"""
Main para UltimateEnhancedHerbie con RLHF integrado
Combina todas las funcionalidades sin recursión
"""

import os
import sys
import logging
from datetime import datetime
from typing import Optional

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ultimate_herbie_rlhf.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Importar componentes necesarios
try:
    # Importar el agente original (ajustar ruta según tu estructura)
    from ultimateEnhancedHerbie import UltimateSuperEnhancedHerbieAgent
    from frameworkManager import EnhancedFrameworkDatabase

    # Importar sistema RLHF
    from rlhf_enhanced_herbie import (
        RLHFWrapper,
        integrate_rlhf_with_existing_agent
    )

except ImportError as e:
    print(f"❌ Error importando módulos: {e}")
    print("🔧 Asegúrate de tener todos los archivos en el mismo directorio")
    sys.exit(1)


class UltimateHerbieWithRLHF:
    """Clase principal que integra UltimateEnhancedHerbie con RLHF"""

    def __init__(self):
        print("🚀 Inicializando Ultimate Enhanced Herbie con RLHF...")

        try:
            # Crear agente base
            print("   📡 Creando agente base...")
            self.base_agent = UltimateSuperEnhancedHerbieAgent()

            # Integrar RLHF
            print("   🧠 Integrando sistema RLHF...")
            self.agent = integrate_rlhf_with_existing_agent(self.base_agent)

            # Estado de la aplicación
            self.rlhf_enabled = False
            self.session_start = datetime.now()

            print("✅ Inicialización completada")

        except Exception as e:
            print(f"❌ Error durante inicialización: {e}")
            raise

    def show_welcome_message(self):
        """Muestra mensaje de bienvenida completo"""

        print("\n" + "=" * 70)
        print("🤖 ULTIMATE ENHANCED HERBIE CON RLHF")
        print("=" * 70)

        print("\n🎯 Características principales:")
        print("   • 🔧 Ejecución real de comandos CLI")
        print("   • ☁️ Integración completa con GitHub")
        print("   • 🧠 Aprendizaje por feedback humano (RLHF)")
        print("   • 📊 Telemetría avanzada y métricas")
        print("   • 🎨 Estilos de conversación adaptativos")
        print("   • 🔍 Análisis inteligente de dependencias")

        print("\n📋 Frameworks soportados:")
        frameworks = EnhancedFrameworkDatabase.get_framework_names()
        for i, framework in enumerate(frameworks, 1):
            print(f"   {i}. {framework.upper()}")

        print("\n🧠 Modo RLHF (Reinforcement Learning from Human Feedback):")
        print("   El agente aprende de tu feedback para mejorar sus respuestas")
        print("   Cada interacción puede ser valorada y comentada")

        # Preguntar si quiere habilitar RLHF
        print("\n" + "─" * 50)
        rlhf_choice = input("¿Quieres habilitar el modo RLHF? (s/n): ").strip().lower()

        if rlhf_choice in ['s', 'sí', 'si', 'yes', 'y']:
            self.enable_rlhf()
        else:
            print("🔄 Modo normal habilitado (sin aprendizaje)")

        print("\n📝 Comandos disponibles:")
        print("   • Conversación normal: Solo escribe tu mensaje")
        print("   • /help - Mostrar ayuda")
        print("   • /stats - Estadísticas del sistema")

        if self.rlhf_enabled:
            print("   • /feedback <rating> [comentario] - Dar feedback (1-5)")
            print("   • /rlhf-stats - Estadísticas de aprendizaje")
            print("   • /toggle-rlhf - Activar/desactivar RLHF")

        print("   • /quit - Salir del programa")

        print("\n🎉 ¡Listo para ayudarte! ¿Qué proyecto quieres crear hoy?")

    def enable_rlhf(self):
        """Habilita el modo RLHF"""
        self.rlhf_enabled = True
        print("🧠 Modo RLHF habilitado")
        print("💡 Ahora Herbie aprenderá de tu feedback para mejorar")
        print("📊 Usa '/feedback <1-5>' después de cada respuesta")

    def disable_rlhf(self):
        """Deshabilita el modo RLHF"""
        self.rlhf_enabled = False
        print("🔄 Modo RLHF deshabilitado")
        print("📝 Herbie funcionará en modo normal")

    def process_command(self, user_input: str) -> bool:
        """Procesa comandos especiales. Retorna True si se procesó un comando"""

        if user_input.startswith('/'):
            command_parts = user_input.split(maxsplit=2)
            command = command_parts[0].lower()

            if command == '/help':
                self.show_help()
                return True

            elif command == '/stats':
                self.show_system_stats()
                return True

            elif command == '/rlhf-stats':
                if self.rlhf_enabled:
                    self.show_rlhf_stats()
                else:
                    print("❌ RLHF no está habilitado")
                return True

            elif command == '/feedback':
                if self.rlhf_enabled:
                    self.process_feedback(command_parts)
                else:
                    print("❌ RLHF no está habilitado. Usa '/toggle-rlhf' para activarlo")
                return True

            elif command == '/toggle-rlhf':
                if self.rlhf_enabled:
                    self.disable_rlhf()
                else:
                    self.enable_rlhf()
                return True

            elif command in ['/quit', '/exit']:
                return self.quit_application()

            else:
                print(f"❌ Comando desconocido: {command}")
                print("💡 Usa '/help' para ver comandos disponibles")
                return True

        return False

    def process_feedback(self, command_parts: list):
        """Procesa comando de feedback"""

        if len(command_parts) < 2:
            print("❌ Formato: /feedback <rating> [comentario]")
            print("💡 Ejemplo: /feedback 4 Muy buena respuesta")
            return

        try:
            rating = int(command_parts[1])
            if rating < 1 or rating > 5:
                print("❌ Rating debe estar entre 1 y 5")
                return

            comment = command_parts[2] if len(command_parts) > 2 else ""

            # Dar feedback usando el sistema RLHF
            self.agent.give_feedback(rating, comment)

            # Mensaje de confirmación
            feedback_msg = {
                1: "😞 Feedback negativo registrado - trabajaré en mejorar",
                2: "😐 Feedback bajo registrado - necesito mejorar",
                3: "🤔 Feedback neutral registrado - puedo hacerlo mejor",
                4: "😊 Feedback positivo registrado - ¡gracias!",
                5: "🎉 Feedback excelente registrado - ¡me alegra ayudarte!"
            }

            print(feedback_msg[rating])

        except ValueError:
            print("❌ Rating debe ser un número entero (1-5)")

    def show_help(self):
        """Muestra ayuda completa"""

        print("\n" + "=" * 50)
        print("📚 AYUDA - ULTIMATE ENHANCED HERBIE")
        print("=" * 50)

        print("\n🎯 Ejemplos de uso:")
        print("   • 'Quiero crear una app React llamada mi-proyecto'")
        print("   • 'Necesito un proyecto Django para una API'")
        print("   • 'Crear aplicación Vue con routing'")
        print("   • '¿Qué necesito para desarrollar con Angular?'")

        print("\n📋 Comandos del sistema:")
        print("   /help          - Mostrar esta ayuda")
        print("   /stats         - Estadísticas del sistema")
        print("   /quit          - Salir del programa")

        if self.rlhf_enabled:
            print("\n🧠 Comandos RLHF:")
            print("   /feedback <1-5> [comentario] - Dar feedback")
            print("   /rlhf-stats                  - Estadísticas de aprendizaje")
            print("   /toggle-rlhf                 - Activar/desactivar RLHF")

            print("\n📊 Escala de feedback:")
            print("   1 - Muy malo    😞")
            print("   2 - Malo        😐")
            print("   3 - Regular     🤔")
            print("   4 - Bueno       😊")
            print("   5 - Excelente   🎉")

        print("\n🔧 Funcionalidades:")
        print("   • Creación automática de proyectos")
        print("   • Verificación de dependencias")
        print("   • Ejecución de comandos CLI")
        print("   • Creación de repositorios GitHub")
        print("   • Subida automática de código")

        if self.rlhf_enabled:
            print("   • Aprendizaje de estilos de conversación")
            print("   • Adaptación basada en feedback")

    def show_system_stats(self):
        """Muestra estadísticas del sistema"""

        print("\n" + "=" * 50)
        print("📊 ESTADÍSTICAS DEL SISTEMA")
        print("=" * 50)

        session_duration = datetime.now() - self.session_start

        print(f"\n⏱️  Sesión actual:")
        print(f"   Duración: {session_duration}")
        print(f"   Inicio: {self.session_start.strftime('%Y-%m-%d %H:%M:%S')}")

        print(f"\n🧠 Estado RLHF:")
        print(f"   Habilitado: {'✅ Sí' if self.rlhf_enabled else '❌ No'}")

        print(f"\n📋 Frameworks soportados:")
        frameworks = EnhancedFrameworkDatabase.get_framework_names()
        print(f"   Total: {len(frameworks)}")
        print(f"   Lista: {', '.join(frameworks)}")

        # Información del entorno
        print(f"\n🔧 Entorno:")
        print(f"   Python: {sys.version.split()[0]}")
        print(f"   Plataforma: {sys.platform}")
        print(f"   Directorio: {os.getcwd()}")

        # Verificar tokens
        github_token = os.getenv('GITHUB_TOKEN')
        google_key = os.getenv('GOOGLE_API_KEY')

        print(f"\n🔑 Configuración:")
        print(f"   GitHub Token: {'✅ Configurado' if github_token else '❌ No configurado'}")
        print(f"   Google API Key: {'✅ Configurado' if google_key else '❌ No configurado'}")

    def show_rlhf_stats(self):
        """Muestra estadísticas de aprendizaje RLHF"""

        try:
            stats = self.agent.get_rlhf_stats()

            print("\n" + "=" * 50)
            print("🧠 ESTADÍSTICAS DE APRENDIZAJE RLHF")
            print("=" * 50)

            print(f"\n📊 Feedback recibido:")
            print(f"   Total: {stats.get('total_feedback', 0)}")
            print(f"   Rating promedio: {stats.get('average_rating', 0):.2f}/5")

            if 'rating_distribution' in stats:
                print(f"\n📈 Distribución de ratings:")
                for rating, count in stats['rating_distribution'].items():
                    stars = "⭐" * int(rating)
                    print(f"   {stars} ({rating}): {count} votos")

            if 'learned_styles' in stats and stats['learned_styles']:
                print(f"\n🎨 Estilos aprendidos:")
                for context, styles in stats['learned_styles'].items():
                    print(f"   {context.upper()}:")
                    for style, score in styles.items():
                        indicator = "📈" if score > 0 else "📉" if score < 0 else "➖"
                        print(f"     {indicator} {style}: {score:+.1f}")

        except Exception as e:
            print(f"❌ Error obteniendo estadísticas RLHF: {e}")

    def quit_application(self) -> bool:
        """Finaliza la aplicación"""

        print("\n" + "=" * 50)
        print("👋 FINALIZANDO SESIÓN")
        print("=" * 50)

        session_duration = datetime.now() - self.session_start
        print(f"\n⏱️  Duración de la sesión: {session_duration}")

        if self.rlhf_enabled:
            try:
                stats = self.agent.get_rlhf_stats()
                feedback_count = stats.get('total_feedback', 0)
                avg_rating = stats.get('average_rating', 0)

                print(f"\n🧠 Resumen de aprendizaje:")
                print(f"   Feedback recibido: {feedback_count}")
                print(f"   Rating promedio: {avg_rating:.2f}/5")

                if feedback_count > 0:
                    print(f"   ¡Gracias por ayudarme a aprender! 🎓")

            except Exception as e:
                print(f"⚠️  Error obteniendo estadísticas finales: {e}")

        print(f"\n🚀 ¡Gracias por usar Ultimate Enhanced Herbie!")
        print(f"🔥 ¡Que tengas un desarrollo increíble!")

        return True

    def run(self):
        """Ejecuta el bucle principal de la aplicación"""

        try:
            # Mostrar mensaje de bienvenida
            self.show_welcome_message()

            # Bucle principal
            while True:
                try:
                    user_input = input("\n💬 Tú: ").strip()

                    if not user_input:
                        continue

                    # Procesar comandos especiales
                    if self.process_command(user_input):
                        if user_input.startswith('/quit') or user_input.startswith('/exit'):
                            break
                        continue

                    # Procesar entrada normal
                    print()  # Línea en blanco para mejor legibilidad

                    if self.rlhf_enabled:
                        # Usar modo RLHF
                        response = self.agent.rlhf_chat(user_input, use_rlhf=True)
                        print(f"🤖 Herbie: {response}")
                        print(f"💡 Usa '/feedback <1-5>' para ayudarme a mejorar")
                    else:
                        # Usar modo normal
                        response = self.agent.chat(user_input)
                        print(f"🤖 Herbie: {response}")

                except KeyboardInterrupt:
                    print("\n\n⌨️  Interrupción detectada")
                    break
                except EOFError:
                    print("\n\n📄 Fin de entrada detectado")
                    break
                except Exception as e:
                    print(f"\n❌ Error procesando entrada: {e}")
                    logger.error(f"Error en bucle principal: {e}")
                    continue

        except Exception as e:
            print(f"\n❌ Error fatal: {e}")
            logger.error(f"Error fatal en aplicación: {e}")

        finally:
            self.quit_application()


def main():
    """Función main principal"""

    print("🚀 Iniciando Ultimate Enhanced Herbie con RLHF...")

    # Verificar configuración
    if not os.getenv('GITHUB_TOKEN'):
        print("⚠️  GITHUB_TOKEN no configurado - funcionalidad GitHub limitada")

    if not os.getenv('GOOGLE_API_KEY'):
        print("⚠️  GOOGLE_API_KEY no configurado - funcionalidad IA limitada")

    try:
        # Crear y ejecutar aplicación
        app = UltimateHerbieWithRLHF()
        app.run()

    except KeyboardInterrupt:
        print("\n\n⌨️  Interrupción por teclado - finalizando...")
    except Exception as e:
        print(f"\n❌ Error crítico: {e}")
        logger.error(f"Error crítico en main: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()