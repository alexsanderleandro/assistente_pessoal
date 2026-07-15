"""Modelos das tabelas do banco (ver PRD.md seção 6.3)."""
from datetime import datetime, timezone

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from database import Base


class MonitoredPage(Base):
    __tablename__ = "monitored_pages"

    id = Column(Integer, primary_key=True)
    url = Column(String, nullable=False)
    nome_amigavel = Column(String, nullable=False)
    criado_em = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # guarda o último conteúdo capturado, usado como base de comparação
    # no próximo ciclo do agendador (ver diffing.py)
    ultimo_conteudo = Column(Text, nullable=True)
    ultima_verificacao = Column(DateTime, nullable=True)
    ultimo_erro = Column(Text, nullable=True)

    changes = relationship("Change", back_populates="page", cascade="all, delete-orphan")


class Change(Base):
    __tablename__ = "changes"

    id = Column(Integer, primary_key=True)
    page_id = Column(Integer, ForeignKey("monitored_pages.id"), nullable=False)
    conteudo_novo = Column(Text, nullable=False)
    contexto = Column(Text)
    detectado_em = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    page = relationship("MonitoredPage", back_populates="changes")
