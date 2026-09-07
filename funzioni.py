"""Funzioni di supporto per il progetto BUTTAFUORI."""

import configparser
import os


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
PERCORSO_CONFIG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.ini")
CHIAVI_COMBINAZIONI = (
    "RULLI_SERIE", "RULLI_MODIFICA", "RULLI_RICAMBIO",
    "ACCESSORI_SERIE", "ACCESSORI_MODIFICA", "ACCESSORI_RICAMBIO",
)
CHIAVI_SORGENTI = tuple(
    f"{combinazione}_{indice}"
    for combinazione in CHIAVI_COMBINAZIONI
    for indice in (1, 2)
)
CHIAVI_TORNI = tuple(f"TORNI_{nome}" for nome in CHIAVI_SORGENTI)


def salva_percorsi(percorsi: dict[str, str]) -> None:
    """Salva i percorsi applicativi nel file INI locale."""
    config = configparser.ConfigParser()
    config["PERCORSI"] = {nome: percorsi[nome] for nome in (*CHIAVI_SORGENTI, *CHIAVI_TORNI)}
    with open(PERCORSO_CONFIG, "w", encoding="utf-8") as config_file:
        config.write(config_file)


def inizializza_percorsi() -> dict[str, str]:
    """Legge i percorsi dal file INI, creandolo con i valori predefiniti."""
    config = configparser.ConfigParser()
    if os.path.isfile(PERCORSO_CONFIG):
        config.read(PERCORSO_CONFIG, encoding="utf-8")
    radice_rulli = config.get("PERCORSI", "RULLI", fallback=PERCORSO_RULLI)
    radice_torni = config.get("PERCORSI", "TORNI", fallback=PERCORSO_TORNIO)
    predefiniti = {
        "RULLI_SERIE": radice_rulli,
        "RULLI_MODIFICA": radice_rulli,
        "RULLI_RICAMBIO": os.path.join(radice_rulli, "RICAMBI", "SERIE"),
        "ACCESSORI_SERIE": os.path.join(radice_rulli, "ACC"),
        "ACCESSORI_MODIFICA": os.path.join(radice_rulli, "ACC"),
        "ACCESSORI_RICAMBIO": os.path.join(radice_rulli, "ACC", "RICAMBI", "SERIE"),
    }
    percorsi = {
        f"{nome}_1": config.get("PERCORSI", nome, fallback=percorso)
        for nome, percorso in predefiniti.items()
    }
    percorsi.update({
        f"{nome}_2": "" for nome in CHIAVI_COMBINAZIONI
    })
    percorsi.update({f"TORNI_{nome}_1": radice_torni for nome in CHIAVI_COMBINAZIONI})
    percorsi.update({f"TORNI_{nome}_2": "" for nome in CHIAVI_COMBINAZIONI})
    if config.has_section("PERCORSI"):
        for nome in (*CHIAVI_SORGENTI, *CHIAVI_TORNI):
            percorsi[nome] = config.get("PERCORSI", nome, fallback=percorsi[nome])
    if not os.path.isfile(PERCORSO_CONFIG):
        salva_percorsi(percorsi)
    return percorsi
