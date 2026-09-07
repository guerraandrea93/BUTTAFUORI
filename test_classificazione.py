import tempfile
import unittest
from pathlib import Path

from classificazione import leggi_cartella, leggi_cartelle


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


if __name__ == "__main__":
    unittest.main()
