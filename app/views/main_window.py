import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import ttkbootstrap as tb

from .theme import (
    C_ACCENT,
    C_ACCENT_DIM,
    C_BG,
    C_ERROR,
    C_OUTLINE,
    C_SURFACE,
    C_SURFACE_H,
    C_TEXT,
    C_TEXT_DIM,
    SONIC_ETHEREAL,
    configure_all_styles,
)


class MainWindow:
    VERSION = "0.1.0"

    def __init__(self, presenter) -> None:
        self._presenter = presenter
        self._app: tb.Window | None = None
        self._status_label: tk.Label | None = None
        self._progress_bar: ttk.Progressbar | None = None
        self._file_label: tk.Label | None = None
        self._selected_file: str | None = None
        self._install_button: tb.Button | None = None

        self._mode_var: tk.StringVar | None = None
        self._output_dir: str | None = None

    # ── Construcción principal ───────────────────────────────────────────────
    def build(self) -> tb.Window:
        self._app = tb.Window(themename="darkly")
        self._app.title("VocalRemoverAI")
        self._app.geometry("1100x700")
        self._app.minsize(900, 580)

        style = tb.Style()
        style.register_theme(SONIC_ETHEREAL)
        style.theme_use("sonic-ethereal")
        configure_all_styles(style)

        self._app.grid_columnconfigure(0, weight=1)
        self._app.grid_rowconfigure(1, weight=1)
        self._app.grid_rowconfigure(2, weight=0)

        self._build_topbar(self._app)
        self._build_main_area(self._app)
        self._build_footer(self._app)
        self._setup_callbacks()
        return self._app

    # ── Top Bar ──────────────────────────────────────────────────────────────
    def _build_topbar(self, parent) -> None:
        bar = ttk.Frame(parent, style="TopBar.TFrame", height=56)
        bar.grid(row=0, column=0, sticky="ew")
        bar.grid_columnconfigure(1, weight=1)
        bar.grid_propagate(False)

        logo = tk.Label(
            bar,
            text="♪  VocalRemoverAI",
            font=("Segoe UI", 20, "bold"),
            fg=C_ACCENT,
            bg=C_SURFACE,
        )
        logo.grid(row=0, column=0, padx=24, pady=12, sticky="w")

        self._status_label = tk.Label(
            bar,
            text="Listo para procesar",
            font=(13,),
            fg=C_TEXT_DIM,
            bg=C_SURFACE,
        )
        self._status_label.grid(row=0, column=1, sticky="")

        options_btn = tb.Button(
            bar,
            text="⚙  Opciones",
            command=self._open_options_modal,
            bootstyle="outline-primary",
            width=14,
        )
        options_btn.grid(row=0, column=2, padx=(0, 16), pady=11)

        self._install_button = tb.Button(
            bar,
            text="⚠ Instalar dependencias",
            command=self._on_install_dependencies,
            bootstyle="danger",
        )
        self._install_button.grid(row=0, column=3, padx=(0, 16), pady=11)
        self._install_button.grid_remove()

    # ── Área principal ───────────────────────────────────────────────────────
    def _build_main_area(self, parent) -> None:
        wrapper = tk.Frame(parent, bg=C_BG)
        wrapper.grid(row=1, column=0, sticky="nsew", padx=48, pady=32)
        wrapper.grid_columnconfigure(0, weight=1)
        wrapper.grid_rowconfigure(0, weight=1)

        drop_card = tk.Frame(
            wrapper,
            bg=C_SURFACE,
            highlightbackground=C_OUTLINE,
            highlightthickness=2,
        )
        drop_card.grid(row=0, column=0, sticky="nsew")
        drop_card.grid_columnconfigure(0, weight=1)
        drop_card.grid_rowconfigure(0, weight=1)

        inner = tk.Frame(drop_card, bg=C_SURFACE)
        inner.grid(row=0, column=0)

        icon_label = tk.Label(
            inner,
            text="🎵",
            font=(64,),
            fg=C_ACCENT,
            bg=C_SURFACE,
        )
        icon_label.pack(pady=(0, 16))

        drop_title = tk.Label(
            inner,
            text="Arrastra tu audio o video aquí",
            font=("Segoe UI", 24, "bold"),
            fg=C_TEXT,
            bg=C_SURFACE,
        )
        drop_title.pack()

        formats_label = tk.Label(
            inner,
            text="MP3 · WAV · FLAC · OGG · M4A · MP4 · AVI · MKV · MOV",
            font=(13,),
            fg=C_TEXT_DIM,
            bg=C_SURFACE,
        )
        formats_label.pack(pady=(6, 0))

        self._file_label = tk.Label(
            inner,
            text="",
            font=(12,),
            fg=C_ACCENT_DIM,
            bg=C_SURFACE,
            wraplength=500,
        )
        self._file_label.pack(pady=(8, 0))

        sep = tk.Label(
            inner,
            text="─────  o  ─────",
            fg=C_OUTLINE,
            bg=C_SURFACE,
        )
        sep.pack(pady=20)

        select_btn = tb.Button(
            inner,
            text="📂  Seleccionar Archivo",
            command=self._on_select_file,
            bootstyle="success",
            width=28,
        )
        select_btn.pack()

        self._progress_bar = ttk.Progressbar(
            inner,
            style="Accent.Horizontal.TProgressbar",
            mode="determinate",
            maximum=1.0,
            length=320,
        )
        self._progress_bar.pack(pady=(24, 0))
        self._progress_bar["value"] = 0
        self._progress_bar.pack_forget()

    # ── Footer ───────────────────────────────────────────────────────────────
    def _build_footer(self, parent) -> None:
        footer = ttk.Frame(parent, style="Footer.TFrame", height=36)
        footer.grid(row=2, column=0, sticky="ew")
        footer.grid_columnconfigure(1, weight=1)
        footer.grid_propagate(False)

        left = tk.Label(
            footer,
            text=f"VocalRemoverAI v{self.VERSION}  ·  Powered by Demucs AI (Meta)",
            font=(11,),
            fg=C_TEXT_DIM,
            bg=C_SURFACE,
        )
        left.grid(row=0, column=0, padx=20, pady=8, sticky="w")

        device = self._presenter.get_device().upper()
        device_fg = C_ACCENT if device == "CUDA" else C_TEXT_DIM
        device_icon = "⚡" if device == "CUDA" else "🔲"

        right = tk.Label(
            footer,
            text=f"{device_icon} {device} mode  ·  © 2025 VocalRemoverAI",
            font=(11,),
            fg=device_fg,
            bg=C_SURFACE,
        )
        right.grid(row=0, column=2, padx=20, pady=8, sticky="e")

    # ── Modal de Opciones ────────────────────────────────────────────────────
    def _open_options_modal(self) -> None:
        modal = tb.Toplevel(self._app)
        modal.title("Opciones de Separación")
        modal.geometry("520x400")
        modal.configure(bg=C_BG)
        modal.grab_set()
        modal.resizable(False, False)
        modal.lift()
        modal.focus_force()

        self._app.update_idletasks()
        x = self._app.winfo_x() + (self._app.winfo_width() // 2) - 260
        y = self._app.winfo_y() + (self._app.winfo_height() // 2) - 200
        modal.geometry(f"520x400+{x}+{y}")

        header_frame = ttk.Frame(modal, style="ModalHeader.TFrame", height=56)
        header_frame.pack(fill="x")
        header_frame.pack_propagate(False)

        title_lbl = tk.Label(
            header_frame,
            text="⚙  Opciones de Separación",
            font=("Segoe UI", 16, "bold"),
            fg=C_ACCENT,
            bg=C_SURFACE,
        )
        title_lbl.pack(side="left", padx=20, pady=14)

        close_btn = tb.Button(
            header_frame,
            text="✕",
            command=modal.destroy,
            bootstyle="secondary-outline",
            width=4,
        )
        close_btn.pack(side="right", padx=12, pady=10)

        content = tk.Frame(modal, bg=C_BG)
        content.pack(fill="both", expand=True, padx=24, pady=16)

        mode_label = tk.Label(
            content,
            text="MODO DE SEPARACIÓN",
            font=("Segoe UI", 11, "bold"),
            fg=C_ACCENT,
            bg=C_BG,
        )
        mode_label.pack(anchor="w")

        mode_card = tk.Frame(content, bg=C_SURFACE_H)
        mode_card.pack(fill="x", pady=(8, 20))

        current_mode = self._presenter.get_mode()
        self._mode_var = tk.StringVar(value=current_mode)

        modes = [
            ("instrumental_only", "🎸  Solo Instrumental", "Elimina las voces, conserva la música"),
            ("vocals_only",       "🎤  Solo Voz",          "Extrae únicamente la pista vocal"),
            ("both",              "🎵  Instrumental + Voz", "Genera ambas pistas por separado"),
        ]
        for val, label, subtitle in modes:
            row = tk.Frame(mode_card, bg=C_SURFACE_H)
            row.pack(fill="x", padx=16, pady=8)

            rb = ttk.Radiobutton(
                row,
                text=label,
                variable=self._mode_var,
                value=val,
            )
            rb.pack(side="left")

            sub = tk.Label(
                row,
                text=subtitle,
                font=(11,),
                fg=C_TEXT_DIM,
                bg=C_SURFACE_H,
            )
            sub.pack(side="right", padx=8)

        # ── Sección: Directorio de salida ─────────────────────────────────────
        out_label = tk.Label(
            content,
            text="DIRECTORIO DE SALIDA",
            font=("Segoe UI", 11, "bold"),
            fg=C_ACCENT,
            bg=C_BG,
        )
        out_label.pack(anchor="w")

        out_card = tk.Frame(content, bg=C_SURFACE_H)
        out_card.pack(fill="x", pady=(8, 0))
        out_card.grid_columnconfigure(0, weight=1)

        out_dir = self._presenter.get_output_directory()
        current_out = out_dir or "Mismo directorio que el archivo de origen"
        self._out_path_label = tk.Label(
            out_card,
            text=current_out,
            font=(12,),
            fg=C_TEXT_DIM,
            bg=C_SURFACE_H,
            anchor="w",
        )
        self._out_path_label.grid(row=0, column=0, padx=16, pady=14, sticky="ew")

        change_btn = tb.Button(
            out_card,
            text="Cambiar...",
            command=lambda: self._pick_output_dir(self._out_path_label),
            bootstyle="outline-success",
            width=12,
        )
        change_btn.grid(row=0, column=1, padx=(0, 12), pady=12)

        def _apply():
            self._presenter.set_mode(self._mode_var.get())
            modal.destroy()
            mode_names = {
                "instrumental_only": "Solo Instrumental",
                "vocals_only": "Solo Voz",
                "both": "Instrumental + Voz",
            }
            self._on_status_update(f"Modo: {mode_names[self._mode_var.get()]}")

        apply_btn = tb.Button(
            modal,
            text="✓  Aplicar",
            command=_apply,
            bootstyle="success",
        )
        apply_btn.pack(fill="x", padx=24, pady=(12, 20))

    def _pick_output_dir(self, label_widget) -> None:
        path = filedialog.askdirectory(title="Seleccionar directorio de salida")
        if path:
            self._presenter.set_output_directory(path)
            short = path if len(path) < 50 else "..." + path[-47:]
            label_widget.configure(text=short)

    # ── Eventos de archivos ──────────────────────────────────────────────────
    def _on_select_file(self) -> None:
        file_path = filedialog.askopenfilename(
            title="Seleccionar archivo de audio o video",
            filetypes=[
                ("Audio/Video", "*.mp3 *.wav *.flac *.ogg *.m4a *.mp4 *.avi *.mkv *.mov"),
                ("Audio", "*.mp3 *.wav *.flac *.ogg *.m4a"),
                ("Video", "*.mp4 *.avi *.mkv *.mov"),
                ("Todos los archivos", "*.*"),
            ],
        )
        if file_path:
            self._selected_file = file_path
            name = os.path.basename(file_path)
            self._file_label.configure(text=f"📄  {name}")
            mode = self._mode_var.get() if self._mode_var else "instrumental_only"
            self._presenter.set_mode(mode)
            self._presenter.process_file(file_path)

    # ── Callbacks del presenter ──────────────────────────────────────────────
    def _setup_callbacks(self) -> None:
        self._presenter.set_callback("status",              self._on_status_update)
        self._presenter.set_callback("processing_started",  self._on_processing_started)
        self._presenter.set_callback("processing_finished", self._on_processing_finished)
        self._presenter.set_callback("processing_complete", self._on_processing_complete)
        self._presenter.set_callback("error",               self._on_error)
        self._presenter.set_callback("install_progress",    self._on_install_progress)
        self._presenter.set_callback("install_complete",    self._on_install_complete)
        self._presenter.set_callback("install_error",       self._on_install_error)

    def _on_status_update(self, message: str) -> None:
        if self._status_label:
            self._status_label.configure(text=message, fg=C_TEXT_DIM)

    def _on_processing_started(self) -> None:
        if self._progress_bar:
            self._progress_bar.pack(pady=(24, 0))
            self._progress_bar.configure(mode="indeterminate")
            self._progress_bar.start()
        if self._status_label:
            self._status_label.configure(text="⏳  Procesando...", fg=C_ACCENT)

    def _on_processing_finished(self) -> None:
        if self._progress_bar:
            self._progress_bar.stop()
            self._progress_bar.configure(mode="determinate")
            self._progress_bar["value"] = 1.0

    def _on_processing_complete(self, output_files: dict) -> None:
        count = len(output_files)
        names = "  ·  ".join(output_files.keys())
        s = "s" if count > 1 else ""
        msg = f"✅  {count} archivo{s} generado{s}:  {names}"
        if self._status_label:
            self._status_label.configure(text=msg, fg=C_ACCENT)
        if self._progress_bar:
            self._progress_bar["value"] = 1.0

    def _on_error(self, message: str) -> None:
        if self._status_label:
            self._status_label.configure(text=f"❌  {message}", fg=C_ERROR)
        if self._progress_bar:
            self._progress_bar.stop()
            self._progress_bar["value"] = 0
            self._progress_bar.pack_forget()
        messagebox.showerror("Error", message)

    # ── Instalación de dependencias ──────────────────────────────────────────
    def _on_install_dependencies(self) -> None:
        dialog = tb.Toplevel(self._app)
        dialog.title("Instalando dependencias")
        dialog.geometry("680x400")
        dialog.configure(bg=C_BG)
        dialog.grab_set()

        tk.Label(
            dialog,
            text="📦  Instalando dependencias...",
            font=("Segoe UI", 15, "bold"),
            fg=C_ACCENT,
            bg=C_BG,
        ).pack(padx=20, pady=(16, 8), anchor="w")

        self._install_log_box = tk.Text(
            dialog,
            bg=C_SURFACE,
            fg="#c8f0c8",
            font=("Courier New", 11),
            wrap="word",
            state="disabled",
            relief="flat",
            borderwidth=0,
            padx=8,
            pady=8,
        )
        self._install_log_box.pack(fill="both", expand=True, padx=20, pady=(0, 8))

        scrollbar = ttk.Scrollbar(dialog, orient="vertical", command=self._install_log_box.yview)
        scrollbar.place(in_=self._install_log_box, relx=1.0, rely=0, relheight=1.0, x=-20)
        self._install_log_box.configure(yscrollcommand=scrollbar.set)

        self._install_close_btn = tb.Button(
            dialog,
            text="Cerrar",
            state="disabled",
            bootstyle="secondary",
        )
        self._install_close_btn.configure(command=dialog.destroy)
        self._install_close_btn.pack(pady=(0, 16))

        self._install_button.configure(state="disabled", text="Instalando...")
        self._presenter.install_packages()

    def _append_install_log(self, text: str) -> None:
        if not hasattr(self, "_install_log_box") or self._install_log_box is None:
            return
        self._install_log_box.configure(state="normal")
        self._install_log_box.insert("end", text + "\n")
        self._install_log_box.see("end")
        self._install_log_box.configure(state="disabled")

    def _on_install_progress(self, message: str) -> None:
        if self._app:
            self._app.after(0, lambda m=message: self._append_install_log(m))

    def _on_install_complete(self, _success: bool) -> None:
        def _finish():
            self._append_install_log("\n✅ Instalación completada.")
            if hasattr(self, "_install_close_btn") and self._install_close_btn:
                self._install_close_btn.configure(
                    state="normal", bootstyle="success"
                )
            if self._install_button:
                self._install_button.grid_remove()
            if self._status_label:
                self._status_label.configure(text="✅  Dependencias instaladas", fg=C_ACCENT)
        if self._app:
            self._app.after(0, _finish)

    def _on_install_error(self, message: str) -> None:
        def _show_err():
            self._append_install_log(f"\n❌ Error: {message}")
            if hasattr(self, "_install_close_btn") and self._install_close_btn:
                self._install_close_btn.configure(
                    state="normal", bootstyle="danger"
                )
            if self._install_button:
                self._install_button.configure(state="normal", text="⚠ Instalar dependencias")
        if self._app:
            self._app.after(0, _show_err)

    # ── Check de dependencias al arrancar ────────────────────────────────────
    def check_and_show_install_button(self) -> None:
        if not self._presenter.check_dependencies():
            self._install_button.grid()
            missing = self._presenter.get_missing_packages()
            if self._status_label:
                self._status_label.configure(
                    text=f"⚠  Dependencias faltantes: {', '.join(missing)}",
                    fg=C_ERROR,
                )

    def run(self) -> None:
        if self._app:
            self.check_and_show_install_button()
            self._app.mainloop()
