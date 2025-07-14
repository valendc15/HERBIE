#!/usr/bin/env python3
"""
Herbie Agent - Función Interactiva Corregida
Sistema de chat conversacional para crear proyectos
"""

import os
import sys
import time
from typing import Dict, List, Optional
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.prompt import Prompt, Confirm
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

# Cargar variables de entorno
try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass  # dotenv no es obligatorio

# Agregar src al path si es necesario
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

try:
    from herbie.agent import HerbieAgent
    from herbie.utils.logging_config import setup_logging
except ImportError:
    # Fallback para testing sin instalación completa
    print("⚠️  Módulos de Herbie no encontrados, usando modo simulado")


    class MockAgent:
        def __init__(self):
            self.learning_mode = "few_shot"
            self.confidence_threshold = 0.7

        def process_request(self, user_input):
            # Simular procesamiento
            time.sleep(1)
            return type('Response', (), {
                'success': True,
                'result': {
                    'framework': 'react',
                    'repo_name': 'test-project',
                    'is_private': False,
                    'description': 'Proyecto de prueba',
                    'init_command': 'npx create-react-app test-project'
                },
                'response_time': 1.2,
                'confidence': 0.85,
                'reasoning': 'Análisis simulado para testing'
            })()

        def set_learning_mode(self, mode):
            self.learning_mode = mode


    HerbieAgent = MockAgent
    setup_logging = lambda: type('Logger', (), {'info': print, 'error': print, 'warning': print})()

logger = setup_logging()
console = Console()


class InteractiveHerbie:
    def __init__(self):
        try:
            self.agent = HerbieAgent()
        except Exception as e:
            console.print(f"⚠️  Error inicializando agente: {e}")
            self.agent = None

        self.user_name = "Usuario"
        self.conversation_history = []
        self.session_stats = {
            'projects_created': 0,
            'repos_created': 0,
            'session_start': time.time()
        }

    def welcome_message(self):
        """Mensaje de bienvenida personalizado"""
        console.clear()

        welcome_text = Text()
        welcome_text.append("¡Hola! Soy ", style="bold blue")
        welcome_text.append("H.E.R.B.I.E.", style="bold green")
        welcome_text.append(" 🤖\n", style="bold blue")
        welcome_text.append("(Helpful Engine for Repository Building and Intelligent Execution)\n\n")
        welcome_text.append(
            "Estoy aquí para ayudarte a crear proyectos y repositorios de GitHub de manera inteligente.\n")
        welcome_text.append("Puedo trabajar con React, Vue, Django, FastAPI, Flutter y más frameworks.\n\n")

        console.print(Panel(welcome_text, border_style="green", title="🚀 Bienvenido a Herbie"))

    def get_user_name(self):
        """Obtiene nombre del usuario"""
        try:
            name = Prompt.ask("¿Cómo te llamas?", default="Desarrollador")
            self.user_name = name

            greeting = Text()
            greeting.append(f"¡Perfecto, {name}! ", style="bold green")
            greeting.append("Es un placer conocerte. ", style="cyan")
            greeting.append("Estoy listo para ayudarte a crear proyectos increíbles.", style="bold cyan")

            console.print(Panel(greeting, border_style="blue", title="👋 ¡Hola!"))
        except (KeyboardInterrupt, EOFError):
            console.print("\n👋 ¡Hasta luego!")
            sys.exit(0)

    def show_capabilities(self):
        """Muestra capacidades del agente"""
        table = Table(title="🛠️ Mis Capacidades", show_header=True, header_style="bold magenta")
        table.add_column("Framework", style="cyan", width=12)
        table.add_column("Comando de Ejemplo", style="green", width=40)
        table.add_column("Descripción", style="yellow", width=30)

        examples = [
            ("React", "crea una app React para gestión de tareas", "Aplicaciones web interactivas"),
            ("Vue.js", "aplicación Vue para dashboard", "Interfaces de usuario modernas"),
            ("Django", "API Django privada para usuarios", "Backend robusto con Python"),
            ("FastAPI", "API FastAPI para blog", "APIs rápidas y modernas"),
            ("Flutter", "app Flutter para móvil", "Aplicaciones móviles multiplataforma"),
            ("Angular", "aplicación Angular empresarial", "Apps web escalables"),
            ("Rails", "aplicación Rails para e-commerce", "Web apps con Ruby"),
            ("Flask", "API Flask para microservicios", "APIs ligeras con Python")
        ]

        for framework, example, desc in examples:
            table.add_row(framework, example, desc)

        console.print(table)

        # Consejos adicionales
        tips = Text()
        tips.append("\n💡 Consejos para obtener mejores resultados:\n", style="bold cyan")
        tips.append("• Menciona si quieres el repositorio privado o público\n", style="dim")
        tips.append("• Describe el propósito del proyecto\n", style="dim")
        tips.append("• Menciona características especiales (auth, base de datos, etc.)\n", style="dim")
        tips.append("• Usa lenguaje natural, ¡no te preocupes por comandos específicos!\n", style="dim")

        console.print(tips)

    def show_help_menu(self):
        """Muestra menú de ayuda"""
        help_text = Text()
        help_text.append("📚 Comandos Disponibles:\n\n", style="bold cyan")
        help_text.append("• 'ayuda' o 'help' - Mostrar esta ayuda\n", style="green")
        help_text.append("• 'capacidades' - Ver frameworks soportados\n", style="green")
        help_text.append("• 'estadísticas' - Ver estadísticas de la sesión\n", style="green")
        help_text.append("• 'historial' - Ver historial de proyectos\n", style="green")
        help_text.append("• 'salir' o 'exit' - Salir del programa\n", style="green")

        console.print(Panel(help_text, border_style="blue", title="📖 Ayuda"))

    def show_session_stats(self):
        """Muestra estadísticas de la sesión"""
        session_time = time.time() - self.session_stats['session_start']

        stats_text = Text()
        stats_text.append("📊 Estadísticas de la Sesión:\n\n", style="bold cyan")
        stats_text.append(f"👤 Usuario: {self.user_name}\n", style="white")
        stats_text.append(f"⏱️ Tiempo de sesión: {session_time / 60:.1f} minutos\n", style="white")
        stats_text.append(f"🚀 Proyectos analizados: {self.session_stats['projects_created']}\n", style="white")
        stats_text.append(f"📦 Repositorios creados: {self.session_stats['repos_created']}\n", style="white")
        if self.agent:
            stats_text.append(f"🎯 Modo de aprendizaje: {getattr(self.agent, 'learning_mode', 'N/A')}\n", style="white")

        console.print(Panel(stats_text, border_style="yellow", title="📈 Estadísticas"))

    def show_project_history(self):
        """Muestra historial de proyectos"""
        if not self.conversation_history:
            console.print("📝 No hay proyectos en el historial de esta sesión")
            return

        table = Table(title="📋 Historial de Proyectos", show_header=True, header_style="bold magenta")
        table.add_column("#", style="cyan", width=3)
        table.add_column("Proyecto", style="green", width=25)
        table.add_column("Framework", style="yellow", width=12)
        table.add_column("Estado", style="white", width=15)

        for i, project in enumerate(self.conversation_history, 1):
            status = "✅ Completado" if project.get('completed', False) else "⏳ Analizado"
            table.add_row(
                str(i),
                project.get('name', 'Sin nombre'),
                project.get('framework', 'N/A'),
                status
            )

        console.print(table)

    def process_user_input(self, user_input: str):
        """Procesa entrada del usuario con animación"""

        if not self.agent:
            console.print("❌ Agente no disponible")
            return None

        # Mostrar que está procesando
        with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
                transient=True
        ) as progress:
            task = progress.add_task("🧠 Analizando tu solicitud...", total=None)

            try:
                # Simular procesamiento por pasos
                time.sleep(0.5)
                progress.update(task, description="📝 Procesando lenguaje natural...")
                time.sleep(0.5)
                progress.update(task, description="🔍 Detectando framework...")
                time.sleep(0.5)
                progress.update(task, description="⚙️ Generando configuración...")

                # Procesar con el agente
                response = self.agent.process_request(user_input)

                progress.update(task, description="✅ Análisis completo")
                time.sleep(0.5)

                return response

            except Exception as e:
                progress.update(task, description=f"❌ Error: {str(e)}")
                time.sleep(1)
                return None

    def show_analysis_result(self, response, user_input: str):
        """Muestra resultado del análisis de forma atractiva"""

        if not response or not response.success:
            error_msg = response.error if response else "Error desconocido"
            console.print(Panel(
                f"❌ [bold red]Ups! Hubo un problema:[/bold red]\n\n{error_msg}\n\n"
                f"💡 [cyan]Sugerencia:[/cyan] Intenta ser más específico sobre el tipo de proyecto",
                border_style="red",
                title="Error en el Análisis"
            ))
            return

        result = response.result

        # Panel principal con resultado
        result_text = Text()
        result_text.append("📊 Análisis Completado\n\n", style="bold green")

        # Información del proyecto
        result_text.append("🎯 Información del Proyecto:\n", style="bold")
        result_text.append(f"   🔧 Framework: ", style="white")
        result_text.append(f"{result.get('framework', 'N/A')}\n", style="bold cyan")
        result_text.append(f"   📁 Nombre: ", style="white")
        result_text.append(f"{result.get('repo_name', 'N/A')}\n", style="bold green")
        result_text.append(f"   🔒 Visibilidad: ", style="white")
        result_text.append(f"{'🔐 Privado' if result.get('is_private') else '🌐 Público'}\n", style="bold yellow")
        result_text.append(f"   📝 Descripción: ", style="white")
        result_text.append(f"{result.get('description', 'N/A')}\n", style="white")

        if result.get('init_command'):
            result_text.append(f"   ⚡ Comando: ", style="white")
            result_text.append(f"{result.get('init_command')}\n", style="bold blue")

        # Métricas de rendimiento
        result_text.append(f"\n📈 Métricas de Rendimiento:\n", style="bold")
        result_text.append(f"   ⏱️ Tiempo: {response.response_time:.2f}s\n", style="dim")
        result_text.append(f"   🎯 Confianza: {response.confidence:.1%}\n", style="dim")
        if self.agent:
            result_text.append(f"   🧠 Modo: {getattr(self.agent, 'learning_mode', 'N/A')}", style="dim")

        console.print(Panel(result_text, border_style="green", title="🎉 Proyecto Analizado"))

        # Mostrar razonamiento en panel separado
        if hasattr(response, 'reasoning') and response.reasoning:
            console.print(Panel(
                response.reasoning,
                border_style="blue",
                title="🧠 Mi Proceso de Razonamiento"
            ))

    def ask_next_action(self, result: Dict) -> str:
        """Pregunta qué hacer a continuación con opciones mejoradas"""

        console.print("\n🤔 [bold cyan]¿Qué te gustaría hacer ahora?[/bold cyan]")

        options = [
            "1. 📋 Crear otro proyecto",
            "2. 📊 Ver estadísticas",
            "3. 📖 Ver ayuda",
            "4. 🚪 Salir"
        ]

        # Solo mostrar opciones de GitHub si hay token configurado
        if os.getenv('GITHUB_TOKEN'):
            options.insert(0, "1. 🚀 Crear repositorio en GitHub")
            options = [f"{i}. {opt.split('.', 1)[1]}" for i, opt in enumerate(options, 1)]

        for option in options:
            console.print(f"   {option}")

        try:
            if os.getenv('GITHUB_TOKEN'):
                choice = Prompt.ask(
                    "\n🎯 Elige una opción",
                    choices=["1", "2", "3", "4", "5"],
                    default="2"
                )
            else:
                choice = Prompt.ask(
                    "\n🎯 Elige una opción",
                    choices=["1", "2", "3", "4"],
                    default="1"
                )
            return choice
        except (KeyboardInterrupt, EOFError):
            return "4"  # Salir

    def create_github_repo(self, result: Dict):
        """Información sobre crear repositorio en GitHub"""

        if not os.getenv('GITHUB_TOKEN'):
            console.print(Panel(
                "❌ [bold red]Token de GitHub no configurado[/bold red]\n\n"
                "Para crear repositorios necesitas configurar tu token:\n\n"
                "1. Ve a GitHub → Settings → Developer settings → Personal access tokens\n"
                "2. Crea un nuevo token con permisos de 'repo'\n"
                "3. Ejecuta: export GITHUB_TOKEN='tu_token_aquí'\n"
                "4. O agrégalo a tu archivo .env",
                border_style="red",
                title="⚙️ Configuración Requerida"
            ))
            return

        # Mostrar información del proyecto
        summary = Text()
        summary.append("📋 Información del Proyecto:\n\n", style="bold")
        summary.append(f"📁 Nombre: {result['repo_name']}\n", style="white")
        summary.append(f"📝 Descripción: {result.get('description', 'Sin descripción')}\n", style="white")
        summary.append(f"🔒 Visibilidad: {'Privado' if result.get('is_private') else 'Público'}\n", style="white")
        summary.append(f"🔧 Framework: {result.get('framework', 'N/A')}\n", style="white")
        summary.append(f"⚡ Comando: {result.get('init_command', 'N/A')}\n", style="dim")

        console.print(Panel(summary, border_style="blue", title="📋 Resumen"))

        console.print(Panel(
            "🚀 Para crear el repositorio:\n\n"
            "1. Copia el comando de inicialización\n"
            "2. Ejecuta el comando en tu terminal\n"
            "3. Configura git en el directorio creado\n"
            "4. Crea el repositorio en GitHub\n"
            "5. Haz push del código inicial\n\n"
            "💡 En futuras versiones esto será automático",
            border_style="green",
            title="🛠️ Próximos Pasos"
        ))

    def handle_special_commands(self, user_input: str) -> bool:
        """Maneja comandos especiales, retorna True si se procesó un comando"""

        command = user_input.lower().strip()

        if command in ['ayuda', 'help']:
            self.show_help_menu()
            return True

        elif command in ['capacidades', 'capabilities']:
            self.show_capabilities()
            return True

        elif command in ['estadísticas', 'stats', 'estadisticas']:
            self.show_session_stats()
            return True

        elif command in ['historial', 'history']:
            self.show_project_history()
            return True

        elif command in ['salir', 'exit', 'quit']:
            return True

        return False

    def run_interactive_session(self):
        """Ejecuta una sesión interactiva completa"""

        try:
            # Bienvenida
            self.welcome_message()
            self.get_user_name()

            # Mostrar capacidades iniciales
            try:
                show_help = Confirm.ask(
                    f"\n🤔 ¿Quieres ver mis capacidades, {self.user_name}?",
                    default=True
                )
                if show_help:
                    self.show_capabilities()
            except (KeyboardInterrupt, EOFError):
                console.print("\n👋 ¡Hasta luego!")
                return

            # Loop principal
            while True:
                console.print(f"\n👋 [bold cyan]¡Hola {self.user_name}![/bold cyan]")

                # Obtener input del usuario
                try:
                    user_input = Prompt.ask(
                        "💬 Cuéntame, ¿qué proyecto quieres crear? (o escribe 'ayuda' para ver opciones)",
                        default=""
                    )
                except (KeyboardInterrupt, EOFError):
                    console.print("\n👋 ¡Hasta luego!")
                    break

                if not user_input:
                    console.print("❌ [yellow]Por favor, describe el proyecto que quieres crear[/yellow]")
                    continue

                # Manejar comandos especiales
                if self.handle_special_commands(user_input):
                    if user_input.lower() in ['salir', 'exit', 'quit']:
                        break
                    continue

                # Procesar input del proyecto
                response = self.process_user_input(user_input)

                if response:
                    # Actualizar estadísticas
                    self.session_stats['projects_created'] += 1

                    # Agregar al historial
                    if response.success:
                        self.conversation_history.append({
                            'input': user_input,
                            'name': response.result.get('repo_name', 'Sin nombre'),
                            'framework': response.result.get('framework', 'N/A'),
                            'completed': False,
                            'timestamp': time.time()
                        })

                    # Mostrar resultado
                    self.show_analysis_result(response, user_input)

                    if response.success:
                        result = response.result

                        # Loop de acciones
                        while True:
                            try:
                                choice = self.ask_next_action(result)

                                if choice == "1":
                                    if os.getenv('GITHUB_TOKEN'):
                                        self.create_github_repo(result)
                                        break
                                    else:
                                        # Crear otro proyecto
                                        break
                                elif choice == "2":
                                    if os.getenv('GITHUB_TOKEN'):
                                        # Crear otro proyecto
                                        break
                                    else:
                                        # Ver estadísticas
                                        self.show_session_stats()
                                elif choice == "3":
                                    if os.getenv('GITHUB_TOKEN'):
                                        # Ver estadísticas
                                        self.show_session_stats()
                                    else:
                                        # Ver ayuda
                                        self.show_help_menu()
                                elif choice == "4":
                                    if os.getenv('GITHUB_TOKEN'):
                                        # Ver ayuda
                                        self.show_help_menu()
                                    else:
                                        # Salir
                                        return
                                elif choice == "5":
                                    # Salir (solo si hay GitHub token)
                                    return

                            except (KeyboardInterrupt, EOFError):
                                console.print("\n👋 ¡Hasta luego!")
                                return

        except Exception as e:
            console.print(f"\n❌ [bold red]Error inesperado:[/bold red] {str(e)}")
            logger.error(f"Error en sesión interactiva: {e}")

        finally:
            # Mensaje de despedida
            session_time = time.time() - self.session_stats['session_start']

            goodbye_text = Text()
            goodbye_text.append(f"🤖 Gracias por usar Herbie, {self.user_name}!\n\n", style="bold green")
            goodbye_text.append(f"📊 Resumen de la sesión:\n", style="bold")
            goodbye_text.append(f"   ⏱️ Tiempo: {session_time / 60:.1f} minutos\n", style="white")
            goodbye_text.append(f"   🚀 Proyectos analizados: {self.session_stats['projects_created']}\n", style="white")
            goodbye_text.append(f"   📦 Repositorios creados: {self.session_stats['repos_created']}\n", style="white")
            goodbye_text.append(f"\n🚀 ¡Que tengas un excelente día desarrollando!", style="bold cyan")

            console.print(Panel(goodbye_text, border_style="green", title="👋 ¡Hasta luego!"))


def herbie_interactive():
    """
    Función principal para ejecutar Herbie de forma interactiva

    Esta función puede ser importada y ejecutada desde otros módulos:

    Example:
        from herbie_interactive import herbie_interactive
        herbie_interactive()
    """

    try:
        # Crear y ejecutar instancia interactiva
        herbie = InteractiveHerbie()
        herbie.run_interactive_session()

    except Exception as e:
        console.print(f"❌ [bold red]Error iniciando Herbie:[/bold red] {str(e)}")

        # Mostrar ayuda básica
        console.print(Panel(
            "🔧 Posibles soluciones:\n\n"
            "1. Verifica que tengas las dependencias instaladas:\n"
            "   pip install rich\n\n"
            "2. Configura las variables de entorno necesarias:\n"
            "   - GOOGLE_API_KEY (opcional para funcionalidad completa)\n"
            "   - GITHUB_TOKEN (opcional, para crear repos)\n\n"
            "3. Ejecuta desde el directorio raíz del proyecto\n\n"
            "💡 El sistema funciona en modo simulado sin configuración",
            border_style="blue",
            title="🆘 Ayuda"
        ))


def main():
    """Función principal para ejecutar desde línea de comandos"""
    herbie_interactive()


if __name__ == "__main__":
    main()