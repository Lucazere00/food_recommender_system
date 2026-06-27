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


def get_css() -> str:
    return f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500&family=Libre+Caslon+Display&display=swap');

    :root {{
        --bg: {PALETTE["bg"]};
        --sidebar: {PALETTE["bg_sidebar"]};
        --surface: {PALETTE["surface"]};
        --border: {PALETTE["border"]};
        --ink: {PALETTE["ink"]};
        --soft: {PALETTE["ink_soft"]};
        --muted: {PALETTE["muted"]};
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

    .block-container {{
        width: 100%;
        max-width: none;
        padding: 48px 72px 48px;
    }}

    .block-container > div {{
        width: min(100%, 832px);
        margin: 0;
    }}

    /* Sidebar */
    section[data-testid="stSidebar"] {{
        width: 462px !important;
        min-width: 462px !important;
        background: var(--sidebar);
        border-right: 1px solid var(--border);
    }}

    section[data-testid="stSidebar"] > div:first-child {{
        width: 462px !important;
        box-sizing: border-box;
        padding: 40px 30px 28px !important;
    }}

    section[data-testid="stSidebar"] [data-testid="stSidebarNav"] {{
        display: none;
    }}

    .sidebar-brand {{
        text-align: center;
        margin: -100px 0 66px;
    }}

    section[data-testid="stSidebar"] p.sidebar-title {{
        margin: 0 !important;
        font-family: "Libre Caslon Display", Georgia, serif !important;
        font-size: 30px !important;
        line-height: 1.2 !important;
        color: var(--ink) !important;
    }}

    section[data-testid="stSidebar"] p.sidebar-subtitle {{
        margin: 16px 0 0 !important;
        color: var(--soft) !important;
        font-size: 24px !important;
        line-height: 1.35 !important;
    }}

    section[data-testid="stSidebar"] [data-testid="stPageLink"] {{
        margin-bottom: 17px;
    }}

    section[data-testid="stSidebar"] [data-testid="stPageLink"] a {{
        min-height: 55px;
        padding: 0 20px 0 74px;
        border-radius: 15px;
        color: var(--ink);
        font-size: 27px !important;
        font-weight: 400;
        text-decoration: none;
    }}

    section[data-testid="stSidebar"] [data-testid="stPageLink"] a p {{
        margin: 0 !important;
        font-size: 27px !important;
        line-height: 1.25 !important;
    }}

    section[data-testid="stSidebar"] [data-testid="stPageLink"] a[aria-current="page"] {{
        background: var(--terra-soft);
        color: var(--terra-dark);
    }}

    section[data-testid="stSidebar"] [data-testid="stPageLink"] a:hover {{
        background: rgba(243, 217, 196, .55);
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
        padding: 9px 20px 9px 74px;
        color: var(--ink) !important;
        font-size: 27px !important;
        line-height: 37px !important;
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

    .recipe-meta {{
        margin: 0 0 8px;
        color: var(--soft);
        font-size: .85rem;
    }}

    .recipe-score {{
        color: var(--terra);
        font-weight: 500;
        text-align: right;
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

    @media (max-width: 1100px) {{
        section[data-testid="stSidebar"],
        section[data-testid="stSidebar"] > div {{
            width: 360px !important;
            min-width: 360px !important;
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


def recipe_card_html(
    name: str,
    meta: str,
    score_label: str,
    score_value,
    pills_have=None,
    pills_missing=None,
    highlighted=False,
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
    pills_block = (
        f'<div style="margin-bottom:8px">{pills_html}</div>' if pills_html else ""
    )

    return (
        f'<div class="{css_class}">'
        f'<p class="recipe-title">{escape(str(name))}</p>'
        f'<p class="recipe-meta">{escape(str(meta))}</p>'
        f"{pills_block}"
        f'<p class="recipe-score">{escape(str(score_label))}: '
        f"{escape(str(score_value))}</p>"
        "</div>"
    )


def model_card_html(
    icon: str,
    title: str,
    description: str,
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

    return (
        f'<div class="{css_class}"><div>{badge}'
        f'<p class="model-card-title">{escape(title)}</p>'
        f"{description_html}</div></div>"
    )


def empty_state_html(message: str) -> str:
    return f'<div class="empty-state">{escape(message)}</div>'
