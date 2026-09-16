import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from classificazione import leggi_cartella, leggi_cartelle, leggi_contenuto_cartelle, leggi_note_txt


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
            Path(cartella, "avviso.txt").write_text("Controllare il rullo\n", encoding="utf-8")

            with patch("classificazione.os.scandir", wraps=os.scandir) as scandir:
                risultato = leggi_contenuto_cartelle((cartella,), "SERIE")

        self.assertEqual(scandir.call_count, 1)
        self.assertEqual(len(risultato.elementi), 1)
        self.assertTrue(risultato.elementi[0].presenza_prt)
        self.assertEqual(risultato.elementi[0].varianti, {"M"})
        self.assertEqual(risultato.note[0].prima_riga, "Controllare il rullo")


if __name__ == "__main__":
    unittest.main()
