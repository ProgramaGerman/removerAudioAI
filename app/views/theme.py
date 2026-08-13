from ttkbootstrap.style.theme import ThemeDefinition

# ── Paleta "Sonic Ethereal" ─────────────────────────────────────
C_BG         = "#0c0c1f"
C_SURFACE    = "#17172f"
C_SURFACE_H  = "#1d1d37"
C_SURFACE_HH = "#23233f"
C_ACCENT     = "#49f4c8"
C_ACCENT_DIM = "#00d4aa"
C_TEXT       = "#e5e3ff"
C_TEXT_DIM   = "#aaa8c3"
C_OUTLINE    = "#46465c"
C_ERROR      = "#ff716c"

SONIC_ETHEREAL = ThemeDefinition(
    name="sonic-ethereal",
    mode="dark",
    colors={
        "primary":   C_ACCENT,
        "secondary": C_SURFACE,
        "success":   C_ACCENT_DIM,
        "info":      C_ACCENT,
        "warning":   "#f0a847",
        "danger":    C_ERROR,
        "light":     C_TEXT,
        "dark":      C_BG,
        "bg":        C_BG,
        "fg":        C_TEXT,
        "selectbg":  C_ACCENT,
        "selectfg":  C_BG,
        "border":    C_OUTLINE,
        "inputfg":   C_TEXT,
        "inputbg":   C_SURFACE_H,
        "active":    C_SURFACE_HH,
    },
)


def configure_label_styles(style):
    style.configure("Accent.TLabel", foreground=C_ACCENT)
    style.configure("Dim.TLabel", foreground=C_TEXT_DIM)
    style.configure("AccentDim.TLabel", foreground=C_ACCENT_DIM)
    style.configure("Error.TLabel", foreground=C_ERROR)
    style.configure("SurfaceH.TLabel", foreground=C_TEXT, background=C_SURFACE_H)


def configure_frame_styles(style):
    style.configure("TopBar.TFrame", background=C_SURFACE)
    style.configure("Footer.TFrame", background=C_SURFACE)
    style.configure("Surface.TFrame", background=C_SURFACE)
    style.configure("SurfaceH.TFrame", background=C_SURFACE_H)
    style.configure("SurfaceHH.TFrame", background=C_SURFACE_HH)
    style.configure("DropCard.TFrame", background=C_SURFACE, relief="solid", borderwidth=2)
    style.configure("ModalHeader.TFrame", background=C_SURFACE)


def configure_progressbar_styles(style):
    style.configure(
        "Accent.Horizontal.TProgressbar",
        background=C_ACCENT,
        troughcolor=C_SURFACE_HH,
        thickness=4,
    )


def configure_all_styles(style):
    configure_label_styles(style)
    configure_frame_styles(style)
    configure_progressbar_styles(style)
