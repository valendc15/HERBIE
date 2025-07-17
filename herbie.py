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


@dataclass
class ParsedInput:
    repo_name: Optional[str] = None
    description: Optional[str] = None
    is_private: Optional[bool] = None
    framework: Optional[str] = None
    missing_fields: List[str] = None
    confidence: float = 0.0
    assumptions: List[str] = None


@dataclass
class AIDecision:
    action: str
    confidence: float
    reasoning: str
    data: Dict = None


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
            },
            "description": "Framework JavaScript para crear interfaces de usuario interactivas"
        },
        "vue": {
            "commands": ["npm create vue@latest", "vue create"],
            "check_cmd": "node",
            "package_managers": ["npm", "yarn", "pnpm"],
            "install_instructions": {
                "windows": "Instala Node.js desde https://nodejs.org/",
                "linux": "sudo apt-get install nodejs npm",
                "darwin": "brew install node"
            },
            "description": "Framework JavaScript progresivo para crear aplicaciones web"
        },
        "angular": {
            "commands": ["ng new"],
            "check_cmd": "ng",
            "package_managers": ["npm", "yarn"],
            "install_instructions": {
                "windows": "npm install -g @angular/cli",
                "linux": "sudo npm install -g @angular/cli",
                "darwin": "npm install -g @angular/cli"
            },
            "description": "Framework TypeScript para crear aplicaciones web robustas"
        },
        "rails": {
            "commands": ["rails new"],
            "check_cmd": "rails",
            "package_managers": ["gem", "bundle"],
            "install_instructions": {
                "windows": "Instala Ruby desde https://rubyinstaller.org/",
                "linux": "sudo apt-get install ruby-full",
                "darwin": "brew install ruby"
            },
            "description": "Framework Ruby para desarrollo web rápido y elegante"
        },
        "django": {
            "commands": ["django-admin startproject"],
            "check_cmd": "django-admin",
            "package_managers": ["pip", "poetry"],
            "install_instructions": {
                "windows": "pip install django",
                "linux": "pip install django",
                "darwin": "pip install django"
            },
            "description": "Framework Python para desarrollo web con baterías incluidas"
        },
        "fastapi": {
            "commands": ["fastapi-cli new"],
            "check_cmd": "fastapi-cli",
            "package_managers": ["pip", "poetry"],
            "install_instructions": {
                "windows": "pip install fastapi-cli",
                "linux": "pip install fastapi-cli",
                "darwin": "pip install fastapi-cli"
            },
            "description": "Framework Python moderno para crear APIs rápidas y robustas"
        },
        "nextjs": {
            "commands": ["npx create-next-app@latest"],
            "check_cmd": "node",
            "package_managers": ["npm", "yarn", "pnpm"],
            "install_instructions": {
                "windows": "Instala Node.js desde https://nodejs.org/",
                "linux": "sudo apt-get install nodejs npm",
                "darwin": "brew install node"
            },
            "description": "Framework React para aplicaciones web con SSR y generación estática"
        },
        "flutter": {
            "commands": ["flutter create"],
            "check_cmd": "flutter",
            "package_managers": ["pub"],
            "install_instructions": {
                "windows": "Descarga Flutter SDK desde https://flutter.dev/docs/get-started/install/windows",
                "linux": "sudo snap install flutter --classic",
                "darwin": "brew install flutter"
            },
            "description": "Framework de Google para crear aplicaciones móviles multiplataforma"
        }
    }

    @classmethod
    def get_framework_info(cls, framework: str) -> Optional[Dict]:
        return cls.FRAMEWORKS.get(framework.lower())

    @classmethod
    def get_framework_names(cls) -> List[str]:
        return list(cls.FRAMEWORKS.keys())

    @classmethod
    def get_framework_description(cls, framework: str) -> str:
        info = cls.get_framework_info(framework)
        return info.get('description', 'Framework para desarrollo') if info else 'Framework desconocido'

    @classmethod
    def get_all_frameworks_info(cls) -> str:
        """Retorna información completa de todos los frameworks para la IA"""
        info = []
        for name, data in cls.FRAMEWORKS.items():
            info.append(f"- {name}: {data['description']}")
        return "\n".join(info)


class AIIntelligenceCore:
    """Núcleo de inteligencia artificial para todas las decisiones del agente"""

    def __init__(self, llm):
        self.llm = llm
        self.system_context = {
            "frameworks": FrameworkDatabase.get_all_frameworks_info(),
            "framework_names": FrameworkDatabase.get_framework_names(),
            "os": platform.system().lower(),
            "agent_name": "Herbie",
            "agent_personality": "friendly, intelligent, helpful, expressive, creative"
        }

    def analyze_user_intent(self, user_input: str, conversation_history: List[Dict] = None) -> AIDecision:
        """Analizar la intención del usuario usando IA"""

        history_context = ""
        if conversation_history:
            recent_history = conversation_history[-3:]  # Últimos 3 mensajes
            history_context = "\n".join([f"{msg['role']}: {msg['content']}" for msg in recent_history])

        prompt = f"""
Eres {self.system_context['agent_name']}, un agente inteligente especializado en crear repositorios de GitHub.

Historial de conversación reciente:
{history_context}

Mensaje actual del usuario: "{user_input}"

Contexto disponible:
- Frameworks disponibles: {self.system_context['framework_names']}
- Personalidad del agente: {self.system_context['agent_personality']}

Analiza la intención del usuario y responde con JSON:
{{
  "intent": "crear_proyecto|confirmar_proyecto|modificar_proyecto|cancelar_proyecto|conversacion_general|ayuda|saludo|agradecimiento|despedida|unclear",
  "confidence": 0.0-1.0,
  "reasoning": "explicación detallada de por qué clasificaste así la intención",
  "context_clues": ["lista", "de", "pistas", "contextuales", "que", "usaste"],
  "emotional_tone": "neutral|excited|confused|frustrated|happy|etc",
  "needs_clarification": true/false
}}

Sé muy inteligente para detectar intenciones sutiles, contexto emocional, y matices del lenguaje.
"""

        try:
            response = self.llm.invoke([HumanMessage(content=prompt)])
            content = response.content.strip()

            start = content.find('{')
            end = content.rfind('}') + 1
            json_str = content[start:end]
            data = json.loads(json_str)

            return AIDecision(
                action=data.get('intent', 'unclear'),
                confidence=data.get('confidence', 0.0),
                reasoning=data.get('reasoning', ''),
                data=data
            )

        except Exception as e:
            logger.error(f"Error en análisis de intención: {e}")
            return AIDecision(
                action='unclear',
                confidence=0.0,
                reasoning=f"Error procesando: {str(e)}",
                data={}
            )

    def parse_project_requirements(self, user_input: str) -> ParsedInput:
        """Parsear y inferir requerimientos del proyecto usando IA"""

        prompt = f"""
Eres un experto en análisis de requerimientos de proyectos de software.

Mensaje del usuario: "{user_input}"

Frameworks disponibles:
{self.system_context['frameworks']}

Tu tarea es extraer e inferir información inteligentemente:

1. Si mencionan conceptos vagos, haz inferencias inteligentes:
   - "web app", "sitio", "página" → React
   - "API", "backend", "microservicio" → FastAPI
   - "app móvil", "mobile" → Flutter
   - "e-commerce", "tienda" → Next.js

2. Si no especifican privacidad, asume público por defecto

3. Genera nombres creativos pero descriptivos si no se especifica

4. Crea descripciones atractivas basadas en el contexto

Responde con JSON:
{{
  "repo_name": "nombre-generado-o-extraido",
  "description": "descripción-atractiva-generada",
  "is_private": true/false,
  "framework": "framework-elegido",
  "confidence": 0.0-1.0,
  "assumptions": ["lista", "de", "suposiciones", "hechas"],
  "missing_critical_info": ["lista", "de", "info", "crítica", "faltante"],
  "inferred_project_type": "web|mobile|api|desktop|etc",
  "creativity_level": 0.0-1.0
}}

Sé creativo, inteligente y haz suposiciones razonables.
"""

        try:
            response = self.llm.invoke([HumanMessage(content=prompt)])
            content = response.content.strip()

            start = content.find('{')
            end = content.rfind('}') + 1
            json_str = content[start:end]
            data = json.loads(json_str)

            return ParsedInput(
                repo_name=data.get('repo_name'),
                description=data.get('description'),
                is_private=data.get('is_private', False),
                framework=data.get('framework'),
                confidence=data.get('confidence', 0.0),
                assumptions=data.get('assumptions', []),
                missing_fields=data.get('missing_critical_info', [])
            )

        except Exception as e:
            logger.error(f"Error parseando requerimientos: {e}")
            return ParsedInput(
                repo_name="mi-proyecto-increible",
                description="Un proyecto increíble creado con Herbie",
                is_private=False,
                framework="react",
                confidence=0.3,
                assumptions=["Fallback por error en IA"],
                missing_fields=["confirmation"]
            )

    def analyze_project_confirmation(self, user_input: str, project_data: Dict) -> AIDecision:
        """Analizar respuesta de confirmación del proyecto"""

        prompt = f"""
El usuario tiene un proyecto pendiente:
- Nombre: {project_data.get('repo_name')}
- Framework: {project_data.get('framework')}
- Privacidad: {'Privado' if project_data.get('is_private') else 'Público'}
- Descripción: {project_data.get('description')}

Respuesta del usuario: "{user_input}"

Analiza qué quiere hacer. Responde con JSON:
{{
  "action": "confirm|modify|cancel|need_clarification",
  "confidence": 0.0-1.0,
  "reasoning": "explicación detallada de la interpretación",
  "emotional_response": "como debería responder emocionalmente",
  "specific_field_to_modify": "repo_name|framework|is_private|description|null",
  "new_value": "valor-nuevo-si-aplica",
  "user_sentiment": "positive|negative|neutral|confused"
}}

Considera:
- Confirmaciones pueden ser creativas: emojis, diferentes idiomas, expresiones únicas
- Modificaciones pueden ser sutiles: "mejor que sea privado", "cambia a Vue"
- Cancelaciones pueden ser indirectas: "no me gusta", "mejor no"
- Detecta frustración o confusión para responder apropiadamente

Sé muy inteligente para detectar matices y contexto emocional.
"""

        try:
            response = self.llm.invoke([HumanMessage(content=prompt)])
            content = response.content.strip()

            start = content.find('{')
            end = content.rfind('}') + 1
            json_str = content[start:end]
            data = json.loads(json_str)

            return AIDecision(
                action=data.get('action', 'need_clarification'),
                confidence=data.get('confidence', 0.0),
                reasoning=data.get('reasoning', ''),
                data=data
            )

        except Exception as e:
            logger.error(f"Error analizando confirmación: {e}")
            return AIDecision(
                action='need_clarification',
                confidence=0.0,
                reasoning=f"Error procesando: {str(e)}",
                data={}
            )

    def generate_response(self, intent: str, context: Dict, user_input: str) -> str:
        """Generar respuesta personalizada usando IA"""

        prompt = f"""
Eres Herbie, un agente inteligente para crear repositorios de GitHub.

Personalidad: {self.system_context['agent_personality']}

Contexto de la situación:
- Intención detectada: {intent}
- Mensaje del usuario: "{user_input}"
- Contexto adicional: {json.dumps(context, indent=2)}

Frameworks disponibles:
{self.system_context['frameworks']}

Intenciones especiales a manejar:
- ask_local_initialization: Preguntar si quiere inicializar el framework localmente
- project_creation_success_with_local: Éxito creando repo + código local
- project_creation_partial_success_with_local: Repo creado, código local listo, problemas subiendo
- project_creation_success_repo_only: Solo repositorio creado, sin código local
- framework_setup_failed: Error configurando framework (incluir repo_url si existe)

Genera una respuesta que sea:
1. Acorde a tu personalidad (amigable, inteligente, expresiva)
2. Contextualmente apropiada
3. Útil y accionable
4. Con emojis y formato atractivo
5. Que mantenga el flujo conversacional

Para "ask_local_initialization": pregunta si quiere inicializar el framework localmente después de crear el repo
Para intenciones de éxito: incluye información relevante como URLs, paths locales, próximos pasos
Para errores: sé empático pero positivo, ofrece soluciones

Responde directamente con el texto de la respuesta, NO con JSON.
Usa markdown para formato cuando sea apropiado.
"""

        try:
            response = self.llm.invoke([HumanMessage(content=prompt)])
            return response.content.strip()

        except Exception as e:
            logger.error(f"Error generando respuesta: {e}")
            return f"🤔 Hmm, tuve un problemilla técnico procesando tu mensaje. ¿Podrías intentar de nuevo? {str(e)}"

    def generate_project_summary(self, project_data: Dict) -> str:
        """Generar resumen del proyecto usando IA"""

        prompt = f"""
Eres Herbie, un agente entusiasta para crear proyectos.

Datos del proyecto:
{json.dumps(project_data, indent=2)}

Framework info: {FrameworkDatabase.get_framework_description(project_data.get('framework', 'unknown'))}

Genera un resumen atractivo y profesional del proyecto que incluya:
1. Título llamativo
2. Detalles del proyecto con emojis
3. Descripción del framework elegido
4. Opciones claras para confirmar o modificar
5. Tono entusiasta pero profesional

Usa formato markdown y emojis. Responde directamente con el texto.
"""

        try:
            response = self.llm.invoke([HumanMessage(content=prompt)])
            return response.content.strip()

        except Exception as e:
            logger.error(f"Error generando resumen: {e}")
            return f"📋 Resumen del proyecto: {project_data.get('repo_name', 'mi-proyecto')}"


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
        """Genera explicación detallada sobre dependencias faltantes usando IA"""
        framework_info = FrameworkDatabase.get_framework_info(framework)
        if not framework_info:
            return "Framework no reconocido. Verifique el nombre del framework."

        system = self.system_info["os"]
        install_cmd = framework_info["install_instructions"].get(system, "Consulte la documentación oficial")

        prompt = f"""
Eres un profesor experto en ingeniería de software y desarrollo.

Situación:
- Framework: {framework}
- Sistema operativo: {system}
- Comando de instalación: {install_cmd}
- Info del framework: {json.dumps(framework_info, indent=2)}

Genera una explicación clara, educativa y profesional que incluya:
1. Explicación del problema de manera amigable
2. Pasos específicos de instalación para {system}
3. Comandos exactos a ejecutar
4. Cómo verificar instalación exitosa
5. Problemas comunes y soluciones
6. Tono profesional pero accesible

Usa formato markdown y emojis apropiados.
"""

        try:
            response = self.llm.invoke([HumanMessage(content=prompt)])
            return response.content.strip()
        except Exception as e:
            logger.error(f"Error explicando dependencia: {e}")
            return f"Necesitas instalar {framework}. Comando sugerido: {install_cmd}"

    def generate_install_md(self, framework: str, project_name: str) -> str:
        """Genera archivo INSTALL.md completo usando IA"""
        framework_info = FrameworkDatabase.get_framework_info(framework)
        system = self.system_info["os"]

        prompt = f"""
Eres un experto en documentación técnica.

Crea un archivo INSTALL.md profesional y completo para:
- Proyecto: {project_name}
- Framework: {framework}
- Sistema: {system}
- Info del framework: {json.dumps(framework_info, indent=2)}

El archivo debe incluir:
1. Título atractivo y descripción del proyecto
2. Tabla de contenidos
3. Requisitos del sistema
4. Instalación paso a paso
5. Configuración del entorno
6. Comandos para ejecutar
7. Solución de problemas
8. Recursos adicionales
9. Licencia y contribuciones

Usa formato Markdown profesional con emojis apropiados.
Hazlo completo, útil y fácil de seguir.
"""

        try:
            response = self.llm.invoke([HumanMessage(content=prompt)])
            return response.content.strip()
        except Exception as e:
            logger.error(f"Error generando INSTALL.md: {e}")
            return f"# Instalación de {project_name}\n\nFramework: {framework}\nSistema: {system}"

    def init_framework_project(self, project_info: ProjectInfo) -> Dict:
        """Inicializa proyecto con el framework especificado"""
        logger.info(f"Iniciando proyecto {project_info.repo_name} con framework {project_info.framework}")

        # Verificar requisitos
        requirements_check = self.check_framework_requirements(project_info.framework)
        if not requirements_check["available"]:
            return {
                "success": False,
                "message": self.explain_missing_dependency(project_info.framework),
                "install_md": self.generate_install_md(project_info.framework, project_info.repo_name)
            }

        # Ejecutar comando de inicialización
        try:
            logger.info(f"Ejecutando: {project_info.init_command}")
            result = subprocess.run(
                project_info.init_command.split(),
                check=True,
                capture_output=True,
                text=True,
                timeout=300
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
            temperature=0.3
        )

        self.headers = {
            'Authorization': f'token {self.github_token}',
            'Accept': 'application/vnd.github.v3+json',
            'Content-Type': 'application/json'
        }

        self.framework_helper = HerbieFrameworkHelper(self.llm)
        self.username = self._get_username()
        self.ai_core = AIIntelligenceCore(self.llm)

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

    def create_project_info(self, parsed_input: ParsedInput) -> ProjectInfo:
        """Convierte ParsedInput a ProjectInfo con comandos de inicialización usando IA"""

        # Usar IA para generar el comando de inicialización más apropiado
        prompt = f"""
Eres un experto en frameworks de desarrollo.

Datos del proyecto:
- Nombre: {parsed_input.repo_name}
- Framework: {parsed_input.framework}
- Descripción: {parsed_input.description}

Framework disponible: {FrameworkDatabase.get_framework_info(parsed_input.framework)}

Genera el comando de inicialización más apropiado para este framework.

Responde con JSON:
{{
  "init_command": "comando-completo-de-inicializacion",
  "additional_setup": ["comando1", "comando2"] o null,
  "reasoning": "explicación de por qué elegiste este comando"
}}

Considera:
- Usar las mejores prácticas para cada framework
- Incluir configuraciones recomendadas
- Comandos adicionales si son necesarios (instalación de dependencias, etc.)
"""

        try:
            response = self.repo_creator.llm.invoke([HumanMessage(content=prompt)])
            content = response.content.strip()

            start = content.find('{')
            end = content.rfind('}') + 1
            json_str = content[start:end]
            data = json.loads(json_str)

            init_command = data.get('init_command',
                                    self._get_default_init_command(parsed_input.framework, parsed_input.repo_name))
            additional_setup = data.get('additional_setup')

        except Exception as e:
            logger.error(f"Error generando comando de inicialización: {e}")
            init_command = self._get_default_init_command(parsed_input.framework, parsed_input.repo_name)
            additional_setup = None

        return ProjectInfo(
            repo_name=parsed_input.repo_name,
            description=parsed_input.description,
            is_private=parsed_input.is_private,
            framework=parsed_input.framework,
            init_command=init_command,
            additional_setup=additional_setup
        )

    def _get_default_init_command(self, framework: str, repo_name: str) -> str:
        """Comando de inicialización por defecto como fallback"""
        if framework == "react":
            return f"npx create-react-app {repo_name}"
        elif framework == "vue":
            return f"npm create vue@latest {repo_name}"
        elif framework == "angular":
            return f"ng new {repo_name} --routing --style=css"
        elif framework == "nextjs":
            return f"npx create-next-app@latest {repo_name}"
        elif framework == "django":
            return f"django-admin startproject {repo_name}"
        elif framework == "fastapi":
            return f"mkdir {repo_name}"
        elif framework == "rails":
            return f"rails new {repo_name}"
        elif framework == "flutter":
            return f"flutter create {repo_name}"
        else:
            return f"mkdir {repo_name}"

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
            subprocess.run(["git", "config", "user.name", self.username], check=True)
            subprocess.run(["git", "config", "user.email", f"{self.username}@users.noreply.github.com"], check=True)
            logger.info("Configuración de Git establecida")
        except Exception as e:
            logger.warning(f"No se pudo configurar Git: {e}")

    def push_local_to_repo(self, repo_name: str) -> bool:
        """Sube código local a repositorio GitHub"""
        try:
            if not os.path.exists(repo_name):
                logger.error(f"Directorio {repo_name} no existe")
                return False

            original_dir = os.getcwd()
            os.chdir(repo_name)

            self._setup_git_config()

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
                log_cmd = cmd.copy()
                if len(log_cmd) > 2 and "github.com" in log_cmd[2]:
                    log_cmd[2] = log_cmd[2].replace(self.github_token, "***TOKEN***")

                logger.info(f"Ejecutando: {' '.join(log_cmd)}")

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

            for root, dirs, files in os.walk(repo_name):
                dirs[:] = [d for d in dirs if not d.startswith('.') and d != 'node_modules']

                for file in files:
                    if file.startswith('.'):
                        continue

                    file_path = os.path.join(root, file)
                    relative_path = os.path.relpath(file_path, repo_name)

                    try:
                        with open(file_path, 'rb') as f:
                            content = f.read()

                        encoded_content = base64.b64encode(content).decode('utf-8')

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


class HerbieAgent:
    """Agente inteligente completamente basado en IA"""

    def __init__(self):
        self.repo_creator = GitHubRepoCreator()
        self.ai_core = self.repo_creator.ai_core
        self.conversation_history = []
        self.pending_project = None
        self.user_context = {}

    def chat(self, user_input: str) -> str:
        """Manejar conversación completamente con IA"""

        # Añadir al historial
        self.conversation_history.append({"role": "user", "content": user_input})

        try:
            # Analizar intención con IA
            intent_analysis = self.ai_core.analyze_user_intent(user_input, self.conversation_history)

            logger.info(f"Intención detectada: {intent_analysis.action} (confianza: {intent_analysis.confidence})")

            # Enrutar según la intención
            if intent_analysis.action == "crear_proyecto":
                return self._handle_project_creation(user_input, intent_analysis)
            elif intent_analysis.action == "confirmar_proyecto":
                return self._handle_project_confirmation(user_input, intent_analysis)
            elif intent_analysis.action == "modificar_proyecto":
                return self._handle_project_modification(user_input, intent_analysis)
            elif intent_analysis.action == "cancelar_proyecto":
                return self._handle_project_cancellation(user_input, intent_analysis)
            else:
                return self._handle_general_conversation(user_input, intent_analysis)

        except Exception as e:
            logger.error(f"Error en chat: {e}")
            response = self.ai_core.generate_response(
                intent="error",
                context={"error": str(e), "user_input": user_input},
                user_input=user_input
            )
            self.conversation_history.append({"role": "assistant", "content": response})
            return response

    def _handle_project_creation(self, user_input: str, intent_analysis: AIDecision) -> str:
        """Manejar creación de proyecto completamente con IA"""

        # Parsear requerimientos con IA
        parsed_input = self.ai_core.parse_project_requirements(user_input)

        # Almacenar como proyecto pendiente
        self.pending_project = {
            'repo_name': parsed_input.repo_name,
            'framework': parsed_input.framework,
            'is_private': parsed_input.is_private,
            'description': parsed_input.description,
            'confidence': parsed_input.confidence,
            'assumptions': parsed_input.assumptions
        }

        # Generar resumen del proyecto con IA
        summary = self.ai_core.generate_project_summary(self.pending_project)

        self.conversation_history.append({"role": "assistant", "content": summary})
        return summary

    def _handle_project_confirmation(self, user_input: str, intent_analysis: AIDecision) -> str:
        """Manejar confirmación del proyecto con IA"""

        if not self.pending_project:
            response = self.ai_core.generate_response(
                intent="no_pending_project",
                context={},
                user_input=user_input
            )
            self.conversation_history.append({"role": "assistant", "content": response})
            return response

        # Ejecutar creación del proyecto
        return self._execute_project_creation()

    def _handle_project_modification(self, user_input: str, intent_analysis: AIDecision) -> str:
        """Manejar modificación del proyecto con IA"""

        if not self.pending_project:
            response = self.ai_core.generate_response(
                intent="no_pending_project",
                context={},
                user_input=user_input
            )
            self.conversation_history.append({"role": "assistant", "content": response})
            return response

        # Analizar qué quiere modificar
        modification_analysis = self.ai_core.analyze_project_confirmation(user_input, self.pending_project)

        if modification_analysis.confidence > 0.6 and modification_analysis.data.get('specific_field_to_modify'):
            # Aplicar modificación
            field = modification_analysis.data['specific_field_to_modify']
            new_value = modification_analysis.data.get('new_value')

            if field == 'repo_name' and new_value:
                self.pending_project['repo_name'] = new_value.lower().replace(' ', '-')
            elif field == 'framework' and new_value:
                if new_value.lower() in FrameworkDatabase.get_framework_names():
                    self.pending_project['framework'] = new_value.lower()
                    self.pending_project['description'] = f"Proyecto {new_value} creado con Herbie"
                else:
                    return self.ai_core.generate_response(
                        intent="invalid_framework",
                        context={"requested_framework": new_value,
                                 "available_frameworks": FrameworkDatabase.get_framework_names()},
                        user_input=user_input
                    )
            elif field == 'is_private' and new_value:
                # Usar IA para determinar si quiere privado o público
                privacy_prompt = f"El usuario dijo: '{new_value}'. ¿Quiere que el repositorio sea privado o público? Responde solo 'privado' o 'publico'."
                try:
                    privacy_response = self.repo_creator.llm.invoke([HumanMessage(content=privacy_prompt)])
                    self.pending_project['is_private'] = 'privado' in privacy_response.content.lower()
                except:
                    self.pending_project['is_private'] = True  # Default a privado si hay error
            elif field == 'description' and new_value:
                self.pending_project['description'] = new_value

            # Generar nuevo resumen
            summary = self.ai_core.generate_project_summary(self.pending_project)
            self.conversation_history.append({"role": "assistant", "content": summary})
            return summary
        else:
            # Pedir aclaración
            response = self.ai_core.generate_response(
                intent="need_clarification",
                context={"modification_analysis": modification_analysis.data},
                user_input=user_input
            )
            self.conversation_history.append({"role": "assistant", "content": response})
            return response

    def _handle_project_cancellation(self, user_input: str, intent_analysis: AIDecision) -> str:
        """Manejar cancelación del proyecto con IA"""

        self.pending_project = None

        response = self.ai_core.generate_response(
            intent="project_cancelled",
            context={"reason": intent_analysis.reasoning},
            user_input=user_input
        )

        self.conversation_history.append({"role": "assistant", "content": response})
        return response

    def _handle_general_conversation(self, user_input: str, intent_analysis: AIDecision) -> str:
        """Manejar conversación general con IA"""

        response = self.ai_core.generate_response(
            intent=intent_analysis.action,
            context={
                "intent_data": intent_analysis.data,
                "frameworks": FrameworkDatabase.get_framework_names(),
                "conversation_history": self.conversation_history[-3:] if len(
                    self.conversation_history) > 3 else self.conversation_history
            },
            user_input=user_input
        )

        self.conversation_history.append({"role": "assistant", "content": response})
        return response

    def _execute_project_creation(self) -> str:
        """Ejecutar la creación del proyecto"""
        if not self.pending_project:
            return "❌ No hay proyecto pendiente para crear."

        try:
            # Generar mensaje de inicio usando IA
            start_message = self.ai_core.generate_response(
                intent="starting_project_creation",
                context={"project": self.pending_project},
                user_input="iniciando creación"
            )
            print(start_message)

            # Convertir a ProjectInfo
            parsed_input = ParsedInput(
                repo_name=self.pending_project['repo_name'],
                description=self.pending_project['description'],
                is_private=self.pending_project['is_private'],
                framework=self.pending_project['framework'],
                missing_fields=[]
            )

            project_info = self.repo_creator.create_project_info(parsed_input)

            # Crear repositorio primero
            print("☁️ Creando repositorio en GitHub...")
            repo = self.repo_creator.create_repository(project_info)
            if not repo:
                self.pending_project = None
                return self.ai_core.generate_response(
                    intent="github_repo_creation_failed",
                    context={"project": project_info.__dict__},
                    user_input="error creando repositorio"
                )

            # Preguntar si quiere inicializar el framework localmente
            local_init_question = self.ai_core.generate_response(
                intent="ask_local_initialization",
                context={
                    "project": project_info.__dict__,
                    "repo_url": repo['html_url']
                },
                user_input="preguntar inicialización local"
            )

            print(f"\n🤖 Herbie: {local_init_question}")

            # Obtener respuesta del usuario
            user_response = input("\n💬 Tú: ").strip()

            # Analizar respuesta con IA
            local_init_analysis = self.ai_core.analyze_user_intent(user_response, self.conversation_history)

            final_response = ""

            if local_init_analysis.action in ["confirmar_proyecto",
                                              "crear_proyecto"] and local_init_analysis.confidence > 0.6:
                # Usuario quiere inicializar localmente
                print("🔧 Inicializando proyecto localmente...")
                framework_result = self.repo_creator.framework_helper.init_framework_project(project_info)

                if not framework_result['success']:
                    error_response = self.ai_core.generate_response(
                        intent="framework_setup_failed",
                        context={
                            "error_message": framework_result['message'],
                            "project": project_info.__dict__,
                            "repo_url": repo['html_url']
                        },
                        user_input="error de framework"
                    )

                    # Generar archivo de instalación si está disponible
                    if 'install_md' in framework_result:
                        install_file = f"INSTALL_{project_info.repo_name}.md"
                        with open(install_file, "w", encoding="utf-8") as f:
                            f.write(framework_result['install_md'])
                        error_response += f"\n\n📄 He creado un archivo de instalación: {install_file}"

                    final_response = error_response
                else:
                    # Subir código al repositorio
                    print("📤 Subiendo código al repositorio...")
                    upload_success = self.repo_creator.push_local_to_repo(project_info.repo_name)
                    if not upload_success:
                        upload_success = self.repo_creator.push_local_to_repo_alternative(project_info.repo_name)

                    if upload_success:
                        final_response = self.ai_core.generate_response(
                            intent="project_creation_success_with_local",
                            context={
                                "project": project_info.__dict__,
                                "repo_url": repo['html_url'],
                                "clone_url": repo['clone_url'],
                                "local_path": os.path.abspath(project_info.repo_name)
                            },
                            user_input="proyecto creado exitosamente con código local"
                        )
                    else:
                        final_response = self.ai_core.generate_response(
                            intent="project_creation_partial_success_with_local",
                            context={
                                "project": project_info.__dict__,
                                "repo_url": repo['html_url'],
                                "local_path": os.path.abspath(project_info.repo_name)
                            },
                            user_input="proyecto creado con problemas de subida pero código local listo"
                        )
            else:
                # Usuario no quiere inicializar localmente
                final_response = self.ai_core.generate_response(
                    intent="project_creation_success_repo_only",
                    context={
                        "project": project_info.__dict__,
                        "repo_url": repo['html_url'],
                        "clone_url": repo['clone_url']
                    },
                    user_input="repositorio creado sin código local"
                )

            # Limpiar proyecto pendiente
            self.pending_project = None

            self.conversation_history.append({"role": "assistant", "content": final_response})
            return final_response

        except Exception as e:
            logger.error(f"Error ejecutando creación: {e}")
            self.pending_project = None

            error_response = self.ai_core.generate_response(
                intent="unexpected_error",
                context={"error": str(e)},
                user_input="error inesperado"
            )

            self.conversation_history.append({"role": "assistant", "content": error_response})
            return error_response


def main():
    """Función principal para interactuar con el usuario"""

    # Generar mensaje de bienvenida con IA
    try:
        agent = HerbieAgent()

        welcome_message = agent.ai_core.generate_response(
            intent="welcome_message",
            context={"frameworks": FrameworkDatabase.get_framework_names()},
            user_input="bienvenida"
        )

        print("🤖 Herbie - Agente Inteligente para GitHub")
        print("=" * 50)
        print(f"\n{welcome_message}")

        while True:
            user_input = input("\n💬 Tú: ").strip()

            # Analizar si quiere salir usando IA
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
                prompt_response = agent.ai_core.generate_response(
                    intent="empty_input",
                    context={},
                    user_input=""
                )
                print(f"🤖 Herbie: {prompt_response}")
                continue

            print()
            response = agent.chat(user_input)
            print(f"🤖 Herbie: {response}")

    except KeyboardInterrupt:
        print("\n\n👋 ¡Hasta luego! Que tengas un día increíble! 🌟")
    except Exception as e:
        print(f"\n❌ Error inicializando Herbie: {e}")
        print("\n🔧 Asegúrate de tener configurado:")
        print("   • GITHUB_TOKEN: Token de GitHub con permisos de repositorio")
        print("   • GOOGLE_API_KEY: API key de Google Generative AI")


if __name__ == "__main__":
    main()