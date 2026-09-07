"""Lettura locale di una singola cartella sorgente."""
import os
import re
from dataclasses import dataclass, field

_MIN_RE = re.compile(r"^([MPSRT])[_\- ]?(.*)$", re.IGNORECASE)

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

def _chiave(stem: str) -> tuple[str, str | None]:
    match = _MIN_RE.match(stem)
    if match: return match.group(2).strip(), match.group(1).upper()
    return stem.strip(), None

def leggi_cartella(cartella: str, tipo: str) -> list[ElementoProgramma]:
    """Legge esclusivamente i file immediati (mai os.walk)."""
    elementi: dict[str, ElementoProgramma] = {}
    try: voci = os.scandir(cartella)
    except OSError: return []
    with voci:
        for voce in voci:
            if not voce.is_file(): continue
            lower = voce.name.lower()
            if lower.endswith(".min"):
                base, variante = _chiave(os.path.splitext(voce.name)[0])
                if not base: continue
                elemento = elementi.setdefault(base.casefold(), ElementoProgramma(base))
                if variante:
                    elemento.varianti.add(variante); elemento.percorsi[variante] = voce.path
            elif lower.endswith(".prt"):
                base, _ = _chiave(os.path.splitext(voce.name)[0])
                elemento = elementi.setdefault(base.casefold(), ElementoProgramma(base))
                elemento.presenza_prt = True; elemento.percorsi["PRT"] = voce.path
    risultati = list(elementi.values())
    if tipo == "SERIE":
        for elemento in risultati: elemento.varianti -= {"R", "T"}
    return sorted(risultati, key=lambda e: e.identificativo.casefold())
