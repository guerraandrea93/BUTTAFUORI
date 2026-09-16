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


def salva_percorsi(percorsi: dict[str, str]) -> None:
    """Salva i percorsi applicativi nel file INI locale."""
    config = configparser.ConfigParser()
    config["PERCORSI"] = {
        nome: percorsi[nome] for nome in (*CHIAVI_SORGENTI, *CHIAVI_TORNI)
    }
    with open(PERCORSO_CONFIG, "w", encoding="utf-8") as config_file:
        config.write(config_file)


def _primo_percorso(config, chiavi, fallback):
    for chiave in chiavi:
        valore = config.get("PERCORSI", chiave, fallback="").strip()
        if valore:
            return valore
    return fallback


def inizializza_percorsi() -> dict[str, str]:
    """Legge i percorsi e migra le precedenti chiavi TORNI quando possibile."""
    config = configparser.ConfigParser()
    if os.path.isfile(PERCORSO_CONFIG):
        config.read(PERCORSO_CONFIG, encoding="utf-8")
    radice_rulli = config.get("PERCORSI", "RULLI", fallback=PERCORSO_RULLI)
    radice_torni = config.get("PERCORSI", "TORNIO", fallback=PERCORSO_TORNIO)
    predefiniti_sorgenti = {
        "RULLI_SERIE": radice_rulli,
        "RULLI_MODIFICA": radice_rulli,
        "RULLI_RICAMBIO": os.path.join(radice_rulli, "RICAMBI", "SERIE"),
        "ACCESSORI_SERIE": os.path.join(radice_rulli, "ACC"),
        "ACCESSORI_MODIFICA": os.path.join(radice_rulli, "ACC"),
        "ACCESSORI_RICAMBIO": os.path.join(radice_rulli, "ACC", "RICAMBI", "SERIE"),
    }
    percorsi = {
        f"{nome}_1": config.get("PERCORSI", nome, fallback=percorso)
        for nome, percorso in predefiniti_sorgenti.items()
    }
    percorsi.update({f"{nome}_2": "" for nome in CHIAVI_COMBINAZIONI})
    if config.has_section("PERCORSI"):
        for nome in CHIAVI_SORGENTI:
            percorsi[nome] = config.get("PERCORSI", nome, fallback=percorsi[nome])

    predefiniti_torni = {
        "TORNI_SGROSSATURA": _primo_percorso(
            config,
            ("TORNI_SGROSSATURA", "TORNI_RULLI_SGROSSATURA"),
            os.path.join(radice_torni, "SGROSSATURA"),
        ),
        "TORNI_FINITURA": _primo_percorso(
            config,
            ("TORNI_FINITURA", "TORNI_RULLI_FINITURA"),
            os.path.join(radice_torni, "FINITURA"),
        ),
        "TORNI_MODIFICHE": _primo_percorso(
            config,
            ("TORNI_MODIFICHE", "TORNI_RULLI_MODIFICHE", "TORNI_RULLI_RICAMBI"),
            os.path.join(radice_torni, "MODIFICHE"),
        ),
        "TORNI_ACC_SERIE": _primo_percorso(
            config,
            ("TORNI_ACC_SERIE",),
            os.path.join(radice_torni, "ACC", "SERIE"),
        ),
        "TORNI_ACC_MODIFICHE": _primo_percorso(
            config,
            ("TORNI_ACC_MODIFICHE",),
            os.path.join(radice_torni, "ACC", "MODIFICHE"),
        ),
    }
    percorsi.update(predefiniti_torni)
    if not os.path.isfile(PERCORSO_CONFIG):
        salva_percorsi(percorsi)
    return percorsi
