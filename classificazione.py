"""Lettura locale delle cartelle sorgenti."""
import os
import re
from dataclasses import dataclass, field

_MIN_RE = re.compile(r"^([MPSRT])[_\- ]?(.*)$", re.IGNORECASE)
_REVISIONE_FINALE_RE = re.compile(r"-(\d+)$")


@dataclass
class ElementoProgramma:
    identificativo: str
    presenza_prt: bool = False
    varianti: set[str] = field(default_factory=set)
    percorsi: dict[str, str] = field(default_factory=dict)
    warning_codes: list[str] = field(default_factory=list)

    @property
    def presenza_m(self): return "M" in self.varianti

    @property
    def presenza_p(self): return "P" in self.varianti

    @property
    def presenza_s(self): return "S" in self.varianti

    @property
    def presenza_r(self): return "R" in self.varianti

    @property
    def presenza_t(self): return "T" in self.varianti


@dataclass(frozen=True)
class NotaTxt:
    titolo: str
    prima_riga: str
    percorso: str


@dataclass
class RisultatoLettura:
    elementi: list[ElementoProgramma]
    note: list[NotaTxt]


def _chiave(stem: str) -> tuple[str, str | None]:
    match = _MIN_RE.match(stem)
    if match:
        return match.group(2).strip(), match.group(1).upper()
    return stem.strip(), None


def _filtra_elementi(elementi: dict[str, ElementoProgramma], tipo: str) -> list[ElementoProgramma]:
    risultati = elementi.values()
    if tipo in {"SERIE", "MODIFICA"}:
        revisione_attesa = lambda revisione: revisione == 0 if tipo == "SERIE" else revisione > 0
        risultati = (
            elemento for elemento in risultati
            if (match := _REVISIONE_FINALE_RE.search(elemento.identificativo))
            and revisione_attesa(int(match.group(1)))
        )
    return sorted(risultati, key=lambda elemento: elemento.identificativo.casefold())


def _leggi_contenuto(cartelle, tipo: str, includi_programmi: bool, includi_note: bool) -> RisultatoLettura:
    """Scansiona una sola volta ogni cartella richiesta."""
    elementi: dict[str, ElementoProgramma] = {}
    note: list[NotaTxt] = []
    estensioni_ammesse = {".min", ".prt"} if includi_programmi else set()
    if includi_note:
        estensioni_ammesse.add(".txt")

    for cartella in cartelle:
        try:
            voci = os.scandir(cartella)
        except OSError:
            continue
        with voci:
            for voce in voci:
                estensione = os.path.splitext(voce.name)[1].casefold()
                if estensione not in estensioni_ammesse:
                    continue
                try:
                    if not voce.is_file():
                        continue
                except OSError:
                    continue

                stem = os.path.splitext(voce.name)[0]
                if includi_programmi and estensione == ".min":
                    base, variante = _chiave(stem)
                    if not base:
                        continue
                    elemento = elementi.setdefault(base.casefold(), ElementoProgramma(base))
                    if variante:
                        elemento.varianti.add(variante)
                        elemento.percorsi.setdefault(variante, voce.path)
                elif includi_programmi and estensione == ".prt":
                    base, _ = _chiave(stem)
                    if not base:
                        continue
                    elemento = elementi.setdefault(base.casefold(), ElementoProgramma(base))
                    elemento.presenza_prt = True
                    elemento.percorsi.setdefault("PRT", voce.path)
                elif includi_note and estensione == ".txt":
                    try:
                        with open(voce.path, "r", encoding="utf-8-sig", errors="replace") as file_txt:
                            prima_riga = file_txt.readline().rstrip("\r\n")
                    except OSError:
                        prima_riga = "[Impossibile leggere il file]"
                    note.append(NotaTxt(voce.name, prima_riga, voce.path))

    return RisultatoLettura(
        elementi=_filtra_elementi(elementi, tipo) if includi_programmi else [],
        note=sorted(note, key=lambda nota: nota.titolo.casefold()),
    )


def leggi_contenuto_cartelle(cartelle, tipo: str) -> RisultatoLettura:
    """Restituisce programmi e note con una sola scansione per cartella."""
    return _leggi_contenuto(cartelle, tipo, includi_programmi=True, includi_note=True)


def leggi_cartella(cartella: str, tipo: str) -> list[ElementoProgramma]:
    return leggi_cartelle((cartella,), tipo)


def leggi_cartelle(cartelle, tipo: str) -> list[ElementoProgramma]:
    """Compatibilità: legge i programmi senza aprire gli eventuali TXT."""
    return _leggi_contenuto(cartelle, tipo, includi_programmi=True, includi_note=False).elementi


def leggi_note_txt(cartelle) -> list[NotaTxt]:
    """Compatibilità: legge titolo e prima riga dei soli TXT."""
    return _leggi_contenuto(cartelle, "", includi_programmi=False, includi_note=True).note
