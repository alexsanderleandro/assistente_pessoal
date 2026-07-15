"""Detecção de conteúdo novo entre duas capturas da mesma página.

Compara linha a linha ignorando diferenças de espaçamento/formatação
(PRD.md seção 7.3), e para cada trecho novo extrai algumas linhas de
contexto antes/depois (PRD.md seção 4.3)."""
import difflib
from dataclasses import dataclass

CONTEXT_LINES = 2


@dataclass
class DetectedChange:
    conteudo_novo: str
    contexto: str


def _linhas_normalizadas(texto: str) -> list[str]:
    # remove espaços nas pontas e linhas vazias para não acusar
    # mudança onde só a formatação foi alterada
    return [linha.strip() for linha in texto.splitlines() if linha.strip()]


def detect_new_content(old_text: str | None, new_text: str) -> list[DetectedChange]:
    """Retorna os trechos de conteúdo novo encontrados em new_text
    que não existiam em old_text. Se old_text for None (primeira
    captura), não há baseline para comparar, então nada é reportado."""
    if not old_text:
        return []

    old_lines = _linhas_normalizadas(old_text)
    new_lines = _linhas_normalizadas(new_text)

    matcher = difflib.SequenceMatcher(None, old_lines, new_lines)
    changes: list[DetectedChange] = []

    for tag, _i1, _i2, j1, j2 in matcher.get_opcodes():
        if tag not in ("insert", "replace"):
            continue

        conteudo_novo = "\n".join(new_lines[j1:j2])
        antes = new_lines[max(0, j1 - CONTEXT_LINES):j1]
        depois = new_lines[j2:j2 + CONTEXT_LINES]
        contexto = "\n".join(antes + ["..."] + depois) if (antes or depois) else ""

        changes.append(DetectedChange(conteudo_novo=conteudo_novo, contexto=contexto))

    return changes
