"""Agendador: orquestra a verificação periódica de todas as páginas
monitoradas (ver PRD.md seção 6.4 - a cada 2h, dias úteis, 00h01-23h59)."""
from datetime import datetime, timedelta, timezone

RETENCAO_DIAS = 7

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from database import SessionLocal
from models import MonitoredPage, Change
from capture import fetch_page_content, PageFetchError
from diffing import detect_new_content
from notifications import manager


def run_monitoring_cycle() -> None:
    """Executa um ciclo completo: captura, compara e persiste mudanças
    para cada página monitorada. Cada página é isolada — erro em uma
    não interrompe as demais (PRD.md seção 7.5)."""
    db = SessionLocal()
    paginas_com_mudanca: list[str] = []
    try:
        pages = db.query(MonitoredPage).all()
        for page in pages:
            agora = datetime.now(timezone.utc)
            try:
                novo_conteudo = fetch_page_content(page.url)
                mudancas = detect_new_content(page.ultimo_conteudo, novo_conteudo)

                for mudanca in mudancas:
                    db.add(Change(
                        page_id=page.id,
                        conteudo_novo=mudanca.conteudo_novo,
                        contexto=mudanca.contexto,
                    ))
                if mudancas:
                    paginas_com_mudanca.append(page.nome_amigavel)

                page.ultimo_conteudo = novo_conteudo
                page.ultima_verificacao = agora
                page.ultimo_erro = None
            except PageFetchError as e:
                # não interrompe o ciclo das outras páginas; apenas registra
                # o erro para exibição amigável no dashboard (PRD.md 4.5)
                page.ultima_verificacao = agora
                page.ultimo_erro = str(e)

        db.commit()
    finally:
        db.close()

    # notifica só depois do commit, para o dashboard já encontrar os dados
    # persistidos caso o usuário atualize a página ao ver o popup (PRD.md 4.4)
    for nome_amigavel in paginas_com_mudanca:
        manager.notify({"nome_amigavel": nome_amigavel})


def cleanup_old_changes() -> None:
    """Remove mudanças com mais de 7 dias (PRD.md seção 3 - retenção de dados).
    Roda todo dia, inclusive fins de semana, para o limite ser sempre respeitado."""
    db = SessionLocal()
    try:
        limite = datetime.now(timezone.utc) - timedelta(days=RETENCAO_DIAS)
        db.query(Change).filter(Change.detectado_em < limite).delete()
        db.commit()
    finally:
        db.close()


def start_scheduler() -> BackgroundScheduler:
    scheduler = BackgroundScheduler(timezone="America/Sao_Paulo")
    scheduler.add_job(
        run_monitoring_cycle,
        trigger=CronTrigger(day_of_week="mon-fri", hour="0-23/2", minute=1),
        id="monitoring_cycle",
    )
    scheduler.add_job(
        cleanup_old_changes,
        trigger=CronTrigger(hour=0, minute=5),
        id="cleanup_old_changes",
    )
    scheduler.start()
    return scheduler
