"""Configuração da conexão com o banco SQLite."""
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# caminho absoluto para não depender do diretório de trabalho de onde
# o processo é iniciado; arquivo fica fora do controle de versão (.gitignore)
BASE_DIR = Path(__file__).resolve().parent
DATABASE_URL = f"sqlite:///{BASE_DIR / 'data' / 'monitor.db'}"

# check_same_thread=False necessário pois FastAPI acessa a conexão em threads diferentes
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    # dependency do FastAPI: garante que a sessão sempre é fechada após o uso
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
