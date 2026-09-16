"""GUI principale: selezione e verifica delle sorgenti RULLI."""
import os
import queue
import shutil
import threading
import tkinter as tk
from datetime import datetime
from tkinter import filedialog, messagebox, ttk

try:
    from .classificazione import ElementoProgramma, leggi_contenuto_cartelle
    from .funzioni import CHIAVI_SORGENTI, CHIAVI_SORGENTI_OBBLIGATORIE, CHIAVI_TORNI, ETICHETTE_SORGENTI, ETICHETTE_TORNI, COLORE_AZZURRO, COLORE_NAVY, COLORE_RIGA_ALTERNATA, COLORE_TESTO, inizializza_percorsi, salva_percorsi
    from .percorsi import Selezione, applica_destinazione_temporanea, cartelle_sorgenti, descrizione_sorgente, pianifica_destinazioni
    from .warning import valuta
except ImportError:
    from classificazione import ElementoProgramma, leggi_contenuto_cartelle
    from funzioni import CHIAVI_SORGENTI, CHIAVI_SORGENTI_OBBLIGATORIE, CHIAVI_TORNI, ETICHETTE_SORGENTI, ETICHETTE_TORNI, COLORE_AZZURRO, COLORE_NAVY, COLORE_RIGA_ALTERNATA, COLORE_TESTO, inizializza_percorsi, salva_percorsi
    from percorsi import Selezione, applica_destinazione_temporanea, cartelle_sorgenti, descrizione_sorgente, pianifica_destinazioni
    from warning import valuta


DIMENSIONE_BLOCCO = 150


def etichetta_elemento(elemento: ElementoProgramma) -> str:
    return f"📁 {elemento.identificativo}" if elemento.is_cartella else elemento.identificativo


def main() -> None:
    root = tk.Tk()
    root.title("BUTTAFUORI - selezione sorgente")
    root.geometry("1050x650")
    root.minsize(820, 520)
    percorsi = inizializza_percorsi()
    cosa, tipo, codice, codice_z = (
        tk.StringVar(), tk.StringVar(), tk.StringVar(), tk.StringVar()
    )
    ordinamento = tk.StringVar(value="ALFABETICO")
    stato = tk.StringVar(value="Seleziona COSA e TIPO, poi inserisci un codice SERIE.")
    recenti_frame = ttk.Frame(root)
    cartella_corrente = [None]
    elementi_correnti: dict[str, ElementoProgramma] = {}
    piano_corrente = []
    destinazione_personalizzata = [None]
    selezione_piano = [()]
    caricamento_in_corso = [False]
    risultati_caricamento: queue.Queue = queue.Queue()

    def svuota_tabella():
        righe = table.get_children()
        if righe:
            table.delete(*righe)

    def svuota_note():
        for widget in note_area.winfo_children():
            widget.destroy()

    def apri_configurazione_percorsi(titolo, chiavi_percorsi):
        dialogo = tk.Toplevel(root)
        dialogo.title(titolo)
        dialogo.transient(root)
        dialogo.grab_set()
        dialogo.resizable(True, False)
        etichette = {
            nome: ETICHETTE_SORGENTI.get(
                nome,
                ETICHETTE_TORNI.get(
                    nome,
                    nome.rsplit("_", 1)[0].replace("_", " - ")
                    + " " + nome.rsplit("_", 1)[1],
                ),
            )
            for nome in chiavi_percorsi
        }
        valori = {nome: tk.StringVar(value=percorsi[nome]) for nome in chiavi_percorsi}

        def sfoglia(nome):
            percorso_attuale = valori[nome].get().strip()
            opzioni = {"parent": dialogo, "title": f"Seleziona cartella {nome}", "mustexist": True}
            if os.path.isdir(percorso_attuale):
                opzioni["initialdir"] = percorso_attuale
            selezionato = filedialog.askdirectory(**opzioni)
            if selezionato:
                valori[nome].set(selezionato)

        for riga, nome in enumerate(chiavi_percorsi):
            ttk.Label(dialogo, text=etichette[nome]).grid(row=riga, column=0, padx=(16, 8), pady=7, sticky="w")
            ttk.Entry(dialogo, textvariable=valori[nome], width=64).grid(row=riga, column=1, padx=8, pady=10, sticky="ew")
            ttk.Button(dialogo, text="Sfoglia...", command=lambda n=nome: sfoglia(n)).grid(row=riga, column=2, padx=(8, 16), pady=10)

        def salva():
            nuovi = {nome: valori[nome].get().strip() for nome in chiavi_percorsi}
            obbligatorie = set(CHIAVI_TORNI) | set(CHIAVI_SORGENTI_OBBLIGATORIE)
            non_validi = [
                nome for nome, percorso in nuovi.items()
                if (not percorso and nome in obbligatorie)
                or (percorso and not os.path.isdir(percorso))
            ]
            if non_validi:
                messagebox.showerror(
                    "Percorso non valido",
                    "Il percorso non esiste o non è una cartella:\n" + "\n".join(f"{nome}: {nuovi[nome]}" for nome in non_validi),
                    parent=dialogo,
                )
                return
            aggiornati = dict(percorsi)
            aggiornati.update(nuovi)
            try:
                salva_percorsi(aggiornati)
            except OSError as exc:
                messagebox.showerror("Errore salvataggio", f"Impossibile salvare i percorsi:\n{exc}", parent=dialogo)
                return
            sorgenti_modificate = any(
                nome in CHIAVI_SORGENTI and nuovi[nome] != percorsi[nome]
                for nome in chiavi_percorsi
            )
            percorsi.update(nuovi)
            aggiorna_destinazioni()
            if sorgenti_modificate:
                cartella_corrente[0] = None
                aggiorna_btn.configure(state="disabled")
                svuota_tabella()
                svuota_note()
                stato.set("Percorso RULLI aggiornato. Verifica nuovamente la sorgente.")
            dialogo.destroy()

        pulsanti = ttk.Frame(dialogo)
        pulsanti.grid(row=len(chiavi_percorsi), column=0, columnspan=3, padx=16, pady=(8, 16), sticky="e")
        ttk.Button(pulsanti, text="Annulla", command=dialogo.destroy).pack(side="left", padx=(0, 8))
        ttk.Button(pulsanti, text="Salva", command=salva).pack(side="left")
        dialogo.columnconfigure(1, weight=1)
        dialogo.wait_visibility()
        dialogo.focus_set()

    barra_menu = tk.Menu(root)
    menu_opzioni = tk.Menu(barra_menu, tearoff=False)
    menu_opzioni.add_command(
        label="Percorsi RULLI...",
        command=lambda: apri_configurazione_percorsi("Percorsi RULLI", CHIAVI_SORGENTI),
    )
    menu_opzioni.add_command(
        label="Percorsi TORNI...",
        command=lambda: apri_configurazione_percorsi("Percorsi TORNI", CHIAVI_TORNI),
    )
    barra_menu.add_cascade(label="Opzioni", menu=menu_opzioni)
    root.configure(menu=barra_menu)

    header = tk.Frame(root, bg=COLORE_NAVY)
    header.pack(fill="x")
    tk.Label(header, text="BUTTAFUORI", bg=COLORE_NAVY, fg="white", font=("Segoe UI", 20, "bold")).pack(anchor="w", padx=18, pady=10)
    controls = tk.Frame(root, bg=COLORE_AZZURRO)
    controls.pack(fill="x", padx=14, pady=14)

    radio_buttons = []

    def radio_row(row, label, variable, values):
        tk.Label(controls, text=label, bg=COLORE_AZZURRO, fg=COLORE_TESTO, width=10, anchor="w", font=("Segoe UI", 10, "bold")).grid(row=row, column=0, padx=10, pady=5, sticky="w")
        for col, value in enumerate(values, 1):
            radio = ttk.Radiobutton(controls, text=value, value=value, variable=variable)
            radio.grid(row=row, column=col, padx=8, pady=5, sticky="w")
            radio_buttons.append(radio)

    radio_row(0, "COSA", cosa, ("RULLI", "ACCESSORI"))
    radio_row(1, "TIPO", tipo, ("SERIE", "MODIFICA", "RICAMBIO"))
    tk.Label(controls, text="SERIE", bg=COLORE_AZZURRO, fg=COLORE_TESTO, width=10, anchor="w", font=("Segoe UI", 10, "bold")).grid(row=2, column=0, padx=10, pady=5, sticky="w")
    entry = ttk.Entry(controls, textvariable=codice, width=28)
    entry.grid(row=2, column=1, columnspan=2, padx=12, pady=5, sticky="ew")
    tk.Label(
        controls, text="Z RICAMBIO", bg=COLORE_AZZURRO, fg=COLORE_TESTO,
        width=10, anchor="w", font=("Segoe UI", 10, "bold"),
    ).grid(row=3, column=0, padx=10, pady=5, sticky="w")
    entry_z = ttk.Entry(controls, textvariable=codice_z, width=28, state="disabled")
    entry_z.grid(row=3, column=1, columnspan=2, padx=12, pady=5, sticky="ew")
    tk.Label(
        controls, text="ORDINA", bg=COLORE_AZZURRO, fg=COLORE_TESTO,
        width=10, anchor="w", font=("Segoe UI", 10, "bold"),
    ).grid(row=4, column=0, padx=10, pady=5, sticky="w")
    ordina_alfabetico = ttk.Radiobutton(
        controls, text="ALFABETICO", value="ALFABETICO", variable=ordinamento,
    )
    ordina_alfabetico.grid(row=4, column=1, padx=8, pady=5, sticky="w")
    ordina_modifica = ttk.Radiobutton(
        controls, text="ULTIMA MODIFICA", value="ULTIMA MODIFICA", variable=ordinamento,
    )
    ordina_modifica.grid(row=4, column=2, padx=8, pady=5, sticky="w")
    radio_buttons.extend((ordina_alfabetico, ordina_modifica))

    body = ttk.Panedwindow(root, orient="horizontal")
    body.pack(fill="both", expand=True, padx=14, pady=(0, 14))
    sinistra = ttk.Frame(body)
    destra = ttk.LabelFrame(body, text="DESTINAZIONI PREVISTE")
    body.add(sinistra, weight=3)
    body.add(destra, weight=2)
    status_bar = ttk.Frame(sinistra)
    status_bar.pack(fill="x", pady=(0, 6))
    ttk.Label(status_bar, textvariable=stato).pack(side="left", anchor="w")
    note_area = ttk.Frame(sinistra)
    note_area.pack(fill="x", pady=(0, 6))
    columns = ("PRT", "M", "P", "S", "R", "T", "modifica", "warning")
    table = ttk.Treeview(sinistra, columns=columns, show="tree headings", selectmode="extended")
    table.heading("#0", text="RULLO / ACCESSORIO")
    table.column("#0", width=260, anchor="w")
    for col in ("PRT", "M", "P", "S", "R", "T"):
        table.heading(col, text=col)
        table.column(col, width=45, anchor="center")
    table.heading("modifica", text="ULTIMA MODIFICA")
    table.column("modifica", width=135, anchor="center")
    table.heading("warning", text="WARNING VISIVO")
    table.column("warning", width=320, anchor="w")
    table.tag_configure("pari", background=COLORE_RIGA_ALTERNATA)
    table.tag_configure("dispari", background="white")
    table.tag_configure("warning", background="#FFFBE6", foreground="#7A4B00")
    scroll = ttk.Scrollbar(sinistra, orient="vertical", command=table.yview)
    table.configure(yscrollcommand=scroll.set)
    table.pack(side="left", fill="both", expand=True)
    scroll.pack(side="right", fill="y")

    ttk.Label(
        destra,
        text="Seleziona uno o più programmi per vedere le cartelle in cui verranno copiati.",
        wraplength=360,
        justify="left",
    ).pack(fill="x", padx=10, pady=(8, 6))
    colonne_destinazione = ("programma", "cartella", "stato")
    tabella_destinazioni = ttk.Treeview(
        destra, columns=colonne_destinazione, show="headings", selectmode="none",
    )
    tabella_destinazioni.heading("programma", text="FILE")
    tabella_destinazioni.heading("cartella", text="CARTELLA")
    tabella_destinazioni.heading("stato", text="STATO")
    tabella_destinazioni.column("programma", width=130, anchor="w")
    tabella_destinazioni.column("cartella", width=230, anchor="w")
    tabella_destinazioni.column("stato", width=130, anchor="center")
    tabella_destinazioni.pack(fill="both", expand=True, padx=10, pady=(0, 8))
    pulsanti_destinazione = ttk.Frame(destra)
    pulsanti_destinazione.pack(fill="x", padx=10, pady=(0, 8))
    cambia_dest_btn = ttk.Button(
        pulsanti_destinazione,
        text="CAMBIA DESTINAZIONE...",
        state="disabled",
        command=lambda: cambia_destinazione(),
    )
    cambia_dest_btn.pack(side="left", fill="x", expand=True)
    ripristina_dest_btn = ttk.Button(
        pulsanti_destinazione,
        text="RIPRISTINA REGOLA",
        state="disabled",
        command=lambda: ripristina_destinazione(),
    )
    ripristina_dest_btn.pack(side="left", fill="x", expand=True, padx=(8, 0))
    copia_btn = ttk.Button(
        destra, text="COPIA PROGRAMMI", state="disabled",
        command=lambda: copia_programmi(),
    )
    copia_btn.pack(fill="x", padx=10, pady=(0, 10))

    def aggiorna_destinazioni(*_):
        for item in tabella_destinazioni.get_children():
            tabella_destinazioni.delete(item)
        piano_corrente.clear()
        identificativi = tuple(sorted(
            table.item(item, "text")
            for item in table.selection()
            if table.item(item, "text") in elementi_correnti
        ))
        if identificativi != selezione_piano[0]:
            destinazione_personalizzata[0] = None
            selezione_piano[0] = identificativi
        selezionati = [elementi_correnti[nome] for nome in identificativi]
        if not selezionati or cartella_corrente[0] is None:
            cambia_dest_btn.configure(state="disabled")
            ripristina_dest_btn.configure(state="disabled")
            copia_btn.configure(state="disabled")
            return
        try:
            piano = pianifica_destinazioni(
                percorsi,
                Selezione(cosa.get(), tipo.get()),
                codice.get(),
                selezionati,
                cartella_corrente[0],
                cartella_z=codice_z.get(),
            )
        except ValueError as exc:
            tabella_destinazioni.insert("", "end", values=("ERRORE", str(exc), "BLOCCATO"))
            cambia_dest_btn.configure(state="disabled")
            ripristina_dest_btn.configure(state="disabled")
            copia_btn.configure(state="disabled")
            return
        if destinazione_personalizzata[0]:
            piano = applica_destinazione_temporanea(
                piano, destinazione_personalizzata[0]
            )
        piano_corrente.extend(piano)
        for operazione in piano:
            if os.path.isfile(operazione.destinazione):
                esito = "SOVRASCRIVE"
            elif os.path.isdir(operazione.cartella_destinazione):
                esito = "ESISTE"
            else:
                esito = "DA CREARE"
            if destinazione_personalizzata[0]:
                esito = "MANUALE · " + esito
            tabella_destinazioni.insert(
                "", "end",
                values=(operazione.nome_file, operazione.cartella_destinazione, esito),
            )
        attivo = "normal" if piano_corrente else "disabled"
        cambia_dest_btn.configure(state=attivo)
        ripristina_dest_btn.configure(
            state="normal" if destinazione_personalizzata[0] else "disabled"
        )
        copia_btn.configure(state=attivo)

    def cambia_destinazione():
        if not piano_corrente:
            return
        iniziale = piano_corrente[0].cartella_destinazione
        while iniziale and not os.path.isdir(iniziale):
            genitore = os.path.dirname(iniziale)
            if genitore == iniziale:
                iniziale = ""
                break
            iniziale = genitore
        opzioni = {
            "parent": root,
            "title": "Destinazione temporanea per i file selezionati",
            "mustexist": True,
        }
        if iniziale:
            opzioni["initialdir"] = iniziale
        scelta = filedialog.askdirectory(**opzioni)
        if scelta:
            destinazione_personalizzata[0] = scelta
            aggiorna_destinazioni()

    def ripristina_destinazione():
        destinazione_personalizzata[0] = None
        aggiorna_destinazioni()

    def copia_programmi():
        if not piano_corrente:
            return
        cartelle = {operazione.cartella_destinazione for operazione in piano_corrente}
        sovrascritture = sum(
            os.path.isfile(operazione.destinazione) for operazione in piano_corrente
        )
        dettaglio = (
            f"File da copiare: {len(piano_corrente)}\n"
            f"Cartelle interessate: {len(cartelle)}"
        )
        if sovrascritture:
            dettaglio += f"\nFile esistenti da sovrascrivere: {sovrascritture}"
        if not messagebox.askyesno(
            "Conferma copia",
            dettaglio + "\n\nProcedere con la copia?",
            parent=root,
        ):
            return
        errori = []
        copiati = 0
        for operazione in piano_corrente:
            try:
                os.makedirs(operazione.cartella_destinazione, exist_ok=True)
                shutil.copy2(operazione.sorgente, operazione.destinazione)
                copiati += 1
            except OSError as exc:
                errori.append(f"{operazione.nome_file}: {exc}")
        if not errori:
            destinazione_personalizzata[0] = None
        aggiorna_destinazioni()
        if errori:
            messagebox.showwarning(
                "Copia completata con errori",
                f"Copiati: {copiati}\nErrori: {len(errori)}\n\n"
                + "\n".join(errori[:10]),
                parent=root,
            )
        else:
            messagebox.showinfo(
                "Copia completata",
                f"Copiati correttamente {copiati} file.",
                parent=root,
            )

    def mostra_note_txt(note):
        svuota_note()
        for nota in note:
            riga = tk.Frame(note_area, bg="#FFF3B0", padx=8, pady=5)
            riga.pack(fill="x", pady=2)
            tk.Label(riga, text=nota.titolo, bg="#FFF3B0", fg="#5C4500", font=("Segoe UI", 10, "bold")).pack(side="left")
            tk.Label(riga, text=nota.prima_riga or "(prima riga vuota)", bg="#FFF3B0", fg="#5C4500", anchor="w").pack(side="left", fill="x", expand=True, padx=(12, 0))

    def imposta_controlli_caricamento(attivo: bool):
        stato_widget = "disabled" if attivo else "normal"
        entry.configure(state=stato_widget)
        entry_z.configure(
            state="normal" if not attivo and tipo.get() == "RICAMBIO" else "disabled"
        )
        verifica_btn.configure(state=stato_widget)
        for radio in radio_buttons:
            radio.configure(state=stato_widget)
        latest_btn.configure(
            state="disabled" if attivo or not (cosa.get() and tipo.get()) else "normal"
        )
        aggiorna_btn.configure(
            state="disabled" if attivo or cartella_corrente[0] is None else "normal"
        )

    def termina_caricamento(
        cartelle_esistenti,
        elementi,
        note,
        date_modifica,
        selezionati,
        tipo_corrente,
        indice=0,
        da_selezionare=None,
    ):
        if da_selezionare is None:
            mostra_note_txt(note)
            elementi_correnti.update(
                (etichetta_elemento(elemento), elemento) for elemento in elementi
            )
            da_selezionare = []

        fine = min(indice + DIMENSIONE_BLOCCO, len(elementi))
        for posizione in range(indice, fine):
            elemento = elementi[posizione]
            warning = valuta(elemento, tipo_corrente)
            flags = tuple("✓" if presente else "" for presente in (
                elemento.presenza_prt, elemento.presenza_m, elemento.presenza_p,
                elemento.presenza_s, elemento.presenza_r, elemento.presenza_t,
            ))
            tag = "warning" if warning else ("pari" if posizione % 2 == 0 else "dispari")
            etichetta = etichetta_elemento(elemento)
            timestamp = date_modifica[etichetta]
            modifica = (
                datetime.fromtimestamp(timestamp).strftime("%d/%m/%Y %H:%M")
                if timestamp else "—"
            )
            item_id = table.insert(
                "", "end", text=etichetta,
                values=(*flags, modifica, "⚠ " + "; ".join(warning) if warning else ""),
                tags=(tag,),
            )
            if etichetta in selezionati:
                da_selezionare.append(item_id)

        if fine < len(elementi):
            stato.set(f"Creazione tabella: {fine}/{len(elementi)} elementi")
            root.after_idle(
                termina_caricamento,
                cartelle_esistenti, elementi, note, date_modifica,
                selezionati, tipo_corrente, fine, da_selezionare,
            )
            return

        if da_selezionare:
            table.selection_set(da_selezionare)
        caricamento_in_corso[0] = False
        imposta_controlli_caricamento(False)
        aggiorna_destinazioni()
        stato.set(f"{' | '.join(cartelle_esistenti)} - {len(elementi)} elementi")

    def controlla_caricamenti():
        try:
            while True:
                dati = risultati_caricamento.get_nowait()
                if dati[0] == "errore":
                    caricamento_in_corso[0] = False
                    imposta_controlli_caricamento(False)
                    stato.set(f"Errore durante la lettura: {dati[1]}")
                    continue

                _, cartelle, cartelle_esistenti, selezionati, tipo_corrente, risultato, date_modifica = dati
                if not cartelle_esistenti:
                    caricamento_in_corso[0] = False
                    cartella_corrente[0] = None
                    mostra_note_txt(())
                    imposta_controlli_caricamento(False)
                    stato.set("Sorgente non trovata: " + " | ".join(cartelle))
                    continue

                cartella_corrente[0] = cartelle
                termina_caricamento(
                    cartelle_esistenti,
                    risultato.elementi,
                    risultato.note,
                    date_modifica,
                    selezionati,
                    tipo_corrente,
                )
        except queue.Empty:
            pass
        root.after(50, controlla_caricamenti)

    def carica(cartelle: list[str], mantieni_selezione: bool = False) -> None:
        if caricamento_in_corso[0]:
            return
        caricamento_in_corso[0] = True
        selezionati = {
            table.item(item, "text") for item in table.selection()
        } if mantieni_selezione else set()
        if not mantieni_selezione:
            destinazione_personalizzata[0] = None
            selezione_piano[0] = ()
        tipo_corrente = tipo.get()
        ordinamento_corrente = ordinamento.get()
        svuota_tabella()
        svuota_note()
        elementi_correnti.clear()
        aggiorna_destinazioni()
        imposta_controlli_caricamento(True)
        stato.set("Lettura cartelle in corso...")

        def lavoro():
            try:
                cartelle_esistenti = [
                    cartella for cartella in cartelle if os.path.isdir(cartella)
                ]
                risultato = leggi_contenuto_cartelle(cartelle_esistenti, tipo_corrente)
                date_modifica = {}
                for elemento in risultato.elementi:
                    date = []
                    for percorso in elemento.percorsi.values():
                        try:
                            date.append(os.path.getmtime(percorso))
                        except OSError:
                            continue
                    date_modifica[etichetta_elemento(elemento)] = max(date, default=0.0)

                if ordinamento_corrente == "ULTIMA MODIFICA":
                    risultato.elementi.sort(
                        key=lambda elemento: (
                            date_modifica[etichetta_elemento(elemento)],
                            elemento.identificativo.casefold(),
                        ),
                        reverse=True,
                    )
                else:
                    risultato.elementi.sort(
                        key=lambda elemento: elemento.identificativo.casefold()
                    )
                risultati_caricamento.put((
                    "ok", cartelle, cartelle_esistenti, selezionati,
                    tipo_corrente, risultato, date_modifica,
                ))
            except Exception as exc:
                risultati_caricamento.put(("errore", exc))

        threading.Thread(
            target=lavoro, name="lettura-sorgenti", daemon=True
        ).start()

    def verifica():
        recenti_frame.pack_forget()
        value = codice.get().strip()
        z_value = codice_z.get().strip()
        if not value or not cosa.get() or not tipo.get():
            stato.set("Completa COSA, TIPO e SERIE.")
            return
        if tipo.get() == "RICAMBIO" and not z_value:
            stato.set("Per i RICAMBI inserisci anche la cartella Z.")
            return
        carica(cartelle_sorgenti(
            percorsi,
            Selezione(cosa.get(), tipo.get()),
            value,
            z_value,
        ))

    def aggiorna():
        if cartella_corrente[0] is not None:
            carica(cartella_corrente[0], mantieni_selezione=True)

    def scegli_recente(name):
        codice.set(name.removeprefix("Z"))
        recenti_frame.pack_forget()
        verifica()

    def mostra_recenti():
        for child in recenti_frame.winfo_children():
            child.destroy()
        parents = {
            os.path.dirname(cartella)
            for cartella in cartelle_sorgenti(percorsi, Selezione(cosa.get(), tipo.get()), "_")
        }
        candidate = {}
        errori = []
        for parent in parents:
            try:
                with os.scandir(parent) as voci:
                    for voce in voci:
                        if voce.is_dir():
                            modifica = voce.stat().st_mtime
                            precedente = candidate.get(voce.name.casefold())
                            if precedente is None or modifica > precedente[1]:
                                candidate[voce.name.casefold()] = (voce.name, modifica)
            except OSError as exc:
                errori.append(str(exc))
        candidate = sorted(candidate.values(), key=lambda voce: voce[1], reverse=True)[:5]
        if not candidate and errori:
            stato.set(f"Impossibile leggere le ultime cartelle: {errori[0]}")
            return
        if not candidate:
            ttk.Label(recenti_frame, text="Nessuna cartella pertinente trovata.").pack(anchor="w")
        for nome, modifica in candidate:
            when = datetime.fromtimestamp(modifica).strftime("%d/%m/%Y %H:%M")
            ttk.Button(recenti_frame, text=f"{nome}    {when}", command=lambda n=nome: scegli_recente(n)).pack(fill="x", pady=2)
        recenti_frame.pack(fill="x", padx=14, pady=(0, 8), before=body)

    def abilita_recenti(*_):
        if not caricamento_in_corso[0]:
            latest_btn.configure(state="normal" if cosa.get() and tipo.get() else "disabled")
            entry_z.configure(state="normal" if tipo.get() == "RICAMBIO" else "disabled")

    cosa.trace_add("write", abilita_recenti)
    tipo.trace_add("write", abilita_recenti)
    ordinamento.trace_add("write", lambda *_: aggiorna())
    table.bind("<<TreeviewSelect>>", aggiorna_destinazioni)
    aggiorna_btn = ttk.Button(status_bar, text="↻ AGGIORNA", command=aggiorna, state="disabled")
    aggiorna_btn.pack(side="right")
    latest_btn = ttk.Button(controls, text="ULTIME MODIFICATE", command=mostra_recenti, state="disabled")
    latest_btn.grid(row=2, column=3, padx=12, pady=5)
    verifica_btn = ttk.Button(controls, text="VERIFICA SORGENTE", command=verifica)
    verifica_btn.grid(row=2, column=4, padx=8, pady=5)
    entry.bind("<Return>", lambda _: verifica())
    entry_z.bind("<Return>", lambda _: verifica())
    controls.columnconfigure(2, weight=0)
    footer = ttk.Frame(root)
    footer.pack(fill="x", padx=14, pady=(0, 12))
    ttk.Button(footer, text="SELEZIONA TUTTI", command=lambda: table.selection_set(table.get_children())).pack(side="left")
    ttk.Label(
        footer, text="Controlla le destinazioni a destra prima di copiare."
    ).pack(side="right")
    root.after(50, controlla_caricamenti)
    root.mainloop()


if __name__ == "__main__":
    main()
