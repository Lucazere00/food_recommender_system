"""Stile condiviso dell'applicazione Food Recommender."""

from html import escape


PALETTE = {
    "bg": "#FAF7F1",
    "bg_sidebar": "#F2EBDD",
    "surface": "#FFFFFF",
    "border": "#E2D3B8",
    "ink": "#30271F",
    "ink_soft": "#806F5B",
    "muted": "#9D8E78",
    "terracotta": "#BF4D2D",
    "terracotta_dark": "#682B18",
    "terracotta_soft": "#F3D9C4",
    "sage": "#5C7A52",
    "sage_soft": "#E3EBE2",
}


TABLER_ICON_PATHS = {
    "home": (
        '<path d="M5 12l-2 0l9 -9l9 9l-2 0" />'
        '<path d="M5 12v7a2 2 0 0 0 2 2h10a2 2 0 0 0 2 -2v-7" />'
        '<path d="M9 21v-6a2 2 0 0 1 2 -2h2a2 2 0 0 1 2 2v6" />'
    ),
    "trophy": (
        '<path d="M8 21l8 0" />'
        '<path d="M12 17l0 4" />'
        '<path d="M7 4l10 0" />'
        '<path d="M17 4v8a5 5 0 0 1 -10 0v-8" />'
        '<path d="M5 9a2 2 0 0 1 -2 -2v-1a2 2 0 0 1 2 -2h2" />'
        '<path d="M19 9a2 2 0 0 0 2 -2v-1a2 2 0 0 0 -2 -2h-2" />'
    ),
    "salad": (
        '<path d="M7 21h10" />'
        '<path d="M12 21a9 9 0 0 0 9 -9h-18a9 9 0 0 0 9 9z" />'
        '<path d="M11.38 12a2.4 2.4 0 0 1 -.38 -1.31a2.4 2.4 0 0 1 4.8 0a2.4 2.4 0 0 1 -.38 1.31" />'
        '<path d="M13 8l3 -5" />'
        '<path d="M10.9 7.25l-2.9 -4.25" />'
        '<path d="M7 12a2 2 0 1 1 4 0" />'
    ),
    "apple": (
        '<path d="M12 14.528c-3.879 -4.512 -8 -1.8 -8 2.472c0 3 2 5 4 5c1.5 0 2.5 -1 4 -1s2.5 1 4 1c2 0 4 -2 4 -5c0 -4.272 -4.121 -6.984 -8 -2.472z" />'
        '<path d="M12 14.528v-6.528" />'
        '<path d="M12 8c0 -2.21 1.79 -4 4 -4" />'
    ),
    "mood-smile": (
        '<path d="M12 12m-9 0a9 9 0 1 0 18 0a9 9 0 1 0 -18 0" />'
        '<path d="M9 10l.01 0" />'
        '<path d="M15 10l.01 0" />'
        '<path d="M9.5 15a3.5 3.5 0 0 0 5 0" />'
    ),
    "users": (
        '<path d="M9 7m-4 0a4 4 0 1 0 8 0a4 4 0 1 0 -8 0" />'
        '<path d="M3 21v-2a4 4 0 0 1 4 -4h4a4 4 0 0 1 4 4v2" />'
        '<path d="M16 3.13a4 4 0 0 1 0 7.75" />'
        '<path d="M21 21v-2a4 4 0 0 0 -3 -3.85" />'
    ),
    "puzzle": (
        '<path d="M4 7h3a1 1 0 0 0 1 -1a2 2 0 0 1 4 0a1 1 0 0 0 1 1h3a1 1 0 0 1 1 1v3a1 1 0 0 0 1 1a2 2 0 0 1 0 4a1 1 0 0 0 -1 1v3a1 1 0 0 1 -1 1h-3a1 1 0 0 1 -1 -1a2 2 0 0 0 -4 0a1 1 0 0 1 -1 1h-3a1 1 0 0 1 -1 -1v-3a1 1 0 0 1 1 -1a2 2 0 0 0 0 -4a1 1 0 0 1 -1 -1v-3a1 1 0 0 1 1 -1" />'
    ),
    "soup": (
        '<path d="M5 11h14" />'
        '<path d="M6 11a6 6 0 0 0 12 0" />'
        '<path d="M8 18h8" />'
        '<path d="M9 7c-.5 -.6 -.5 -1.4 0 -2" />'
        '<path d="M12 7c-.5 -.6 -.5 -1.4 0 -2" />'
        '<path d="M15 7c-.5 -.6 -.5 -1.4 0 -2" />'
    ),
    "chevron-down": (
        '<path d="M6 9l6 6l6 -6" />'
    ),
}


def tabler_icon(name: str, size: int = 18, color: str = None) -> str:
    icon_name = name.removeprefix("ti-")
    paths = TABLER_ICON_PATHS.get(icon_name)
    if not paths:
        return ""

    color_style = f" color: {escape(color)};" if color else ""
    return (
        f'<span class="tabler-icon tabler-icon-{escape(icon_name)}" '
        f'aria-hidden="true" style="width:{size}px;height:{size}px;{color_style}">'
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" '
        'viewBox="0 0 24 24" fill="none" stroke="currentColor" '
        'stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
        f"{paths}</svg></span>"
    )


def get_css() -> str:
    return f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500&family=Libre+Caslon+Display&display=swap');

    :root {{
        --bg: {PALETTE["bg"]};
        --sidebar: {PALETTE["bg_sidebar"]};
        --surface: {PALETTE["surface"]};
        --surface-1: #EEE7DA;
        --border: {PALETTE["border"]};
        --ink: {PALETTE["ink"]};
        --soft: {PALETTE["ink_soft"]};
        --muted: {PALETTE["muted"]};
        --text-muted: {PALETTE["muted"]};
        --bg-accent: #EAF3DE;
        --terra: {PALETTE["terracotta"]};
        --terra-dark: {PALETTE["terracotta_dark"]};
        --terra-soft: {PALETTE["terracotta_soft"]};
    }}

    html, body, [class*="css"] {{
        font-family: "DM Sans", sans-serif;
        color: var(--ink);
    }}

    .stApp {{
        background: var(--bg);
    }}

    header[data-testid="stHeader"] {{
        background: transparent;
    }}

    #MainMenu, footer {{
        visibility: hidden;
    }}

    [data-testid="stAppDeployButton"] {{
        display: none;
    }}

    [data-testid="stStatusWidget"],
    [data-testid="stSpinner"],
    [data-testid="stToast"],
    div[data-testid="stDecoration"],
    div[data-testid="stToolbar"] {{
        display: none !important;
    }}

    .block-container {{
        width: 100%;
        max-width: none;
        padding: 48px 72px 48px;
    }}

    .block-container > div {{
        width: min(100%, 832px);
        margin: 0;
    }}

    /* ============================================================
       SIDEBAR STATICA — sempre visibile, non collassabile
       ============================================================ */

    /* Forza la sidebar ad essere sempre espansa e di larghezza fissa,
       indipendentemente dall'attributo aria-expanded che Streamlit
       potrebbe impostare a "false" */
    section[data-testid="stSidebar"] {{
        background: var(--sidebar) !important;
        border-right: 1px solid var(--border);
        width: 462px !important;
        min-width: 462px !important;
        max-width: 462px !important;
        transform: none !important;
        visibility: visible !important;
        position: relative !important;
        z-index: 10 !important;
        pointer-events: auto !important;
        transition: none !important;
    }}

    section[data-testid="stSidebar"] > div:first-child {{
        width: 462px !important;
        box-sizing: border-box;
        padding: 40px 30px 28px !important;
        position: relative !important;
        z-index: 11 !important;
        transition: none !important;
    }}

    /* Nasconde completamente il pulsante toggle/freccia di apertura-chiusura,
       in tutte le varianti di data-testid usate dalle diverse versioni di Streamlit */
    button[data-testid="stSidebarCollapseButton"],
    button[data-testid="stExpandSidebarButton"],
    button[data-testid="baseButton-headerNoPadding"],
    button[aria-label*="sidebar" i],
    button[title*="sidebar" i],
    button[aria-label*="Hide" i],
    button[title*="Hide" i],
    button[aria-label*="Collapse" i],
    button[title*="Collapse" i],
    [data-testid="collapsedControl"],
    [data-testid="stSidebarCollapsedControl"],
    [data-testid="stSidebarHeader"] {{
        display: none !important;
        visibility: hidden !important;
        opacity: 0 !important;
        pointer-events: none !important;
        width: 0 !important;
        height: 0 !important;
        overflow: hidden !important;
    }}

    /* Nasconde completamente la navigazione automatica multipagina di Streamlit */
    [data-testid="stSidebarNav"],
    [data-testid="stSidebarNav"] *,
    nav[aria-label="Main navigation"],
    nav[aria-label="Main navigation"] * {{
        display: none !important;
        visibility: hidden !important;
        height: 0 !important;
        min-height: 0 !important;
        margin: 0 !important;
        padding: 0 !important;
        overflow: hidden !important;
    }}

    .sidebar-brand {{
        display: flex;
        align-items: center;
        justify-content: flex-start;
        gap: 10px;
        margin: 0 0 34px;
        padding-left: 8px;
    }}

    section[data-testid="stSidebar"] p.sidebar-title {{
        margin: 0 !important;
        font-family: "Libre Caslon Display", Georgia, serif !important;
        font-size: 25px !important;
        line-height: 1.2 !important;
        color: var(--ink) !important;
    }}

    .sidebar-brand-icon {{
        color: var(--terra);
        display: inline-flex;
        align-items: center;
        justify-content: center;
    }}

    section[data-testid="stSidebar"] [data-testid="stPageLink"],
    section[data-testid="stSidebar"] .stButton {{
        margin-bottom: 17px;
    }}

    section[data-testid="stSidebar"] [data-testid="stPageLink"],
    section[data-testid="stSidebar"] [data-testid="stPageLink"] *,
    section[data-testid="stSidebar"] .stButton,
    section[data-testid="stSidebar"] .stButton * {{
        pointer-events: auto !important;
    }}

    section[data-testid="stSidebar"] [data-testid="stPageLink"] a,
    section[data-testid="stSidebar"] .stButton > button {{
        min-height: 55px;
        padding: 0 20px 0 54px;
        border-radius: 15px;
        border: 0;
        background: transparent;
        color: var(--ink);
        font-size: 27px !important;
        font-weight: 400;
        text-decoration: none;
        width: 100%;
        justify-content: flex-start;
        box-shadow: none;
        cursor: pointer;
    }}

    section[data-testid="stSidebar"] [data-testid="stPageLink"] a p,
    section[data-testid="stSidebar"] .stButton > button p {{
        margin: 0 !important;
        font-size: 27px !important;
        line-height: 1.25 !important;
    }}

    .tabler-icon {{
        display: inline-flex;
        align-items: center;
        justify-content: center;
        flex: 0 0 auto;
        color: currentColor;
        line-height: 1;
        vertical-align: -0.15em;
    }}

    .tabler-icon svg {{
        display: block;
    }}

    .sidebar-nav-icon {{
        display: flex;
        align-items: center;
        justify-content: center;
        position: relative;
        top: 39px;
        left: 20px;
        z-index: 2;
        width: 23px;
        height: 0;
        min-height: 0;
        color: var(--soft);
        pointer-events: none;
    }}

    .sidebar-nav-icon.active {{
        color: var(--terra-dark);
    }}

    section[data-testid="stSidebar"] [data-testid="stPageLink"] a[aria-current="page"] {{
        background: var(--terra-soft);
        color: var(--terra-dark);
    }}

    section[data-testid="stSidebar"] .stButton > button[kind="primary"] {{
        background: var(--terra-soft);
        color: var(--terra-dark);
        font-weight: 600;
    }}

    section[data-testid="stSidebar"] [data-testid="stPageLink"] a:hover,
    section[data-testid="stSidebar"] .stButton > button:hover {{
        background: rgba(243, 217, 196, .55);
        color: var(--ink);
    }}

    section[data-testid="stSidebar"] p.nav-group {{
        margin: 27px 20px 14px !important;
        color: var(--muted) !important;
        font-size: 22px !important;
        line-height: 1 !important;
        letter-spacing: .04em;
        text-transform: uppercase;
    }}

    section[data-testid="stSidebar"] p.nav-placeholder {{
        min-height: 55px;
        margin: 0 !important;
        padding: 9px 20px;
        color: var(--ink) !important;
        font-size: 27px !important;
        line-height: 37px !important;
    }}

    section[data-testid="stSidebar"] p.nav-placeholder-home {{
        min-height: 55px;
        margin: 0 0 17px !important;
        padding: 9px 20px !important;
        border-radius: 15px;
        background: var(--terra-soft);
        color: var(--terra-dark) !important;
        font-size: 27px !important;
        font-weight: 600 !important;
        line-height: 37px !important;
        text-align: center;
    }}

    .sidebar-spacer {{
        height: 63px;
    }}

    .sidebar-user-divider {{
        border-top: 1px solid var(--border);
        margin: 0 0 22px;
    }}

    section[data-testid="stSidebar"] .stTextInput label p {{
        color: var(--muted) !important;
        font-size: 20px !important;
    }}

    section[data-testid="stSidebar"] .stTextInput input {{
        height: 64px;
        padding: 0 20px;
        border: 1px solid var(--border);
        border-radius: 16px;
        background: var(--surface);
        color: var(--ink);
        font-size: 24px;
        box-shadow: none;
    }}

    section[data-testid="stSidebar"] .stTextInput input::placeholder {{
        color: var(--muted);
        opacity: 1;
    }}

    /* Sposta il contenuto principale in modo che non venga mai
       sovrapposto dalla sidebar fissa, anche se Streamlit tenta
       di "collassarla" internamente */
    div[data-testid="stAppViewContainer"] > section.main {{
        margin-left: 0 !important;
        position: relative !important;
        z-index: 0 !important;
    }}

    /* Home */
    .home-shell {{
        margin-bottom: 46px;
    }}

    p.eyebrow {{
        margin: 0 0 2px !important;
        color: var(--terra) !important;
        font-size: 24px !important;
        line-height: 1.2 !important;
        letter-spacing: .055em;
        text-transform: uppercase;
    }}

    h1.home-title {{
        margin: 0 0 19px !important;
        font-family: "Libre Caslon Display", Georgia, serif !important;
        color: var(--ink) !important;
        font-size: 56px !important;
        font-weight: 400 !important;
        line-height: 1.08 !important;
    }}

    p.home-intro {{
        max-width: 830px;
        margin: 0 !important;
        color: var(--soft) !important;
        font-size: 28px !important;
        line-height: 1.65 !important;
    }}

    .model-card {{
        box-sizing: border-box;
        min-height: 294px;
        padding: 78px 28px 28px;
        border: 1px solid var(--border);
        border-radius: 19px;
        background: var(--surface);
    }}

    p.model-card-title {{
        display: flex;
        align-items: center;
        gap: 10px;
        margin: 0 0 8px !important;
        color: var(--ink) !important;
        font-size: 26px !important;
        font-weight: 400 !important;
        line-height: 1.3 !important;
    }}

    p.model-card-desc {{
        margin: 0 !important;
        color: var(--soft) !important;
        font-size: 23px !important;
        line-height: 1.65 !important;
    }}

    .model-card.featured {{
        position: relative;
        display: flex;
        align-items: center;
        min-height: 152px;
        margin: 0 0 36px;
        padding: 28px 38px 28px 145px;
        border: 4px solid var(--terra);
        border-radius: 20px;
    }}

    .model-card.featured::before {{
        content: "";
        position: absolute;
        left: 36px;
        top: 50%;
        width: 80px;
        height: 80px;
        border-radius: 50%;
        background: var(--terra-soft);
        transform: translateY(-50%);
    }}

    .model-card-featured-icon {{
        position: absolute;
        left: 36px;
        top: 50%;
        width: 80px;
        height: 80px;
        display: flex;
        align-items: center;
        justify-content: center;
        color: var(--terra-dark);
        transform: translateY(-50%);
        z-index: 1;
    }}

    p.featured-badge {{
        margin: 0 0 6px !important;
        color: #9A371E !important;
        font-size: 20px !important;
        line-height: 1.2 !important;
    }}

    .model-card.featured p.model-card-title {{
        margin: 0 !important;
        font-size: 27px !important;
    }}

    .model-grid {{
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: 24px;
    }}

    .model-card-note {{
        display: flex;
        align-items: flex-start;
        padding-top: 40px;
        border-color: #E1B98F;
        background: var(--terra-soft);
    }}

    .model-card-note p {{
        margin: 0 !important;
        color: var(--terra-dark) !important;
        font-size: 23px !important;
        line-height: 1.65 !important;
    }}

    /* Componenti condivisi dalle altre pagine */
    h1, h2, h3 {{
        font-family: "Libre Caslon Display", Georgia, serif !important;
        color: var(--ink) !important;
        font-weight: 400 !important;
    }}

    .recipe-card {{
        margin-bottom: 10px;
        padding: 16px 20px;
        border: 1px solid var(--border);
        border-radius: 14px;
        background: var(--surface);
    }}

    .recipe-card.highlighted {{
        border: 2px solid var(--terra);
    }}

    .recipe-title {{
        margin: 0 0 4px;
        color: var(--ink);
        font-size: 1.05rem;
        font-weight: 500;
    }}

    .recipe-card-header {{
        display: flex;
        align-items: flex-start;
        justify-content: space-between;
        gap: 16px;
    }}

    .recipe-card-header .recipe-title {{
        flex: 1;
    }}

    .votes-badge {{
        flex: 0 0 auto;
        padding: 3px 10px;
        border-radius: 20px;
        font-size: 11px;
        font-weight: 500;
        white-space: nowrap;
    }}

    .ready-badge {{
        flex: 0 0 auto;
        padding: 3px 10px;
        border-radius: 20px;
        background: var(--bg-accent);
        color: #0C447C;
        font-size: 11px;
        font-weight: 500;
        white-space: nowrap;
    }}

    .recipe-meta {{
        margin: 0 0 8px;
        color: var(--soft);
        font-size: .85rem;
    }}

    .health-goal-badge {{
        flex: 0 0 auto;
        display: inline-flex;
        align-items: center;
        gap: 5px;
        padding: 3px 10px;
        border-radius: 20px;
        font-size: 11px;
        font-weight: 500;
        white-space: nowrap;
    }}

    .health-goal-badge.ottima {{
        background: #FCEBEB;
        color: #791F1F;
    }}

    .health-goal-badge.buona {{
        background: #FAEEDA;
        color: #633806;
    }}

    .health-goal-badge.discreta {{
        background: #EAF3DE;
        color: #27500A;
    }}

    .compatibility-badge {{
        flex: 0 0 auto;
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 3px 10px;
        border-radius: 20px;
        font-size: 11px;
        font-weight: 500;
        white-space: nowrap;
    }}

    .compatibility-badge .tabler-icon {{
        width: 12px !important;
        height: 12px !important;
    }}

    .compatibility-badge.ottima {{
        background: #FCEBEB;
        color: #791F1F;
    }}

    .compatibility-badge.buona {{
        background: #FAEEDA;
        color: #633806;
    }}

    .compatibility-badge.scarsa {{
        background: var(--surface-1);
        color: var(--soft);
    }}

    .nutrient-bars {{
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 12px;
        margin: 8px 0 10px;
    }}

    .nutrient-bar-labels {{
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 4px;
        color: var(--text-muted);
        font-size: 11px;
        font-weight: 500;
    }}

    .nutrient-bar-track {{
        height: 5px;
        overflow: hidden;
        border-radius: 20px;
        background: var(--surface-1);
    }}

    .nutrient-bar-fill {{
        height: 100%;
        border-radius: 20px;
    }}

    .recipe-score {{
        color: var(--terra);
        font-weight: 500;
        text-align: right;
    }}

    .recipe-score-row {{
        display: flex;
        justify-content: flex-end;
        align-items: center;
        gap: 8px;
    }}

    .recipe-score-row .recipe-score {{
        margin: 0;
    }}

    .vs-average-badge {{
        padding: 2px 8px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 500;
        white-space: nowrap;
    }}

    .match-bar-block {{
        margin: 10px 0 8px;
    }}

    .match-bar-labels {{
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 5px;
        color: var(--text-muted);
        font-size: 11px;
        font-weight: 500;
    }}

    .match-bar-track {{
        height: 6px;
        overflow: hidden;
        border-radius: 20px;
        background: var(--surface-1);
    }}

    .match-bar-fill {{
        height: 100%;
        border-radius: 20px;
    }}

    .load-more-icon-label {{
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 8px;
        margin-top: 14px;
        color: var(--ink);
        font-weight: 500;
    }}

    .pill {{
        display: inline-block;
        margin: 2px 4px 2px 0;
        padding: 2px 9px;
        border-radius: 6px;
        font-size: .72rem;
        font-weight: 500;
    }}

    .pill-have {{
        background: {PALETTE["sage_soft"]};
        color: {PALETTE["sage"]};
    }}

    .pill-ingredient {{
        background: #E3EBE2;
        color: #3B6D11;
    }}

    .pill-neutral {{
        background: #F0EBE1;
        color: var(--ink);
    }}

    .ai-param-pills {{
        margin: 10px 0 18px;
    }}

    .ai-quote {{
        margin: 0 0 18px;
        padding: 14px 18px;
        border-left: 4px solid var(--terra);
        background: #FFFDF8;
        color: var(--soft);
        font-family: "Libre Caslon Display", Georgia, serif;
        font-size: 1.16rem;
        line-height: 1.55;
    }}

    .mode-separator {{
        margin: 42px 0 22px;
    }}

    .pill-missing {{
        background: var(--terra-soft);
        color: var(--terra-dark);
    }}

    .empty-state {{
        padding: 24px;
        border: 1px dashed #E0BFA0;
        border-radius: 12px;
        background: var(--terra-soft);
        color: var(--soft);
        text-align: center;
    }}

    .stButton > button {{
        border: 0;
        border-radius: 8px;
        background: var(--terra);
        color: white;
        font-weight: 500;
    }}

    .stButton > button:disabled,
    .stButton > button[disabled] {{
        opacity: 1 !important;
        cursor: pointer !important;
        filter: none !important;
    }}

    .stButton > button:disabled *,
    .stButton > button[disabled] * {{
        opacity: 1 !important;
    }}

    @media (max-width: 1100px) {{
        section[data-testid="stSidebar"] {{
            width: 360px !important;
            min-width: 360px !important;
            max-width: 360px !important;
        }}

        section[data-testid="stSidebar"] > div:first-child {{
            width: 360px !important;
        }}

        .block-container {{
            padding-left: 34px;
            padding-right: 34px;
        }}

        .block-container > div {{
            width: 100%;
        }}

        .model-grid {{
            grid-template-columns: repeat(2, minmax(0, 1fr));
        }}
    }}

    @media (max-width: 760px) {{
        .block-container {{
            padding: 40px 20px;
        }}

        .home-title {{
            font-size: 43px;
        }}

        .home-intro {{
            font-size: 21px;
        }}

        .model-grid {{
            grid-template-columns: 1fr;
        }}
    }}
</style>
"""


def popularity_page_css() -> str:
    return ""


def render_sidebar(mode: str = "internal") -> None:
    import streamlit as st

    page_links = [
        ("home", "app.py", "Home", "home"),
        ("popularity", "pages/popularity.py", "1 · Popolari", "trophy"),
        ("svuota_frigo", "pages/svuota_frigo.py", "2 · Svuota-frigo", "salad"),
        ("salutistico", "pages/salutistico.py", "3 · Salutistico", "apple"),
        ("mood", "pages/mood.py", "4 · Mood", "mood-smile"),
    ]

    def set_current_page(page_key: str) -> None:
        st.session_state["current_page"] = page_key

    def nav_item(page_key: str, target: str, label: str, icon_name: str) -> None:
        current_page = st.session_state.get("current_page", "home")
        is_active = mode == "internal" and current_page == page_key
        icon_class = "sidebar-nav-icon active" if is_active else "sidebar-nav-icon"

        st.markdown(
            f'<div class="{icon_class}">{tabler_icon(icon_name, size=23)}</div>',
            unsafe_allow_html=True,
        )
        if mode == "pages":
            st.page_link(target, label=label, use_container_width=True)
            return

        st.button(
            label,
            key=f"nav_{page_key}",
            type="primary" if is_active else "secondary",
            use_container_width=True,
            on_click=set_current_page,
            args=(page_key,),
        )

    with st.sidebar:
        st.markdown(
            '<div class="sidebar-brand">'
            f'<span class="sidebar-brand-icon">{tabler_icon("soup", size=26)}</span>'
            '<p class="sidebar-title">Food Recommender</p>'
            "</div>",
            unsafe_allow_html=True,
        )

        nav_item(*page_links[0])

        st.markdown('<p class="nav-group">Senza profilo</p>', unsafe_allow_html=True)
        nav_item(*page_links[1])
        nav_item(*page_links[2])

        st.markdown('<p class="nav-group">Con vincoli</p>', unsafe_allow_html=True)
        nav_item(*page_links[3])
        nav_item(*page_links[4])

        if "user_id" not in st.session_state:
            st.session_state.user_id = ""


def recipe_card_html(
    name: str,
    meta: str,
    score_label: str,
    score_value,
    pills_have=None,
    pills_missing=None,
    highlighted=False,
    votes_badge: dict | None = None,
    score_separator: str = ": ",
    ingredients=None,
    steps=None,
    vs_average: float | None = None,
    match_pct: float | None = None,
    ready_badge: bool = False,
    goal_badge: dict | None = None,
    nutrient_bars=None,
    compat_pct: float | None = None,
    compat_label: str | None = None,
    protein_pdv: float | None = None,
    fat_pdv: float | None = None,
) -> str:
    pills_html = ""
    if pills_have:
        pills_html += "".join(
            f'<span class="pill pill-have">{escape(str(p))}</span>'
            for p in pills_have
        )
    if pills_missing:
        pills_html += "".join(
            f'<span class="pill pill-missing">+ {escape(str(p))}</span>'
            for p in pills_missing
        )

    css_class = "recipe-card highlighted" if highlighted else "recipe-card"
    if votes_badge:
        css_class += " with-votes"
    pills_block = (
        f'<div style="margin-bottom:8px">{pills_html}</div>' if pills_html else ""
    )
    badges_html = ""
    badge_items = []
    if votes_badge:
        numero_voti = int(votes_badge.get("numero_voti", 0))
        if numero_voti >= 200:
            badge_bg = "#EAF3DE"
            badge_color = "#27500A"
            badge_label = "alta fiducia"
        elif numero_voti >= 50:
            badge_bg = "#FAEEDA"
            badge_color = "#633806"
            badge_label = "media fiducia"
        else:
            badge_bg = "#FCEBEB"
            badge_color = "#791F1F"
            badge_label = "fiducia bassa"
        badge_items.append(
            f'<span class="votes-badge" style="background:{badge_bg}; color:{badge_color};">'
            f"{numero_voti} voti · {badge_label}</span>"
        )
    if ready_badge:
        badge_items.append('<span class="ready-badge">pronta subito</span>')
    if compat_label is not None:
        compat_tone = ""
        if compat_pct is not None:
            if compat_pct >= 75:
                compat_tone = "ottima"
            elif compat_pct >= 40:
                compat_tone = "buona"
            else:
                compat_tone = "scarsa"
        badge_items.append(
            '<span class="compatibility-badge '
            f'{compat_tone}">{tabler_icon("ti-flame", size=12)}'
            f'<span>{escape(str(compat_label))}</span></span>'
        )
    elif goal_badge:
        badge_tone = escape(str(goal_badge.get("tone", "discreta")))
        badge_label = escape(str(goal_badge.get("label", "")))
        badge_items.append(
            f'<span class="health-goal-badge {badge_tone}">{badge_label}</span>'
        )
    if badge_items:
        badges_html = (
            '<div style="display:flex; gap:8px; align-items:center;">'
            f"{''.join(badge_items)}</div>"
        )

    title_html = (
        '<div class="recipe-card-header">'
        f'<p class="recipe-title">{escape(str(name))}</p>'
        f"{badges_html}"
        "</div>"
    )
    if compat_pct is not None:
        score_html = (
            '<p class="recipe-score">'
            f"Compatibilità con l'obiettivo: {int(round(float(compat_pct)))}%"
            "</p>"
        )
    else:
        score_html = (
            f'<p class="recipe-score">{escape(str(score_label))}{escape(str(score_separator))}'
            f"{escape(str(score_value))}</p>"
        )
    if vs_average is not None:
        if vs_average >= 0:
            average_bg = "#EAF3DE"
            average_color = "#27500A"
            average_text = f"+{vs_average:.2f} sopra la media"
        else:
            average_bg = "#FCEBEB"
            average_color = "#791F1F"
            average_text = f"{abs(vs_average):.2f} sotto la media"
        score_html = (
            '<div class="recipe-score-row">'
            f"{score_html}"
            f'<span class="vs-average-badge" style="background:{average_bg}; color:{average_color};">'
            f"{escape(average_text)}</span>"
            "</div>"
        )
    match_bar_html = ""
    if match_pct is not None:
        match_pct_clean = max(0, min(100, int(round(float(match_pct)))))
        if match_pct_clean >= 80:
            match_color = "#639922"
        elif match_pct_clean >= 40:
            match_color = "#EF9F27"
        else:
            match_color = "#E24B4A"
        match_bar_html = (
            '<div class="match-bar-block">'
            '<div class="match-bar-labels">'
            "<span>Corrispondenza ingredienti</span>"
            f"<span>{match_pct_clean}%</span>"
            "</div>"
            '<div class="match-bar-track">'
            f'<div class="match-bar-fill" style="width:{match_pct_clean}%; background:{match_color};"></div>'
            "</div>"
            "</div>"
        )

    nutrient_bars_html = ""
    if protein_pdv is not None or fat_pdv is not None:
        nutrient_entries = []
        if protein_pdv is not None:
            nutrient_entries.append(
                {
                    "label": "Proteine",
                    "value": protein_pdv,
                    "suffix": "% DV",
                    "color": "#3B6D11",
                }
            )
        if fat_pdv is not None:
            nutrient_entries.append(
                {
                    "label": "Grassi",
                    "value": fat_pdv,
                    "suffix": "% DV",
                    "color": "#B08B3A",
                }
            )
        nutrient_bars = nutrient_entries

    if nutrient_bars:
        nutrient_items = []
        for nutrient in nutrient_bars:
            value = float(nutrient.get("value", 0))
            max_value = float(nutrient.get("max", 100))
            width_pct = 0 if max_value == 0 else max(0, min(100, (value / max_value) * 100))
            label = escape(str(nutrient.get("label", "")))
            suffix = escape(str(nutrient.get("suffix", "")))
            color = escape(str(nutrient.get("color", "#639922")))
            display_value = f"{int(round(value))}{suffix}"
            nutrient_items.append(
                '<div class="nutrient-bar">'
                '<div class="nutrient-bar-labels">'
                f"<span>{label}</span>"
                f"<span>{escape(display_value)}</span>"
                "</div>"
                '<div class="nutrient-bar-track">'
                f'<div class="nutrient-bar-fill" style="width:{width_pct:.1f}%; background:{color};"></div>'
                "</div>"
                "</div>"
            )
        nutrient_bars_html = f'<div class="nutrient-bars">{"".join(nutrient_items)}</div>'

    return (
        f'<div class="{css_class}">'
        f"{title_html}"
        f'<p class="recipe-meta">{escape(str(meta))}</p>'
        f"{match_bar_html}"
        f"{nutrient_bars_html}"
        f"{pills_block}"
        f"{score_html}"
        "</div>"
    )


def ingredient_pills_html(ingredients: list[str]) -> str:
    """Genera le pillole degli ingredienti per i dettagli ricetta."""
    if not ingredients:
        return ""
    return "".join(
        f'<span class="pill pill-ingredient">{escape(str(ingredient))}</span>'
        for ingredient in ingredients
    )


def param_pills_html(
    mood_dict: dict | None = None,
    health_dict: dict | None = None,
    ingredients_list: list[str] | None = None,
) -> str:
    """Genera pillole neutre per i parametri estratti dal testo libero."""
    pills = []

    if ingredients_list:
        for ingredient in ingredients_list:
            pills.append(f"ingrediente: {ingredient}")

    if mood_dict:
        for axis, value in mood_dict.items():
            pills.append(f"{axis}: {float(value):+.1f}")

    if health_dict:
        labels = {
            "max_calories": "max kcal",
            "min_protein_pct": "proteine min",
            "tags_required": "tag",
            "profile_name": "profilo",
        }
        for key, value in health_dict.items():
            if value in (None, [], ""):
                continue
            display_value = ", ".join(value) if isinstance(value, list) else value
            pills.append(f"{labels.get(key, key)}: {display_value}")

    if not pills:
        pills = ["nessun vincolo esplicito"]

    pills_html = "".join(
        f'<span class="pill pill-neutral">{escape(str(pill))}</span>'
        for pill in pills
    )
    return f'<div class="ai-param-pills">{pills_html}</div>'


def explanation_quote_html(text: str) -> str:
    return f'<div class="ai-quote">{escape(str(text))}</div>'


def model_card_html(
    icon: str,
    title: str,
    description: str,
    icon_name: str = None,
    featured: bool = False,
) -> str:
    css_class = "model-card featured" if featured else "model-card"
    badge = (
        '<p class="featured-badge">consigliato per iniziare</p>'
        if featured
        else ""
    )
    description_html = (
        f'<p class="model-card-desc">{escape(description)}</p>'
        if description
        else ""
    )
    selected_icon = icon_name or icon or ""
    featured_icon_html = (
        f'<span class="model-card-featured-icon">'
        f'{tabler_icon(selected_icon, size=38, color="#8C3A1F")}</span>'
        if featured and selected_icon
        else ""
    )
    title_icon_html = (
        tabler_icon(selected_icon, size=20, color="#7A6A57")
        if selected_icon and not featured
        else ""
    )

    return (
        f'<div class="{css_class}">{featured_icon_html}<div>{badge}'
        f'<p class="model-card-title">{title_icon_html}<span>{escape(title)}</span></p>'
        f"{description_html}</div></div>"
    )


def empty_state_html(message: str) -> str:
    return f'<div class="empty-state">{escape(message)}</div>'
