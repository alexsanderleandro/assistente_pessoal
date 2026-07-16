"""Ponto de entrada da aplicação FastAPI."""
import asyncio
from datetime import datetime, timezone
from pathlib import Path
from typing import List
from zoneinfo import ZoneInfo

from fastapi import Depends, FastAPI, Form, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from database import Base, engine, get_db
import models  # noqa: F401 - garante que as tabelas sejam registradas antes do create_all
import schemas
from scheduler import start_scheduler
from notifications import manager

BASE_DIR = Path(__file__).resolve().parent
FUSO_LOCAL = ZoneInfo("America/Sao_Paulo")

app = FastAPI(title="Monitor de Páginas")
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=BASE_DIR / "templates")


def data_local(dt: datetime | None) -> str:
    """Converte um datetime armazenado em UTC (o SQLite descarta o tzinfo,
    mas o valor ainda representa UTC) para o horário de Brasília ao exibir."""
    if dt is None:
        return "Nunca"
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(FUSO_LOCAL).strftime("%d/%m/%Y %H:%M")


templates.env.filters["data_local"] = data_local

# cria as tabelas no startup; em produção real usaríamos migrations, mas
# para o volume deste projeto (9 páginas) isso é suficiente
Base.metadata.create_all(bind=engine)

_scheduler = None


@app.on_event("startup")
def on_startup():
    global _scheduler
    manager.set_loop(asyncio.get_event_loop())
    _scheduler = start_scheduler()


@app.websocket("/ws/notifications")
async def websocket_notifications(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # conexão é somente para receber broadcasts; ignoramos qualquer
            # mensagem enviada pelo cliente, só usamos para detectar desconexão
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)


@app.on_event("shutdown")
def on_shutdown():
    if _scheduler:
        _scheduler.shutdown(wait=False)


def _listar_paginas_com_mudancas(db: Session) -> list[models.MonitoredPage]:
    paginas = (
        db.query(models.MonitoredPage)
        .options(joinedload(models.MonitoredPage.changes))
        .all()
    )
    # mudanças mais recentes primeiro (PRD.md seção 5.2)
    for pagina in paginas:
        pagina.changes.sort(key=lambda c: c.detectado_em, reverse=True)
    return paginas


def _ultima_atualizacao_global(db: Session) -> datetime | None:
    """Timestamp da verificação automática mais recente, entre todas as
    páginas monitoradas (exibido no cabeçalho do dashboard)."""
    return db.query(func.max(models.MonitoredPage.ultima_verificacao)).scalar()


def _contexto_lista_paginas(db: Session) -> dict:
    return {
        "paginas": _listar_paginas_com_mudancas(db),
        "ultima_atualizacao": _ultima_atualizacao_global(db),
    }


@app.get("/", response_class=HTMLResponse)
def dashboard(request: Request, db: Session = Depends(get_db)):
    return templates.TemplateResponse(
        request, "dashboard.html", _contexto_lista_paginas(db)
    )


@app.get("/paginas", response_class=HTMLResponse)
def listar_paginas(request: Request, db: Session = Depends(get_db)):
    """Retorna só a lista de páginas (partial), usada pelo HTMX para
    atualizar o dashboard automaticamente ao receber notificação via
    WebSocket, sem recarregar a página inteira."""
    return templates.TemplateResponse(
        request, "_lista_paginas.html", _contexto_lista_paginas(db)
    )


@app.post("/paginas", response_class=HTMLResponse)
def adicionar_pagina(
    request: Request,
    url: str = Form(...),
    nome_amigavel: str = Form(...),
    db: Session = Depends(get_db),
):
    db.add(models.MonitoredPage(url=url, nome_amigavel=nome_amigavel))
    db.commit()
    return templates.TemplateResponse(
        request, "_lista_paginas.html", _contexto_lista_paginas(db)
    )


@app.delete("/paginas/{page_id}", response_class=HTMLResponse)
def remover_pagina(request: Request, page_id: int, db: Session = Depends(get_db)):
    db_page = db.query(models.MonitoredPage).filter(models.MonitoredPage.id == page_id).first()
    if db_page:
        db.delete(db_page)
        db.commit()
    return templates.TemplateResponse(
        request, "_lista_paginas.html", _contexto_lista_paginas(db)
    )


@app.get("/health")
def health_check():
    # rota simples para validar que o servidor está no ar
    return {"status": "ok"}


@app.post("/api/monitored-pages", response_model=schemas.MonitoredPageOut)
def create_monitored_page(page: schemas.MonitoredPageCreate, db: Session = Depends(get_db)):
    db_page = models.MonitoredPage(url=page.url, nome_amigavel=page.nome_amigavel)
    db.add(db_page)
    db.commit()
    db.refresh(db_page)
    return db_page


@app.get("/api/monitored-pages", response_model=List[schemas.MonitoredPageOut])
def list_monitored_pages(db: Session = Depends(get_db)):
    return db.query(models.MonitoredPage).all()


@app.delete("/api/monitored-pages/{page_id}", status_code=204)
def delete_monitored_page(page_id: int, db: Session = Depends(get_db)):
    db_page = db.query(models.MonitoredPage).filter(models.MonitoredPage.id == page_id).first()
    if not db_page:
        raise HTTPException(status_code=404, detail="Página não encontrada")
    db.delete(db_page)
    db.commit()
