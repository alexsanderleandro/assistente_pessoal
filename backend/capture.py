"""Motor de captura: abre a página com navegador real (Playwright) para
garantir que conteúdo carregado via JavaScript também seja extraído
(ver PRD.md seção 6.1 - execução de JS é obrigatória)."""
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

TIMEOUT_MS = 30_000


class PageFetchError(Exception):
    """Erro amigável ao tentar capturar o conteúdo de uma página."""


def fetch_page_content(url: str) -> str:
    """Renderiza a URL e retorna o texto visível da página.

    Levanta PageFetchError com mensagem amigável em caso de falha,
    para que o usuário possa investigar manualmente (ver PRD.md 4.5/7.1).
    """
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            try:
                page = browser.new_page()
                page.goto(url, timeout=TIMEOUT_MS, wait_until="networkidle")
                return page.inner_text("body")
            finally:
                browser.close()
    except PlaywrightTimeoutError:
        raise PageFetchError(
            f"Tempo esgotado ao carregar a página. Verifique manualmente: {url}"
        )
    except Exception as exc:
        raise PageFetchError(
            f"Não foi possível acessar a página no momento. Verifique manualmente: {url} ({exc})"
        )
