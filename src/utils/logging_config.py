# src/herbie/utils/logging_config.py
import logging
import os
from pathlib import Path


def setup_logging():
    """Configura sistema de logging"""

    # Crear directorio de logs
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    # Configurar formato
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Handler para archivo
    file_handler = logging.FileHandler(log_dir / "herbie.log")
    file_handler.setFormatter(formatter)

    # Handler para consola
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    # Configurar logger principal
    logger = logging.getLogger("herbie")
    logger.setLevel(logging.INFO)
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger