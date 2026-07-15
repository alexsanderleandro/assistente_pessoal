"""Ponto de entrada da aplicação FastAPI."""
import asyncio
from pathlib import Path
from typing import List

from fastapi import Depends, FastAPI, Form, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session, joinedload

from database import Base, engine, get_db
import models  # noqa: F401 - garante que as tabelas sejam registradas antes do create_all
import schemas
from scheduler import start_scheduler
from notifications import manager

BASE_DIR = Path(__file__).resolve().parent

app = FastAPI(title="Monitor de Páginas")
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=BASE_DIR / "templates")

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


@app.get("/", response_class=HTMLResponse)
def dashboard(request: Request, db: Session = Depends(get_db)):
    paginas = _listar_paginas_com_mudancas(db)
    return templates.TemplateResponse(
        request, "dashboard.html", {"paginas": paginas}
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
    paginas = _listar_paginas_com_mudancas(db)
    return templates.TemplateResponse(
        request, "_lista_paginas.html", {"paginas": paginas}
    )


@app.delete("/paginas/{page_id}", response_class=HTMLResponse)
def remover_pagina(request: Request, page_id: int, db: Session = Depends(get_db)):
    db_page = db.query(models.MonitoredPage).filter(models.MonitoredPage.id == page_id).first()
    if db_page:
        db.delete(db_page)
        db.commit()
    paginas = _listar_paginas_com_mudancas(db)
    return templates.TemplateResponse(
        request, "_lista_paginas.html", {"paginas": paginas}
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
