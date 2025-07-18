# Integración del Enhanced Framework Manager en el HerbieAgent original
from typing import Optional

from frameworkManager import *
from herbie import *


# Modificaciones en HerbieFrameworkHelper
class EnhancedHerbieFrameworkHelper:
    def __init__(self, llm):
        self.llm = llm
        self.cli_manager = IntelligentCLIManager(llm)
        self.system_info = {
            "os": platform.system().lower(),
            "version": platform.release(),
            "architecture": platform.machine()
        }

    def check_framework_requirements(self, framework: str) -> Dict:
        """Verifica requisitos usando el sistema mejorado"""
        setup_result = self.cli_manager.generate_setup_instructions(framework, "temp_project")

        if setup_result.success:
            return {
                "available": True,
                "dependencies": setup_result.dependencies,
                "setup_commands": setup_result.setup_commands
            }
        else:
            return {
                "available": False,
                "reason": setup_result.message,
                "dependencies": setup_result.dependencies,
                "setup_commands": setup_result.setup_commands,
                "troubleshooting": setup_result.troubleshooting
            }

    def generate_intelligent_setup_guide(self, framework: str, project_name: str) -> str:
        """Genera guía inteligente de configuración"""
        setup_result = self.cli_manager.generate_setup_instructions(framework, project_name)

        if not self.llm:
            return self._generate_basic_guide(setup_result)

        try:
            from langchain.schema import HumanMessage

            # Preparar información de dependencias
            dep_info = []
            for dep in setup_result.dependencies:
                status_emoji = {
                    DependencyStatus.AVAILABLE: "✅",
                    DependencyStatus.MISSING: "❌",
                    DependencyStatus.OUTDATED: "⚠️",
                    DependencyStatus.UNKNOWN: "❓"
                }

                dep_info.append({
                    "name": dep.name,
                    "status": dep.status.value,
                    "emoji": status_emoji[dep.status],
                    "current_version": dep.current_version,
                    "required_version": dep.required_version,
                    "install_command": dep.install_command
                })

            prompt = f"""
Eres Herbie, un agente técnico experto y amigable.

Situación del proyecto:
- Framework: {framework}
- Proyecto: {project_name}
- Sistema: {self.system_info['os']}
- Configuración exitosa: {setup_result.success}

Dependencias analizadas:
{json.dumps(dep_info, indent=2)}

Comandos de configuración:
{json.dumps(setup_result.setup_commands, indent=2)}

Próximos pasos:
{json.dumps(setup_result.next_steps, indent=2)}

Genera una guía completa que incluya:
1. 📋 Resumen del estado actual
2. 🔧 Dependencias necesarias (con estado actual)
3. 📝 Instrucciones paso a paso específicas para {self.system_info['os']}
4. 🚀 Comandos exactos para ejecutar
5. 🔍 Cómo verificar que todo funciona
6. 🆘 Solución de problemas comunes
7. 🎯 Próximos pasos después de la configuración

Usa formato Markdown, emojis apropiados y sé muy específico con los comandos.
El tono debe ser profesional pero amigable, como un mentor técnico.
"""

            response = self.llm.invoke([HumanMessage(content=prompt)])
            return response.content.strip()

        except Exception as e:
            logger.error(f"Error generando guía con IA: {e}")
            return self._generate_basic_guide(setup_result)

    def _generate_basic_guide(self, setup_result: FrameworkSetupResult) -> str:
        """Genera guía básica sin IA"""
        guide = f"""
# Guía de Configuración

## Estado: {"✅ Listo" if setup_result.success else "❌ Necesita configuración"}

### Dependencias:
"""

        for dep in setup_result.dependencies:
            status_emoji = {
                DependencyStatus.AVAILABLE: "✅",
                DependencyStatus.MISSING: "❌",
                DependencyStatus.OUTDATED: "⚠️",
                DependencyStatus.UNKNOWN: "❓"
            }

            guide += f"\n- {status_emoji[dep.status]} **{dep.name}**: {dep.status.value}"
            if dep.current_version:
                guide += f" (versión: {dep.current_version})"
            if dep.install_command:
                guide += f"\n  - Instalación: `{dep.install_command}`"

        guide += "\n\n### Comandos de configuración:\n"
        for cmd in setup_result.setup_commands:
            guide += f"```bash\n{cmd}\n```\n"

        guide += "\n### Próximos pasos:\n"
        for step in setup_result.next_steps:
            guide += f"- {step}\n"

        if setup_result.troubleshooting:
            guide += f"\n### Solución de problemas:\n{setup_result.troubleshooting}"

        return guide

    def init_framework_project(self, project_info: ProjectInfo) -> Dict:
        """Inicializa proyecto usando el sistema mejorado"""
        logger.info(f"Iniciando proyecto {project_info.repo_name} con framework {project_info.framework}")

        # Usar el CLI manager mejorado
        setup_result = self.cli_manager.execute_framework_setup(
            project_info.framework,
            project_info.repo_name,
            auto_install=True
        )

        if setup_result.success:
            return {
                "success": True,
                "message": setup_result.message,
                "setup_result": setup_result
            }
        else:
            return {
                "success": False,
                "message": setup_result.message,
                "setup_guide": self.generate_intelligent_setup_guide(
                    project_info.framework,
                    project_info.repo_name
                ),
                "setup_result": setup_result
            }


# Modificaciones en el AIIntelligenceCore
class EnhancedAIIntelligenceCore(AIIntelligenceCore):
    """Versión mejorada del núcleo de IA con soporte para CLI inteligente"""

    def __init__(self, llm):
        super().__init__(llm)
        self.cli_manager = IntelligentCLIManager(llm)

    def generate_framework_status_response(self, framework: str, project_name: str,
                                           user_input: str) -> str:
        """Genera respuesta sobre el estado del framework"""

        setup_result = self.cli_manager.generate_setup_instructions(framework, project_name)

        prompt = f"""
Eres Herbie, un agente técnico amigable.

El usuario preguntó: "{user_input}"

Información del framework {framework}:
- Configuración exitosa: {setup_result.success}
- Mensaje del sistema: {setup_result.message}
- Dependencias: {len(setup_result.dependencies)} analizadas

Estado de dependencias:
"""

        for dep in setup_result.dependencies:
            prompt += f"- {dep.name}: {dep.status.value}"
            if dep.current_version:
                prompt += f" (v{dep.current_version})"
            if dep.required_version:
                prompt += f" [requiere: {dep.required_version}]"
            prompt += "\n"

        prompt += f"""
Comandos necesarios: {len(setup_result.setup_commands)}
Próximos pasos: {len(setup_result.next_steps)}

Genera una respuesta que:
1. Responda específicamente a la pregunta del usuario
2. Proporcione el estado actual del framework
3. Indique claramente qué necesita hacer el usuario
4. Sea técnicamente preciso pero fácil de entender
5. Use emojis apropiados y formato markdown
6. Incluya comandos específicos si es necesario

Si hay dependencias faltantes, enfócate en eso.
Si todo está listo, enfócate en crear el proyecto.
"""

        try:
            response = self.llm.invoke([HumanMessage(content=prompt)])
            return response.content.strip()
        except Exception as e:
            logger.error(f"Error generando respuesta de framework: {e}")
            return f"Hay un problema técnico analizando {framework}. {setup_result.message}"

    def analyze_framework_readiness(self, framework: str, project_name: str) -> Dict:
        """Analiza si el framework está listo para usar"""

        setup_result = self.cli_manager.generate_setup_instructions(framework, project_name)

        missing_deps = [dep for dep in setup_result.dependencies
                        if dep.status == DependencyStatus.MISSING]
        outdated_deps = [dep for dep in setup_result.dependencies
                         if dep.status == DependencyStatus.OUTDATED]

        readiness_score = 1.0
        if missing_deps:
            readiness_score -= 0.5
        if outdated_deps:
            readiness_score -= 0.3

        return {
            "ready": setup_result.success,
            "readiness_score": readiness_score,
            "missing_dependencies": [dep.name for dep in missing_deps],
            "outdated_dependencies": [dep.name for dep in outdated_deps],
            "setup_commands": setup_result.setup_commands,
            "next_steps": setup_result.next_steps,
            "full_result": setup_result
        }


# Modificaciones en GitHubRepoCreator
class EnhancedGitHubRepoCreator(GitHubRepoCreator):
    """Versión mejorada del creador de repositorios"""

    def __init__(self):
        super().__init__()
        # Reemplazar el framework helper con la versión mejorada
        self.framework_helper = EnhancedHerbieFrameworkHelper(self.llm)
        # Reemplazar el AI core con la versión mejorada
        self.ai_core = EnhancedAIIntelligenceCore(self.llm)


# Modificaciones en HerbieAgent
class EnhancedHerbieAgent(HerbieAgent):
    """Versión mejorada del agente con CLI inteligente"""

    def __init__(self):
        # Usar la versión mejorada del repo creator
        self.repo_creator = EnhancedGitHubRepoCreator()
        self.ai_core = self.repo_creator.ai_core
        self.conversation_history = []
        self.pending_project = None
        self.user_context = {}

    def _handle_framework_inquiry(self, user_input: str, framework: str = None) -> str:
        """Maneja preguntas específicas sobre frameworks"""

        if not framework:
            # Intentar extraer framework del input
            framework = self._extract_framework_from_input(user_input)

        if not framework:
            return self.ai_core.generate_response(
                intent="framework_inquiry_no_framework",
                context={"available_frameworks": EnhancedFrameworkDatabase.get_framework_names()},
                user_input=user_input
            )

        # Generar respuesta específica sobre el framework
        response = self.ai_core.generate_framework_status_response(
            framework,
            "proyecto-ejemplo",
            user_input
        )

        self.conversation_history.append({"role": "assistant", "content": response})
        return response

    def _extract_framework_from_input(self, user_input: str) -> Optional[str]:
        """Extrae framework mencionado en el input"""
        frameworks = EnhancedFrameworkDatabase.get_framework_names()
        user_lower = user_input.lower()

        for framework in frameworks:
            if framework in user_lower:
                return framework

        # Buscar variaciones comunes
        variations = {
            "react": ["react", "reactjs", "react.js"],
            "vue": ["vue", "vuejs", "vue.js"],
            "angular": ["angular", "angularjs"],
            "nextjs": ["next", "nextjs", "next.js"],
            "django": ["django", "python web"],
            "fastapi": ["fastapi", "fast api"],
            "rails": ["rails", "ruby on rails", "ror"],
            "flutter": ["flutter", "dart"]
        }

        for framework, terms in variations.items():
            if any(term in user_lower for term in terms):
                return framework

        return None

    def _execute_project_creation(self) -> str:
        """Versión mejorada de la ejecución del proyecto"""
        if not self.pending_project:
            return "❌ No hay proyecto pendiente para crear."

        try:
            # Analizar preparación del framework
            framework_readiness = self.ai_core.analyze_framework_readiness(
                self.pending_project['framework'],
                self.pending_project['repo_name']
            )

            # Si el framework no está listo, proporcionar guía
            if not framework_readiness['ready']:
                missing_deps = framework_readiness['missing_dependencies']
                setup_guide = self.repo_creator.framework_helper.generate_intelligent_setup_guide(
                    self.pending_project['framework'],
                    self.pending_project['repo_name']
                )

                response = self.ai_core.generate_response(
                    intent="framework_not_ready",
                    context={
                        "framework": self.pending_project['framework'],
                        "project_name": self.pending_project['repo_name'],
                        "missing_dependencies": missing_deps,
                        "setup_guide": setup_guide,
                        "readiness_score": framework_readiness['readiness_score']
                    },
                    user_input="framework no está listo"
                )

                self.conversation_history.append({"role": "assistant", "content": response})
                return response

            # Continuar con la creación normal del proyecto
            return super()._execute_project_creation()

        except Exception as e:
            logger.error(f"Error en ejecución mejorada: {e}")
            return super()._execute_project_creation()


# Función main actualizada
def enhanced_main():
    """Función principal mejorada"""

    try:
        agent = EnhancedHerbieAgent()

        welcome_message = agent.ai_core.generate_response(
            intent="welcome_message",
            context={
                "frameworks": EnhancedFrameworkDatabase.get_framework_names(),
                "features": [
                    "Detección inteligente de dependencias",
                    "Configuración automática de frameworks",
                    "Guías de instalación personalizadas",
                    "Solución de problemas automática"
                ]
            },
            user_input="bienvenida"
        )

        print("🤖 Herbie - Agente Inteligente con CLI Mejorado")
        print("=" * 55)
        print(f"\n{welcome_message}")
        print("\n💡 Nuevas características:")
        print("   • Detección automática de dependencias")
        print("   • Configuración inteligente de frameworks")
        print("   • Guías de instalación personalizadas")
        print("   • Solución de problemas automática")
        print("\n📝 Ejemplos de uso:")
        print('   • "Quiero crear una app React"')
        print('   • "¿Tengo todo para hacer un proyecto Django?"')
        print('   • "Configura Angular en mi sistema"')

        while True:
            user_input = input("\n💬 Tú: ").strip()

            if user_input:
                exit_analysis = agent.ai_core.analyze_user_intent(user_input, [])
                if exit_analysis.action == "despedida" and exit_analysis.confidence > 0.7:
                    farewell_message = agent.ai_core.generate_response(
                        intent="farewell",
                        context={},
                        user_input=user_input
                    )
                    print(f"\n🤖 Herbie: {farewell_message}")
                    break

            if not user_input:
                continue

            # Detectar si es una pregunta sobre framework específico
            framework = agent._extract_framework_from_input(user_input)
            if framework and any(
                    word in user_input.lower() for word in ["tengo", "instalado", "necesito", "configurar", "setup"]):
                print(f"\n🔍 Analizando configuración de {framework}...")
                response = agent._handle_framework_inquiry(user_input, framework)
            else:
                print()
                response = agent.chat(user_input)

            print(f"🤖 Herbie: {response}")

    except KeyboardInterrupt:
        print("\n\n👋 ¡Hasta luego! ¡Que tengas un desarrollo increíble! 🚀")
    except Exception as e:
        print(f"\n❌ Error inicializando Herbie: {e}")
        print("\n🔧 Asegúrate de tener configurado:")
        print("   • GITHUB_TOKEN: Token de GitHub con permisos de repositorio")
        print("   • GOOGLE_API_KEY: API key de Google Generative AI")


if __name__ == "__main__":
    enhanced_main()