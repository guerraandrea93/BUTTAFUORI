"""GUI principale: selezione e verifica delle sorgenti RULLI."""
import os
import tkinter as tk
from datetime import datetime
from tkinter import messagebox, ttk

try:
    from .classificazione import ElementoProgramma, leggi_cartella
    from .funzioni import COLORE_AZZURRO, COLORE_NAVY, COLORE_RIGA_ALTERNATA, COLORE_TESTO, inizializza_percorsi
    from .percorsi import Selezione, cartella_sorgente, descrizione_sorgente
    from .warning import valuta
except ImportError:
    from classificazione import ElementoProgramma, leggi_cartella
    from funzioni import COLORE_AZZURRO, COLORE_NAVY, COLORE_RIGA_ALTERNATA, COLORE_TESTO, inizializza_percorsi
    from percorsi import Selezione, cartella_sorgente, descrizione_sorgente
    from warning import valuta


def main() -> None:
    root = tk.Tk(); root.title("BUTTAFUORI — selezione sorgente")
    root.geometry("1050x650"); root.minsize(820, 520)
    percorsi = inizializza_percorsi()
    cosa, tipo, codice = tk.StringVar(), tk.StringVar(), tk.StringVar()
    stato = tk.StringVar(value="Seleziona COSA e TIPO, poi inserisci un codice SERIE.")
    recenti_frame = ttk.Frame(root)
    header = tk.Frame(root, bg=COLORE_NAVY); header.pack(fill="x")
    tk.Label(header, text="BUTTAFUORI", bg=COLORE_NAVY, fg="white", font=("Segoe UI", 20, "bold")).pack(anchor="w", padx=18, pady=10)
    controls = tk.Frame(root, bg=COLORE_AZZURRO); controls.pack(fill="x", padx=14, pady=14)

    def radio_row(row, label, variable, values):
        tk.Label(controls, text=label, bg=COLORE_AZZURRO, fg=COLORE_TESTO, width=10, anchor="w", font=("Segoe UI", 10, "bold")).grid(row=row, column=0, padx=10, pady=5, sticky="w")
        for col, value in enumerate(values, 1):
            ttk.Radiobutton(controls, text=value, value=value, variable=variable).grid(row=row, column=col, padx=12, pady=5, sticky="w")
    radio_row(0, "COSA", cosa, ("RULLI", "ACCESSORI")); radio_row(1, "TIPO", tipo, ("SERIE", "MODIFICA", "RICAMBIO"))
    tk.Label(controls, text="SERIE", bg=COLORE_AZZURRO, fg=COLORE_TESTO, width=10, anchor="w", font=("Segoe UI", 10, "bold")).grid(row=2, column=0, padx=10, pady=5, sticky="w")
    entry = ttk.Entry(controls, textvariable=codice, width=28); entry.grid(row=2, column=1, columnspan=2, padx=12, pady=5, sticky="ew")

    def abilita(*_): latest_btn.configure(state="normal" if cosa.get() and tipo.get() else "disabled")
    cosa.trace_add("write", abilita); tipo.trace_add("write", abilita)

    body = ttk.Frame(root); body.pack(fill="both", expand=True, padx=14, pady=(0, 14))
    ttk.Label(body, textvariable=stato).pack(anchor="w", pady=(0, 6))
    columns = ("M", "P", "S", "R", "T", "warning")
    table = ttk.Treeview(body, columns=columns, show="tree headings", selectmode="extended")
    table.heading("#0", text="RULLO / ACCESSORIO"); table.column("#0", width=260, anchor="w")
    for col in columns[:-1]: table.heading(col, text=col); table.column(col, width=55, anchor="center")
    table.heading("warning", text="WARNING VISIVO"); table.column("warning", width=320, anchor="w")
    table.tag_configure("pari", background=COLORE_RIGA_ALTERNATA); table.tag_configure("dispari", background="white")
    table.tag_configure("warning", background="#FFF1C2", foreground="#7A4B00")
    scroll = ttk.Scrollbar(body, orient="vertical", command=table.yview); table.configure(yscrollcommand=scroll.set)
    table.pack(side="left", fill="both", expand=True); scroll.pack(side="right", fill="y")

    def carica(cartella: str) -> None:
        for item in table.get_children(): table.delete(item)
        elementi: list[ElementoProgramma] = leggi_cartella(cartella, tipo.get())
        if not os.path.isdir(cartella): stato.set(f"Sorgente non trovata: {cartella}"); return
        for index, elemento in enumerate(elementi):
            warning = valuta(elemento, tipo.get())
            flags = tuple("✓" if v in elemento.varianti else "" for v in ("M", "P", "S", "R", "T"))
            tag = "warning" if warning else ("pari" if index % 2 == 0 else "dispari")
            table.insert("", "end", text=elemento.identificativo, values=(*flags, "⚠ " + "; ".join(warning) if warning else ""), tags=(tag,))
        stato.set(f"{descrizione_sorgente(Selezione(cosa.get(), tipo.get()))} — {len(elementi)} elementi")

    def verifica():
        recenti_frame.pack_forget(); value = codice.get().strip()
        if not value or not cosa.get() or not tipo.get(): stato.set("Completa COSA, TIPO e SERIE."); return
        carica(cartella_sorgente(percorsi["RULLI"], Selezione(cosa.get(), tipo.get()), value))

    def scegli_recente(path, name):
        codice.set(name.removeprefix("Z")); recenti_frame.pack_forget(); carica(path)

    def mostra_recenti():
        for child in recenti_frame.winfo_children(): child.destroy()
        parent = os.path.dirname(cartella_sorgente(percorsi["RULLI"], Selezione(cosa.get(), tipo.get()), "_"))
        try:
            candidate = [x for x in os.scandir(parent) if x.is_dir()]
            candidate.sort(key=lambda x: x.stat().st_mtime, reverse=True); candidate = candidate[:5]
        except OSError as exc: stato.set(f"Impossibile leggere le ultime cartelle: {exc}"); return
        if not candidate: ttk.Label(recenti_frame, text="Nessuna cartella pertinente trovata.").pack(anchor="w")
        for item in candidate:
            when = datetime.fromtimestamp(item.stat().st_mtime).strftime("%d/%m/%Y %H:%M")
            ttk.Button(recenti_frame, text=f"{item.name}    {when}", command=lambda p=item.path, n=item.name: scegli_recente(p, n)).pack(fill="x", pady=2)
        recenti_frame.pack(fill="x", padx=14, pady=(0, 8), before=body)

    latest_btn = ttk.Button(controls, text="ULTIME MODIFICATE", command=mostra_recenti, state="disabled"); latest_btn.grid(row=2, column=3, padx=12, pady=5)
    ttk.Button(controls, text="VERIFICA SORGENTE", command=verifica).grid(row=2, column=4, padx=8, pady=5); entry.bind("<Return>", lambda _: verifica())
    controls.columnconfigure(2, weight=1)
    footer = ttk.Frame(root); footer.pack(fill="x", padx=14, pady=(0, 12))
    ttk.Button(footer, text="SELEZIONA TUTTI", command=lambda: table.selection_set(table.get_children())).pack(side="left")
    ttk.Button(footer, text="AVANTI", command=lambda: messagebox.showinfo("Fase 2", "La verifica TORNI e la copia saranno implementate nella Fase 2.")).pack(side="right")
    root.mainloop()


if __name__ == "__main__": main()
