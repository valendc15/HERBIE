# INTEGRACIÓN CORRECTA: Construyendo sobre el EnhancedHerbie original
# Esta implementación EXTIENDE las capacidades sin romper la funcionalidad existente

import time
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum
import subprocess
import os
import logging

from enhancedHerbie import *
# Importar todas las clases del sistema original
from frameworkManager import *
from herbie import *

logger = logging.getLogger(__name__)


@dataclass
class ExecutionResult:
    """Resultado de ejecución de comando con telemetría completa"""
    success: bool
    command: str
    message: str
    output: str = ""
    error: str = ""
    execution_time: float = 0.0
    exit_code: int = 0
    working_directory: str = ""
    timestamp: float = field(default_factory=time.time)


@dataclass
class ProjectExecutionContext:
    """Contexto completo de ejecución del proyecto"""
    project_name: str
    framework: str
    local_path: Optional[str] = None
    github_url: Optional[str] = None
    execution_log: List[ExecutionResult] = field(default_factory=list)
    dependencies_verified: List[DependencyInfo] = field(default_factory=list)
    setup_result: Optional[FrameworkSetupResult] = None
    total_execution_time: float = 0.0
    success: bool = False


class ExecutionPhase(Enum):
    DEPENDENCY_CHECK = "dependency_check"
    PROJECT_CREATION = "project_creation"
    GITHUB_SETUP = "github_setup"
    CODE_UPLOAD = "code_upload"
    FINALIZATION = "finalization"


class RealCommandExecutor:
    """Ejecutor de comandos reales con telemetría avanzada"""

    def __init__(self, llm=None):
        self.llm = llm
        self.execution_history = []
        self.current_phase = None

    def execute_command(self, command: str, timeout: int = 300,
                        working_dir: Optional[str] = None,
                        phase: ExecutionPhase = None) -> ExecutionResult:
        """
        Ejecuta comando con telemetría completa y manejo de errores avanzado

        Args:
            command: Comando a ejecutar
            timeout: Tiempo límite en segundos
            working_dir: Directorio de trabajo
            phase: Fase de ejecución para logging

        Returns:
            ExecutionResult con información completa
        """

        start_time = time.time()
        original_dir = os.getcwd()

        try:
            # Cambiar directorio si es necesario
            if working_dir and os.path.exists(working_dir):
                os.chdir(working_dir)

            # Logging inicial
            phase_info = f"[{phase.value}] " if phase else ""
            logger.info(f"{phase_info}Ejecutando: {command}")
            print(f"🔧 {phase_info}Ejecutando: {command}")

            # Ejecutar comando
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=working_dir
            )

            execution_time = time.time() - start_time

            # Crear resultado
            exec_result = ExecutionResult(
                success=result.returncode == 0,
                command=command,
                message="Comando ejecutado exitosamente" if result.returncode == 0 else f"Error en comando (código: {result.returncode})",
                output=result.stdout,
                error=result.stderr,
                execution_time=execution_time,
                exit_code=result.returncode,
                working_directory=working_dir or original_dir
            )

            # Logging de resultado
            if exec_result.success:
                print(f"✅ Completado en {execution_time:.2f}s")
                logger.info(f"Comando exitoso en {execution_time:.2f}s")
            else:
                print(f"❌ Error en {execution_time:.2f}s: {result.stderr}")
                logger.error(f"Error en comando: {result.stderr}")

            # Almacenar en historial
            self.execution_history.append(exec_result)

            return exec_result

        except subprocess.TimeoutExpired:
            execution_time = time.time() - start_time
            exec_result = ExecutionResult(
                success=False,
                command=command,
                message=f"Comando excedió tiempo límite ({timeout}s)",
                error="Timeout",
                execution_time=execution_time,
                exit_code=-1,
                working_directory=working_dir or original_dir
            )

            print(f"⏱️ Timeout después de {execution_time:.2f}s")
            logger.error(f"Timeout en comando: {command}")

            self.execution_history.append(exec_result)
            return exec_result

        except Exception as e:
            execution_time = time.time() - start_time
            exec_result = ExecutionResult(
                success=False,
                command=command,
                message=f"Error inesperado: {str(e)}",
                error=str(e),
                execution_time=execution_time,
                exit_code=-999,
                working_directory=working_dir or original_dir
            )

            print(f"💥 Error inesperado: {str(e)}")
            logger.error(f"Error inesperado en comando: {str(e)}")

            self.execution_history.append(exec_result)
            return exec_result

        finally:
            os.chdir(original_dir)

    def get_execution_summary(self) -> Dict:
        """Genera resumen de ejecución con métricas"""

        total_commands = len(self.execution_history)
        successful_commands = sum(1 for cmd in self.execution_history if cmd.success)
        total_time = sum(cmd.execution_time for cmd in self.execution_history)

        return {
            "total_commands": total_commands,
            "successful_commands": successful_commands,
            "failed_commands": total_commands - successful_commands,
            "success_rate": successful_commands / total_commands if total_commands > 0 else 0,
            "total_execution_time": total_time,
            "average_command_time": total_time / total_commands if total_commands > 0 else 0,
            "execution_history": self.execution_history
        }


class EnhancedIntelligentCLIManager(IntelligentCLIManager):
    """Versión mejorada del CLI Manager con capacidades de ejecución real"""

    def __init__(self, llm=None):
        super().__init__(llm)
        self.executor = RealCommandExecutor(llm)
        self.github_token = os.getenv('GITHUB_TOKEN')

    def execute_framework_setup_real(self, framework: str, project_name: str) -> ProjectExecutionContext:
        """
        Ejecuta la configuración completa del framework con ejecución real

        Esta es la función principal que orquesta todo el proceso
        """

        context = ProjectExecutionContext(
            project_name=project_name,
            framework=framework
        )

        start_time = time.time()

        try:
            # FASE 1: Verificación de dependencias
            print(f"\n🔍 FASE 1: Verificando dependencias para {framework}")
            context.dependencies_verified = self.check_framework_dependencies(framework)

            missing_deps = [dep for dep in context.dependencies_verified
                            if dep.status == DependencyStatus.MISSING]

            if missing_deps:
                context.setup_result = FrameworkSetupResult(
                    success=False,
                    project_name=project_name,
                    framework=framework,
                    dependencies=context.dependencies_verified,
                    setup_commands=[],
                    next_steps=[f"Instalar {dep.name}: {dep.install_command}" for dep in missing_deps],
                    message=f"❌ Dependencias faltantes: {', '.join([dep.name for dep in missing_deps])}"
                )
                return context

            # FASE 2: Creación del proyecto
            print(f"\n🚀 FASE 2: Creando proyecto {framework}")
            project_created = self._execute_project_creation(framework, project_name, context)

            if not project_created:
                context.setup_result = FrameworkSetupResult(
                    success=False,
                    project_name=project_name,
                    framework=framework,
                    dependencies=context.dependencies_verified,
                    setup_commands=[],
                    next_steps=[],
                    message="❌ Error creando proyecto local"
                )
                return context

            # FASE 3: Configuración de GitHub (si token disponible)
            if self.github_token:
                print(f"\n☁️ FASE 3: Configurando GitHub")
                github_created = self._execute_github_setup(project_name, context)

                if github_created:
                    # FASE 4: Subida de código
                    print(f"\n📤 FASE 4: Subiendo código a GitHub")
                    self._execute_code_upload(project_name, context)

            # FASE 5: Finalización
            print(f"\n🎉 FASE 5: Finalizando configuración")
            context.success = True
            context.total_execution_time = time.time() - start_time

            # Generar resultado final
            context.setup_result = self._generate_final_setup_result(context)

            return context

        except Exception as e:
            logger.error(f"Error en ejecución completa: {e}")
            context.setup_result = FrameworkSetupResult(
                success=False,
                project_name=project_name,
                framework=framework,
                dependencies=context.dependencies_verified,
                setup_commands=[],
                next_steps=[],
                message=f"❌ Error inesperado: {str(e)}"
            )
            return context

    def _execute_project_creation(self, framework: str, project_name: str,
                                  context: ProjectExecutionContext) -> bool:
        """Ejecuta la creación del proyecto según el framework"""

        framework_info = self.framework_db.get_framework_info(framework)
        if not framework_info:
            return False

        # Verificar que el directorio no exista
        if os.path.exists(project_name):
            print(f"⚠️ Directorio '{project_name}' ya existe, eliminando...")
            result = self.executor.execute_command(
                f"rm -rf {project_name}" if os.name != 'nt' else f"rmdir /s /q {project_name}",
                phase=ExecutionPhase.PROJECT_CREATION
            )
            if not result.success:
                return False

        # Ejecutar comando principal de creación
        primary_command = framework_info["primary_commands"][0].format(project_name=project_name)

        result = self.executor.execute_command(
            primary_command,
            timeout=600,  # 10 minutos para creación
            phase=ExecutionPhase.PROJECT_CREATION
        )

        if not result.success:
            return False

        # Verificar que el proyecto se creó
        project_path = os.path.abspath(project_name)
        if not os.path.exists(project_path):
            return False

        context.local_path = project_path

        # Ejecutar comandos adicionales de setup
        for setup_cmd in framework_info.get("setup_commands", []):
            if setup_cmd.startswith("cd "):
                continue  # Saltar comandos de cd

            formatted_cmd = setup_cmd.format(project_name=project_name)

            result = self.executor.execute_command(
                formatted_cmd,
                timeout=300,
                working_dir=project_path,
                phase=ExecutionPhase.PROJECT_CREATION
            )

            # No fallar si comandos adicionales fallan
            if not result.success:
                logger.warning(f"Comando adicional falló: {formatted_cmd}")

        return True

    def _execute_github_setup(self, project_name: str, context: ProjectExecutionContext) -> bool:
        """Crea repositorio en GitHub"""

        try:
            import requests

            headers = {
                'Authorization': f'token {self.github_token}',
                'Accept': 'application/vnd.github.v3+json',
                'Content-Type': 'application/json'
            }

            data = {
                "name": project_name,
                "description": f"Proyecto {context.framework} creado con Enhanced Herbie",
                "private": False,
                "has_issues": True,
                "has_projects": True,
                "has_wiki": True,
                "auto_init": False
            }

            response = requests.post(
                "https://api.github.com/user/repos",
                headers=headers,
                json=data,
                timeout=30
            )

            if response.status_code == 201:
                repo_data = response.json()
                context.github_url = repo_data['html_url']
                print(f"✅ Repositorio creado: {context.github_url}")
                return True
            else:
                print(f"❌ Error creando repositorio: {response.status_code}")
                return False

        except Exception as e:
            print(f"❌ Error en GitHub setup: {e}")
            return False

    def _execute_code_upload(self, project_name: str, context: ProjectExecutionContext) -> bool:
        """Sube código a GitHub"""

        if not context.local_path or not context.github_url:
            return False

        try:
            # Obtener username
            username = self._get_github_username()
            if not username:
                return False

            # Configurar git
            commands = [
                "git init",
                f"git config user.name '{username}'",
                f"git config user.email '{username}@users.noreply.github.com'",
                f"git remote add origin https://{self.github_token}@github.com/{username}/{project_name}.git",
                "git add .",
                'git commit -m "Initial commit created by Enhanced Herbie"',
                "git branch -M main",
                "git push -u origin main"
            ]

            for cmd in commands:
                result = self.executor.execute_command(
                    cmd,
                    timeout=120,
                    working_dir=context.local_path,
                    phase=ExecutionPhase.CODE_UPLOAD
                )

                if not result.success:
                    print(f"❌ Error en git: {cmd}")
                    return False

            print("✅ Código subido exitosamente a GitHub")
            return True

        except Exception as e:
            print(f"❌ Error subiendo código: {e}")
            return False

    def _get_github_username(self) -> Optional[str]:
        """Obtiene username de GitHub"""

        try:
            import requests

            headers = {
                'Authorization': f'token {self.github_token}',
                'Accept': 'application/vnd.github.v3+json'
            }

            response = requests.get("https://api.github.com/user", headers=headers, timeout=10)

            if response.status_code == 200:
                return response.json().get('login')

        except Exception as e:
            logger.error(f"Error obteniendo username: {e}")

        return None

    def _generate_final_setup_result(self, context: ProjectExecutionContext) -> FrameworkSetupResult:
        """Genera resultado final con toda la información"""

        execution_summary = self.executor.get_execution_summary()

        message = f"🎉 ¡Proyecto '{context.project_name}' creado exitosamente!"

        if context.local_path:
            message += f"\n📁 Ruta local: {context.local_path}"

        if context.github_url:
            message += f"\n🌐 GitHub: {context.github_url}"

        message += f"\n⏱️ Tiempo total: {context.total_execution_time:.2f}s"
        message += f"\n📊 Comandos ejecutados: {execution_summary['successful_commands']}/{execution_summary['total_commands']}"

        # Generar próximos pasos
        framework_info = self.framework_db.get_framework_info(context.framework)
        next_steps = []

        if context.local_path:
            next_steps.append(f"1. Navegar al proyecto: cd {context.project_name}")

        if framework_info:
            if context.framework == "react":
                next_steps.extend([
                    "2. Iniciar servidor: npm start",
                    "3. Abrir: http://localhost:3000",
                    "4. Editar: src/App.js"
                ])
            elif context.framework == "vue":
                next_steps.extend([
                    "2. Iniciar servidor: npm run dev",
                    "3. Abrir: http://localhost:5173",
                    "4. Editar: src/App.vue"
                ])
            elif context.framework == "django":
                next_steps.extend([
                    "2. Iniciar servidor: python manage.py runserver",
                    "3. Abrir: http://localhost:8000",
                    "4. Crear app: python manage.py startapp myapp"
                ])

        if context.github_url:
            next_steps.append(f"5. Ver repositorio: {context.github_url}")

        return FrameworkSetupResult(
            success=context.success,
            project_name=context.project_name,
            framework=context.framework,
            dependencies=context.dependencies_verified,
            setup_commands=[cmd.command for cmd in context.execution_log],
            next_steps=next_steps,
            message=message
        )


class SuperEnhancedHerbieFrameworkHelper(EnhancedHerbieFrameworkHelper):
    """Versión super mejorada que integra ejecución real"""

    def __init__(self, llm):
        super().__init__(llm)
        # Reemplazar CLI manager con versión mejorada
        self.cli_manager = EnhancedIntelligentCLIManager(llm)
        self.executor = self.cli_manager.executor

    def init_framework_project(self, project_info) -> Dict:
        """Inicialización mejorada con ejecución real"""

        logger.info(f"Iniciando proyecto mejorado: {project_info.repo_name} ({project_info.framework})")

        # Ejecutar configuración completa
        context = self.cli_manager.execute_framework_setup_real(
            project_info.framework,
            project_info.repo_name
        )

        # Convertir contexto a formato esperado
        return {
            "success": context.success,
            "message": context.setup_result.message if context.setup_result else "Error procesando",
            "setup_result": context.setup_result,
            "execution_context": context,
            "execution_summary": self.executor.get_execution_summary()
        }

    def generate_execution_report(self, context: ProjectExecutionContext) -> str:
        """Genera reporte detallado de ejecución usando IA"""

        if not self.llm:
            return "Reporte de ejecución no disponible sin IA"

        try:
            from langchain.schema import HumanMessage

            execution_summary = self.executor.get_execution_summary()

            prompt = f"""
Eres un experto en DevOps y automatización. Genera un reporte técnico detallado de la ejecución del proyecto.

Datos de ejecución:
- Proyecto: {context.project_name}
- Framework: {context.framework}
- Éxito: {context.success}
- Tiempo total: {context.total_execution_time:.2f}s
- Comandos ejecutados: {execution_summary['successful_commands']}/{execution_summary['total_commands']}
- Tasa de éxito: {execution_summary['success_rate']:.2%}

Comandos ejecutados:
"""

            for cmd in context.execution_log:
                status = "✅" if cmd.success else "❌"
                prompt += f"{status} {cmd.command} ({cmd.execution_time:.2f}s)\n"

            prompt += """
Genera un reporte que incluya:
1. 📊 Resumen ejecutivo
2. 🔧 Análisis de performance
3. 📋 Detalles de ejecución
4. 🔍 Puntos de mejora
5. 📈 Métricas clave

Usa formato markdown y sé técnicamente preciso.
"""

            response = self.llm.invoke([HumanMessage(content=prompt)])
            return response.content.strip()

        except Exception as e:
            logger.error(f"Error generando reporte: {e}")
            return f"Error generando reporte: {str(e)}"


class UltimateSuperEnhancedHerbieAgent(EnhancedHerbieAgent):
    """Versión final que integra todas las mejoras"""

    def __init__(self):
        # Usar el creador de repositorios mejorado
        self.repo_creator = EnhancedGitHubRepoCreator()

        # Reemplazar framework helper con versión super mejorada
        self.repo_creator.framework_helper = SuperEnhancedHerbieFrameworkHelper(self.repo_creator.llm)

        # Usar AI core mejorado
        self.ai_core = self.repo_creator.ai_core
        self.conversation_history = []
        self.pending_project = None
        self.user_context = {}

    def _execute_project_creation(self) -> str:
        """Ejecución mejorada del proyecto con telemetría completa"""

        if not self.pending_project:
            return "❌ No hay proyecto pendiente para crear."

        try:
            # Generar mensaje de inicio
            start_message = self.ai_core.generate_response(
                intent="starting_enhanced_project_creation",
                context={"project": self.pending_project},
                user_input="iniciando creación mejorada"
            )
            print(start_message)


            parsed_input = ParsedInput(
                repo_name=self.pending_project['repo_name'],
                description=self.pending_project['description'],
                is_private=self.pending_project['is_private'],
                framework=self.pending_project['framework'],
                missing_fields=[]
            )

            project_info = self.repo_creator.create_project_info(parsed_input)

            # Ejecutar con framework helper mejorado
            result = self.repo_creator.framework_helper.init_framework_project(project_info)

            if result["success"]:
                # Generar reporte de ejecución
                execution_context = result.get("execution_context")
                if execution_context:
                    report = self.repo_creator.framework_helper.generate_execution_report(execution_context)

                    # Respuesta final con reporte
                    final_response = self.ai_core.generate_response(
                        intent="project_creation_success_with_report",
                        context={
                            "project": project_info.__dict__,
                            "execution_report": report,
                            "execution_summary": result.get("execution_summary", {})
                        },
                        user_input="proyecto creado exitosamente con reporte"
                    )
                else:
                    final_response = result["message"]
            else:
                final_response = result["message"]

            # Limpiar proyecto pendiente
            self.pending_project = None

            self.conversation_history.append({"role": "assistant", "content": final_response})
            return final_response

        except Exception as e:
            logger.error(f"Error en ejecución super mejorada: {e}")
            self.pending_project = None

            error_response = self.ai_core.generate_response(
                intent="unexpected_error_enhanced",
                context={"error": str(e)},
                user_input="error inesperado en versión mejorada"
            )

            self.conversation_history.append({"role": "assistant", "content": error_response})
            return error_response


# Función main mejorada
def ultimate_enhanced_main():
    """Función principal con todas las mejoras integradas"""

    try:
        agent = UltimateSuperEnhancedHerbieAgent()

        welcome_message = agent.ai_core.generate_response(
            intent="welcome_message_ultimate",
            context={
                "frameworks": EnhancedFrameworkDatabase.get_framework_names(),
                "features": [
                    "🔧 Ejecución real de comandos",
                    "📊 Telemetría completa",
                    "☁️ Integración GitHub automática",
                    "🤖 Inteligencia artificial avanzada",
                    "📈 Reportes de ejecución",
                    "🔍 Análisis de dependencias",
                    "⚡ Performance optimizada"
                ]
            },
            user_input="bienvenida ultimate"
        )

        print("🤖 Ultimate Enhanced Herbie - Agente de Desarrollo Avanzado")
        print("=" * 65)
        print(f"\n{welcome_message}")
        print("\n🚀 Características avanzadas:")
        print("   • Ejecución real de comandos con telemetría")
        print("   • Creación automática de repositorios GitHub")
        print("   • Análisis de dependencias en tiempo real")
        print("   • Reportes detallados de ejecución")
        print("   • Manejo robusto de errores")
        print("   • Logging avanzado y métricas")

        while True:
            user_input = input("\n💬 Tú: ").strip()

            if user_input:
                exit_analysis = agent.ai_core.analyze_user_intent(user_input, [])
                if exit_analysis.action == "despedida" and exit_analysis.confidence > 0.7:
                    farewell_message = agent.ai_core.generate_response(
                        intent="farewell_ultimate",
                        context={},
                        user_input=user_input
                    )
                    print(f"\n🤖 Herbie: {farewell_message}")
                    break

            if not user_input:
                continue

            print()
            response = agent.chat(user_input)
            print(f"🤖 Herbie: {response}")

    except KeyboardInterrupt:
        print("\n\n👋 ¡Hasta luego! ¡Desarrollo increíble con Enhanced Herbie! 🚀✨")
    except Exception as e:
        print(f"\n❌ Error inicializando Ultimate Enhanced Herbie: {e}")
        print("\n🔧 Requisitos:")
        print("   • GITHUB_TOKEN: Token de GitHub")
        print("   • GOOGLE_API_KEY: API key de Google")
        print("   • Node.js/Python según framework")


if __name__ == "__main__":
    ultimate_enhanced_main()
