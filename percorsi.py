"""Costruzione dei percorsi sorgente e delle destinazioni TORNI."""
import os
import re
from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class Selezione:
    cosa: str
    tipo: str


@dataclass(frozen=True)
class OperazioneCopia:
    programma: str
    variante: str
    sorgente: str
    cartella_destinazione: str

    @property
    def nome_file(self) -> str:
        return os.path.basename(self.sorgente)

    @property
    def destinazione(self) -> str:
        return os.path.join(self.cartella_destinazione, self.nome_file)


def _aggiungi_unica(cartelle: list[str], gia_aggiunte: set[str], cartella: str) -> None:
    chiave = os.path.normcase(os.path.normpath(cartella))
    if chiave not in gia_aggiunte:
        cartelle.append(cartella)
        gia_aggiunte.add(chiave)


def _cerca_cartella(radice: str, nome: str, profondita_massima: int = 2) -> list[str]:
    """Cerca una cartella per nome sotto la radice, limitando la profondità."""
    trovate = []
    if not os.path.isdir(radice):
        return trovate
    radice = os.path.normpath(radice)
    for corrente, directory, _ in os.walk(radice):
        relativo = os.path.relpath(corrente, radice)
        profondita = 0 if relativo == "." else len(relativo.split(os.sep))
        if profondita >= profondita_massima:
            directory[:] = []
        for nome_directory in directory:
            if nome_directory.casefold() == nome.casefold():
                trovate.append(os.path.join(corrente, nome_directory))
    return trovate


def cartelle_sorgenti(percorsi: dict[str, str], selezione: Selezione, codice: str) -> list[str]:
    codice = codice.strip()
    combinazione = f"{selezione.cosa}_{selezione.tipo}"
    nome_cartella = _normalizza_z(codice) if selezione.tipo == "RICAMBIO" else codice
    cartelle = []
    gia_aggiunte = set()
    for indice in (1, 2):
        radice = percorsi.get(f"{combinazione}_{indice}", "").strip()
        if not radice:
            continue
        diretta = os.path.join(radice, nome_cartella)
        if os.path.isdir(diretta):
            _aggiungi_unica(cartelle, gia_aggiunte, diretta)
            continue
        trovate = _cerca_cartella(radice, nome_cartella) if selezione.tipo == "RICAMBIO" else []
        if trovate:
            for cartella in trovate:
                _aggiungi_unica(cartelle, gia_aggiunte, cartella)
        else:
            _aggiungi_unica(cartelle, gia_aggiunte, diretta)
    return cartelle


def descrizione_sorgente(selezione: Selezione) -> str:
    return f"{selezione.cosa} / {selezione.tipo}"


def _normalizza_z(codice: str) -> str:
    codice = codice.strip()
    return "Z" + codice[1:] if codice.upper().startswith("Z") else f"Z{codice}"


def ricava_serie_ricambio(cartelle_sorgente) -> str:
    """Ricava 25010 da percorsi come .../SERIE 25010/Z30100."""
    for cartella in cartelle_sorgente:
        parti = [parte for parte in re.split(r"[\\/]+", os.path.normpath(cartella)) if parte]
        for parte in reversed(parti[:-1]):
            match = re.fullmatch(r"(?:SERIE[\s_-]*)?(\d{4,})", parte, re.IGNORECASE)
            if match:
                return match.group(1)
    raise ValueError(
        "Impossibile ricavare la serie del ricambio dal percorso sorgente. "
        "È attesa una cartella come '25010' oppure 'SERIE 25010' sopra la cartella Z."
    )


def _radici_torni(percorsi: dict[str, str], selezione: Selezione) -> list[str]:
    combinazione = f"{selezione.cosa}_{selezione.tipo}"
    radici = []
    gia_aggiunte = set()
    for indice in (1, 2):
        radice = percorsi.get(f"TORNI_{combinazione}_{indice}", "").strip()
        if radice:
            _aggiungi_unica(radici, gia_aggiunte, radice)
    return radici


def _destinazione(
    radice: str,
    selezione: Selezione,
    serie: str,
    cartella_z: str,
    variante: str,
    giorno: date,
) -> str:
    caso = (selezione.cosa, selezione.tipo)
    if caso == ("RULLI", "SERIE"):
        reparto = "SGROSSATURA" if variante == "M" else "FINITURA"
        return os.path.join(radice, reparto, serie)
    if caso == ("RULLI", "MODIFICA"):
        return os.path.join(radice, "MODIFICHE", serie, giorno.strftime("%d-%m-%y"))
    if caso == ("RULLI", "RICAMBIO"):
        return os.path.join(radice, "MODIFICHE", cartella_z, serie)
    if caso == ("ACCESSORI", "SERIE"):
        return os.path.join(radice, "ACCESSORI", serie)
    if caso == ("ACCESSORI", "MODIFICA"):
        return os.path.join(
            radice, "ACCESSORI", "MODIFICHE", serie, giorno.strftime("%d-%m-%y")
        )
    if caso == ("ACCESSORI", "RICAMBIO"):
        return os.path.join(radice, "ACCESSORI", "MODIFICHE", cartella_z, serie)
    raise ValueError(f"Combinazione non gestita: {selezione.cosa} / {selezione.tipo}")


def pianifica_destinazioni(
    percorsi: dict[str, str],
    selezione: Selezione,
    codice: str,
    elementi,
    cartelle_sorgente,
    giorno: date | None = None,
) -> list[OperazioneCopia]:
    """Genera una riga di copia per ogni file MIN ammesso dalle sei regole."""
    giorno = giorno or date.today()
    serie = codice.strip()
    cartella_z = ""
    if selezione.tipo == "RICAMBIO":
        serie = ricava_serie_ricambio(cartelle_sorgente)
        cartella_z = _normalizza_z(codice)
    if not serie:
        raise ValueError("Codice serie mancante.")

    consentite = (
        {"M", "P", "S", "R", "T"}
        if selezione.tipo == "MODIFICA"
        else {"M", "P", "S"}
    )
    radici = _radici_torni(percorsi, selezione)
    if not radici:
        raise ValueError("Nessun percorso TORNI configurato per questa combinazione.")

    operazioni = []
    for elemento in elementi:
        for variante, sorgente in sorted(elemento.percorsi.items()):
            if variante not in consentite:
                continue
            for radice in radici:
                operazioni.append(
                    OperazioneCopia(
                        programma=elemento.identificativo,
                        variante=variante,
                        sorgente=sorgente,
                        cartella_destinazione=_destinazione(
                            radice, selezione, serie, cartella_z, variante, giorno
                        ),
                    )
                )
    return operazioni
