"""Funzioni di supporto per il progetto BUTTAFUORI."""

import configparser
import json
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
DIRECTORY_PROGETTO = os.path.dirname(os.path.abspath(__file__))
PERCORSO_CONFIG = os.path.join(DIRECTORY_PROGETTO, "percorsi.json")
PERCORSO_CONFIG_LEGACY = os.path.join(DIRECTORY_PROGETTO, "config.ini")

CHIAVI_COMBINAZIONI = (
    "RULLI_SERIE", "RULLI_MODIFICA", "RULLI_RICAMBIO",
    "ACCESSORI_SERIE", "ACCESSORI_MODIFICA", "ACCESSORI_RICAMBIO",
)
CHIAVI_SORGENTI = ("RULLI_UNIVERSALE", *CHIAVI_COMBINAZIONI)
ETICHETTE_SORGENTI = {
    "RULLI_UNIVERSALE": "DIRECTORY UNIVERSALE",
    "RULLI_SERIE": "SECONDARIA - RULLI / SERIE",
    "RULLI_MODIFICA": "SECONDARIA - RULLI / MODIFICHE",
    "RULLI_RICAMBIO": "SECONDARIA - RULLI / RICAMBI",
    "ACCESSORI_SERIE": "SECONDARIA - ACCESSORI / SERIE",
    "ACCESSORI_MODIFICA": "SECONDARIA - ACCESSORI / MODIFICHE",
    "ACCESSORI_RICAMBIO": "SECONDARIA - ACCESSORI / RICAMBI",
}
CHIAVI_TORNI = (
    "TORNI_SGROSSATURA",
    "TORNI_FINITURA",
    "TORNI_MODIFICHE",
    "TORNI_ACC_SERIE",
    "TORNI_ACC_MODIFICHE",
)
ETICHETTE_TORNI = {
    "TORNI_SGROSSATURA": "TORNIO / SGROSSATURA",
    "TORNI_FINITURA": "TORNIO / FINITURA",
    "TORNI_MODIFICHE": "TORNIO / MODIFICHE",
    "TORNI_ACC_SERIE": "TORNIO / ACC / SERIE",
    "TORNI_ACC_MODIFICHE": "TORNIO / ACC / MODIFICHE",
}


def _percorsi_predefiniti() -> dict[str, str]:
    return {
        "RULLI_UNIVERSALE": PERCORSO_RULLI,
        "RULLI_SERIE": PERCORSO_RULLI,
        "RULLI_MODIFICA": PERCORSO_RULLI,
        "RULLI_RICAMBIO": os.path.join(PERCORSO_RULLI, "RICAMBI"),
        "ACCESSORI_SERIE": os.path.join(PERCORSO_RULLI, "ACC"),
        "ACCESSORI_MODIFICA": os.path.join(PERCORSO_RULLI, "ACC"),
        "ACCESSORI_RICAMBIO": os.path.join(PERCORSO_RULLI, "ACC", "RICAMBI"),
        "TORNI_SGROSSATURA": os.path.join(PERCORSO_TORNIO, "SGROSSATURA"),
        "TORNI_FINITURA": os.path.join(PERCORSO_TORNIO, "FINITURA"),
        "TORNI_MODIFICHE": os.path.join(PERCORSO_TORNIO, "MODIFICHE"),
        "TORNI_ACC_SERIE": os.path.join(PERCORSO_TORNIO, "ACC", "SERIE"),
        "TORNI_ACC_MODIFICHE": os.path.join(PERCORSO_TORNIO, "ACC", "MODIFICHE"),
    }


def salva_percorsi(percorsi: dict[str, str]) -> None:
    """Salva i sette percorsi RULLI e i cinque percorsi TORNI in JSON."""
    dati = {
        "PERCORSI_RULLI": {
            nome: percorsi.get(nome, "") for nome in CHIAVI_SORGENTI
        },
        "PERCORSI_TORNI": {
            nome: percorsi.get(nome, "") for nome in CHIAVI_TORNI
        },
    }
    temporaneo = PERCORSO_CONFIG + ".tmp"
    with open(temporaneo, "w", encoding="utf-8") as config_file:
        json.dump(dati, config_file, ensure_ascii=False, indent=2)
        config_file.write("\n")
    os.replace(temporaneo, PERCORSO_CONFIG)


def _leggi_json() -> dict[str, str]:
    if not os.path.isfile(PERCORSO_CONFIG):
        return {}
    try:
        with open(PERCORSO_CONFIG, "r", encoding="utf-8") as config_file:
            dati = json.load(config_file)
    except (OSError, json.JSONDecodeError, TypeError):
        return {}
    if not isinstance(dati, dict):
        return {}

    percorsi = {}
    for sezione in ("PERCORSI_RULLI", "PERCORSI_TORNI"):
        valori = dati.get(sezione, {})
        if isinstance(valori, dict):
            percorsi.update(
                (nome, valore) for nome, valore in valori.items()
                if isinstance(valore, str)
            )
    return percorsi


def _leggi_config_legacy() -> dict[str, str]:
    """Migra il precedente INI quando il JSON non è ancora disponibile."""
    if not os.path.isfile(PERCORSO_CONFIG_LEGACY):
        return {}
    config = configparser.ConfigParser()
    try:
        config.read(PERCORSO_CONFIG_LEGACY, encoding="utf-8")
    except (configparser.Error, OSError):
        return {}
    if not config.has_section("PERCORSI"):
        return {}

    def primo(*nomi, fallback=""):
        for nome in nomi:
            valore = config.get("PERCORSI", nome, fallback="").strip()
            if valore:
                return valore
        return fallback

    radice_rulli = primo(
        "RULLI", "RULLI_SERIE_1", "RULLI_SERIE", fallback=PERCORSO_RULLI
    )
    radice_torni = primo("TORNIO", fallback=PERCORSO_TORNIO)
    migrati = {
        "RULLI_UNIVERSALE": radice_rulli,
        **{
            nome: primo(f"{nome}_1", nome, fallback=percorso)
            for nome, percorso in {
                "RULLI_SERIE": radice_rulli,
                "RULLI_MODIFICA": radice_rulli,
                "RULLI_RICAMBIO": os.path.join(radice_rulli, "RICAMBI"),
                "ACCESSORI_SERIE": os.path.join(radice_rulli, "ACC"),
                "ACCESSORI_MODIFICA": os.path.join(radice_rulli, "ACC"),
                "ACCESSORI_RICAMBIO": os.path.join(radice_rulli, "ACC", "RICAMBI"),
            }.items()
        },
        "TORNI_SGROSSATURA": primo(
            "TORNI_SGROSSATURA", "TORNI_RULLI_SGROSSATURA",
            fallback=os.path.join(radice_torni, "SGROSSATURA"),
        ),
        "TORNI_FINITURA": primo(
            "TORNI_FINITURA", "TORNI_RULLI_FINITURA",
            fallback=os.path.join(radice_torni, "FINITURA"),
        ),
        "TORNI_MODIFICHE": primo(
            "TORNI_MODIFICHE", "TORNI_RULLI_MODIFICHE", "TORNI_RULLI_RICAMBI",
            fallback=os.path.join(radice_torni, "MODIFICHE"),
        ),
        "TORNI_ACC_SERIE": primo(
            "TORNI_ACC_SERIE", fallback=os.path.join(radice_torni, "ACC", "SERIE")
        ),
        "TORNI_ACC_MODIFICHE": primo(
            "TORNI_ACC_MODIFICHE",
            fallback=os.path.join(radice_torni, "ACC", "MODIFICHE"),
        ),
    }
    return migrati


def inizializza_percorsi() -> dict[str, str]:
    """Legge il JSON e completa o migra automaticamente la configurazione."""
    percorsi = _percorsi_predefiniti()
    caricati = _leggi_json()
    if not caricati:
        caricati = _leggi_config_legacy()
    percorsi.update(caricati)

    if not os.path.isfile(PERCORSO_CONFIG):
        salva_percorsi(percorsi)
    return percorsi
