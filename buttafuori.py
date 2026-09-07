"""GUI principale: selezione e verifica delle sorgenti RULLI."""
import os
import tkinter as tk
from datetime import datetime
from tkinter import filedialog, messagebox, ttk

try:
    from .classificazione import ElementoProgramma, leggi_cartelle
    from .funzioni import CHIAVI_SORGENTI, CHIAVI_TORNI, COLORE_AZZURRO, COLORE_NAVY, COLORE_RIGA_ALTERNATA, COLORE_TESTO, inizializza_percorsi, salva_percorsi
    from .percorsi import Selezione, cartelle_sorgenti, descrizione_sorgente
    from .warning import valuta
except ImportError:
    from classificazione import ElementoProgramma, leggi_cartelle
    from funzioni import CHIAVI_SORGENTI, CHIAVI_TORNI, COLORE_AZZURRO, COLORE_NAVY, COLORE_RIGA_ALTERNATA, COLORE_TESTO, inizializza_percorsi, salva_percorsi
    from percorsi import Selezione, cartelle_sorgenti, descrizione_sorgente
    from warning import valuta


def main() -> None:
    root = tk.Tk()
    root.title("BUTTAFUORI - selezione sorgente")
    root.geometry("1050x650")
    root.minsize(820, 520)
    percorsi = inizializza_percorsi()
    cosa, tipo, codice = tk.StringVar(), tk.StringVar(), tk.StringVar()
    stato = tk.StringVar(value="Seleziona COSA e TIPO, poi inserisci un codice SERIE.")
    recenti_frame = ttk.Frame(root)
    cartella_corrente = [None]

    def apri_configurazione_percorsi(titolo, chiavi_percorsi):
        dialogo = tk.Toplevel(root)
        dialogo.title(titolo)
        dialogo.transient(root)
        dialogo.grab_set()
        dialogo.resizable(True, False)
        etichette = {
            nome: nome.removeprefix("TORNI_").rsplit("_", 1)[0].replace("_", " - ")
            + " " + nome.rsplit("_", 1)[1]
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
            non_validi = [
                nome for nome, percorso in nuovi.items()
                if (not percorso and (nome.endswith("_1") or nome == "TORNI"))
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
            if sorgenti_modificate:
                cartella_corrente[0] = None
                aggiorna_btn.configure(state="disabled")
                for item in table.get_children():
                    table.delete(item)
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

    def radio_row(row, label, variable, values):
        tk.Label(controls, text=label, bg=COLORE_AZZURRO, fg=COLORE_TESTO, width=10, anchor="w", font=("Segoe UI", 10, "bold")).grid(row=row, column=0, padx=10, pady=5, sticky="w")
        for col, value in enumerate(values, 1):
            ttk.Radiobutton(controls, text=value, value=value, variable=variable).grid(row=row, column=col, padx=8, pady=5, sticky="w")

    radio_row(0, "COSA", cosa, ("RULLI", "ACCESSORI"))
    radio_row(1, "TIPO", tipo, ("SERIE", "MODIFICA", "RICAMBIO"))
    tk.Label(controls, text="SERIE", bg=COLORE_AZZURRO, fg=COLORE_TESTO, width=10, anchor="w", font=("Segoe UI", 10, "bold")).grid(row=2, column=0, padx=10, pady=5, sticky="w")
    entry = ttk.Entry(controls, textvariable=codice, width=28)
    entry.grid(row=2, column=1, columnspan=2, padx=12, pady=5, sticky="ew")

    body = ttk.Frame(root)
    body.pack(fill="both", expand=True, padx=14, pady=(0, 14))
    status_bar = ttk.Frame(body)
    status_bar.pack(fill="x", pady=(0, 6))
    ttk.Label(status_bar, textvariable=stato).pack(side="left", anchor="w")
    columns = ("PRT", "M", "P", "S", "R", "T", "warning")
    table = ttk.Treeview(body, columns=columns, show="tree headings", selectmode="extended")
    table.heading("#0", text="RULLO / ACCESSORIO")
    table.column("#0", width=260, anchor="w")
    for col in columns[:-1]:
        table.heading(col, text=col)
        table.column(col, width=55, anchor="center")
    table.heading("warning", text="WARNING VISIVO")
    table.column("warning", width=320, anchor="w")
    table.tag_configure("pari", background=COLORE_RIGA_ALTERNATA)
    table.tag_configure("dispari", background="white")
    table.tag_configure("warning", background="#FFFBE6", foreground="#7A4B00")
    scroll = ttk.Scrollbar(body, orient="vertical", command=table.yview)
    table.configure(yscrollcommand=scroll.set)
    table.pack(side="left", fill="both", expand=True)
    scroll.pack(side="right", fill="y")

    def carica(cartelle: list[str], mantieni_selezione: bool = False) -> None:
        selezionati = {table.item(item, "text") for item in table.selection()} if mantieni_selezione else set()
        for item in table.get_children():
            table.delete(item)
        cartelle_esistenti = [cartella for cartella in cartelle if os.path.isdir(cartella)]
        if not cartelle_esistenti:
            cartella_corrente[0] = None
            aggiorna_btn.configure(state="disabled")
            stato.set("Sorgente non trovata: " + " | ".join(cartelle))
            return
        elementi: list[ElementoProgramma] = leggi_cartelle(cartelle_esistenti, tipo.get())
        cartella_corrente[0] = cartelle
        aggiorna_btn.configure(state="normal")
        da_selezionare = []
        for index, elemento in enumerate(elementi):
            warning = valuta(elemento, tipo.get())
            flags = tuple("✓" if presente else "" for presente in (
                elemento.presenza_prt, elemento.presenza_m, elemento.presenza_p,
                elemento.presenza_s, elemento.presenza_r, elemento.presenza_t,
            ))
            tag = "warning" if warning else ("pari" if index % 2 == 0 else "dispari")
            item_id = table.insert("", "end", text=elemento.identificativo,
                                   values=(*flags, "⚠ " + "; ".join(warning) if warning else ""), tags=(tag,))
            if elemento.identificativo in selezionati:
                da_selezionare.append(item_id)
        if da_selezionare:
            table.selection_set(da_selezionare)
        stato.set(f"{' | '.join(cartelle_esistenti)} - {len(elementi)} elementi")

    def verifica():
        recenti_frame.pack_forget()
        value = codice.get().strip()
        if not value or not cosa.get() or not tipo.get():
            stato.set("Completa COSA, TIPO e SERIE.")
            return
        carica(cartelle_sorgenti(percorsi, Selezione(cosa.get(), tipo.get()), value))

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
        latest_btn.configure(state="normal" if cosa.get() and tipo.get() else "disabled")

    cosa.trace_add("write", abilita_recenti)
    tipo.trace_add("write", abilita_recenti)
    aggiorna_btn = ttk.Button(status_bar, text="↻ AGGIORNA", command=aggiorna, state="disabled")
    aggiorna_btn.pack(side="right")
    latest_btn = ttk.Button(controls, text="ULTIME MODIFICATE", command=mostra_recenti, state="disabled")
    latest_btn.grid(row=2, column=3, padx=12, pady=5)
    ttk.Button(controls, text="VERIFICA SORGENTE", command=verifica).grid(row=2, column=4, padx=8, pady=5)
    entry.bind("<Return>", lambda _: verifica())
    controls.columnconfigure(2, weight=0)
    footer = ttk.Frame(root)
    footer.pack(fill="x", padx=14, pady=(0, 12))
    ttk.Button(footer, text="SELEZIONA TUTTI", command=lambda: table.selection_set(table.get_children())).pack(side="left")
    ttk.Button(footer, text="AVANTI", command=lambda: messagebox.showinfo("Fase 2", "La verifica TORNI e la copia saranno implementate nella Fase 2.")).pack(side="right")
    root.mainloop()


if __name__ == "__main__":
    main()
