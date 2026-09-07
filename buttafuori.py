"""Interfaccia grafica del progetto BUTTAFUORI."""

import tkinter as tk
import os
import re
from datetime import datetime
from tkinter import ttk

try:
    import customtkinter as ctk
    MODERNA = True
except ImportError:
    MODERNA = False

try:
    from .funzioni import (COLORE_AZZURRO, COLORE_NAVY, COLORE_RIGA_ALTERNATA,
                           COLORE_SELEZIONE, COLORE_TESTO, inizializza_percorsi)
except ImportError:
    from funzioni import (COLORE_AZZURRO, COLORE_NAVY, COLORE_RIGA_ALTERNATA,
                          COLORE_SELEZIONE, COLORE_TESTO, inizializza_percorsi)


def main() -> None:
    """Avvia la GUI con CustomTkinter quando disponibile."""
    if MODERNA:
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")
        finestra = ctk.CTk()
        Frame, Label, Button, Entry = ctk.CTkFrame, ctk.CTkLabel, ctk.CTkButton, ctk.CTkEntry
    else:
        finestra = tk.Tk()
        Frame, Label, Button, Entry = ttk.Frame, ttk.Label, ttk.Button, ttk.Entry

    finestra.title("BUTTAFUORI")
    def massimizza_finestra() -> None:
        try:
            finestra.state("zoomed")
        except tk.TclError:
            finestra.geometry(f"{finestra.winfo_screenwidth()}x{finestra.winfo_screenheight()}+0+0")

    finestra.after(100, massimizza_finestra)
    finestra.configure(bg=COLORE_RIGA_ALTERNATA)
    percorsi = inizializza_percorsi()
    azioni_sezioni = {}

    def cambia_sorgenti() -> None:
        dialogo = ctk.CTkToplevel(finestra) if MODERNA else tk.Toplevel(finestra)
        dialogo.title("Cambia sorgenti")
        dialogo.geometry("650x220")
        dialogo.transient(finestra)
        dialogo.grab_set()
        pannello = Frame(dialogo, fg_color=COLORE_RIGA_ALTERNATA) if MODERNA else Frame(dialogo)
        pannello.pack(fill="both", expand=True, padx=20, pady=20)
        campi = {}
        for riga, nome in enumerate(("RULLI", "TORNIO")):
            Label(pannello, text=f"Percorso {nome}").grid(row=riga, column=0, padx=8, pady=10, sticky="w")
            campo = Entry(pannello, width=55)
            campo.insert(0, percorsi[nome])
            campo.grid(row=riga, column=1, padx=8, pady=10, sticky="ew")
            campi[nome] = campo
        pannello.columnconfigure(1, weight=1)
        def salva() -> None:
            percorsi.update({nome: campo.get().strip() for nome, campo in campi.items()})
            for azioni in azioni_sezioni.values():
                azioni["radice"]()
            dialogo.destroy()
        Button(pannello, text="Salva", command=salva).grid(row=2, column=1, padx=8, pady=12, sticky="e")

    barra_titolo = Frame(finestra, fg_color=COLORE_NAVY) if MODERNA else tk.Frame(finestra, bg=COLORE_NAVY)
    barra_titolo.pack(fill="x")
    Label(barra_titolo, text="BUTTAFUORI", text_color="white" if MODERNA else None,
          fg_color=COLORE_NAVY if MODERNA else None,
          font=("Segoe UI", 22, "bold")).pack(side="left", padx=18, pady=10)

    barra_menu = Frame(finestra, fg_color=COLORE_AZZURRO) if MODERNA else tk.Frame(finestra, bg=COLORE_AZZURRO)
    barra_menu.pack(fill="x")
    menu = tk.Menu(finestra, tearoff=False, bg=COLORE_AZZURRO, fg=COLORE_TESTO)
    opzioni = tk.Menu(menu, tearoff=False, bg=COLORE_AZZURRO, fg=COLORE_TESTO)
    opzioni.add_command(label="Cambia sorgenti", command=cambia_sorgenti)
    opzioni.add_separator()
    for nome in ("RULLI", "TORNIO"):
        sotto_menu = tk.Menu(opzioni, tearoff=False, bg=COLORE_AZZURRO, fg=COLORE_TESTO)
        sotto_menu.add_command(
            label="Nascondi selezionate",
            command=lambda n=nome: azioni_sezioni[n]["nascondi"](),
        )
        sotto_menu.add_command(
            label="Ripristina selezionate",
            command=lambda n=nome: azioni_sezioni[n]["ripristina"](),
        )
        sotto_menu.add_command(
            label="Ripristina tutte le righe nascoste",
            command=lambda n=nome: azioni_sezioni[n]["ripristina_tutte"](),
        )
        sotto_menu.add_command(
            label="Mostra / nascondi righe nascoste",
            command=lambda n=nome: azioni_sezioni[n]["alterna"](),
        )
        sotto_menu.add_command(
            label="Torna alla cartella principale",
            command=lambda n=nome: azioni_sezioni[n]["radice"](),
        )
        opzioni.add_cascade(label=nome, menu=sotto_menu)

    def apri_opzioni() -> None:
        posizione_x = barra_menu.winfo_rootx()
        posizione_y = barra_menu.winfo_rooty() + barra_menu.winfo_height()
        try:
            opzioni.tk_popup(posizione_x, posizione_y)
        finally:
            opzioni.grab_release()

    Button(barra_menu, text="Opzioni", command=apri_opzioni).pack(side="left", padx=8, pady=4)
    if MODERNA:
        schede = ctk.CTkTabview(finestra, fg_color=COLORE_RIGA_ALTERNATA,
                                 segmented_button_selected_color=COLORE_NAVY,
                                 segmented_button_selected_hover_color=COLORE_SELEZIONE)
        schede.pack(fill="both", expand=True, padx=20, pady=20)
        scheda_buttafuori = schede.add("BUTTAFUORI")
        scheda_esplora_file = schede.add("Esplora file")
    else:
        schede = ttk.Notebook(finestra)
        schede.pack(fill="both", expand=True, padx=20, pady=20)
        scheda_buttafuori = ttk.Frame(schede)
        schede.add(scheda_buttafuori, text="BUTTAFUORI")
        scheda_esplora_file = ttk.Frame(schede)
        schede.add(scheda_esplora_file, text="Esplora file")

    contenuto = Frame(scheda_esplora_file, fg_color=COLORE_RIGA_ALTERNATA if MODERNA else None)
    contenuto.pack(fill="both", expand=True, padx=20, pady=20)
    righe_nascoste = {"RULLI": set(), "TORNIO": set()}

    def crea_sezione(parent, nome):
        percorso_corrente = percorsi[nome]
        cronologia = []

        def torna_indietro() -> None:
            nonlocal percorso_corrente
            if cronologia:
                percorso_corrente = cronologia.pop()
                aggiorna_elenco()

        sezione = Frame(parent, fg_color=COLORE_AZZURRO if MODERNA else None)
        sezione.pack(side="left", fill="both", expand=True, padx=8)
        barra_percorso = Frame(sezione, fg_color=COLORE_AZZURRO if MODERNA else None)
        barra_percorso.pack(fill="x", padx=12, pady=10)
        if MODERNA:
            Button(barra_percorso, text="←", command=torna_indietro, width=34, height=28,
                   fg_color=COLORE_NAVY, hover_color=COLORE_SELEZIONE).pack(side="left", padx=(0, 8))
        else:
            Button(barra_percorso, text="←", command=torna_indietro).pack(side="left", padx=(0, 8))
        titolo_sezione = Label(barra_percorso, text=nome, text_color=COLORE_TESTO if MODERNA else None,
                               font=("Segoe UI", 24, "bold"))
        titolo_sezione.pack(side="left")
        barra_ricerca = Frame(sezione, fg_color=COLORE_AZZURRO if MODERNA else None)
        barra_ricerca.pack(fill="x", padx=12, pady=(0, 8))
        ricerca_var = tk.StringVar()
        Label(barra_ricerca, text="Cerca:", text_color=COLORE_TESTO if MODERNA else None).pack(
            side="left", padx=(0, 8)
        )
        campo_ricerca = Entry(barra_ricerca, textvariable=ricerca_var)
        campo_ricerca.pack(side="left", fill="x", expand=True)
        area_elenco = ttk.Frame(sezione)
        area_elenco.pack(fill="both", expand=True, padx=12, pady=(0, 12))
        tabella = ttk.Treeview(area_elenco, columns=("ultima_modifica", "creazione"), show="tree headings")
        tabella.column("#0", anchor="w", width=240)
        tabella.column("ultima_modifica", anchor="center", width=145)
        tabella.column("creazione", anchor="center", width=145)
        tabella.heading("ultima_modifica", text="Ultima modifica")
        tabella.heading("creazione", text="Creazione")
        tabella.tag_configure("pari", background=COLORE_RIGA_ALTERNATA)
        tabella.tag_configure("dispari", background="white")
        tabella.tag_configure("nascosta", background="#E5E7EB", foreground="#6B7280")
        barra_scorrimento = ttk.Scrollbar(area_elenco, orient="vertical", command=tabella.yview)
        tabella.configure(yscrollcommand=barra_scorrimento.set)
        tabella.pack(side="left", fill="both", expand=True)
        barra_scorrimento.pack(side="right", fill="y")

        def apri_cartella(event) -> None:
            nonlocal percorso_corrente
            riga = tabella.identify_row(event.y)
            if not riga:
                return
            elemento = tabella.item(riga, "text")
            cartella = os.path.join(percorso_corrente, elemento)
            if os.path.isdir(cartella):
                cronologia.append(percorso_corrente)
                percorso_corrente = cartella
                aggiorna_elenco()

        tabella.bind("<Double-1>", apri_cartella)

        mostra_nascoste = False
        ordinamento_colonna = "nome"
        ordinamento_decrescente = False
        def aggiorna_elenco() -> None:
            righe_correnti = tabella.get_children()
            if righe_correnti:
                tabella.delete(*righe_correnti)
            nome_cartella = os.path.basename(os.path.normpath(percorso_corrente))
            titolo = "SERIE" if re.fullmatch(r"\d{5,}[A-Za-z]*", nome_cartella) else nome_cartella
            tabella.heading("#0", text=titolo or nome)
            percorso_relativo = os.path.relpath(percorso_corrente, percorsi[nome])
            percorso_relativo_windows = percorso_relativo.replace(os.sep, "\\")
            percorso_visualizzato = nome if percorso_relativo == "." else (
                f"{nome}\\{percorso_relativo_windows}"
            )
            titolo_sezione.configure(text=percorso_visualizzato)
            try:
                elementi = sorted(os.listdir(percorso_corrente), key=str.lower)
            except OSError:
                elementi = []
            voci = []
            filtro = ricerca_var.get().strip().lower()
            for elemento in elementi:
                percorso_elemento = os.path.join(percorso_corrente, elemento)
                if not mostra_nascoste and percorso_elemento in righe_nascoste[nome]:
                    continue
                if filtro and filtro not in elemento.lower():
                    continue
                try:
                    statistiche = os.stat(percorso_elemento)
                    ultima_modifica = statistiche.st_mtime
                    creazione = statistiche.st_ctime
                except OSError:
                    ultima_modifica = creazione = 0
                voci.append((elemento, percorso_elemento, ultima_modifica, creazione))
            indice_ordinamento = {"nome": 0, "ultima_modifica": 2, "creazione": 3}[ordinamento_colonna]
            voci.sort(key=lambda voce: voce[indice_ordinamento].lower() if indice_ordinamento == 0
                       else voce[indice_ordinamento], reverse=ordinamento_decrescente)
            for indice, (elemento, percorso_elemento, ultima_modifica, creazione) in enumerate(voci):
                tag = "nascosta" if percorso_elemento in righe_nascoste[nome] else (
                    "pari" if indice % 2 == 0 else "dispari"
                )
                data_modifica = datetime.fromtimestamp(ultima_modifica).strftime("%d/%m/%Y %H:%M") if ultima_modifica else ""
                data_creazione = datetime.fromtimestamp(creazione).strftime("%d/%m/%Y %H:%M") if creazione else ""
                tabella.insert("", "end", text=elemento,
                               values=(data_modifica, data_creazione), tags=(tag,))

        def ordina_colonna(colonna: str) -> None:
            nonlocal ordinamento_colonna, ordinamento_decrescente
            if ordinamento_colonna == colonna:
                ordinamento_decrescente = not ordinamento_decrescente
            else:
                ordinamento_colonna = colonna
                ordinamento_decrescente = colonna != "nome"
            aggiorna_elenco()

        tabella.heading("#0", text="SERIE", command=lambda: ordina_colonna("nome"))
        tabella.heading("ultima_modifica", command=lambda: ordina_colonna("ultima_modifica"))
        tabella.heading("creazione", command=lambda: ordina_colonna("creazione"))
        campo_ricerca.bind("<KeyRelease>", lambda _evento: aggiorna_elenco())

        def nascondi_selezionate() -> None:
            righe_nascoste[nome].update(
                os.path.join(percorso_corrente, tabella.item(riga, "text"))
                for riga in tabella.selection()
            )
            aggiorna_elenco()

        menu_contestuale = tk.Menu(tabella, tearoff=False, bg=COLORE_AZZURRO, fg=COLORE_TESTO)
        menu_contestuale.add_command(label="Nascondi selezionate", command=nascondi_selezionate)

        def mostra_menu_contestuale(event) -> None:
            riga = tabella.identify_row(event.y)
            if not riga:
                return
            if riga not in tabella.selection():
                tabella.selection_set(riga)
            try:
                menu_contestuale.tk_popup(event.x_root, event.y_root)
            finally:
                menu_contestuale.grab_release()

        tabella.bind("<Button-3>", mostra_menu_contestuale)

        def ripristina_selezionate() -> None:
            for riga in tabella.selection():
                righe_nascoste[nome].discard(
                    os.path.join(percorso_corrente, tabella.item(riga, "text"))
                )
            aggiorna_elenco()

        def ripristina_tutte_le_righe() -> None:
            righe_nascoste[nome].clear()
            aggiorna_elenco()

        def alterna_righe_nascoste() -> None:
            nonlocal mostra_nascoste
            mostra_nascoste = not mostra_nascoste
            aggiorna_elenco()

        def torna_alla_radice() -> None:
            nonlocal percorso_corrente
            percorso_corrente = percorsi[nome]
            cronologia.clear()
            aggiorna_elenco()

        azioni_sezioni[nome] = {
            "nascondi": nascondi_selezionate,
            "ripristina": ripristina_selezionate,
            "ripristina_tutte": ripristina_tutte_le_righe,
            "alterna": alterna_righe_nascoste,
            "indietro": torna_indietro,
            "radice": torna_alla_radice,
        }
        aggiorna_elenco()
        return tabella

    crea_sezione(contenuto, "RULLI")
    crea_sezione(contenuto, "TORNIO")

    if MODERNA:
        sotto_schede = ctk.CTkTabview(scheda_buttafuori, fg_color=COLORE_RIGA_ALTERNATA,
                                       segmented_button_selected_color=COLORE_NAVY,
                                       segmented_button_selected_hover_color=COLORE_SELEZIONE)
        sotto_schede.pack(fill="both", expand=True, padx=20, pady=20)
        scheda_serie = sotto_schede.add("SERIE")
    else:
        sotto_schede = ttk.Notebook(scheda_buttafuori)
        sotto_schede.pack(fill="both", expand=True, padx=20, pady=20)
        scheda_serie = ttk.Frame(sotto_schede)
        sotto_schede.add(scheda_serie, text="SERIE")

    area_serie = Frame(scheda_serie, fg_color=COLORE_RIGA_ALTERNATA if MODERNA else None)
    area_serie.pack(fill="both", expand=True, padx=20, pady=20)
    barra_ricerca_serie = Frame(area_serie, fg_color=COLORE_AZZURRO if MODERNA else None)
    barra_ricerca_serie.pack(fill="x", pady=(0, 12))
    codice_serie = tk.StringVar()
    Label(barra_ricerca_serie, text="Codice serie:", text_color=COLORE_TESTO if MODERNA else None,
          font=("Segoe UI", 14, "bold")).pack(side="left", padx=12, pady=10)
    campo_codice_serie = Entry(barra_ricerca_serie, textvariable=codice_serie)
    campo_codice_serie.pack(side="left", fill="x", expand=True, padx=(0, 10), pady=10)

    stato_serie = Label(area_serie, text="Inserisci un codice serie per caricare i relativi file.",
                         text_color=COLORE_TESTO if MODERNA else None)
    stato_serie.pack(anchor="w", pady=(0, 8))
    corpo_serie = ttk.Frame(area_serie)
    corpo_serie.pack(fill="both", expand=True)
    area_tabella_serie = ttk.Frame(corpo_serie)
    area_tabella_serie.pack(side="left", fill="both", expand=True, padx=(0, 6))
    area_sgrossatura = ttk.Frame(corpo_serie)
    area_sgrossatura.pack(side="left", fill="both", expand=True, padx=6)
    area_finitura = ttk.Frame(corpo_serie)
    area_finitura.pack(side="left", fill="both", expand=True, padx=(6, 0))
    colonne_serie = ("revisione", "M", "P", "S", "R", "T", "ultima_modifica", "creazione")
    tabella_serie = ttk.Treeview(area_tabella_serie, columns=colonne_serie, show="tree headings")
    tabella_serie.heading("#0", text="NOME")
    tabella_serie.column("#0", anchor="w", width=250)
    tabella_serie.heading("revisione", text="Revisione")
    tabella_serie.column("revisione", anchor="center", width=80)
    for colonna in ("M", "P", "S", "R", "T"):
        tabella_serie.heading(colonna, text=colonna)
        tabella_serie.column(colonna, anchor="center", width=45)
    tabella_serie.heading("ultima_modifica", text="Ultima modifica")
    tabella_serie.heading("creazione", text="Creazione")
    tabella_serie.column("ultima_modifica", anchor="center", width=145)
    tabella_serie.column("creazione", anchor="center", width=145)
    tabella_serie.tag_configure("pari", background=COLORE_RIGA_ALTERNATA)
    tabella_serie.tag_configure("dispari", background="white")
    barra_scorrimento_serie = ttk.Scrollbar(area_tabella_serie, orient="vertical", command=tabella_serie.yview)
    tabella_serie.configure(yscrollcommand=barra_scorrimento_serie.set)
    tabella_serie.pack(side="left", fill="both", expand=True)
    barra_scorrimento_serie.pack(side="right", fill="y")

    def crea_sezione_tornio(parent, titolo: str):
        sezione_tornio = ttk.LabelFrame(parent, text=titolo, padding=8)
        sezione_tornio.pack(fill="both", expand=True, pady=(0, 12))
        stato = ttk.Label(sezione_tornio, text="Inserisci un codice serie.")
        stato.pack(anchor="w", pady=(0, 6))
        tabella = ttk.Treeview(sezione_tornio, columns=(), show="tree headings", height=8)
        tabella.heading("#0", text="SERIE")
        tabella.column("#0", width=250, anchor="w")
        tabella.tag_configure("pari", background=COLORE_RIGA_ALTERNATA)
        tabella.tag_configure("dispari", background="white")
        tabella.pack(fill="both", expand=True)
        return tabella, stato

    sezioni_tornio = {
        "SGROSSATURA": crea_sezione_tornio(area_sgrossatura, "SGROSSATURA"),
        "FINITURA": crea_sezione_tornio(area_finitura, "FINITURA"),
    }

    def svuota_tabella_serie() -> None:
        righe = tabella_serie.get_children()
        if righe:
            tabella_serie.delete(*righe)

    def svuota_tabella(tabella) -> None:
        righe = tabella.get_children()
        if righe:
            tabella.delete(*righe)

    def trova_cartella(codice: str, radice: str) -> str | None:
        percorso_diretto = os.path.join(radice, codice)
        if os.path.isdir(percorso_diretto):
            return percorso_diretto
        try:
            for percorso, cartelle, _file in os.walk(radice):
                for cartella in cartelle:
                    if cartella.casefold() == codice.casefold():
                        return os.path.join(percorso, cartella)
        except OSError:
            return None
        return None

    def aggiorna_sezioni_tornio(codice: str) -> None:
        for nome_sezione, (tabella, stato) in sezioni_tornio.items():
            svuota_tabella(tabella)
            if not codice:
                stato.configure(text="Inserisci un codice serie.")
                continue
            radice = os.path.join(percorsi["TORNIO"], nome_sezione)
            cartella = trova_cartella(codice, radice)
            if cartella:
                percorso_relativo = os.path.relpath(cartella, radice).replace(os.sep, "\\")
                tabella.insert("", "end", text=percorso_relativo, tags=("pari",))
                stato.configure(text="Cartella della serie trovata.")
            else:
                stato.configure(text="Cartella della serie non presente.")

    def carica_serie() -> None:
        svuota_tabella_serie()
        codice = codice_serie.get().strip()
        if not codice:
            stato_serie.configure(text="Inserisci un codice serie per caricare i relativi file.")
            aggiorna_sezioni_tornio("")
            return
        aggiorna_sezioni_tornio(codice)
        cartella_serie = trova_cartella(codice, percorsi["RULLI"])
        if not cartella_serie:
            stato_serie.configure(text=f"Serie {codice} non trovata in RULLI.")
            return
        stato_serie.configure(text=f"RULLI\\{os.path.relpath(cartella_serie, percorsi['RULLI'])}")
        try:
            file_serie = sorted(os.listdir(cartella_serie), key=str.lower)
        except OSError:
            file_serie = []
        programmi = {}
        for file in file_serie:
            if not file.lower().endswith(".min"):
                continue
            nome_base = os.path.splitext(file)[0]
            lettera = nome_base[:1].upper()
            nome_programma = nome_base[1:].lstrip("_- ") if lettera in {"M", "P", "S", "R", "T"} else nome_base
            corrispondenza_revisione = re.search(r"-(\d+)$", nome_programma)
            revisione = corrispondenza_revisione.group(1) if corrispondenza_revisione else ""
            if corrispondenza_revisione:
                nome_programma = nome_programma[:corrispondenza_revisione.start()]
            try:
                statistiche = os.stat(os.path.join(cartella_serie, file))
                ultima_modifica = statistiche.st_mtime
                creazione = statistiche.st_ctime
            except OSError:
                ultima_modifica = creazione = 0
            programma = programmi.setdefault((nome_programma, revisione), {
                "lettere": set(), "ultima_modifica": 0, "creazione": 0,
            })
            if lettera in {"M", "P", "S", "R", "T"}:
                programma["lettere"].add(lettera)
            programma["ultima_modifica"] = max(programma["ultima_modifica"], ultima_modifica)
            if not programma["creazione"] or (creazione and creazione < programma["creazione"]):
                programma["creazione"] = creazione
        for indice, ((nome_programma, revisione), programma) in enumerate(
                sorted(programmi.items(), key=lambda voce: (voce[0][0].lower(), voce[0][1]))):
            ultima_modifica = programma["ultima_modifica"]
            creazione = programma["creazione"]
            data_modifica = datetime.fromtimestamp(ultima_modifica).strftime("%d/%m/%Y %H:%M") if ultima_modifica else ""
            data_creazione = datetime.fromtimestamp(creazione).strftime("%d/%m/%Y %H:%M") if creazione else ""
            spunte = tuple("✓" if lettera in programma["lettere"] else "" for lettera in ("M", "P", "S", "R", "T"))
            tabella_serie.insert("", "end", text=nome_programma,
                                 values=(revisione, *spunte, data_modifica, data_creazione),
                                 tags=("pari" if indice % 2 == 0 else "dispari",))

    Button(barra_ricerca_serie, text="Cerca", command=carica_serie).pack(side="right", padx=12, pady=10)
    campo_codice_serie.bind("<Return>", lambda _evento: carica_serie())
    finestra.mainloop()


if __name__ == "__main__":
    main()
