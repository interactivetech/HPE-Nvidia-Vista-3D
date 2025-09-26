import base64
import mimetypes
from pathlib import Path
import streamlit as st


def render_niivue_badge() -> None:
    """Render a NiiVue badge linking to the official site."""
    target_url = "https://niivue.com/"

    # Local hero candidates (optional) — prefer niivue.png
    hero_candidates = [
        Path(__file__).parent / 'niivue.png',
        Path(__file__).parent / 'CT-Image-Planes-768x768.jpeg',
        Path(__file__).parent / 'vista-3d.jpg',
    ]
    hero_path = next((p for p in hero_candidates if p.exists()), None)
    hero_b64 = ''
    hero_mime = 'image/jpeg'
    if hero_path and hero_path.exists():
        guessed_mime, _ = mimetypes.guess_type(str(hero_path))
        hero_mime = guessed_mime or 'image/jpeg'
        hero_b64 = base64.b64encode(hero_path.read_bytes()).decode('utf-8')

    card_css = f"""
    <style>
      .nvw-card {{
        position: relative; display: block; border-radius: 14px; overflow: hidden;
        margin-top: 6px; border: 1px solid rgba(0, 162, 255, 0.35);
        background: radial-gradient(120% 120% at 0% 0%, #0e1014 0%, #0a0c12 45%, #12151a 100%);
        box-shadow: 0 6px 18px rgba(0,0,0,0.35), inset 0 0 0 1px rgba(0,162,255,0.08);
        transition: transform .15s ease, box-shadow .2s ease, border-color .2s ease; text-decoration: none;
      }}
      .nvw-card:hover {{ transform: translateY(-2px); box-shadow: 0 10px 24px rgba(0,0,0,0.45), inset 0 0 0 1px rgba(0,162,255,0.12); border-color: rgba(0,162,255,0.6); }}
      .nvw-card, .nvw-card:hover, .nvw-card * {{ text-decoration: none !important; }}
      .nvw-hero {{ height: 100px; background: linear-gradient(180deg, rgba(0,0,0,0.0), rgba(0,0,0,0.35)), url('data:{hero_mime};base64,{hero_b64}') center/cover no-repeat; filter: saturate(1.05) contrast(1.05); }}
      .nvw-body {{ padding: 12px; }}
      .nvw-title {{ display: flex; align-items: center; gap: 8px; color: #e8f2ff; font-weight: 800; letter-spacing: .2px; }}
      .nvw-wordmark {{ color: #00a2ff; font-size: 13px; font-weight: 900; letter-spacing: .8px; text-transform: uppercase; line-height: 1; }}
      .nvw-desc {{ color: #cfe4ff; font-size: 12px; line-height: 1.35; margin-top: 6px; opacity: .95; }}
      .nvw-cta {{ margin-top: 10px; display: inline-block; width: 100%; text-align: center; color: #0b0d0a; background: #00a2ff; border-radius: 10px; padding: 7px 10px; font-weight: 700; font-size: 12px; letter-spacing: .2px; border: none; }}
      .nvw-cta:hover {{ filter: brightness(1.05); }}
    </style>
    """

    card_html = f"""
    <a class="nvw-card" href="{target_url}" target="_blank" rel="noopener noreferrer">
      <div class="nvw-hero"></div>
      <div class="nvw-body">
        <div class="nvw-title"><span class="nvw-wordmark">NiiVue</span><span>WebGL2 Medical Image Viewer</span></div>
        <div class="nvw-desc">Fast, cross‑platform, developer‑friendly viewer for medical images.</div>
        <div class="nvw-cta">Visit niivue.com ↗</div>
      </div>
    </a>
    """

    with st.sidebar.container():
        st.markdown(card_css + card_html, unsafe_allow_html=True)


