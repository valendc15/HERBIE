import os
import subprocess
import shutil
import platform
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path
import json
from enum import Enum

logger = logging.getLogger(__name__)


class DependencyStatus(Enum):
    AVAILABLE = "available"
    MISSING = "missing"
    OUTDATED = "outdated"
    UNKNOWN = "unknown"


@dataclass
class DependencyInfo:
    name: str
    status: DependencyStatus
    current_version: Optional[str] = None
    required_version: Optional[str] = None
    install_command: Optional[str] = None
    check_command: Optional[str] = None


@dataclass
class FrameworkSetupResult:
    success: bool
    message: str
    dependencies: List[DependencyInfo]
    setup_commands: List[str]
    next_steps: List[str]
    troubleshooting: Optional[str] = None


class EnhancedFrameworkDatabase:
    """Base de conocimiento extendida con información detallada de dependencias"""

    FRAMEWORKS = {
        "react": {
            "name": "React",
            "description": "Framework JavaScript para crear interfaces de usuario interactivas, los nombres de proyectos no pueden empezar con mayusculas.",
            "primary_commands": [
                "npx create-react-app {project_name}",
                "npm create vite@latest {project_name} -- --template react"
            ],
            "dependencies": [
                {
                    "name": "node",
                    "check_command": "node --version",
                    "required_version": ">=14.0.0",
                    "install_commands": {
                        "windows": "Descarga desde https://nodejs.org/",
                        "linux": "curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash - && sudo apt-get install -y nodejs",
                        "darwin": "brew install node"
                    }
                },
                {
                    "name": "npm",
                    "check_command": "npm --version",
                    "required_version": ">=6.0.0",
                    "install_commands": {
                        "windows": "Incluido con Node.js",
                        "linux": "Incluido con Node.js",
                        "darwin": "Incluido con Node.js"
                    }
                }
            ],
            "setup_commands": [
                "cd {project_name}",
                "npm install",
            ],
            "dev_server_port": 3000,
            "package_manager_alternatives": ["npm", "yarn", "pnpm"]
        },
        "vue": {
            "name": "Vue.js",
            "description": "Framework JavaScript progresivo para crear aplicaciones web",
            "primary_commands": [
                "npm create vue@latest {project_name}",
                "vue create {project_name}"
            ],
            "dependencies": [
                {
                    "name": "node",
                    "check_command": "node --version",
                    "required_version": ">=16.0.0",
                    "install_commands": {
                        "windows": "Descarga desde https://nodejs.org/",
                        "linux": "curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash - && sudo apt-get install -y nodejs",
                        "darwin": "brew install node"
                    }
                },
                {
                    "name": "npm",
                    "check_command": "npm --version",
                    "required_version": ">=7.0.0",
                    "install_commands": {
                        "windows": "Incluido con Node.js",
                        "linux": "Incluido con Node.js",
                        "darwin": "Incluido con Node.js"
                    }
                }
            ],
            "setup_commands": [
                "cd {project_name}",
                "npm install",
                "npm run dev"
            ],
            "dev_server_port": 5173,
            "package_manager_alternatives": ["npm", "yarn", "pnpm"]
        },
        "angular": {
            "name": "Angular",
            "description": "Framework TypeScript para crear aplicaciones web robustas",
            "primary_commands": [
                "ng new {project_name} --routing --style=css"
            ],
            "dependencies": [
                {
                    "name": "node",
                    "check_command": "node --version",
                    "required_version": ">=18.0.0",
                    "install_commands": {
                        "windows": "Descarga desde https://nodejs.org/",
                        "linux": "curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash - && sudo apt-get install -y nodejs",
                        "darwin": "brew install node"
                    }
                },
                {
                    "name": "angular-cli",
                    "check_command": "ng version",
                    "required_version": ">=15.0.0",
                    "install_commands": {
                        "windows": "npm install -g @angular/cli",
                        "linux": "sudo npm install -g @angular/cli",
                        "darwin": "npm install -g @angular/cli"
                    }
                }
            ],
            "setup_commands": [
                "cd {project_name}",
                "ng serve"
            ],
            "dev_server_port": 4200,
            "package_manager_alternatives": ["npm", "yarn"]
        },
        "nextjs": {
            "name": "Next.js",
            "description": "Framework React para aplicaciones web con SSR y generación estática",
            "primary_commands": [
                "npx create-next-app@latest {project_name}",
                "npm create next-app@latest {project_name}"
            ],
            "dependencies": [
                {
                    "name": "node",
                    "check_command": "node --version",
                    "required_version": ">=18.0.0",
                    "install_commands": {
                        "windows": "Descarga desde https://nodejs.org/",
                        "linux": "curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash - && sudo apt-get install -y nodejs",
                        "darwin": "brew install node"
                    }
                },
                {
                    "name": "npm",
                    "check_command": "npm --version",
                    "required_version": ">=8.0.0",
                    "install_commands": {
                        "windows": "Incluido con Node.js",
                        "linux": "Incluido con Node.js",
                        "darwin": "Incluido con Node.js"
                    }
                }
            ],
            "setup_commands": [
                "cd {project_name}",
                "npm run dev"
            ],
            "dev_server_port": 3000,
            "package_manager_alternatives": ["npm", "yarn", "pnpm"]
        },
        "django": {
            "name": "Django",
            "description": "Framework Python para desarrollo web con baterías incluidas",
            "primary_commands": [
                "django-admin startproject {project_name}",
                "python -m django startproject {project_name}"
            ],
            "dependencies": [
                {
                    "name": "python",
                    "check_command": "python --version",
                    "required_version": ">=3.8.0",
                    "install_commands": {
                        "windows": "Descarga desde https://python.org/downloads/",
                        "linux": "sudo apt-get install python3 python3-pip",
                        "darwin": "brew install python"
                    }
                },
                {
                    "name": "pip",
                    "check_command": "pip --version",
                    "required_version": ">=20.0.0",
                    "install_commands": {
                        "windows": "Incluido con Python",
                        "linux": "Incluido con Python",
                        "darwin": "Incluido con Python"
                    }
                },
                {
                    "name": "django",
                    "check_command": "django-admin --version",
                    "required_version": ">=4.0.0",
                    "install_commands": {
                        "windows": "pip install django",
                        "linux": "pip install django",
                        "darwin": "pip install django"
                    }
                }
            ],
            "setup_commands": [
                "cd {project_name}",
                "python manage.py migrate",
                "python manage.py runserver"
            ],
            "dev_server_port": 8000,
            "package_manager_alternatives": ["pip", "poetry", "pipenv"]
        },
        "fastapi": {
            "name": "FastAPI",
            "description": "Framework Python moderno para crear APIs rápidas y robustas",
            "primary_commands": [
                "mkdir {project_name} && cd {project_name}",
                "fastapi dev main.py"
            ],
            "dependencies": [
                {
                    "name": "python",
                    "check_command": "python --version",
                    "required_version": ">=3.8.0",
                    "install_commands": {
                        "windows": "Descarga desde https://python.org/downloads/",
                        "linux": "sudo apt-get install python3 python3-pip",
                        "darwin": "brew install python"
                    }
                },
                {
                    "name": "pip",
                    "check_command": "pip --version",
                    "required_version": ">=20.0.0",
                    "install_commands": {
                        "windows": "Incluido con Python",
                        "linux": "Incluido con Python",
                        "darwin": "Incluido con Python"
                    }
                },
                {
                    "name": "fastapi",
                    "check_command": "python -c \"import fastapi; print(fastapi.__version__)\"",
                    "required_version": ">=0.100.0",
                    "install_commands": {
                        "windows": "pip install fastapi[all]",
                        "linux": "pip install fastapi[all]",
                        "darwin": "pip install fastapi[all]"
                    }
                }
            ],
            "setup_commands": [
                "cd {project_name}",
                "pip install fastapi[all]",
                "fastapi dev main.py"
            ],
            "dev_server_port": 8000,
            "package_manager_alternatives": ["pip", "poetry", "pipenv"]
        },
        "rails": {
            "name": "Ruby on Rails",
            "description": "Framework Ruby para desarrollo web rápido y elegante",
            "primary_commands": [
                "rails new {project_name}",
                "gem install rails && rails new {project_name}"
            ],
            "dependencies": [
                {
                    "name": "ruby",
                    "check_command": "ruby --version",
                    "required_version": ">=3.0.0",
                    "install_commands": {
                        "windows": "Descarga desde https://rubyinstaller.org/",
                        "linux": "sudo apt-get install ruby-full",
                        "darwin": "brew install ruby"
                    }
                },
                {
                    "name": "gem",
                    "check_command": "gem --version",
                    "required_version": ">=3.0.0",
                    "install_commands": {
                        "windows": "Incluido con Ruby",
                        "linux": "Incluido con Ruby",
                        "darwin": "Incluido con Ruby"
                    }
                },
                {
                    "name": "rails",
                    "check_command": "rails --version",
                    "required_version": ">=7.0.0",
                    "install_commands": {
                        "windows": "gem install rails",
                        "linux": "gem install rails",
                        "darwin": "gem install rails"
                    }
                }
            ],
            "setup_commands": [
                "cd {project_name}",
                "bundle install",
                "rails server"
            ],
            "dev_server_port": 3000,
            "package_manager_alternatives": ["gem", "bundler"]
        },
        "flutter": {
            "name": "Flutter",
            "description": "Framework de Google para crear aplicaciones móviles multiplataforma",
            "primary_commands": [
                "flutter create {project_name}",
                "flutter create --platforms=android,ios {project_name}"
            ],
            "dependencies": [
                {
                    "name": "flutter",
                    "check_command": "flutter --version",
                    "required_version": ">=3.0.0",
                    "install_commands": {
                        "windows": "Descarga Flutter SDK desde https://flutter.dev/docs/get-started/install/windows",
                        "linux": "sudo snap install flutter --classic",
                        "darwin": "brew install flutter"
                    }
                },
                {
                    "name": "dart",
                    "check_command": "dart --version",
                    "required_version": ">=2.17.0",
                    "install_commands": {
                        "windows": "Incluido con Flutter",
                        "linux": "Incluido con Flutter",
                        "darwin": "Incluido con Flutter"
                    }
                }
            ],
            "setup_commands": [
                "cd {project_name}",
                "flutter pub get",
                "flutter run"
            ],
            "dev_server_port": None,
            "package_manager_alternatives": ["pub"]
        }
    }

    @classmethod
    def get_framework_info(cls, framework: str) -> Optional[Dict]:
        return cls.FRAMEWORKS.get(framework.lower())

    @classmethod
    def get_framework_names(cls) -> List[str]:
        return list(cls.FRAMEWORKS.keys())


class IntelligentCLIManager:
    """Gestor inteligente de CLI con detección de dependencias y ejecución automática"""

    def __init__(self, llm=None):
        self.llm = llm
        self.os_type = platform.system().lower()
        self.framework_db = EnhancedFrameworkDatabase()

    def check_dependency(self, dependency_info: Dict) -> DependencyInfo:
        """Verifica una dependencia específica"""
        name = dependency_info["name"]
        check_command = dependency_info["check_command"]

        try:
            # Ejecutar comando de verificación
            result = subprocess.run(
                check_command.split(),
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0:
                current_version = self._extract_version(result.stdout)
                required_version = dependency_info.get("required_version")

                if required_version and current_version:
                    if self._compare_versions(current_version, required_version):
                        status = DependencyStatus.AVAILABLE
                    else:
                        status = DependencyStatus.OUTDATED
                else:
                    status = DependencyStatus.AVAILABLE

                return DependencyInfo(
                    name=name,
                    status=status,
                    current_version=current_version,
                    required_version=required_version,
                    install_command=dependency_info["install_commands"].get(self.os_type),
                    check_command=check_command
                )
            else:
                return DependencyInfo(
                    name=name,
                    status=DependencyStatus.MISSING,
                    install_command=dependency_info["install_commands"].get(self.os_type),
                    check_command=check_command
                )

        except Exception as e:
            logger.error(f"Error checking dependency {name}: {e}")
            return DependencyInfo(
                name=name,
                status=DependencyStatus.UNKNOWN,
                install_command=dependency_info["install_commands"].get(self.os_type),
                check_command=check_command
            )

    def _extract_version(self, output: str) -> Optional[str]:
        """Extrae versión de la salida del comando"""
        import re

        # Patrones comunes para versiones
        patterns = [
            r'v?(\d+\.\d+\.\d+)',
            r'version\s+(\d+\.\d+\.\d+)',
            r'(\d+\.\d+\.\d+)',
            r'v?(\d+\.\d+)',
            r'(\d+\.\d+)'
        ]

        for pattern in patterns:
            match = re.search(pattern, output, re.IGNORECASE)
            if match:
                return match.group(1)

        return None

    def _compare_versions(self, current: str, required: str) -> bool:
        """Compara versiones (simplificado)"""
        try:
            # Remover operadores de comparación
            required_clean = required.replace('>=', '').replace('>', '').replace('=', '').strip()

            current_parts = [int(x) for x in current.split('.')]
            required_parts = [int(x) for x in required_clean.split('.')]

            # Rellenar con ceros si es necesario
            max_len = max(len(current_parts), len(required_parts))
            current_parts.extend([0] * (max_len - len(current_parts)))
            required_parts.extend([0] * (max_len - len(required_parts)))

            return current_parts >= required_parts

        except Exception:
            return True  # Si no puede comparar, asume que está bien

    def check_framework_dependencies(self, framework: str) -> List[DependencyInfo]:
        """Verifica todas las dependencias de un framework"""
        framework_info = self.framework_db.get_framework_info(framework)
        if not framework_info:
            return []

        dependencies = []
        for dep_info in framework_info.get("dependencies", []):
            dependency = self.check_dependency(dep_info)
            dependencies.append(dependency)

        return dependencies

    def generate_setup_instructions(self, framework: str, project_name: str) -> FrameworkSetupResult:
        """Genera instrucciones de configuración inteligentes"""
        framework_info = self.framework_db.get_framework_info(framework)
        if not framework_info:
            return FrameworkSetupResult(
                success=False,
                message=f"Framework '{framework}' no reconocido",
                dependencies=[],
                setup_commands=[],
                next_steps=[]
            )

        # Verificar dependencias
        dependencies = self.check_framework_dependencies(framework)
        missing_deps = [dep for dep in dependencies if dep.status == DependencyStatus.MISSING]
        outdated_deps = [dep for dep in dependencies if dep.status == DependencyStatus.OUTDATED]

        if missing_deps or outdated_deps:
            return self._generate_dependency_setup_instructions(
                framework, project_name, dependencies, missing_deps, outdated_deps
            )

        # Todas las dependencias están disponibles
        return self._generate_project_setup_instructions(framework, project_name, dependencies)

    def _generate_dependency_setup_instructions(self, framework: str, project_name: str,
                                                dependencies: List[DependencyInfo],
                                                missing_deps: List[DependencyInfo],
                                                outdated_deps: List[DependencyInfo]) -> FrameworkSetupResult:
        """Genera instrucciones para instalar dependencias faltantes"""

        framework_info = self.framework_db.get_framework_info(framework)

        setup_commands = []
        next_steps = []

        # Comandos de instalación para dependencias faltantes
        for dep in missing_deps:
            if dep.install_command:
                setup_commands.append(f"# Instalar {dep.name}")
                setup_commands.append(dep.install_command)

        # Comandos de actualización para dependencias desactualizadas
        for dep in outdated_deps:
            if dep.install_command:
                setup_commands.append(f"# Actualizar {dep.name}")
                setup_commands.append(dep.install_command)

        # Comandos para crear el proyecto (después de instalar dependencias)
        primary_command = framework_info["primary_commands"][0].format(project_name=project_name)
        setup_commands.append(f"# Crear proyecto {framework}")
        setup_commands.append(primary_command)

        # Comandos adicionales de setup
        for cmd in framework_info["setup_commands"]:
            setup_commands.append(cmd.format(project_name=project_name))

        # Próximos pasos
        next_steps = [
            f"1. Instalar dependencias faltantes: {', '.join([dep.name for dep in missing_deps + outdated_deps])}",
            f"2. Crear proyecto con: {primary_command}",
            f"3. Navegar al directorio: cd {project_name}",
            f"4. Iniciar servidor de desarrollo"
        ]

        if framework_info.get("dev_server_port"):
            next_steps.append(f"5. Abrir navegador en: http://localhost:{framework_info['dev_server_port']}")

        # Generar mensaje usando IA si está disponible
        if self.llm:
            message = self._generate_ai_setup_message(framework, project_name, dependencies, missing_deps,
                                                      outdated_deps)
        else:
            message = f"Necesitas instalar las siguientes dependencias antes de crear el proyecto {framework}: {', '.join([dep.name for dep in missing_deps + outdated_deps])}"

        return FrameworkSetupResult(
            success=False,  # False porque necesita instalación manual
            message=message,
            dependencies=dependencies,
            setup_commands=setup_commands,
            next_steps=next_steps,
            troubleshooting=self._generate_troubleshooting_guide(framework, missing_deps + outdated_deps)
        )

    def _generate_project_setup_instructions(self, framework: str, project_name: str,
                                             dependencies: List[DependencyInfo]) -> FrameworkSetupResult:
        """Genera instrucciones para crear el proyecto (dependencias OK)"""

        framework_info = self.framework_db.get_framework_info(framework)

        # Comando principal para crear proyecto
        primary_command = framework_info["primary_commands"][0].format(project_name=project_name)

        setup_commands = [
            f"# Crear proyecto {framework}",
            primary_command
        ]

        # Comandos adicionales
        for cmd in framework_info["setup_commands"]:
            setup_commands.append(cmd.format(project_name=project_name))

        # Próximos pasos
        next_steps = [
            f"✅ Todas las dependencias están instaladas",
            f"🚀 Proyecto creado exitosamente: {project_name}",
            f"📁 Navegar al directorio: cd {project_name}",
            f"🔧 Instalar dependencias del proyecto",
            f"🚀 Iniciar servidor de desarrollo"
        ]

        if framework_info.get("dev_server_port"):
            next_steps.append(f"🌐 Abrir navegador en: http://localhost:{framework_info['dev_server_port']}")

        # Generar mensaje usando IA si está disponible
        if self.llm:
            message = self._generate_ai_success_message(framework, project_name, dependencies)
        else:
            message = f"¡Perfecto! Todas las dependencias están instaladas. Puedes crear tu proyecto {framework} con: {primary_command}"

        return FrameworkSetupResult(
            success=True,
            message=message,
            dependencies=dependencies,
            setup_commands=setup_commands,
            next_steps=next_steps
        )

    def _generate_ai_setup_message(self, framework: str, project_name: str,
                                   dependencies: List[DependencyInfo],
                                   missing_deps: List[DependencyInfo],
                                   outdated_deps: List[DependencyInfo]) -> str:
        """Genera mensaje de configuración usando IA"""

        if not self.llm:
            return "Necesitas instalar algunas dependencias antes de continuar."

        try:
            from langchain.schema import HumanMessage

            dep_status = []
            for dep in dependencies:
                status_emoji = {
                    DependencyStatus.AVAILABLE: "✅",
                    DependencyStatus.MISSING: "❌",
                    DependencyStatus.OUTDATED: "⚠️",
                    DependencyStatus.UNKNOWN: "❓"
                }

                dep_status.append(f"{status_emoji[dep.status]} {dep.name}: {dep.status.value}")
                if dep.current_version:
                    dep_status.append(f"  Versión actual: {dep.current_version}")
                if dep.required_version:
                    dep_status.append(f"  Versión requerida: {dep.required_version}")

            prompt = f"""
Eres Herbie, un agente amigable y técnico especializado en desarrollo.

Situación:
- Framework: {framework}
- Proyecto: {project_name}
- Sistema operativo: {self.os_type}
- Dependencias faltantes: {[dep.name for dep in missing_deps]}
- Dependencias desactualizadas: {[dep.name for dep in outdated_deps]}

Estado de dependencias:
{chr(10).join(dep_status)}

Genera un mensaje que:
1. Explique la situación de manera clara y amigable
2. Indique qué dependencias necesitan instalación/actualización
3. Proporcione instrucciones específicas para {self.os_type}
4. Sea motivador y profesional
5. Use emojis apropiados

Responde directamente con el mensaje, no con JSON.
"""

            response = self.llm.invoke([HumanMessage(content=prompt)])
            return response.content.strip()

        except Exception as e:
            logger.error(f"Error generando mensaje con IA: {e}")
            return f"Necesitas instalar: {', '.join([dep.name for dep in missing_deps + outdated_deps])}"

    def _generate_ai_success_message(self, framework: str, project_name: str,
                                     dependencies: List[DependencyInfo]) -> str:
        """Genera mensaje de éxito usando IA"""

        if not self.llm:
            return "¡Listo para crear tu proyecto!"

        try:
            from langchain.schema import HumanMessage

            framework_info = self.framework_db.get_framework_info(framework)

            prompt = f"""
Eres Herbie, un agente entusiasta para desarrollo.

Situación:
- Framework: {framework}
- Proyecto: {project_name}
- Todas las dependencias están instaladas ✅
- Descripción del framework: {framework_info.get('description', '')}
- Puerto de desarrollo: {framework_info.get('dev_server_port', 'N/A')}

Genera un mensaje que:
1. Celebre que todo está listo
2. Mencione el próximo paso (crear el proyecto)
3. Sea entusiasta y motivador
4. Incluya información útil sobre el framework
5. Use emojis apropiados

Responde directamente con el mensaje, no con JSON.
"""

            response = self.llm.invoke([HumanMessage(content=prompt)])
            return response.content.strip()

        except Exception as e:
            logger.error(f"Error generando mensaje con IA: {e}")
            return f"¡Perfecto! Listo para crear tu proyecto {framework}."

    def _generate_troubleshooting_guide(self, framework: str, problematic_deps: List[DependencyInfo]) -> str:
        """Genera guía de resolución de problemas"""

        guides = []

        for dep in problematic_deps:
            if dep.name == "node":
                guides.append("""
### Problemas con Node.js:
- **Windows**: Descargar desde nodejs.org y seguir el instalador
- **Linux**: Usar Node Version Manager (nvm) si hay conflictos
- **macOS**: Usar Homebrew o descargar desde nodejs.org
- **Verificar**: `node --version` y `npm --version`
""")
            elif dep.name == "python":
                guides.append("""
### Problemas con Python:
- **Windows**: Asegúrate de marcar "Add to PATH" durante la instalación
- **Linux**: Usar `python3` en lugar de `python`
- **macOS**: Evitar usar Python del sistema, usar Homebrew
- **Verificar**: `python --version` o `python3 --version`
""")
            elif dep.name == "ruby":
                guides.append("""
### Problemas con Ruby:
- **Windows**: Usar RubyInstaller con DevKit
- **Linux**: Instalar build-essential antes de Ruby
- **macOS**: Usar rbenv o RVM para manejar versiones
- **Verificar**: `ruby --version` y `gem --version`
""")

        return "\n".join(guides) if guides else "No hay guías específicas disponibles."

    def execute_framework_setup(self, framework: str, project_name: str,
                                auto_install: bool = False) -> FrameworkSetupResult:
        """Ejecuta la configuración del framework automáticamente"""

        setup_result = self.generate_setup_instructions(framework, project_name)

        if not setup_result.success:
            return setup_result

        # Si todas las dependencias están disponibles, ejecutar comandos
        if auto_install:
            try:
                for command in setup_result.setup_commands:
                    if command.startswith('#'):
                        continue

                    logger.info(f"Ejecutando: {command}")

                    result = subprocess.run(
                        command,
                        shell=True,
                        capture_output=True,
                        text=True,
                        timeout=300
                    )

                    if result.returncode != 0:
                        return FrameworkSetupResult(
                            success=False,
                            message=f"Error ejecutando comando: {command}\n{result.stderr}",
                            dependencies=setup_result.dependencies,
                            setup_commands=setup_result.setup_commands,
                            next_steps=setup_result.next_steps,
                            troubleshooting=f"Error en comando: {command}\nSalida: {result.stderr}"
                        )

                # Actualizar mensaje de éxito
                setup_result.message = f"🎉 ¡Proyecto {project_name} creado exitosamente con {framework}!"

            except Exception as e:
                logger.error(f"Error ejecutando setup: {e}")
                return FrameworkSetupResult(
                    success=False,
                    message=f"Error inesperado durante la configuración: {str(e)}",
                    dependencies=setup_result.dependencies,
                    setup_commands=setup_result.setup_commands,
                    next_steps=setup_result.next_steps,
                    troubleshooting=f"Error inesperado: {str(e)}"
                )

        return setup_result


# Ejemplo de uso
if __name__ == "__main__":
    # Simulación de uso
    cli_manager = IntelligentCLIManager()

    # Verificar dependencias de React
    result = cli_manager.generate_setup_instructions("react", "mi-app-react")

    print("=== RESULTADO DE CONFIGURACIÓN ===")
    print(f"Éxito: {result.success}")
    print(f"Mensaje: {result.message}")
    print("\nDependencias:")
    for dep in result.dependencies:
        print(f"  - {dep.name}: {dep.status.value}")
        if dep.current_version:
            print(f"    Versión: {dep.current_version}")

    print("\nComandos de configuración:")
    for cmd in result.setup_commands:
        print(f"  {cmd}")

    print("\nPróximos pasos:")
    for step in result.next_steps:
        print(f"  {step}")

    if result.troubleshooting:
        print(f"\nResolución de problemas:\n{result.troubleshooting}")