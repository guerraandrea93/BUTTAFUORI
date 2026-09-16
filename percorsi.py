"""Costruzione dei percorsi sorgente e delle destinazioni TORNI."""
import os
import re
from dataclasses import dataclass, replace
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


def applica_destinazione_temporanea(
    operazioni: list[OperazioneCopia], cartella: str
) -> list[OperazioneCopia]:
    """Sposta l'intero piano selezionato in una cartella solo per questa copia."""
    cartella = cartella.strip()
    if not cartella:
        raise ValueError("Cartella di destinazione manuale mancante.")
    return [
        replace(operazione, cartella_destinazione=cartella)
        for operazione in operazioni
    ]


def _aggiungi_unica(cartelle: list[str], gia_aggiunte: set[str], cartella: str) -> None:
    chiave = os.path.normcase(os.path.normpath(cartella))
    if chiave not in gia_aggiunte:
        cartelle.append(cartella)
        gia_aggiunte.add(chiave)


def cartelle_sorgenti(
    percorsi: dict[str, str],
    selezione: Selezione,
    codice: str,
    cartella_z: str = "",
) -> list[str]:
    """Restituisce la cartella universale e la secondaria della modalità.

    La directory universale contiene sempre una sottocartella per serie. Per i
    ricambi solo la directory secondaria aggiunge anche il livello Z.
    """
    codice = codice.strip()
    combinazione = f"{selezione.cosa}_{selezione.tipo}"
    cartelle = []
    gia_aggiunte = set()

    universale = percorsi.get("RULLI_UNIVERSALE", "").strip()
    if universale:
        _aggiungi_unica(
            cartelle, gia_aggiunte, os.path.join(universale, codice)
        )

    secondaria = percorsi.get(combinazione, "").strip()
    if secondaria:
        percorso_secondario = os.path.join(secondaria, codice)
        if selezione.tipo == "RICAMBIO" and cartella_z.strip():
            percorso_secondario = os.path.join(
                percorso_secondario, _normalizza_z(cartella_z)
            )
        _aggiungi_unica(cartelle, gia_aggiunte, percorso_secondario)
    return cartelle


def descrizione_sorgente(selezione: Selezione) -> str:
    return f"{selezione.cosa} / {selezione.tipo}"


def _normalizza_z(codice: str) -> str:
    codice = codice.strip()
    return "Z" + codice[1:] if codice.upper().startswith("Z") else f"Z{codice}"


def ricava_serie_ricambio(cartelle_sorgente) -> str:
    """Ricava 25010 da percorsi come .../RICAMBI/SERIE 25010."""
    for cartella in cartelle_sorgente:
        parti = [parte for parte in re.split(r"[\\/]+", os.path.normpath(cartella)) if parte]
        for parte in reversed(parti):
            match = re.fullmatch(r"(?:SERIE[\s_-]*)?(\d{4,})", parte, re.IGNORECASE)
            if match:
                return match.group(1)
    raise ValueError(
        "Impossibile ricavare la serie del ricambio dal percorso sorgente. "
        "È attesa una cartella come '25010' oppure 'SERIE 25010' sopra la cartella Z."
    )


def ricava_z_ricambio(cartelle_sorgente) -> str:
    """Ricava Z31133 dal percorso sorgente .../14074/Z31133."""
    for cartella in cartelle_sorgente:
        nome = os.path.basename(os.path.normpath(cartella)).strip()
        if re.fullmatch(r"Z.+", nome, re.IGNORECASE):
            return _normalizza_z(nome)
    raise ValueError(
        "Impossibile ricavare la cartella Z dal percorso sorgente."
    )


def _chiavi_richieste(selezione: Selezione) -> tuple[str, ...]:
    caso = (selezione.cosa, selezione.tipo)
    if caso == ("RULLI", "SERIE"):
        return ("TORNI_SGROSSATURA", "TORNI_FINITURA")
    if caso in {("RULLI", "MODIFICA"), ("RULLI", "RICAMBIO")}:
        return ("TORNI_MODIFICHE",)
    if caso == ("ACCESSORI", "SERIE"):
        return ("TORNI_ACC_SERIE",)
    if caso in {("ACCESSORI", "MODIFICA"), ("ACCESSORI", "RICAMBIO")}:
        return ("TORNI_ACC_MODIFICHE",)
    raise ValueError(f"Combinazione non gestita: {selezione.cosa} / {selezione.tipo}")


def _destinazione(
    percorsi: dict[str, str],
    selezione: Selezione,
    serie: str,
    cartella_z: str,
    variante: str,
    giorno: date,
) -> str:
    caso = (selezione.cosa, selezione.tipo)
    if caso == ("RULLI", "SERIE"):
        chiave = "TORNI_SGROSSATURA" if variante == "M" else "TORNI_FINITURA"
        return os.path.join(percorsi[chiave], serie)
    if caso == ("RULLI", "MODIFICA"):
        return os.path.join(
            percorsi["TORNI_MODIFICHE"], serie, giorno.strftime("%d-%m-%y")
        )
    if caso == ("RULLI", "RICAMBIO"):
        return os.path.join(percorsi["TORNI_MODIFICHE"], cartella_z, serie)
    if caso == ("ACCESSORI", "SERIE"):
        return os.path.join(percorsi["TORNI_ACC_SERIE"], serie)
    if caso == ("ACCESSORI", "MODIFICA"):
        return os.path.join(
            percorsi["TORNI_ACC_MODIFICHE"], serie, giorno.strftime("%d-%m-%y")
        )
    if caso == ("ACCESSORI", "RICAMBIO"):
        return os.path.join(
            percorsi["TORNI_ACC_MODIFICHE"], cartella_z, serie
        )
    raise ValueError(f"Combinazione non gestita: {selezione.cosa} / {selezione.tipo}")


def pianifica_destinazioni(
    percorsi: dict[str, str],
    selezione: Selezione,
    codice: str,
    elementi,
    cartelle_sorgente,
    giorno: date | None = None,
    cartella_z: str = "",
) -> list[OperazioneCopia]:
    """Genera una riga di copia per ogni file MIN ammesso dalle sei regole."""
    giorno = giorno or date.today()
    serie = codice.strip()
    if selezione.tipo == "RICAMBIO":
        if not cartella_z.strip():
            raise ValueError("Cartella Z del ricambio mancante.")
        cartella_z = _normalizza_z(cartella_z)
    if not serie:
        raise ValueError("Codice serie mancante.")

    mancanti = [
        chiave for chiave in _chiavi_richieste(selezione)
        if not percorsi.get(chiave, "").strip()
        or not os.path.isdir(percorsi[chiave])
    ]
    if mancanti:
        raise ValueError(
            "Configura una cartella base TORNI esistente per: "
            + ", ".join(mancanti)
        )

    consentite = (
        {"M", "P", "S", "R", "T"}
        if selezione.tipo == "MODIFICA"
        else {"M", "P", "S"}
    )
    operazioni = []
    for elemento in elementi:
        file_min = elemento.file_min or [
            (variante, sorgente)
            for variante, sorgente in elemento.percorsi.items()
            if variante in {"M", "P", "S", "R", "T"}
        ]
        for variante, sorgente in sorted(file_min):
            if variante not in consentite:
                continue
            operazioni.append(
                OperazioneCopia(
                    programma=elemento.identificativo,
                    variante=variante,
                    sorgente=sorgente,
                    cartella_destinazione=_destinazione(
                        percorsi, selezione, serie, cartella_z, variante, giorno
                    ),
                )
            )
    return operazioni
