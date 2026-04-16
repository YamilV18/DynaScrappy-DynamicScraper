import customtkinter as ctk
import threading
import sys
import io
from datetime import datetime

# ── Importar el scraper real ──────────────────────────────────────────────────
from dynamic_scraper import DynamicScraper

# ── Tema global ───────────────────────────────────────────────────────────────
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

BG_BASE    = "#0d0d0d"
BG_CARD    = "#141414"
BG_INPUT   = "#1a1a1a"
BG_HOVER   = "#222222"
ACCENT     = "#00ff88"        # verde neón
ACCENT_DIM = "#00c86a"
TEXT_PRI   = "#f0f0f0"
TEXT_SEC   = "#666666"
TEXT_DIM   = "#333333"
BORDER     = "#2a2a2a"
RED        = "#ff4444"
YELLOW     = "#ffcc00"

FONT_MONO  = ("Consolas", 12)
FONT_MONO_SM = ("Consolas", 10)
FONT_MONO_LG = ("Consolas", 14, "bold")
FONT_TITLE = ("Consolas", 18, "bold")

# ── Redirigir stdout al widget de log ─────────────────────────────────────────
class LogRedirector(io.TextIOBase):
    def __init__(self, callback):
        self.callback = callback

    def write(self, text):
        if text.strip():
            self.callback(text.rstrip())
        return len(text)

    def flush(self):
        pass


# ── Ventana principal ─────────────────────────────────────────────────────────
class DynaScrappyApp(ctk.CTk):

    def __init__(self):
        super().__init__()

        self.title("DYNASCRAPPY")
        self.geometry("820x640")
        self.minsize(720, 560)
        self.configure(fg_color=BG_BASE)
        self.resizable(True, True)

        self.scraper = DynamicScraper(cancel_callback=self._is_cancel_requested)
        self.scraper_thread = None
        self.is_running = False
        self.current_mode = ctk.StringVar(value="files")
        self.cancel_requested = False

        self._build_ui()
        self._redirect_stdout()

        # Iniciar el navegador en background al abrir la app
        threading.Thread(target=self._init_browser, daemon=True).start()

    # ── Construcción de la UI ─────────────────────────────────────────────────

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self._build_header()
        self._build_body()
        self._build_statusbar()

    def _build_header(self):
        header = ctk.CTkFrame(self, fg_color=BG_CARD, corner_radius=0, height=64,
                              border_width=0)
        header.grid(row=0, column=0, sticky="ew")
        header.grid_columnconfigure(1, weight=1)
        header.grid_propagate(False)

        # Logo / nombre
        logo_frame = ctk.CTkFrame(header, fg_color="transparent")
        logo_frame.grid(row=0, column=0, padx=20, pady=0, sticky="w")

        ctk.CTkLabel(logo_frame, text="▶", font=("Consolas", 22, "bold"),
                     text_color=ACCENT).pack(side="left", padx=(0, 8))
        ctk.CTkLabel(logo_frame, text="DYNASCRAPPY", font=FONT_TITLE,
                     text_color=TEXT_PRI).pack(side="left")
        ctk.CTkLabel(logo_frame, text="  dynamic scraper v1.0", font=FONT_MONO_SM,
                     text_color=TEXT_SEC).pack(side="left", pady=(4, 0))

        # Indicador de browser
        self.browser_indicator = ctk.CTkLabel(header, text="● browser: iniciando...",
                                              font=FONT_MONO_SM, text_color=YELLOW)
        self.browser_indicator.grid(row=0, column=1, padx=20, sticky="e")

    def _build_body(self):
        body = ctk.CTkFrame(self, fg_color="transparent")
        body.grid(row=1, column=0, sticky="nsew", padx=16, pady=12)
        body.grid_columnconfigure(0, weight=1)
        body.grid_rowconfigure(3, weight=1)

        self._build_url_card(body)
        self._build_mode_card(body)
        self._build_run_card(body)
        self._build_log_card(body)

    # — Tarjeta URL ————————————————————————————————————————————————————————————
    def _build_url_card(self, parent):
        card = self._card(parent)
        card.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(card, text="URL OBJETIVO", font=FONT_MONO_SM,
                     text_color=TEXT_SEC).grid(row=0, column=0,
                                               sticky="w", padx=14, pady=(10, 4))

        self.url_entry = ctk.CTkEntry(
            card, placeholder_text="https://ejemplo.com/recursos",
            font=FONT_MONO, fg_color=BG_INPUT, border_color=BORDER,
            text_color=TEXT_PRI, placeholder_text_color=TEXT_DIM,
            corner_radius=6, height=36
        )
        self.url_entry.grid(row=1, column=0, padx=14,
                            pady=(0, 12), sticky="ew")

    # — Tarjeta modos + extensiones ——————————————————————————————————————————
    def _build_mode_card(self, parent):
        card = self._card(parent)
        card.grid(row=1, column=0, sticky="ew", pady=(0, 8))
        card.grid_columnconfigure((0, 1, 2, 3), weight=1)

        ctk.CTkLabel(card, text="MODO DE EXTRACCIÓN", font=FONT_MONO_SM,
                     text_color=TEXT_SEC).grid(row=0, column=0, columnspan=4,
                                               sticky="w", padx=14, pady=(10, 6))

        modes = [
            ("files",  "📄  ARCHIVOS"),
            ("images", "🖼  IMÁGENES"),
            ("text",   "📝  TEXTO"),
            ("videos", "🎬  VIDEOS"),
        ]

        self.mode_buttons = {}
        for i, (mode, label) in enumerate(modes):
            btn = ctk.CTkButton(
                card, text=label, font=FONT_MONO,
                fg_color=BG_INPUT, hover_color=BG_HOVER,
                text_color=TEXT_SEC, border_color=BORDER, border_width=1,
                corner_radius=6, height=34,
                command=lambda m=mode: self._select_mode(m)
            )
            btn.grid(row=1, column=i, padx=(14 if i == 0 else 4, 4 if i < 3 else 14),
                     pady=(0, 10), sticky="ew")
            self.mode_buttons[mode] = btn

        self._select_mode("files")  # activo por defecto

        # Panel extensiones (solo visible en modo files)
        self.ext_frame = ctk.CTkFrame(card, fg_color="transparent")
        self.ext_frame.grid(row=2, column=0, columnspan=4, sticky="ew",
                            padx=14, pady=(0, 10))
        self.ext_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(self.ext_frame, text="EXTENSIONES:", font=FONT_MONO_SM,
                     text_color=TEXT_SEC).grid(row=0, column=0, padx=(0, 8))

        self.ext_entry = ctk.CTkEntry(
            self.ext_frame, placeholder_text="pdf, csv, zip, xlsx, docx  (vacío = todos por defecto)",
            font=FONT_MONO_SM, fg_color=BG_INPUT, border_color=BORDER,
            text_color=TEXT_PRI, placeholder_text_color=TEXT_DIM,
            corner_radius=6, height=30
        )
        self.ext_entry.grid(row=0, column=1, sticky="ew")

        # Tags rápidos
        tags_frame = ctk.CTkFrame(self.ext_frame, fg_color="transparent")
        tags_frame.grid(row=1, column=0, columnspan=2, sticky="w", pady=(6, 0))

        for ext in ["pdf", "csv", "zip", "xlsx", "docx", "mp3", "json", "xml"]:
            ctk.CTkButton(
                tags_frame, text=ext, font=FONT_MONO_SM,
                fg_color=BG_INPUT, hover_color=BG_HOVER,
                text_color=TEXT_SEC, border_color=BORDER, border_width=1,
                corner_radius=4, height=22, width=44,
                command=lambda e=ext: self._add_ext(e)
            ).pack(side="left", padx=(0, 4))

    # — Tarjeta ejecutar ——————————————————————————————————————————————————————
    def _build_run_card(self, parent):
        card = self._card(parent)
        card.grid(row=2, column=0, sticky="ew", pady=(0, 8))
        card.grid_columnconfigure(0, weight=1)

        # Frame para los botones
        btn_frame = ctk.CTkFrame(card, fg_color="transparent")
        btn_frame.pack(padx=14, pady=12, fill="x")
        btn_frame.grid_columnconfigure(0, weight=1)

        self.run_btn = ctk.CTkButton(
            btn_frame, text="▶  EJECUTAR", font=FONT_MONO_LG,
            fg_color=ACCENT, hover_color=ACCENT_DIM, text_color="#000000",
            corner_radius=6, height=40,
            command=self._on_run
        )
        self.run_btn.grid(row=0, column=0, sticky="ew")

        self.cancel_btn = ctk.CTkButton(
            btn_frame, text="⏹  CANCELAR", font=FONT_MONO_LG,
            fg_color=RED, hover_color="#cc3333", text_color="#ffffff",
            corner_radius=6, height=40,
            command=self._on_cancel
        )
        # No lo mostramos por ahora

    # — Tarjeta log ——————————————————————————————————————————————————————
    def _build_log_card(self, parent):
        card = self._card(parent)
        card.grid(row=3, column=0, sticky="nsew")
        card.grid_columnconfigure(0, weight=1)
        card.grid_rowconfigure(1, weight=1)

        # Header del log
        log_header = ctk.CTkFrame(card, fg_color="transparent")
        log_header.grid(row=0, column=0, sticky="ew", padx=14, pady=(10, 4))
        log_header.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(log_header, text="CONSOLA DE SALIDA", font=FONT_MONO_SM,
                     text_color=TEXT_SEC).grid(row=0, column=0, sticky="w")

        ctk.CTkButton(
            log_header, text="limpiar", font=FONT_MONO_SM,
            fg_color="transparent", hover_color=BG_HOVER,
            text_color=TEXT_SEC, border_width=0,
            height=22, width=60, corner_radius=4,
            command=self._clear_log
        ).grid(row=0, column=1, sticky="e")

        # Textbox del log
        self.log_box = ctk.CTkTextbox(
            card, font=("Consolas", 11), fg_color="#080808",
            text_color=ACCENT, border_color=BORDER, border_width=1,
            corner_radius=6, wrap="word", state="disabled"
        )
        self.log_box.grid(row=1, column=0, sticky="nsew", padx=14, pady=(0, 14))

        # Configurar tags de color
        self.log_box._textbox.tag_configure("ok",   foreground=ACCENT)
        self.log_box._textbox.tag_configure("warn", foreground=YELLOW)
        self.log_box._textbox.tag_configure("err",  foreground=RED)
        self.log_box._textbox.tag_configure("dim",  foreground=TEXT_SEC)
        self.log_box._textbox.tag_configure("info", foreground="#00ccff")

    def _build_statusbar(self):
        bar = ctk.CTkFrame(self, fg_color=BG_CARD, corner_radius=0, height=28,
                           border_width=0)
        bar.grid(row=2, column=0, sticky="ew")
        bar.grid_columnconfigure(1, weight=1)
        bar.grid_propagate(False)

        self.status_dot = ctk.CTkLabel(bar, text="●", font=("Consolas", 10),
                                        text_color=TEXT_DIM)
        self.status_dot.grid(row=0, column=0, padx=(14, 4), sticky="w")

        self.status_label = ctk.CTkLabel(bar, text="inactivo", font=FONT_MONO_SM,
                                          text_color=TEXT_SEC)
        self.status_label.grid(row=0, column=1, sticky="w")

        self.stats_label = ctk.CTkLabel(bar, text="", font=FONT_MONO_SM,
                                         text_color=TEXT_SEC)
        self.stats_label.grid(row=0, column=2, padx=14, sticky="e")

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _is_cancel_requested(self):
        """Callback para verificar si se solicitó cancelación."""
        return self.cancel_requested

    def _card(self, parent):
        return ctk.CTkFrame(parent, fg_color=BG_CARD, corner_radius=8,
                            border_color=BORDER, border_width=1)

    def _select_mode(self, mode):
        self.current_mode.set(mode)
        for m, btn in self.mode_buttons.items():
            if m == mode:
                btn.configure(fg_color=ACCENT, text_color="#000000",
                               border_color=ACCENT)
            else:
                btn.configure(fg_color=BG_INPUT, text_color=TEXT_SEC,
                               border_color=BORDER)

        # Mostrar/ocultar panel de extensiones
        if hasattr(self, "ext_frame"):
            if mode == "files":
                self.ext_frame.grid()
            else:
                self.ext_frame.grid_remove()

    def _add_ext(self, ext):
        current = self.ext_entry.get().strip()
        parts = [e.strip() for e in current.split(",") if e.strip()]
        if ext not in parts:
            parts.append(ext)
        self.ext_entry.delete(0, "end")
        self.ext_entry.insert(0, ", ".join(parts))

    def _clear_log(self):
        self.log_box.configure(state="normal")
        self.log_box.delete("1.0", "end")
        self.log_box.configure(state="disabled")

    def _log(self, message, tag="ok"):
        ts = datetime.now().strftime("%H:%M:%S")
        line = f"[{ts}]  {message}\n"
        self.log_box.configure(state="normal")
        self.log_box.insert("end", line, tag)
        self.log_box.see("end")
        self.log_box.configure(state="disabled")

    def _set_status(self, running: bool, text: str):
        color = ACCENT if running else TEXT_DIM
        self.status_dot.configure(text_color=color)
        self.status_label.configure(text=text)

    def _redirect_stdout(self):
        """Captura los print() del scraper y los muestra en el log."""
        sys.stdout = LogRedirector(lambda msg: self.after(0, self._classify_log, msg))

    def _classify_log(self, msg: str):
        """Colorea la línea según su prefijo."""
        msg_l = msg.lower()
        if "[ok]" in msg_l or "[✔]" in msg_l:
            tag = "ok"
        elif "[!]" in msg_l or "error" in msg_l or "[error" in msg_l:
            tag = "err"
        elif "[*]" in msg_l:
            tag = "info"
        else:
            tag = "dim"
        self._log(msg, tag)

    # ── Lógica principal ──────────────────────────────────────────────────────

    def _init_browser(self):
        self._log("Iniciando instancia del navegador...", "info")
        self.scraper.iniciar_navegador()
        self.after(0, lambda: self.browser_indicator.configure(
            text="● browser: activo", text_color=ACCENT))
        self._log("Navegador listo.", "ok")
        self._set_status(False, "listo")

    def _on_run(self):
        url = self.url_entry.get().strip()
        if not url:
            self._log("⚠  Ingresa una URL válida.", "warn")
            return
        if self.is_running:
            return

        mode = self.current_mode.get()
        exts_raw = self.ext_entry.get().strip() if mode == "files" else ""
        ext_list = [e.strip() for e in exts_raw.split(",") if e.strip()] or None
        
        # Agregar punto a las extensiones si no lo tienen
        if ext_list:
            ext_list = ["." + e if not e.startswith(".") else e for e in ext_list]

        self.is_running = True
        self.cancel_requested = False
        
        # Cambiar botones: esconder ejecutar, mostrar cancelar
        self.run_btn.grid_remove()
        self.cancel_btn.grid(row=0, column=0, sticky="ew")
        
        self._set_status(True, f"ejecutando · modo: {mode}")
        self._log(f"{'='*48}", "dim")
        self._log(f"URL   : {url}", "info")
        # Mostrar sin punto en el log
        ext_display = [e.lstrip(".") for e in ext_list] if ext_list else []
        self._log(f"MODO  : {mode}" + (f"  |  ext: {', '.join(ext_display)}" if ext_display else ""), "info")
        self._log(f"{'='*48}", "dim")

        self.scraper_thread = threading.Thread(
            target=self._run_scraper,
            args=(url, mode, ext_list),
            daemon=True
        )
        self.scraper_thread.start()

    def _on_cancel(self):
        """Cancela la ejecución actual."""
        if not self.is_running:
            return
        
        self._log("[!] Cancelación solicitada...", "warn")
        self.cancel_requested = True
        
        self._log("[✔] Deteniendo descargas activas...", "info")
        
        # Volver a mostrar botón de ejecutar
        self.cancel_btn.grid_remove()
        self.run_btn.grid(row=0, column=0, sticky="ew")
        
        self._on_done()

    def _run_scraper(self, url, mode, ext_list):
        try:
            self.scraper.run(url, mode=mode, extensions=ext_list)
            self.after(0, self._on_done)
        except Exception as e:
            self.after(0, lambda: self._log(f"ERROR: {e}", "err"))
            self.after(0, self._on_done)

    def _on_done(self):
        self.is_running = False
        self.cancel_btn.grid_remove()
        self.run_btn.grid(row=0, column=0, sticky="ew")
        
        if self.cancel_requested:
            self._set_status(False, "cancelado")
            self._log("[!] Operación cancelada por el usuario.", "warn")
        else:
            self._set_status(False, "completado")
            self._log("[✔] Tarea finalizada. Navegador sigue abierto.", "ok")

    def on_close(self):
        sys.stdout = sys.__stdout__
        self.scraper.cerrar_todo()
        self.destroy()


# ── Punto de entrada ──────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = DynaScrappyApp()
    app.protocol("WM_DELETE_WINDOW", app.on_close)
    app.mainloop()