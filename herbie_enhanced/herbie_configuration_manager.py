#!/usr/bin/env python3
# ============================================================================
# HERBIE CONFIGURATION MANAGER
# Maneja configuración de tokens y variables de entorno
# ============================================================================

import os
import sys
import json
from pathlib import Path
from typing import Dict, Optional


class HerbieConfigManager:
    """Maneja la configuración de Herbie"""

    def __init__(self):
        self.config_file = Path("herbie_config.json")
        self.env_file = Path(".env")
        self.config = {}
        self.load_configuration()

    def load_configuration(self):
        """Carga configuración desde múltiples fuentes"""
        # 1. Intentar cargar desde archivo de configuración
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    self.config = json.load(f)
                print("✅ Configuración cargada desde herbie_config.json")
            except Exception as e:
                print(f"⚠️  Error leyendo configuración: {e}")

        # 2. Intentar cargar desde archivo .env
        if self.env_file.exists():
            try:
                self.load_env_file()
                print("✅ Variables de entorno cargadas desde .env")
            except Exception as e:
                print(f"⚠️  Error leyendo .env: {e}")

        # 3. Cargar desde variables de entorno del sistema
        self.load_system_env()

    def load_env_file(self):
        """Carga variables desde archivo .env"""
        with open(self.env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    key, value = line.split('=', 1)
                    os.environ[key] = value.strip('"').strip("'")

    def load_system_env(self):
        """Carga variables del sistema"""
        # Actualizar configuración con variables de entorno
        env_vars = {
            'github_token': os.getenv('GITHUB_TOKEN'),
            'google_api_key': os.getenv('GOOGLE_API_KEY'),
            'openai_api_key': os.getenv('OPENAI_API_KEY'),
            'anthropic_api_key': os.getenv('ANTHROPIC_API_KEY')
        }

        for key, value in env_vars.items():
            if value:
                self.config[key] = value

    def get_github_token(self) -> Optional[str]:
        """Obtiene token de GitHub"""
        return self.config.get('github_token') or os.getenv('GITHUB_TOKEN')

    def get_google_api_key(self) -> Optional[str]:
        """Obtiene API key de Google"""
        return self.config.get('google_api_key') or os.getenv('GOOGLE_API_KEY')

    def check_configuration(self) -> Dict[str, bool]:
        """Verifica estado de la configuración"""
        return {
            'github_token': bool(self.get_github_token()),
            'google_api_key': bool(self.get_google_api_key()),
            'config_file_exists': self.config_file.exists(),
            'env_file_exists': self.env_file.exists()
        }

    def interactive_setup(self):
        """Configuración interactiva para primera vez"""
        print("🔧 CONFIGURACIÓN INICIAL DE HERBIE")
        print("=" * 50)

        # Verificar configuración actual
        status = self.check_configuration()

        if status['github_token'] and status['google_api_key']:
            print("✅ Configuración completa encontrada!")
            return True

        print("⚠️  Faltan algunas configuraciones. Vamos a configurarlas:")

        # Mostrar opciones
        print("\n📋 OPCIONES DE CONFIGURACIÓN:")
        print("1. Configurar manualmente ahora")
        print("2. Crear archivo .env")
        print("3. Saltar configuración (modo demo)")
        print("4. Mostrar instrucciones detalladas")

        choice = input("\n👉 Elige una opción (1-4): ").strip()

        if choice == '1':
            return self.manual_setup()
        elif choice == '2':
            return self.create_env_file()
        elif choice == '3':
            return self.demo_mode()
        elif choice == '4':
            return self.show_detailed_instructions()
        else:
            print("Opción no válida. Usando modo demo.")
            return self.demo_mode()

    def manual_setup(self) -> bool:
        """Configuración manual paso a paso"""
        print("\n🔧 CONFIGURACIÓN MANUAL")
        print("-" * 30)

        config = {}

        # GitHub Token
        if not self.get_github_token():
            print("\n📋 GITHUB TOKEN:")
            print("   1. Ve a GitHub.com → Settings → Developer settings → Personal access tokens")
            print("   2. Generate new token (classic)")
            print("   3. Selecciona scopes: repo, workflow")

            token = input("\n📝 Ingresa tu GitHub token (o presiona Enter para saltar): ").strip()
            if token:
                config['github_token'] = token
                os.environ['GITHUB_TOKEN'] = token

        # Google API Key
        if not self.get_google_api_key():
            print("\n🔑 GOOGLE API KEY:")
            print("   1. Ve a Google Cloud Console")
            print("   2. Crea proyecto y habilita Gemini API")
            print("   3. Crea credenciales → API Key")

            api_key = input("\n📝 Ingresa tu Google API key (o presiona Enter para saltar): ").strip()
            if api_key:
                config['google_api_key'] = api_key
                os.environ['GOOGLE_API_KEY'] = api_key

        # Guardar configuración
        if config:
            self.config.update(config)
            self.save_configuration()
            print("\n✅ Configuración guardada en herbie_config.json")

        return True

    def create_env_file(self) -> bool:
        """Crea archivo .env"""
        print("\n📄 CREANDO ARCHIVO .env")
        print("-" * 30)

        env_content = """# Herbie Enhanced - Variables de Entorno
# Configuración para acceso a APIs

# GitHub Token (requerido para crear repositorios)
# Obtén uno en: https://github.com/settings/tokens
GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Google API Key (requerido para análisis de IA)
# Obtén una en: https://console.cloud.google.com/
GOOGLE_API_KEY=AIzaSyxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# OpenAI API Key (opcional, para análisis alternativo)
# OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Anthropic API Key (opcional, para análisis alternativo)
# ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
"""

        try:
            with open(self.env_file, 'w') as f:
                f.write(env_content)

            print(f"✅ Archivo .env creado en: {self.env_file.absolute()}")
            print("\n📝 INSTRUCCIONES:")
            print("   1. Abre el archivo .env en tu editor")
            print("   2. Reemplaza 'xxxxxxxxxxxx' con tus tokens reales")
            print("   3. Guarda el archivo")
            print("   4. Ejecuta Herbie nuevamente")

            return False  # Necesita edición manual
        except Exception as e:
            print(f"❌ Error creando archivo .env: {e}")
            return False

    def demo_mode(self) -> bool:
        """Activa modo demo sin configuración"""
        print("\n🎭 MODO DEMO ACTIVADO")
        print("-" * 30)
        print("✅ Herbie funcionará en modo simulación")
        print("✅ No se crearán repositorios reales")
        print("✅ Se usarán respuestas predefinidas")
        print("✅ Perfecto para demostración y testing")

        # Configurar tokens ficticios para que el sistema funcione
        if not self.get_github_token():
            os.environ['GITHUB_TOKEN'] = 'demo_token_github'
        if not self.get_google_api_key():
            os.environ['GOOGLE_API_KEY'] = 'demo_key_google'

        return True

    def show_detailed_instructions(self) -> bool:
        """Muestra instrucciones detalladas"""
        print("\n📚 INSTRUCCIONES DETALLADAS")
        print("=" * 50)

        instructions = """
🔑 OBTENER GITHUB TOKEN:
   1. Ve a https://github.com/settings/tokens
   2. Click "Generate new token" → "Personal access token (classic)"
   3. Selecciona scopes:
      - repo (acceso completo a repositorios)
      - workflow (actualizar GitHub Actions)
      - admin:repo_hook (webhooks)
   4. Copia el token (formato: ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx)

🔑 OBTENER GOOGLE API KEY:
   1. Ve a https://console.cloud.google.com/
   2. Crea un proyecto nuevo o selecciona uno existente
   3. Habilita la API de "Generative Language API"
   4. Ve a "APIs & Services" → "Credentials"
   5. Click "Create credentials" → "API key"
   6. Copia la key (formato: AIzaSyxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx)

💾 CONFIGURAR VARIABLES:

   Opción 1 - Archivo .env:
   Crea archivo .env en el directorio del proyecto:

   GITHUB_TOKEN=tu_token_aquí
   GOOGLE_API_KEY=tu_key_aquí

   Opción 2 - Terminal:
   Linux/Mac:
   export GITHUB_TOKEN="tu_token_aquí"
   export GOOGLE_API_KEY="tu_key_aquí"

   Windows:
   set GITHUB_TOKEN=tu_token_aquí
   set GOOGLE_API_KEY=tu_key_aquí

🎯 EJECUTAR HERBIE:
   python herbie_main_runner.py
"""

        print(instructions)

        response = input("\n¿Quieres continuar con la configuración? (s/n): ").strip().lower()
        if response in ['s', 'si', 'sí', 'y', 'yes']:
            return self.interactive_setup()
        else:
            return self.demo_mode()

    def save_configuration(self):
        """Guarda configuración actual"""
        try:
            # Solo guardar claves que no sean sensibles en el archivo
            safe_config = {
                'configured': True,
                'last_updated': str(Path(__file__).stat().st_mtime),
                'demo_mode': not (self.get_github_token() and self.get_google_api_key())
            }

            with open(self.config_file, 'w') as f:
                json.dump(safe_config, f, indent=2)
        except Exception as e:
            print(f"⚠️  Error guardando configuración: {e}")

    def show_status(self):
        """Muestra estado actual de la configuración"""
        status = self.check_configuration()

        print("\n📊 ESTADO DE CONFIGURACIÓN")
        print("=" * 40)
        print(f"GitHub Token: {'✅ Configurado' if status['github_token'] else '❌ Faltante'}")
        print(f"Google API Key: {'✅ Configurado' if status['google_api_key'] else '❌ Faltante'}")
        print(f"Archivo .env: {'✅ Existe' if status['env_file_exists'] else '❌ No existe'}")
        print(f"Archivo config: {'✅ Existe' if status['config_file_exists'] else '❌ No existe'}")

        if status['github_token'] and status['google_api_key']:
            print("\n🎉 ¡Configuración completa! Herbie está listo para usar.")
        else:
            print("\n⚠️  Configuración incompleta. Algunas funciones usarán simulación.")


def main():
    """Función principal para configuración"""
    config_manager = HerbieConfigManager()

    if len(sys.argv) > 1:
        if sys.argv[1] == 'status':
            config_manager.show_status()
        elif sys.argv[1] == 'setup':
            config_manager.interactive_setup()
        elif sys.argv[1] == 'demo':
            config_manager.demo_mode()
        else:
            print("Uso: python herbie_config_manager.py [status|setup|demo]")
    else:
        config_manager.interactive_setup()


if __name__ == "__main__":
    main()