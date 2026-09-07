"""Funzioni di supporto per il progetto BUTTAFUORI."""


# =========================================================
# PALETTE GRAFICA BLUE NAVY
# =========================================================

COLORE_NAVY = "#1F4E78"
COLORE_TESTO = "#16324F"
COLORE_AZZURRO = "#DCE6F1"
COLORE_RIGA_ALTERNATA = "#F4F8FC"
COLORE_SELEZIONE = "#4F81BD"


# =========================================================
# PERCORSI DATI
# =========================================================

PERCORSO_RULLI = r"G:\RULLI"
PERCORSO_TORNIO = r"\\SRVDNC1\tornio"


def inizializza_percorsi() -> dict[str, str]:
    """Restituisce i percorsi condivisi utilizzati dall'applicazione."""
    return {
        "RULLI": PERCORSO_RULLI,
        "TORNIO": PERCORSO_TORNIO,
    }
