"""Costruzione dei percorsi logici, senza accesso al filesystem."""
import os
from dataclasses import dataclass

@dataclass(frozen=True)
class Selezione:
    cosa: str
    tipo: str

def cartella_sorgente(radice_rulli: str, selezione: Selezione, codice: str) -> str:
    codice = codice.strip()
    if selezione.cosa == "RULLI" and selezione.tipo == "RICAMBIO":
        return os.path.join(radice_rulli, "RICAMBI", "SERIE", f"Z{codice}")
    if selezione.cosa == "ACCESSORI" and selezione.tipo == "RICAMBIO":
        return os.path.join(radice_rulli, "ACC", "RICAMBI", "SERIE", f"Z{codice}")
    parti = ["ACC"] if selezione.cosa == "ACCESSORI" else []
    if selezione.tipo == "MODIFICA": parti.append("MODIFICHE")
    elif selezione.tipo == "RICAMBIO": parti.append("RICAMBI")
    parti.append(codice)
    return os.path.join(radice_rulli, *parti)

def descrizione_sorgente(selezione: Selezione) -> str:
    return f"{selezione.cosa} / {selezione.tipo}"

def destinazione_futura(radice_torni: str, selezione: Selezione, codice: str) -> str:
    if selezione.cosa == "RULLI" and selezione.tipo == "RICAMBIO":
        return os.path.join(radice_torni, "RICAMBI", "SERIE", f"Z{codice}")
    if selezione.cosa == "ACCESSORI" and selezione.tipo == "RICAMBIO":
        return os.path.join(radice_torni, "ACCESSORI", "RICAMBI", f"Z{codice}", "SERIE")
    return os.path.join(radice_torni, selezione.cosa, selezione.tipo, codice)
