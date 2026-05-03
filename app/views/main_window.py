import os
import threading
import customtkinter as ctk
from tkinter import filedialog

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("green")

# ── Paleta "Sonic Ethereal" basada en el diseño Stitch ─────────────────────
C_BG         = "#0c0c1f"   # Fondo principal (surface)
C_SURFACE    = "#17172f"   # Contenedor principal
C_SURFACE_H  = "#1d1d37"   # Contenedor elevado
C_SURFACE_HH = "#23233f"   # Contenedor más elevado (modal, cards)
C_ACCENT     = "#49f4c8"   # Electric Mint (primary)
C_ACCENT_DIM = "#00d4aa"   # Teal (primary_container)
C_TEXT       = "#e5e3ff"   # Texto principal (on_surface)
C_TEXT_DIM   = "#aaa8c3"   # Texto secundario (on_surface_variant)
C_OUTLINE    = "#46465c"   # Borde sutil (outline_variant)
C_ERROR      = "#ff716c"   # Error


class MainWindow:
    VERSION = "0.1.0"

    def __init__(self, presenter) -> None:
        self._presenter = presenter
        self._app: ctk.CTk | None = None
        self._status_label: ctk.CTkLabel | None = None
        self._progress_bar: ctk.CTkProgressBar | None = None
        self._file_label: ctk.CTkLabel | None = None
        self._selected_file: str | None = None
        self._install_button: ctk.CTkButton | None = None

        # Estado del modal de opciones
        self._mode_var: ctk.StringVar | None = None
        self._output_dir: str | None = None

    # ── Construcción principal ───────────────────────────────────────────────
    def build(self) -> ctk.CTk:
        self._app = ctk.CTk()
        self._app.title("VocalRemoverAI")
        self._app.geometry("1100x700")
        self._app.minsize(900, 580)
        self._app.configure(fg_color=C_BG)

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
        bar = ctk.CTkFrame(parent, fg_color=C_SURFACE, height=56, corner_radius=0)
        bar.grid(row=0, column=0, sticky="ew")
        bar.grid_columnconfigure(1, weight=1)
        bar.grid_propagate(False)

        logo = ctk.CTkLabel(
            bar,
            text="♪  VocalRemoverAI",
            font=ctk.CTkFont(family="Segoe UI", size=20, weight="bold"),
            text_color=C_ACCENT,
        )
        logo.grid(row=0, column=0, padx=24, pady=12, sticky="w")

        # Estado en el centro
        self._status_label = ctk.CTkLabel(
            bar,
            text="Listo para procesar",
            font=ctk.CTkFont(size=13),
            text_color=C_TEXT_DIM,
        )
        self._status_label.grid(row=0, column=1, sticky="")

        # Botón Opciones
        options_btn = ctk.CTkButton(
            bar,
            text="⚙  Opciones",
            command=self._open_options_modal,
            fg_color="transparent",
            border_color=C_OUTLINE,
            border_width=1,
            text_color=C_ACCENT,
            hover_color=C_SURFACE_H,
            width=120,
            height=34,
            font=ctk.CTkFont(size=13),
        )
        options_btn.grid(row=0, column=2, padx=(0, 16), pady=11)

        # Botón de instalar dependencias (oculto por defecto)
        self._install_button = ctk.CTkButton(
            bar,
            text="⚠ Instalar dependencias",
            command=self._on_install_dependencies,
            fg_color=C_ERROR,
            hover_color="#e05a56",
            text_color=C_TEXT,
            height=34,
            font=ctk.CTkFont(size=13, weight="bold"),
        )
        self._install_button.grid(row=0, column=3, padx=(0, 16), pady=11)
        self._install_button.grid_remove()

    # ── Área principal ───────────────────────────────────────────────────────
    def _build_main_area(self, parent) -> None:
        wrapper = ctk.CTkFrame(parent, fg_color="transparent")
        wrapper.grid(row=1, column=0, sticky="nsew", padx=48, pady=32)
        wrapper.grid_columnconfigure(0, weight=1)
        wrapper.grid_rowconfigure(0, weight=1)

        # Zona de drop centrada
        drop_card = ctk.CTkFrame(
            wrapper,
            fg_color=C_SURFACE,
            corner_radius=20,
            border_width=2,
            border_color=C_OUTLINE,
        )
        drop_card.grid(row=0, column=0, sticky="nsew")
        drop_card.grid_columnconfigure(0, weight=1)
        drop_card.grid_rowconfigure(0, weight=1)

        inner = ctk.CTkFrame(drop_card, fg_color="transparent")
        inner.grid(row=0, column=0)

        # Ícono musical
        icon_label = ctk.CTkLabel(
            inner,
            text="🎵",
            font=ctk.CTkFont(size=64),
            text_color=C_ACCENT,
        )
        icon_label.pack(pady=(0, 16))

        # Título de drop
        drop_title = ctk.CTkLabel(
            inner,
            text="Arrastra tu audio o video aquí",
            font=ctk.CTkFont(family="Segoe UI", size=24, weight="bold"),
            text_color=C_TEXT,
        )
        drop_title.pack()

        # Formatos soportados
        formats_label = ctk.CTkLabel(
            inner,
            text="MP3 · WAV · FLAC · OGG · M4A · MP4 · AVI · MKV · MOV",
            font=ctk.CTkFont(size=13),
            text_color=C_TEXT_DIM,
        )
        formats_label.pack(pady=(6, 0))

        # Archivo seleccionado
        self._file_label = ctk.CTkLabel(
            inner,
            text="",
            font=ctk.CTkFont(size=12),
            text_color=C_ACCENT_DIM,
            wraplength=500,
        )
        self._file_label.pack(pady=(8, 0))

        # Separador
        sep = ctk.CTkLabel(inner, text="─────  o  ─────", text_color=C_OUTLINE)
        sep.pack(pady=20)

        # Botón seleccionar archivo
        select_btn = ctk.CTkButton(
            inner,
            text="📂  Seleccionar Archivo",
            command=self._on_select_file,
            fg_color=C_ACCENT_DIM,
            hover_color=C_ACCENT,
            text_color=C_BG,
            font=ctk.CTkFont(size=15, weight="bold"),
            height=48,
            width=260,
            corner_radius=12,
        )
        select_btn.pack()

        # Barra de progreso (oculta inicialmente)
        self._progress_bar = ctk.CTkProgressBar(
            inner,
            progress_color=C_ACCENT,
            fg_color=C_SURFACE_HH,
            height=4,
            width=320,
        )
        self._progress_bar.pack(pady=(24, 0))
        self._progress_bar.set(0)
        self._progress_bar.pack_forget()

    # ── Footer ───────────────────────────────────────────────────────────────
    def _build_footer(self, parent) -> None:
        footer = ctk.CTkFrame(parent, fg_color=C_SURFACE, height=36, corner_radius=0)
        footer.grid(row=2, column=0, sticky="ew")
        footer.grid_columnconfigure(1, weight=1)
        footer.grid_propagate(False)

        left = ctk.CTkLabel(
            footer,
            text=f"VocalRemoverAI v{self.VERSION}  ·  Powered by Demucs AI (Meta)",
            font=ctk.CTkFont(size=11),
            text_color=C_TEXT_DIM,
        )
        left.grid(row=0, column=0, padx=20, pady=8, sticky="w")

        device = self._presenter.get_device().upper()
        device_color = C_ACCENT if device == "CUDA" else C_TEXT_DIM
        device_icon = "⚡" if device == "CUDA" else "🔲"
        right = ctk.CTkLabel(
            footer,
            text=f"{device_icon} {device} mode  ·  © 2025 VocalRemoverAI",
            font=ctk.CTkFont(size=11),
            text_color=device_color,
        )
        right.grid(row=0, column=2, padx=20, pady=8, sticky="e")

    # ── Modal de Opciones ────────────────────────────────────────────────────
    def _open_options_modal(self) -> None:
        modal = ctk.CTkToplevel(self._app)
        modal.title("Opciones de Separación")
        modal.geometry("520x400")
        modal.configure(fg_color=C_BG)
        modal.grab_set()
        modal.resizable(False, False)
        modal.lift()
        modal.focus_force()

        # Centrar modal respecto a la ventana principal
        self._app.update_idletasks()
        x = self._app.winfo_x() + (self._app.winfo_width() // 2) - 260
        y = self._app.winfo_y() + (self._app.winfo_height() // 2) - 200
        modal.geometry(f"520x400+{x}+{y}")

        # Header del modal
        header_frame = ctk.CTkFrame(modal, fg_color=C_SURFACE, corner_radius=0, height=56)
        header_frame.pack(fill="x")
        header_frame.pack_propagate(False)
        header_frame.grid_columnconfigure(1, weight=1)

        title_lbl = ctk.CTkLabel(
            header_frame,
            text="⚙  Opciones de Separación",
            font=ctk.CTkFont(family="Segoe UI", size=16, weight="bold"),
            text_color=C_ACCENT,
        )
        title_lbl.pack(side="left", padx=20, pady=14)

        close_btn = ctk.CTkButton(
            header_frame,
            text="✕",
            command=modal.destroy,
            fg_color="transparent",
            hover_color=C_SURFACE_H,
            text_color=C_TEXT_DIM,
            width=36,
            height=36,
            font=ctk.CTkFont(size=14),
        )
        close_btn.pack(side="right", padx=12, pady=10)

        content = ctk.CTkFrame(modal, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=24, pady=16)

        # ── Sección: Modo de separación ──────────────────────────────────────
        mode_label = ctk.CTkLabel(
            content,
            text="MODO DE SEPARACIÓN",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=C_ACCENT,
        )
        mode_label.pack(anchor="w")

        mode_card = ctk.CTkFrame(content, fg_color=C_SURFACE_H, corner_radius=12)
        mode_card.pack(fill="x", pady=(8, 20))

        # Usar el modo actual del presenter
        current_mode = self._presenter.get_mode()
        self._mode_var = ctk.StringVar(value=current_mode)

        modes = [
            ("instrumental_only", "🎸  Solo Instrumental", "Elimina las voces, conserva la música"),
            ("vocals_only",       "🎤  Solo Voz",          "Extrae únicamente la pista vocal"),
            ("both",              "🎵  Instrumental + Voz", "Genera ambas pistas por separado"),
        ]
        for val, label, subtitle in modes:
            row = ctk.CTkFrame(mode_card, fg_color="transparent")
            row.pack(fill="x", padx=16, pady=8)

            rb = ctk.CTkRadioButton(
                row,
                text=label,
                variable=self._mode_var,
                value=val,
                fg_color=C_ACCENT_DIM,
                hover_color=C_ACCENT,
                text_color=C_TEXT,
                font=ctk.CTkFont(size=13),
            )
            rb.pack(side="left")

            sub = ctk.CTkLabel(
                row,
                text=subtitle,
                font=ctk.CTkFont(size=11),
                text_color=C_TEXT_DIM,
            )
            sub.pack(side="right", padx=8)

        # ── Sección: Directorio de salida ─────────────────────────────────────
        out_label = ctk.CTkLabel(
            content,
            text="DIRECTORIO DE SALIDA",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=C_ACCENT,
        )
        out_label.pack(anchor="w")

        out_card = ctk.CTkFrame(content, fg_color=C_SURFACE_H, corner_radius=12)
        out_card.pack(fill="x", pady=(8, 0))
        out_card.grid_columnconfigure(0, weight=1)

        current_out = self._presenter.get_output_directory() or "Mismo directorio que el archivo de origen"
        self._out_path_label = ctk.CTkLabel(
            out_card,
            text=current_out,
            font=ctk.CTkFont(size=12),
            text_color=C_TEXT_DIM,
            anchor="w",
        )
        self._out_path_label.grid(row=0, column=0, padx=16, pady=14, sticky="ew")

        change_btn = ctk.CTkButton(
            out_card,
            text="Cambiar...",
            command=lambda: self._pick_output_dir(self._out_path_label),
            fg_color="transparent",
            border_color=C_ACCENT_DIM,
            border_width=1,
            text_color=C_ACCENT,
            hover_color=C_SURFACE_HH,
            width=100,
            height=30,
            font=ctk.CTkFont(size=12),
        )
        change_btn.grid(row=0, column=1, padx=(0, 12), pady=12)

        # ── Botón Aplicar ─────────────────────────────────────────────────────
        def _apply():
            self._presenter.set_mode(self._mode_var.get())
            modal.destroy()
            mode_names = {
                "instrumental_only": "Solo Instrumental",
                "vocals_only": "Solo Voz",
                "both": "Instrumental + Voz",
            }
            self._on_status_update(f"Modo: {mode_names[self._mode_var.get()]}")

        apply_btn = ctk.CTkButton(
            modal,
            text="✓  Aplicar",
            command=_apply,
            fg_color=C_ACCENT_DIM,
            hover_color=C_ACCENT,
            text_color=C_BG,
            font=ctk.CTkFont(size=14, weight="bold"),
            height=44,
            corner_radius=10,
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
            self._presenter.set_mode(self._mode_var.get() if self._mode_var else "instrumental_only")
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
            self._status_label.configure(text=message, text_color=C_TEXT_DIM)

    def _on_processing_started(self) -> None:
        if self._progress_bar:
            self._progress_bar.pack(pady=(24, 0))
            self._progress_bar.configure(mode="indeterminate")
            self._progress_bar.start()
        if self._status_label:
            self._status_label.configure(text="⏳  Procesando...", text_color=C_ACCENT)

    def _on_processing_finished(self) -> None:
        if self._progress_bar:
            self._progress_bar.stop()
            self._progress_bar.configure(mode="determinate")
            self._progress_bar.set(1)

    def _on_processing_complete(self, output_files: dict) -> None:
        count = len(output_files)
        names = "  ·  ".join(output_files.keys())
        msg = f"✅  {count} archivo{'s' if count > 1 else ''} generado{'s' if count > 1 else ''}:  {names}"
        if self._status_label:
            self._status_label.configure(text=msg, text_color=C_ACCENT)
        if self._progress_bar:
            self._progress_bar.set(1)

    def _on_error(self, message: str) -> None:
        if self._status_label:
            self._status_label.configure(text=f"❌  {message}", text_color=C_ERROR)
        if self._progress_bar:
            self._progress_bar.stop()
            self._progress_bar.set(0)
            self._progress_bar.pack_forget()
        from tkinter import messagebox
        messagebox.showerror("Error", message)

    # ── Instalación de dependencias ──────────────────────────────────────────
    def _on_install_dependencies(self) -> None:
        dialog = ctk.CTkToplevel(self._app)
        dialog.title("Instalando dependencias")
        dialog.geometry("680x400")
        dialog.configure(fg_color=C_BG)
        dialog.grab_set()

        ctk.CTkLabel(
            dialog,
            text="📦  Instalando dependencias...",
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color=C_ACCENT,
        ).pack(padx=20, pady=(16, 8), anchor="w")

        self._install_log_box = ctk.CTkTextbox(
            dialog,
            fg_color=C_SURFACE,
            text_color="#c8f0c8",
            font=ctk.CTkFont(family="Courier New", size=11),
            wrap="word",
            state="disabled",
        )
        self._install_log_box.pack(fill="both", expand=True, padx=20, pady=(0, 8))

        self._install_close_btn = ctk.CTkButton(
            dialog,
            text="Cerrar",
            state="disabled",
            fg_color=C_SURFACE_H,
            text_color=C_TEXT_DIM,
            command=dialog.destroy,
        )
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
                    state="normal", fg_color=C_ACCENT_DIM, text_color=C_BG
                )
            if self._install_button:
                self._install_button.grid_remove()
            if self._status_label:
                self._status_label.configure(text="✅  Dependencias instaladas", text_color=C_ACCENT)
        if self._app:
            self._app.after(0, _finish)

    def _on_install_error(self, message: str) -> None:
        def _show_err():
            self._append_install_log(f"\n❌ Error: {message}")
            if hasattr(self, "_install_close_btn") and self._install_close_btn:
                self._install_close_btn.configure(
                    state="normal", fg_color=C_ERROR, text_color=C_TEXT
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
                    text_color=C_ERROR,
                )

    def run(self) -> None:
        if self._app:
            self.check_and_show_install_button()
            self._app.mainloop()
