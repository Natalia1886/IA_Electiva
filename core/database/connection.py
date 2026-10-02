"""Conexión y gestión de sesiones de la base de datos."""

import os
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from core.database.models import Base

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "tienda_religiosa.db")
DATABASE_URL = f"sqlite:///{DB_PATH}"

# Configuración SQLite con soporte para llaves foráneas y concurrencia segura
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False
)


@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """Crea todas las tablas si no existen."""
    Base.metadata.create_all(bind=engine)


def get_db():
    """Generador de contexto para dependencias FastAPI o scripts."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
