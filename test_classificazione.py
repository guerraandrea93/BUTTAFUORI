import os
import tempfile
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import patch

from classificazione import ElementoProgramma, leggi_cartella, leggi_cartelle, leggi_contenuto_cartelle, leggi_note_txt
from funzioni import CHIAVI_TORNI, ETICHETTE_TORNI
from percorsi import Selezione, applica_destinazione_temporanea, cartelle_sorgenti, pianifica_destinazioni, ricava_serie_ricambio


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

    def test_programmi_e_note_usano_una_sola_scansione(self):
        with tempfile.TemporaryDirectory() as cartella:
            Path(cartella, "M14075C19-0.MIN").touch()
            Path(cartella, "14075C19-0.PRT").touch()
            Path(cartella, "avviso.txt").write_text(
                "Controllare il rullo\n", encoding="utf-8"
            )

            with patch("classificazione.os.scandir", wraps=os.scandir) as scandir:
                risultato = leggi_contenuto_cartelle((cartella,), "SERIE")

        self.assertEqual(scandir.call_count, 1)
        self.assertEqual(len(risultato.elementi), 1)
        self.assertTrue(risultato.elementi[0].presenza_prt)
        self.assertEqual(risultato.elementi[0].varianti, {"M"})
        self.assertEqual(risultato.note[0].prima_riga, "Controllare il rullo")

    def test_mostra_cartella_e_legge_i_suoi_file_immediati(self):
        with tempfile.TemporaryDirectory() as cartella:
            cartella_z = Path(cartella, "Z30100")
            cartella_z.mkdir()
            Path(cartella_z, "M30100-0.MIN").touch()
            Path(cartella_z, "P30100-0.MIN").touch()
            Path(cartella_z, "30100-0.PRT").touch()
            Path(cartella_z, "nota.txt").write_text("Nota ricambio\n", encoding="utf-8")

            risultato = leggi_contenuto_cartelle((cartella,), "RICAMBIO")

        self.assertEqual(len(risultato.elementi), 1)
        elemento = risultato.elementi[0]
        self.assertEqual(elemento.identificativo, "Z30100")
        self.assertTrue(elemento.is_cartella)
        self.assertTrue(elemento.presenza_prt)
        self.assertEqual(elemento.varianti, {"M", "P"})
        self.assertEqual(len(elemento.file_min), 2)
        self.assertEqual(risultato.note[0].titolo, "Z30100 / nota.txt")


class TestDestinazioni(unittest.TestCase):
    def setUp(self):
        self.sgrossatura = os.path.join("TORNIO", "SGROSSATURA")
        self.finitura = os.path.join("TORNIO", "FINITURA")
        self.modifiche = os.path.join("TORNIO", "MODIFICHE")
        self.acc_serie = os.path.join("TORNIO", "ACC", "SERIE")
        self.acc_modifiche = os.path.join("TORNIO", "ACC", "MODIFICHE")
        self.elemento = ElementoProgramma(
            "25040-0",
            varianti={"M", "P", "S", "R", "T"},
            percorsi={
                variante: os.path.join("SORGENE", f"{variante}25040-0.MIN")
                for variante in "MPSRT"
            },
        )
        self.giorno = date(2026, 9, 15)

    def _percorsi(self):
        return {
            "TORNI_SGROSSATURA": self.sgrossatura,
            "TORNI_FINITURA": self.finitura,
            "TORNI_MODIFICHE": self.modifiche,
            "TORNI_ACC_SERIE": self.acc_serie,
            "TORNI_ACC_MODIFICHE": self.acc_modifiche,
        }

    def _piano(self, cosa, tipo, codice="25040", sorgenti=("SORGENE",), elementi=None):
        percorsi = self._percorsi()
        original_isdir = os.path.isdir
        try:
            os.path.isdir = lambda percorso: percorso in percorsi.values()
            return pianifica_destinazioni(
                percorsi,
                Selezione(cosa, tipo),
                codice,
                elementi or [self.elemento],
                sorgenti,
                self.giorno,
            )
        finally:
            os.path.isdir = original_isdir

    def test_configura_esattamente_cinque_cartelle_torni(self):
        self.assertEqual(
            CHIAVI_TORNI,
            (
                "TORNI_SGROSSATURA",
                "TORNI_FINITURA",
                "TORNI_MODIFICHE",
                "TORNI_ACC_SERIE",
                "TORNI_ACC_MODIFICHE",
            ),
        )
        self.assertEqual(
            set(ETICHETTE_TORNI.values()),
            {
                "TORNIO / SGROSSATURA",
                "TORNIO / FINITURA",
                "TORNIO / MODIFICHE",
                "TORNIO / ACC / SERIE",
                "TORNIO / ACC / MODIFICHE",
            },
        )

    def test_rulli_serie_divide_sgrossatura_e_finitura(self):
        piano = self._piano("RULLI", "SERIE")
        destinazioni = {
            operazione.variante: operazione.cartella_destinazione
            for operazione in piano
        }
        self.assertEqual(set(destinazioni), {"M", "P", "S"})
        self.assertEqual(
            destinazioni["M"], os.path.join(self.sgrossatura, "25040")
        )
        self.assertEqual(
            destinazioni["P"], os.path.join(self.finitura, "25040")
        )
        self.assertEqual(destinazioni["P"], destinazioni["S"])

    def test_rulli_modifica_include_mpsrt_e_data(self):
        piano = self._piano("RULLI", "MODIFICA")
        self.assertEqual({operazione.variante for operazione in piano}, set("MPSRT"))
        self.assertTrue(all(
            operazione.cartella_destinazione
            == os.path.join(self.modifiche, "25040", "15-09-26")
            for operazione in piano
        ))

    def test_rulli_ricambio_ricava_serie_dalla_sorgente(self):
        sorgente = os.path.join("RULLI", "RICAMBI", "SERIE 25010")
        self.assertEqual(ricava_serie_ricambio((sorgente,)), "25010")
        cartella_z = ElementoProgramma(
            "Z30100",
            varianti={"M", "P", "S"},
            file_min=[
                (variante, os.path.join("SORGENE", "Z30100", f"{variante}30100.MIN"))
                for variante in "MPS"
            ],
            is_cartella=True,
        )
        piano = self._piano(
            "RULLI", "RICAMBIO", "SERIE 25010", (sorgente,), [cartella_z]
        )
        self.assertEqual({operazione.variante for operazione in piano}, set("MPS"))
        self.assertTrue(all(
            operazione.cartella_destinazione
            == os.path.join(self.modifiche, "Z30100", "25010")
            for operazione in piano
        ))

    def test_accessori_serie(self):
        piano = self._piano("ACCESSORI", "SERIE")
        self.assertEqual({operazione.variante for operazione in piano}, set("MPS"))
        self.assertTrue(all(
            operazione.cartella_destinazione
            == os.path.join(self.acc_serie, "25040")
            for operazione in piano
        ))

    def test_accessori_modifica_include_mpsrt_e_data(self):
        piano = self._piano("ACCESSORI", "MODIFICA")
        self.assertEqual({operazione.variante for operazione in piano}, set("MPSRT"))
        self.assertTrue(all(
            operazione.cartella_destinazione
            == os.path.join(self.acc_modifiche, "25040", "15-09-26")
            for operazione in piano
        ))

    def test_accessori_ricambio(self):
        sorgente = os.path.join("RULLI", "RICAMBI", "25010")
        cartella_z = ElementoProgramma(
            "Z30100",
            varianti={"M", "P", "S"},
            file_min=[
                (variante, os.path.join("SORGENE", "Z30100", f"{variante}30100.MIN"))
                for variante in "MPS"
            ],
            is_cartella=True,
        )
        piano = self._piano(
            "ACCESSORI", "RICAMBIO", "25010", (sorgente,), [cartella_z]
        )
        self.assertEqual({operazione.variante for operazione in piano}, set("MPS"))
        self.assertTrue(all(
            operazione.cartella_destinazione
            == os.path.join(self.acc_modifiche, "Z30100", "25010")
            for operazione in piano
        ))

    def test_ricambio_apre_la_cartella_scritta_non_la_z(self):
        percorsi = {"RULLI_RICAMBIO_1": os.path.join("RULLI", "RICAMBI")}
        cartelle = cartelle_sorgenti(
            percorsi, Selezione("RULLI", "RICAMBIO"), "SERIE 25010"
        )
        self.assertEqual(
            cartelle,
            [os.path.join("RULLI", "RICAMBI", "SERIE 25010")],
        )

    def test_destinazione_temporanea_si_applica_al_piano_selezionato(self):
        piano = self._piano("RULLI", "MODIFICA")
        cartella_manual = os.path.join(self.modifiche, "25040", "12-09-26")
        modificato = applica_destinazione_temporanea(piano, cartella_manual)
        self.assertEqual(len(modificato), len(piano))
        self.assertTrue(all(
            operazione.cartella_destinazione == cartella_manual
            for operazione in modificato
        ))
        self.assertEqual(
            [operazione.sorgente for operazione in modificato],
            [operazione.sorgente for operazione in piano],
        )
        self.assertNotEqual(
            modificato[0].cartella_destinazione,
            piano[0].cartella_destinazione,
        )


if __name__ == "__main__":
    unittest.main()
