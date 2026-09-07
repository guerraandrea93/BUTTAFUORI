"""Regole warning separate dalla raccolta dati e dalla GUI."""
try:
    from .classificazione import ElementoProgramma
except ImportError:
    from classificazione import ElementoProgramma

def valuta(elemento: ElementoProgramma, tipo: str) -> list[str]:
    warning = []
    if tipo == "SERIE" and not {"M", "P", "S"}.issubset(elemento.varianti): warning.append("M/P/S incompleti")
    if elemento.presenza_prt and not elemento.varianti: warning.append("PRT senza MIN")
    if tipo == "MODIFICA" and not elemento.varianti: warning.append("nessun programma MIN")
    elemento.warning_codes = warning
    return warning
