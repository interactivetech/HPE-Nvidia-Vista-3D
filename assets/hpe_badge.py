import base64
import mimetypes
from pathlib import Path
import streamlit as st


def render_hpe_badge() -> None:
    """Render an HPE AI badge linking to HPE AI site."""
    st.sidebar.markdown("---")

    hpe_url = "https://hpe.com/ai"

    # Prepare inline images as base64 so the card renders reliably inside HTML
    try:
        # Prefer the requested hero first
        hero_candidates = [
            Path(__file__).parent / 'hpe-ai.png',
            Path(__file__).parent / 'hpe-ai.jpg',
            Path(__file__).parent / 'HPE.png',     # local fallback
            Path(__file__).parent / 'vista-3d.jpg',
            Path(__file__).parent / 'CT-Image-Planes-768x768.jpeg',
        ]
        hero_path = next((p for p in hero_candidates if p.exists()), None)
        hero_b64 = ''
        hero_mime = 'image/jpeg'
        if hero_path and hero_path.exists():
            guessed_mime, _ = mimetypes.guess_type(str(hero_path))
            hero_mime = guessed_mime or 'image/jpeg'
            hero_b64 = base64.b64encode(hero_path.read_bytes()).decode('utf-8')
    except Exception:
        hero_b64 = ''
        hero_mime = 'image/jpeg'

    card_css = f"""
    <style>
      .hpe-card {{
        position: relative;
        display: block;
        border-radius: 14px;
        overflow: hidden;
        border: 1px solid rgba(0,179,136,0.35);
        background: radial-gradient(120% 120% at 0% 0%, #0f1311 0%, #0a0f0d 45%, #131614 100%);
        box-shadow: 0 6px 18px rgba(0,0,0,0.35), inset 0 0 0 1px rgba(0,179,136,0.08);
        transition: transform .15s ease, box-shadow .2s ease, border-color .2s ease;
        text-decoration: none;
      }}
      .hpe-card:hover {{
        transform: translateY(-2px);
        box-shadow: 0 10px 24px rgba(0,0,0,0.45), inset 0 0 0 1px rgba(0,179,136,0.12);
        border-color: rgba(0,179,136,0.6);
      }}
      .hpe-card, .hpe-card:hover, .hpe-card * {{ text-decoration: none !important; }}
      .hpe-hero {{
        height: 112px;
        background: linear-gradient(180deg, rgba(0,0,0,0.0), rgba(0,0,0,0.35)), url('data:{hero_mime};base64,{hero_b64}') center/cover no-repeat;
        filter: saturate(1.05) contrast(1.05);
      }}
      .hpe-body {{
        padding: 12px 12px 14px 12px;
      }}
      .hpe-title {{
        display: flex; align-items: center; gap: 8px;
        color: #e9f5ee; font-weight: 700; letter-spacing: .2px;
      }}
      .hpe-title .hpe-wordmark {{
        color: #00b388; font-size: 13px; font-weight: 800; letter-spacing: .8px;
        display: inline-block; text-transform: uppercase; line-height: 1;
      }}
      .hpe-kicker {{ color: #00b388; font-size: 11px; font-weight: 700; opacity: .95; }}
      .hpe-name {{ color: #ffffff; font-size: 15px; }}
      .hpe-desc {{ color: #d7dfdb; font-size: 12px; line-height: 1.35; margin-top: 6px; opacity: .95; }}
      .hpe-tags {{ display: flex; flex-wrap: wrap; gap: 6px; margin-top: 10px; }}
      .hpe-tag {{
        font-size: 10.5px; font-weight: 600; letter-spacing: .2px;
        padding: 3px 8px; border-radius: 999px; border: 1px solid rgba(0,179,136,.35);
        color: #84e6c9; background: rgba(0,179,136,.12);
      }}
      .hpe-cta {{
        margin-top: 10px; display: inline-block; width: 100%; text-align: center;
        color: #0b0d0a; background: #00b388; border-radius: 10px; padding: 7px 10px;
        font-weight: 700; font-size: 12px; letter-spacing: .2px; border: none;
      }}
      .hpe-cta:hover {{ filter: brightness(1.05); }}
    </style>
    """

    logo_html = "<span class='hpe-wordmark'>HPE</span>"

    card_html = f"""
    <a class="hpe-card" href="{hpe_url}" target="_blank" rel="noopener noreferrer">
      <div class="hpe-hero"></div>
      <div class="hpe-body">
        <div class="hpe-kicker">AI SOLUTIONS</div>
        <div class="hpe-title">{logo_html}<span class="hpe-name">Artificial Intelligence</span></div>
        <div class="hpe-desc">Accelerate AI from edge to cloud with enterprise-grade platforms.</div>
        <div class="hpe-tags">
          <span class="hpe-tag">AI infrastructure</span>
          <span class="hpe-tag">edge to cloud</span>
          <span class="hpe-tag">GreenLake</span>
        </div>
        <div class="hpe-cta">Explore HPE AI ↗</div>
      </div>
    </a>
    """

    with st.sidebar.container():
        st.markdown(card_css + card_html, unsafe_allow_html=True)


