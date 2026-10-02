"""Logger centralizado del framework para trazabilidad y auditoría."""

import logging
import sys

# Formato estándar y limpio para consola y archivos
LOG_FORMAT = "%(asctime)s [%(levelname)s] [%(name)s]: %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

logging.basicConfig(
    level=logging.INFO,
    format=LOG_FORMAT,
    datefmt=DATE_FORMAT,
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)


def get_logger(name: str) -> logging.Logger:
    """Devuelve un logger configurado con el nombre del módulo."""
    return logging.getLogger(name)
