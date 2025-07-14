import os
import requests
import json
import base64
import shutil
import subprocess
import platform
import logging
from pathlib import Path
from typing import Dict, Optional, List
from dataclasses import dataclass
from dotenv import load_dotenv
from langchain.schema import HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('herbie.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Cargar variables de entorno
load_dotenv()


@dataclass
class ProjectInfo:
    repo_name: str
    description: str
    is_private: bool
    framework: str
    init_command: str
    additional_setup: Optional[List[str]] = None


class FrameworkDatabase:
    """Base de conocimiento de frameworks con comandos y configuraciones"""

    FRAMEWORKS = {
        "react": {
            "commands": ["npx create-react-app", "npm create vite@latest"],
            "check_cmd": "node",
            "package_managers": ["npm", "yarn", "pnpm"],
            "install_instructions": {
                "windows": "Instala Node.js desde https://nodejs.org/",
                "linux": "sudo apt-get install nodejs npm",
                "darwin": "brew install node"
            }
        },
        "vue": {
            "commands": ["npm create vue@latest", "vue create"],
            "check_cmd": "node",
            "package_managers": ["npm", "yarn", "pnpm"],
            "install_instructions": {
                "windows": "Instala Node.js desde https://nodejs.org/",
                "linux": "sudo apt-get install nodejs npm",
                "darwin": "brew install node"
            }
        },
        "angular": {
            "commands": ["ng new"],
            "check_cmd": "ng",
            "package_managers": ["npm", "yarn"],
            "install_instructions": {
                "windows": "npm install -g @angular/cli",
                "linux": "sudo npm install -g @angular/cli",
                "darwin": "npm install -g @angular/cli"
            }
        },
        "rails": {
            "commands": ["rails new"],
            "check_cmd": "rails",
            "package_managers": ["gem", "bundle"],
            "install_instructions": {
                "windows": "Instala Ruby desde https://rubyinstaller.org/",
                "linux": "sudo apt-get install ruby-full",
                "darwin": "brew install ruby"
            }
        },
        "django": {
            "commands": ["django-admin startproject"],
            "check_cmd": "django-admin",
            "package_managers": ["pip", "poetry"],
            "install_instructions": {
                "windows": "pip install django",
                "linux": "pip install django",
                "darwin": "pip install django"
            }
        },
        "fastapi": {
            "commands": ["fastapi-cli new"],
            "check_cmd": "fastapi-cli",
            "package_managers": ["pip", "poetry"],
            "install_instructions": {
                "windows": "pip install fastapi-cli",
                "linux": "pip install fastapi-cli",
                "darwin": "pip install fastapi-cli"
            }
        },
        "nextjs": {
            "commands": ["npx create-next-app@latest"],
            "check_cmd": "node",
            "package_managers": ["npm", "yarn", "pnpm"],
            "install_instructions": {
                "windows": "Instala Node.js desde https://nodejs.org/",
                "linux": "sudo apt-get install nodejs npm",
                "darwin": "brew install node"
            }
        },
        "flutter": {
            "commands": ["flutter create"],
            "check_cmd": "flutter",
            "package_managers": ["pub"],
            "install_instructions": {
                "windows": "Descarga Flutter SDK desde https://flutter.dev/docs/get-started/install/windows",
                "linux": "sudo snap install flutter --classic",
                "darwin": "brew install flutter"
            }
        }
    }

    @classmethod
    def get_framework_info(cls, framework: str) -> Optional[Dict]:
        return cls.FRAMEWORKS.get(framework.lower())


class HerbieFrameworkHelper:
    def __init__(self, llm):
        self.llm = llm
        self.system_info = {
            "os": platform.system().lower(),
            "version": platform.release(),
            "architecture": platform.machine()
        }

    def check_command(self, cmd: str) -> bool:
        """Verifica si un comando está disponible en el sistema"""
        return shutil.which(cmd) is not None

    def check_framework_requirements(self, framework: str) -> Dict:
        """Verifica si los requisitos del framework están instalados"""
        framework_info = FrameworkDatabase.get_framework_info(framework)
        if not framework_info:
            return {"available": False, "reason": "Framework no reconocido"}

        check_cmd = framework_info["check_cmd"]
        if self.check_command(check_cmd):
            return {"available": True}

        return {
            "available": False,
            "reason": f"Comando '{check_cmd}' no encontrado",
            "framework_info": framework_info
        }

    def explain_missing_dependency(self, framework: str) -> str:
        """Genera explicación detallada sobre dependencias faltantes"""
        framework_info = FrameworkDatabase.get_framework_info(framework)
        if not framework_info:
            return "Framework no reconocido. Verifique el nombre del framework."

        system = self.system_info["os"]
        install_cmd = framework_info["install_instructions"].get(system, "Consulte la documentación oficial")

        prompt = f"""
Como experto en desarrollo de software, explica de forma clara y profesional:

Framework: {framework}
Sistema operativo: {system}
Comando de instalación sugerido: {install_cmd}

Proporciona:
1. Explicación breve del problema
2. Pasos específicos de instalación para {system}
3. Comandos exactos a ejecutar
4. Verificación de instalación exitosa
5. Posibles problemas comunes y soluciones

Mantén un tono profesional y educativo, como si fueras un profesor de ingeniería de software.
"""

        response = self.llm.invoke([HumanMessage(content=prompt)])
        return response.content

    def generate_install_md(self, framework: str) -> str:
        """Genera archivo INSTALL.md completo"""
        framework_info = FrameworkDatabase.get_framework_info(framework)
        system = self.system_info["os"]

        prompt = f"""
Como profesor de ingeniería de software, crea un archivo INSTALL.md profesional y completo para un proyecto {framework} en {system}.

Incluye:
1. Título y descripción del proyecto
2. Requisitos del sistema
3. Instalación paso a paso
4. Configuración del entorno de desarrollo
5. Comandos para ejecutar el proyecto
6. Solución de problemas comunes
7. Recursos adicionales

Estructura del framework disponible: {json.dumps(framework_info, indent=2)}

Usa formato Markdown profesional con emojis apropiados.
"""

        response = self.llm.invoke([HumanMessage(content=prompt)])
        return response.content

    def init_framework_project(self, project_info: ProjectInfo) -> Dict:
        """Inicializa proyecto con el framework especificado"""
        logger.info(f"Iniciando proyecto {project_info.repo_name} con framework {project_info.framework}")

        # Verificar requisitos
        requirements_check = self.check_framework_requirements(project_info.framework)
        if not requirements_check["available"]:
            return {
                "success": False,
                "message": self.explain_missing_dependency(project_info.framework),
                "install_md": self.generate_install_md(project_info.framework)
            }

        # Ejecutar comando de inicialización
        try:
            logger.info(f"Ejecutando: {project_info.init_command}")
            result = subprocess.run(
                project_info.init_command.split(),
                check=True,
                capture_output=True,
                text=True,
                timeout=300  # 5 minutos timeout
            )

            # Ejecutar comandos adicionales si existen
            if project_info.additional_setup:
                os.chdir(project_info.repo_name)
                for cmd in project_info.additional_setup:
                    logger.info(f"Ejecutando setup adicional: {cmd}")
                    subprocess.run(cmd.split(), check=True)
                os.chdir("..")

            return {"success": True, "output": result.stdout}

        except subprocess.TimeoutExpired:
            return {"success": False, "message": "Timeout: El comando tomó demasiado tiempo"}
        except subprocess.CalledProcessError as e:
            return {"success": False, "message": f"Error al ejecutar el comando: {e.stderr}"}
        except Exception as e:
            return {"success": False, "message": f"Error inesperado: {str(e)}"}


class GitHubRepoCreator:
    def __init__(self):
        self.github_token = os.getenv('GITHUB_TOKEN')
        self.google_api_key = os.getenv('GOOGLE_API_KEY')

        if not self.github_token:
            raise ValueError("GITHUB_TOKEN es requerido")
        if not self.google_api_key:
            raise ValueError("GOOGLE_API_KEY es requerido")

        self.llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash",
            google_api_key=self.google_api_key,
            temperature=0.3  # Reducir temperatura para más consistencia
        )

        self.headers = {
            'Authorization': f'token {self.github_token}',
            'Accept': 'application/vnd.github.v3+json',
            'Content-Type': 'application/json'
        }

        self.framework_helper = HerbieFrameworkHelper(self.llm)
        self.username = self._get_username()

    def _get_username(self) -> str:
        """Obtiene el nombre de usuario de GitHub"""
        try:
            res = requests.get("https://api.github.com/user", headers=self.headers, timeout=10)
            if res.status_code == 200:
                return res.json().get('login', 'unknown-user')
            else:
                logger.warning(f"Error obteniendo usuario: {res.status_code}")
                return 'unknown-user'
        except Exception as e:
            logger.error(f"Error conectando con GitHub: {e}")
            return 'unknown-user'

    def parse_user_input(self, user_input: str) -> ProjectInfo:
        """Parsea entrada del usuario usando IA"""
        frameworks_list = list(FrameworkDatabase.FRAMEWORKS.keys())

        prompt = f"""
Analiza este mensaje del usuario y extrae información para crear un proyecto:
"{user_input}"

Frameworks disponibles: {frameworks_list}

Responde SOLO con un JSON válido con esta estructura exacta:
{{
  "repo_name": "nombre-del-repositorio",
  "is_private": true/false,
  "description": "descripción del proyecto",
  "framework": "framework-elegido",
  "init_command": "comando-para-inicializar",
  "additional_setup": ["comando1", "comando2"] o null
}}

Reglas:
- repo_name: sin espacios, guiones bajos o caracteres especiales
- framework: debe ser uno de la lista disponible
- init_command: comando completo con argumentos
- Si no se especifica privacidad, usa false
- Si falta información, usa valores razonables
"""

        try:
            response = self.llm.invoke([HumanMessage(content=prompt)])
            content = response.content.strip()

            # Extraer JSON del contenido
            start = content.find('{')
            end = content.rfind('}') + 1

            if start == -1 or end == 0:
                raise ValueError("No se encontró JSON válido en la respuesta")

            json_str = content[start:end]
            data = json.loads(json_str)

            return ProjectInfo(
                repo_name=data['repo_name'],
                description=data['description'],
                is_private=data['is_private'],
                framework=data['framework'],
                init_command=data['init_command'],
                additional_setup=data.get('additional_setup')
            )

        except json.JSONDecodeError as e:
            logger.error(f"Error parseando JSON: {e}")
            raise ValueError("No se pudo interpretar la respuesta de la IA")
        except Exception as e:
            logger.error(f"Error procesando entrada: {e}")
            raise ValueError("Error procesando la entrada del usuario")

    def create_repository(self, project_info: ProjectInfo) -> Optional[Dict]:
        """Crea repositorio en GitHub"""
        url = "https://api.github.com/user/repos"
        data = {
            "name": project_info.repo_name,
            "description": project_info.description,
            "private": project_info.is_private,
            "has_issues": True,
            "has_projects": True,
            "has_wiki": True,
            "auto_init": False
        }

        try:
            res = requests.post(url, headers=self.headers, json=data, timeout=30)
            if res.status_code == 201:
                logger.info(f"Repositorio '{project_info.repo_name}' creado exitosamente")
                return res.json()
            else:
                logger.error(f"Error creando repositorio: {res.status_code} - {res.text}")
                return None
        except Exception as e:
            logger.error(f"Error en petición a GitHub: {e}")
            return None

    def _setup_git_config(self):
        """Configura Git con las credenciales necesarias"""
        try:
            # Configurar usuario (opcional, pero recomendado)
            subprocess.run(["git", "config", "user.name", self.username], check=True)
            subprocess.run(["git", "config", "user.email", f"{self.username}@users.noreply.github.com"], check=True)
            logger.info("Configuración de Git establecida")
        except Exception as e:
            logger.warning(f"No se pudo configurar Git: {e}")

    def push_local_to_repo(self, repo_name: str) -> bool:
        """Sube código local a repositorio GitHub con autenticación mejorada"""
        try:
            if not os.path.exists(repo_name):
                logger.error(f"Directorio {repo_name} no existe")
                return False

            original_dir = os.getcwd()
            os.chdir(repo_name)

            # Configurar Git
            self._setup_git_config()

            # URL con token para autenticación
            repo_url = f"https://{self.github_token}@github.com/{self.username}/{repo_name}.git"

            commands = [
                ["git", "init"],
                ["git", "remote", "add", "origin", repo_url],
                ["git", "add", "."],
                ["git", "commit", "-m", "Initial commit - Created by Herbie Agent"],
                ["git", "branch", "-M", "main"],
                ["git", "push", "-u", "origin", "main"]
            ]

            for cmd in commands:
                # Ocultar token en los logs
                log_cmd = cmd.copy()
                if len(log_cmd) > 2 and "github.com" in log_cmd[2]:
                    log_cmd[2] = log_cmd[2].replace(self.github_token, "***TOKEN***")

                logger.info(f"Ejecutando: {' '.join(log_cmd)}")

                # Configurar entorno para evitar prompts interactivos
                env = os.environ.copy()
                env['GIT_TERMINAL_PROMPT'] = '0'

                result = subprocess.run(
                    cmd,
                    check=True,
                    capture_output=True,
                    text=True,
                    env=env,
                    timeout=60
                )

            os.chdir(original_dir)
            logger.info("Código subido exitosamente a GitHub")
            return True

        except subprocess.TimeoutExpired:
            logger.error("Timeout: El comando git tomó demasiado tiempo")
            os.chdir(original_dir)
            return False
        except subprocess.CalledProcessError as e:
            logger.error(f"Error en comando git: {e.stderr}")
            os.chdir(original_dir)
            return False
        except Exception as e:
            logger.error(f"Error subiendo a GitHub: {e}")
            os.chdir(original_dir)
            return False

    def push_local_to_repo_alternative(self, repo_name: str) -> bool:
        """Método alternativo usando la API de GitHub para subir archivos"""
        try:
            if not os.path.exists(repo_name):
                logger.error(f"Directorio {repo_name} no existe")
                return False

            logger.info("Usando método alternativo: GitHub API")

            # Recorrer archivos del proyecto
            for root, dirs, files in os.walk(repo_name):
                # Ignorar directorios como .git, node_modules, etc.
                dirs[:] = [d for d in dirs if not d.startswith('.') and d != 'node_modules']

                for file in files:
                    if file.startswith('.'):
                        continue

                    file_path = os.path.join(root, file)
                    relative_path = os.path.relpath(file_path, repo_name)

                    # Leer archivo
                    try:
                        with open(file_path, 'rb') as f:
                            content = f.read()

                        # Codificar en base64
                        encoded_content = base64.b64encode(content).decode('utf-8')

                        # Subir via API
                        url = f"https://api.github.com/repos/{self.username}/{repo_name}/contents/{relative_path}"
                        data = {
                            "message": f"Add {relative_path}",
                            "content": encoded_content
                        }

                        response = requests.put(url, headers=self.headers, json=data)
                        if response.status_code not in [200, 201]:
                            logger.warning(f"Error subiendo {relative_path}: {response.status_code}")

                    except Exception as e:
                        logger.warning(f"Error procesando archivo {file_path}: {e}")
                        continue

            logger.info("Archivos subidos via API de GitHub")
            return True

        except Exception as e:
            logger.error(f"Error en método alternativo: {e}")
            return False

    def create_full_flow(self, user_input: str) -> Dict:
        """Flujo completo de creación de repositorio"""
        try:
            project_info = self.parse_user_input(user_input)

            # Inicializar proyecto local
            framework_result = self.framework_helper.init_framework_project(project_info)

            if not framework_result['success']:
                return {
                    "success": False,
                    "message": framework_result['message'],
                    "install_md": framework_result.get('install_md')
                }

            # Crear repositorio
            repo = self.create_repository(project_info)
            if not repo:
                return {"success": False, "message": "No se pudo crear el repositorio en GitHub"}

            # Subir código
            if self.push_local_to_repo(project_info.repo_name):
                return {
                    "success": True,
                    "repo_url": repo['html_url'],
                    "project_info": project_info
                }
            else:
                # Intentar método alternativo
                if self.push_local_to_repo_alternative(project_info.repo_name):
                    return {
                        "success": True,
                        "repo_url": repo['html_url'],
                        "project_info": project_info
                    }
                else:
                    return {"success": False, "message": "Error subiendo código a GitHub"}

        except Exception as e:
            logger.error(f"Error en flujo completo: {e}")
            return {"success": False, "message": f"Error: {str(e)}"}


class HerbieAgent:
    def __init__(self):
        self.repo_creator = GitHubRepoCreator()
        self.conversation_history = []

    def chat(self, user_input: str) -> str:
        """Manejar conversación con el usuario"""

        # Añadir al historial
        self.conversation_history.append({"role": "user", "content": user_input})

        # Analizar si el usuario quiere crear un repositorio
        create_keywords = ["crea", "crear", "nuevo", "repositorio", "repo", "github", "proyecto"]

        if any(keyword in user_input.lower() for keyword in create_keywords):
            return self._handle_repository_creation(user_input)
        else:
            return self._general_response(user_input)

    def _handle_repository_creation(self, user_input: str) -> str:
        """Manejar la creación de repositorios"""
        try:
            print("🔍 Analizando tu solicitud...")

            # Parsear información del proyecto
            project_info = self.repo_creator.parse_user_input(user_input)

            # Mostrar información extraída
            print(f"📋 Información del proyecto:")
            print(f"   - Nombre: {project_info.repo_name}")
            print(f"   - Framework: {project_info.framework}")
            print(f"   - Tipo: {'Privado' if project_info.is_private else 'Público'}")
            print(f"   - Descripción: {project_info.description[:100]}...")

            # Confirmar con el usuario
            confirm = input("\n¿Confirmas la creación del repositorio? (s/n): ").lower().strip()

            if confirm not in ['s', 'si', 'y', 'yes']:
                return "❌ Creación cancelada. Puedes intentar de nuevo con otra descripción."

            print("\n⚙️ Iniciando creación del proyecto...")

            # Crear el repositorio
            result = self.repo_creator.create_full_flow(user_input)

            if result['success']:
                privacy_text = "privado" if project_info.is_private else "público"
                response = f"""✅ ¡Repositorio creado exitosamente!

📁 Nombre: {project_info.repo_name}
🛠️  Framework: {project_info.framework}
🔒 Tipo: {privacy_text}
🌐 URL: {result['repo_url']}

¡Tu proyecto está listo para usar! Ya puedes clonarlo y empezar a trabajar."""

                self.conversation_history.append({"role": "assistant", "content": response})
                return response
            else:
                if 'install_md' in result:
                    install_file = f"{project_info.repo_name}_INSTALL.md"
                    with open(install_file, "w", encoding="utf-8") as f:
                        f.write(result['install_md'])
                    response = f"""❌ No se pudo crear el proyecto completo.

{result['message']}

📄 He creado un archivo de instalación: {install_file}
Revisa las instrucciones para configurar el framework correctamente."""
                else:
                    response = f"❌ Error: {result['message']}"

                self.conversation_history.append({"role": "assistant", "content": response})
                return response

        except Exception as e:
            error_msg = f"❌ Error procesando tu solicitud: {str(e)}"
            self.conversation_history.append({"role": "assistant", "content": error_msg})
            return error_msg

    def _general_response(self, user_input: str) -> str:
        """Respuesta conversacional general"""

        help_keywords = ["ayuda", "help", "como", "qué puedes hacer", "comandos"]

        if any(keyword in user_input.lower() for keyword in help_keywords):
            response = """🤖 ¡Hola! Soy Herbie, tu asistente inteligente para crear repositorios de GitHub.

Puedo ayudarte a:
✅ Crear repositorios públicos o privados
✅ Inicializar proyectos con diferentes frameworks
✅ Configurar el código inicial automáticamente
✅ Subir todo a GitHub listo para usar

🛠️ Frameworks soportados:
React, Vue, Angular, Next.js, Django, FastAPI, Rails, Flutter

💬 Ejemplos de uso:
• "Crea un repositorio público llamado 'mi-blog' con React"
• "Necesito un proyecto privado 'tienda-online' usando Next.js"
• "Haz un repo 'mi-api' con FastAPI para una REST API"

¿Qué proyecto quieres crear hoy?"""
        else:
            response = """¡Hola! 👋 

Soy Herbie, tu asistente para crear repositorios de GitHub con frameworks populares.

Puedo ayudarte a crear un proyecto completo desde cero. Solo dime:
- Qué tipo de proyecto quieres crear
- Qué framework prefieres usar
- Si quieres que sea público o privado

Escribe 'ayuda' para ver ejemplos de uso.

¿En qué proyecto estás pensando?"""

        self.conversation_history.append({"role": "assistant", "content": response})
        return response


def main():
    """Función principal para interactuar con el usuario"""

    print("🤖 Herbie - Asistente Inteligente para GitHub")
    print("=" * 50)

    try:
        # Inicializar el agente
        agent = HerbieAgent()

        print("\n¡Hola! Soy Herbie, tu asistente para crear repositorios de GitHub.")
        print("Puedo ayudarte a crear proyectos completos con diferentes frameworks.")
        print("Todo se configura automáticamente y se sube a GitHub listo para usar.")
        print("\nEscribe 'ayuda' para ver qué puedo hacer o 'salir' para terminar.")

        while True:
            user_input = input("\n📝 Tú: ").strip()

            if user_input.lower() in ['salir', 'exit', 'quit']:
                print("👋 ¡Hasta luego! Que tengas un buen día.")
                break

            if not user_input:
                print("Por favor, dime qué quieres hacer.")
                continue

            print()
            response = agent.chat(user_input)
            print(f"🤖 Herbie: {response}")

    except KeyboardInterrupt:
        print("\n\n👋 ¡Hasta luego!")
    except Exception as e:
        print(f"\n❌ Error inicializando Herbie: {e}")
        print("\nAsegúrate de tener las variables de entorno configuradas:")
        print("- GITHUB_TOKEN: Token de GitHub con permisos de repositorio")
        print("- GOOGLE_API_KEY: API key de Google Generative AI")


if __name__ == "__main__":
    main()