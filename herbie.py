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

    def push_local_to_repo(self, repo_name: str) -> bool:
        """Sube código local a repositorio GitHub"""
        try:
            if not os.path.exists(repo_name):
                logger.error(f"Directorio {repo_name} no existe")
                return False

            original_dir = os.getcwd()
            os.chdir(repo_name)

            commands = [
                ["git", "init"],
                ["git", "remote", "add", "origin", f"https://github.com/{self.username}/{repo_name}.git"],
                ["git", "add", "."],
                ["git", "commit", "-m", "Initial commit - Created by Herbie Agent"],
                ["git", "branch", "-M", "main"],
                ["git", "push", "-u", "origin", "main"]
            ]

            for cmd in commands:
                logger.info(f"Ejecutando: {' '.join(cmd)}")
                result = subprocess.run(cmd, check=True, capture_output=True, text=True)

            os.chdir(original_dir)
            return True

        except subprocess.CalledProcessError as e:
            logger.error(f"Error en comando git: {e.stderr}")
            os.chdir(original_dir)
            return False
        except Exception as e:
            logger.error(f"Error subiendo a GitHub: {e}")
            os.chdir(original_dir)
            return False

    def create_full_flow(self, user_input: str) -> Dict:
        """Flujo completo de creación de repositorio"""
        try:
            print("🔍 Analizando tu mensaje...")
            project_info = self.parse_user_input(user_input)

            print(f"📋 Proyecto: {project_info.repo_name}")
            print(f"🛠️  Framework: {project_info.framework}")
            print(f"🔒 Privado: {'Sí' if project_info.is_private else 'No'}")

            print("\n⚙️ Inicializando proyecto local...")
            framework_result = self.framework_helper.init_framework_project(project_info)

            if not framework_result['success']:
                print("❗ No se pudo inicializar el proyecto localmente.")
                print(framework_result['message'])

                if 'install_md' in framework_result:
                    install_file = f"{project_info.repo_name}_INSTALL.md"
                    with open(install_file, "w", encoding="utf-8") as f:
                        f.write(framework_result['install_md'])
                    print(f"📄 Archivo de instalación creado: {install_file}")

                return {"success": False, "message": framework_result['message']}

            print("✅ Proyecto inicializado localmente")

            print("\n📦 Creando repositorio en GitHub...")
            repo = self.create_repository(project_info)

            if not repo:
                return {"success": False, "message": "No se pudo crear el repositorio en GitHub"}

            print("📤 Subiendo código a GitHub...")
            if self.push_local_to_repo(project_info.repo_name):
                print(f"🎉 ¡Repositorio listo! {repo['html_url']}")
                return {
                    "success": True,
                    "repo_url": repo['html_url'],
                    "project_info": project_info
                }
            else:
                print("⚠️  Repositorio creado pero no se pudo subir el código")
                return {"success": False, "message": "Error subiendo código a GitHub"}

        except Exception as e:
            logger.error(f"Error en flujo completo: {e}")
            return {"success": False, "message": f"Error: {str(e)}"}


def main():
    print("🤖 ¡Hola! Soy Herbie, tu asistente inteligente para crear repositorios de GitHub.")
    print("Puedo ayudarte a crear proyectos con diferentes frameworks y subirlos automáticamente.")
    print("Frameworks soportados:", ", ".join(FrameworkDatabase.FRAMEWORKS.keys()))

    try:
        print("\n¿Qué proyecto vamos a crear hoy?")
        user_input = input("📝 Describe tu proyecto: ")

        if not user_input.strip():
            print("❌ Por favor, describe el proyecto que quieres crear.")
            return

        agent = GitHubRepoCreator()
        result = agent.create_full_flow(user_input)

        if result["success"]:
            print(f"\n✨ ¡Proyecto creado exitosamente!")
            print(f"🔗 URL: {result['repo_url']}")
        else:
            print(f"\n❌ {result['message']}")

    except KeyboardInterrupt:
        print("\n\n👋 ¡Hasta luego!")
    except Exception as e:
        print(f"\n❌ Error inesperado: {e}")
        logger.error(f"Error en main: {e}")


if __name__ == "__main__":
    main()