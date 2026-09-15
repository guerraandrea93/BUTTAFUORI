import os
import tempfile
import unittest
from datetime import date
from pathlib import Path

from classificazione import ElementoProgramma, leggi_cartella, leggi_cartelle, leggi_note_txt
from percorsi import Selezione, pianifica_destinazioni, ricava_serie_ricambio


class TestFiltroRevisioni(unittest.TestCase):
    def test_serie_e_modifica(self):
        nomi = (
            "M14075C19-0.MIN",
            "P14075C19-0.MIN",
            "M14075C19-1.MIN",
            "P14075C19-1.MIN",
            "M14075C19-2.MIN",
        )
        with tempfile.TemporaryDirectory() as cartella:
            for nome in nomi:
                Path(cartella, nome).touch()

            serie = leggi_cartella(cartella, "SERIE")
            modifica = leggi_cartella(cartella, "MODIFICA")

        self.assertEqual([elemento.identificativo for elemento in serie], ["14075C19-0"])
        self.assertEqual(serie[0].varianti, {"M", "P"})
        self.assertEqual(
            [(elemento.identificativo, elemento.varianti) for elemento in modifica],
            [("14075C19-1", {"M", "P"}), ("14075C19-2", {"M"})],
        )

    def test_unisce_due_cartelle_prima_del_filtro(self):
        with tempfile.TemporaryDirectory() as prima, tempfile.TemporaryDirectory() as seconda:
            Path(prima, "M14075C19-1.MIN").touch()
            Path(seconda, "P14075C19-1.MIN").touch()
            Path(seconda, "R14075C19-1.MIN").touch()

            elementi = leggi_cartelle((prima, seconda), "MODIFICA")

        self.assertEqual(len(elementi), 1)
        self.assertEqual(elementi[0].identificativo, "14075C19-1")
        self.assertEqual(elementi[0].varianti, {"M", "P", "R"})

    def test_legge_titolo_e_prima_riga_txt(self):
        with tempfile.TemporaryDirectory() as cartella:
            Path(cartella, "avviso.txt").write_text("Prima riga\nSeconda riga", encoding="utf-8")

            note = leggi_note_txt((cartella,))

        self.assertEqual([(nota.titolo, nota.prima_riga) for nota in note], [("avviso.txt", "Prima riga")])


class TestDestinazioni(unittest.TestCase):
    def setUp(self):
        self.radice = os.path.join("TORNIO")
        self.elemento = ElementoProgramma(
            "25040-0",
            varianti={"M", "P", "S", "R", "T"},
            percorsi={
                variante: os.path.join("SORGENE", f"{variante}25040-0.MIN")
                for variante in "MPSRT"
            },
        )
        self.giorno = date(2026, 9, 15)

    def _percorsi(self, cosa, tipo):
        return {
            f"TORNI_{cosa}_{tipo}_1": self.radice,
            f"TORNI_{cosa}_{tipo}_2": "",
        }

    def _piano(self, cosa, tipo, codice="25040", sorgenti=("SORGENE",)):
        return pianifica_destinazioni(
            self._percorsi(cosa, tipo),
            Selezione(cosa, tipo),
            codice,
            [self.elemento],
            sorgenti,
            self.giorno,
        )

    def test_rulli_serie_divide_sgrossatura_e_finitura(self):
        piano = self._piano("RULLI", "SERIE")
        destinazioni = {
            operazione.variante: operazione.cartella_destinazione
            for operazione in piano
        }
        self.assertEqual(set(destinazioni), {"M", "P", "S"})
        self.assertEqual(
            destinazioni["M"], os.path.join(self.radice, "SGROSSATURA", "25040")
        )
        self.assertEqual(
            destinazioni["P"], os.path.join(self.radice, "FINITURA", "25040")
        )
        self.assertEqual(destinazioni["P"], destinazioni["S"])

    def test_rulli_modifica_include_mpsrt_e_data(self):
        piano = self._piano("RULLI", "MODIFICA")
        self.assertEqual({operazione.variante for operazione in piano}, set("MPSRT"))
        self.assertTrue(all(
            operazione.cartella_destinazione
            == os.path.join(self.radice, "MODIFICHE", "25040", "15-09-26")
            for operazione in piano
        ))

    def test_rulli_ricambio_ricava_serie_dalla_sorgente(self):
        sorgente = os.path.join("RULLI", "RICAMBI", "SERIE 25010", "Z30100")
        self.assertEqual(ricava_serie_ricambio((sorgente,)), "25010")
        piano = self._piano("RULLI", "RICAMBIO", "30100", (sorgente,))
        self.assertEqual({operazione.variante for operazione in piano}, set("MPS"))
        self.assertTrue(all(
            operazione.cartella_destinazione
            == os.path.join(self.radice, "MODIFICHE", "Z30100", "25010")
            for operazione in piano
        ))

    def test_accessori_serie(self):
        piano = self._piano("ACCESSORI", "SERIE")
        self.assertEqual({operazione.variante for operazione in piano}, set("MPS"))
        self.assertTrue(all(
            operazione.cartella_destinazione
            == os.path.join(self.radice, "ACCESSORI", "25040")
            for operazione in piano
        ))

    def test_accessori_modifica_include_mpsrt_e_data(self):
        piano = self._piano("ACCESSORI", "MODIFICA")
        self.assertEqual({operazione.variante for operazione in piano}, set("MPSRT"))
        self.assertTrue(all(
            operazione.cartella_destinazione
            == os.path.join(
                self.radice, "ACCESSORI", "MODIFICHE", "25040", "15-09-26"
            )
            for operazione in piano
        ))

    def test_accessori_ricambio(self):
        sorgente = os.path.join("RULLI", "RICAMBI", "25010", "Z30100")
        piano = self._piano("ACCESSORI", "RICAMBIO", "Z30100", (sorgente,))
        self.assertEqual({operazione.variante for operazione in piano}, set("MPS"))
        self.assertTrue(all(
            operazione.cartella_destinazione
            == os.path.join(
                self.radice, "ACCESSORI", "MODIFICHE", "Z30100", "25010"
            )
            for operazione in piano
        ))


if __name__ == "__main__":
    unittest.main()
