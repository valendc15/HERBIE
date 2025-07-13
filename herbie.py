import os
import requests
import json
from dotenv import load_dotenv
from langchain.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import HumanMessage, SystemMessage
from langchain.prompts import PromptTemplate
import base64

# Cargar variables de entorno
load_dotenv()


class GitHubRepoCreator:
    def __init__(self):
        # Configurar API keys
        self.github_token = os.getenv('GITHUB_TOKEN')
        self.google_api_key = os.getenv('GOOGLE_API_KEY')

        if not self.github_token:
            raise ValueError("GITHUB_TOKEN no encontrado en las variables de entorno")
        if not self.google_api_key:
            raise ValueError("GOOGLE_API_KEY no encontrado en las variables de entorno")

        # Inicializar el modelo de Google Generative AI
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash",
            google_api_key=self.google_api_key,
            temperature=0.7
        )

        # Headers para GitHub API
        self.headers = {
            'Authorization': f'token {self.github_token}',
            'Accept': 'application/vnd.github.v3+json',
            'Content-Type': 'application/json'
        }

    def generate_readme(self, project_description, repo_name):
        """Generar README.md usando Google Generative AI"""

        prompt = f"""
        Genera un README.md profesional y completo para un proyecto de GitHub con las siguientes características:

        Nombre del repositorio: {repo_name}
        Descripción del proyecto: {project_description}

        El README debe incluir:
        1. Título del proyecto
        2. Descripción clara y concisa
        3. Características principales
        4. Instalación (si aplica)
        5. Uso básico (si aplica)
        6. Contribuciones
        7. Licencia
        8. Contacto/Autor

        Usa formato Markdown y hazlo profesional pero accesible. 
        Adapta el contenido según el tipo de proyecto que describas.
        Responde únicamente con el contenido del README en formato Markdown.
        """

        try:
            response = self.llm.invoke([HumanMessage(content=prompt)])
            return response.content
        except Exception as e:
            print(f"Error generando README: {e}")
            return self._default_readme(repo_name, project_description)

    def _default_readme(self, repo_name, description):
        """README básico en caso de error"""
        return f"""# {repo_name}

## Descripción
{description}

## Instalación
```bash
git clone https://github.com/tu-usuario/{repo_name}.git
cd {repo_name}
```

## Uso
Describe aquí cómo usar el proyecto.

## Contribuciones
Las contribuciones son bienvenidas. Por favor, abre un issue primero para discutir los cambios.

## Licencia
Este proyecto está bajo la Licencia MIT.
"""

    def create_repository(self, repo_name, description, is_private=False):
        """Crear repositorio en GitHub"""

        url = "https://api.github.com/user/repos"

        data = {
            "name": repo_name,
            "description": description,
            "private": is_private,
            "has_issues": True,
            "has_projects": True,
            "has_wiki": True,
            "auto_init": False
        }

        try:
            response = requests.post(url, headers=self.headers, json=data)

            if response.status_code == 201:
                repo_data = response.json()
                print(f"✅ Repositorio '{repo_name}' creado exitosamente!")
                print(f"URL: {repo_data['html_url']}")
                return repo_data
            else:
                print(f"❌ Error creando repositorio: {response.status_code}")
                print(f"Respuesta: {response.text}")
                return None

        except Exception as e:
            print(f"❌ Error en la solicitud: {e}")
            return None

    def upload_readme(self, repo_name, readme_content):
        """Subir README.md al repositorio"""

        # Obtener información del usuario
        user_response = requests.get("https://api.github.com/user", headers=self.headers)
        if user_response.status_code != 200:
            print("❌ Error obteniendo información del usuario")
            return False

        username = user_response.json()['login']

        # URL para crear el archivo README
        url = f"https://api.github.com/repos/{username}/{repo_name}/contents/README.md"

        # Codificar el contenido en base64
        encoded_content = base64.b64encode(readme_content.encode()).decode()

        data = {
            "message": "Add README.md",
            "content": encoded_content
        }

        try:
            response = requests.put(url, headers=self.headers, json=data)

            if response.status_code == 201:
                print("✅ README.md subido exitosamente!")
                return True
            else:
                print(f"❌ Error subiendo README: {response.status_code}")
                print(f"Respuesta: {response.text}")
                return False

        except Exception as e:
            print(f"❌ Error subiendo README: {e}")
            return False


class GitHubAgent:
    def __init__(self):
        self.repo_creator = GitHubRepoCreator()
        self.conversation_history = []

    def parse_user_input(self, user_input):
        """Analizar y extraer información del input del usuario"""

        analysis_prompt = f"""
        Analiza el siguiente mensaje del usuario y extrae la información para crear un repositorio de GitHub:

        Mensaje: "{user_input}"

        Extrae:
        1. Nombre del repositorio
        2. Si debe ser privado o público
        3. Descripción del proyecto

        Responde en formato JSON exacto:
        {{
            "repo_name": "nombre_del_repositorio",
            "is_private": true/false,
            "description": "descripción detallada del proyecto"
        }}

        Si la información no está clara, haz suposiciones razonables.
        Si no se especifica privacidad, asume que es público.
        """

        try:
            response = self.repo_creator.llm.invoke([HumanMessage(content=analysis_prompt)])

            # Limpiar la respuesta para extraer solo el JSON
            content = response.content.strip()

            # Buscar el JSON en la respuesta
            start = content.find('{')
            end = content.rfind('}') + 1

            if start != -1 and end != -1:
                json_str = content[start:end]
                return json.loads(json_str)
            else:
                # Si no se encuentra JSON, parsear manualmente
                return self._manual_parse(user_input)

        except Exception as e:
            print(f"Error analizando input: {e}")
            return self._manual_parse(user_input)

    def _manual_parse(self, user_input):
        """Parseo manual básico como fallback"""

        # Convertir a minúsculas para análisis
        lower_input = user_input.lower()

        # Determinar si es privado
        is_private = "privado" in lower_input or "private" in lower_input

        # Extraer nombre del repositorio (buscar patrones comunes)
        repo_name = "mi-proyecto"
        words = user_input.split()
        for i, word in enumerate(words):
            if word.lower() in ["llamado", "named", "nombre", "repositorio"]:
                if i + 1 < len(words):
                    repo_name = words[i + 1].strip('"\'')
                    break

        return {
            "repo_name": repo_name,
            "is_private": is_private,
            "description": user_input
        }

    def create_repository_workflow(self, repo_info):
        """Workflow completo para crear repositorio"""

        try:
            # Crear el repositorio
            repo_data = self.repo_creator.create_repository(
                repo_info["repo_name"],
                repo_info["description"],
                repo_info["is_private"]
            )

            if not repo_data:
                return "❌ Error creando el repositorio en GitHub"

            # Generar README
            print("🔄 Generando README.md...")
            readme_content = self.repo_creator.generate_readme(
                repo_info["description"],
                repo_info["repo_name"]
            )

            # Subir README
            print("📤 Subiendo README.md...")
            success = self.repo_creator.upload_readme(
                repo_info["repo_name"],
                readme_content
            )

            if success:
                privacy_text = "privado" if repo_info["is_private"] else "público"
                return f"""✅ ¡Repositorio creado exitosamente!

📁 Nombre: {repo_info["repo_name"]}
🔒 Tipo: {privacy_text}
📝 README.md: Generado y subido
🌐 URL: https://github.com/{self._get_username()}/{repo_info["repo_name"]}

El README ha sido generado automáticamente basándose en tu descripción del proyecto."""
            else:
                return f"✅ Repositorio '{repo_info['repo_name']}' creado, pero hubo un error subiendo el README"

        except Exception as e:
            return f"❌ Error en el proceso: {str(e)}"

    def _get_username(self):
        """Obtener el username de GitHub"""
        try:
            response = requests.get("https://api.github.com/user", headers=self.repo_creator.headers)
            if response.status_code == 200:
                return response.json()['login']
            else:
                return "tu-usuario"
        except:
            return "tu-usuario"

    def chat(self, user_input):
        """Manejar conversación con el usuario"""

        # Añadir al historial
        self.conversation_history.append({"role": "user", "content": user_input})

        # Analizar si el usuario quiere crear un repositorio
        create_keywords = ["crea", "crear", "nuevo", "repositorio", "repo", "github"]

        if any(keyword in user_input.lower() for keyword in create_keywords):
            # Procesar creación de repositorio
            print("🔄 Analizando tu solicitud...")
            repo_info = self.parse_user_input(user_input)

            print(f"📋 Información extraída:")
            print(f"   - Nombre: {repo_info['repo_name']}")
            print(f"   - Tipo: {'Privado' if repo_info['is_private'] else 'Público'}")
            print(f"   - Descripción: {repo_info['description'][:100]}...")

            # Confirmar con el usuario
            confirm = input("\n¿Confirmas la creación? (s/n): ").lower().strip()

            if confirm in ['s', 'si', 'y', 'yes']:
                response = self.create_repository_workflow(repo_info)
            else:
                response = "❌ Creación cancelada. Puedes intentar de nuevo con otra descripción."
        else:
            # Respuesta conversacional general
            response = self._general_response(user_input)

        # Añadir respuesta al historial
        self.conversation_history.append({"role": "assistant", "content": response})

        return response

    def _general_response(self, user_input):
        """Respuesta conversacional general"""

        help_keywords = ["ayuda", "help", "como", "qué puedes hacer"]

        if any(keyword in user_input.lower() for keyword in help_keywords):
            return """🤖 ¡Hola! Soy tu asistente para crear repositorios de GitHub.

Puedo ayudarte a:
✅ Crear repositorios públicos o privados
✅ Generar README.md automáticamente
✅ Subir el README a tu repositorio

Solo dime algo como:
• "Crea un repositorio público llamado 'mi-web-app' para una aplicación web de tareas"
• "Necesito un repo privado 'proyecto-secreto' que es un sistema de gestión"
• "Haz un repositorio 'mi-blog' para un blog personal con React"

¿Qué repositorio quieres crear hoy?"""

        return """No estoy seguro de qué quieres hacer. 

Puedo ayudarte a crear repositorios de GitHub. Solo dime:
- Nombre del repositorio
- Si debe ser privado o público  
- De qué se trata el proyecto

¿Quieres crear un repositorio?"""


def main():
    """Función principal para interactuar con el usuario"""

    print("🤖 GitHub Repository Creator Agent")
    print("=" * 50)

    try:
        # Inicializar el agente
        agent = GitHubAgent()

        print("\n¡Hola! Soy tu asistente para crear repositorios de GitHub.")
        print("Puedo ayudarte a crear repositorios con README.md generado automáticamente.")
        print("\nEscribe 'ayuda' para ver ejemplos de uso.")

        while True:
            user_input = input("\n📝 Tú: ").strip()

            if user_input.lower() in ['salir', 'exit', 'quit']:
                print("👋 ¡Hasta luego!")
                break

            if not user_input:
                print("Por favor, dime qué quieres hacer.")
                continue

            print()
            response = agent.chat(user_input)
            print(f"🤖 Asistente: {response}")

    except KeyboardInterrupt:
        print("\n\n👋 ¡Hasta luego!")
    except Exception as e:
        print(f"\n❌ Error inicializando el agente: {e}")
        print("\nAsegúrate de tener las variables de entorno configuradas:")
        print("- GITHUB_TOKEN: Token de GitHub con permisos de repositorio")
        print("- GOOGLE_API_KEY: API key de Google Generative AI")


if __name__ == "__main__":
    main()