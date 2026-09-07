"""Costruzione dei percorsi logici, senza accesso al filesystem."""
import os
from dataclasses import dataclass

@dataclass(frozen=True)
class Selezione:
    cosa: str
    tipo: str

def cartelle_sorgenti(percorsi: dict[str, str], selezione: Selezione, codice: str) -> list[str]:
    codice = codice.strip()
    combinazione = f"{selezione.cosa}_{selezione.tipo}"
    nome_cartella = f"Z{codice}" if selezione.tipo == "RICAMBIO" else codice
    cartelle = []
    gia_aggiunte = set()
    for indice in (1, 2):
        radice = percorsi.get(f"{combinazione}_{indice}", "").strip()
        if not radice:
            continue
        cartella = os.path.join(radice, nome_cartella)
        chiave = os.path.normcase(os.path.normpath(cartella))
        if chiave not in gia_aggiunte:
            cartelle.append(cartella)
            gia_aggiunte.add(chiave)
    return cartelle

def descrizione_sorgente(selezione: Selezione) -> str:
    return f"{selezione.cosa} / {selezione.tipo}"

def destinazione_futura(radice_torni: str, selezione: Selezione, codice: str) -> str:
    if selezione.cosa == "RULLI" and selezione.tipo == "RICAMBIO":
        return os.path.join(radice_torni, "RICAMBI", "SERIE", f"Z{codice}")
    if selezione.cosa == "ACCESSORI" and selezione.tipo == "RICAMBIO":
        return os.path.join(radice_torni, "ACCESSORI", "RICAMBI", f"Z{codice}", "SERIE")
    return os.path.join(radice_torni, selezione.cosa, selezione.tipo, codice)
