import base64
import mimetypes
from pathlib import Path
import streamlit as st


def render_nvidia_vista_card() -> None:
    """Render a modern NVIDIA VISTA-3D badge that links to NVIDIA Build."""
    vista_url = "https://build.nvidia.com/nvidia/vista-3d"

    # Prepare inline images as base64 so the card renders reliably inside HTML
    try:
        hero_candidates = [
            Path(__file__).parent / 'vista-3d.jpg',
            Path(__file__).parent / 'vista-3d.png',
            Path(__file__).parent / 'vista-3d.webp',
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
      .nv-card {{
        position: relative;
        display: block;
        border-radius: 14px;
        overflow: hidden;
        margin-bottom: 10px;
        border: 1px solid rgba(118,185,0,0.35);
        background: radial-gradient(120% 120% at 0% 0%, #0f130f 0%, #0b0d0a 45%, #131613 100%);
        box-shadow: 0 6px 18px rgba(0,0,0,0.35), inset 0 0 0 1px rgba(118,185,0,0.08);
        transition: transform .15s ease, box-shadow .2s ease, border-color .2s ease;
        text-decoration: none;
      }}
      .nv-card:hover {{
        transform: translateY(-2px);
        box-shadow: 0 10px 24px rgba(0,0,0,0.45), inset 0 0 0 1px rgba(118,185,0,0.12);
        border-color: rgba(118,185,0,0.6);
      }}
      /* Ensure no underlines appear on any text inside the card */
      .nv-card, .nv-card:hover, .nv-card * {{ text-decoration: none !important; }}
      .nv-hero {{
        height: 112px;
        background: linear-gradient(180deg, rgba(0,0,0,0.0), rgba(0,0,0,0.35)), url('data:{hero_mime};base64,{hero_b64}') center/cover no-repeat;
        filter: saturate(1.05) contrast(1.05);
      }}
      .nv-body {{
        padding: 12px 12px 14px 12px;
      }}
      .nv-title {{
        display: flex; align-items: center; gap: 8px;
        color: #e9f5dd; font-weight: 700; letter-spacing: .2px;
      }}
      .nv-title .nv-wordmark {{
        color: #76b900; font-size: 13px; font-weight: 800; letter-spacing: .8px;
        display: inline-block; text-transform: uppercase; line-height: 1;
      }}
      .nv-kicker {{ color: #a6d36b; font-size: 11px; font-weight: 600; opacity: .9; }}
      .nv-name {{ color: #ffffff; font-size: 15px; }}
      .nv-desc {{ color: #d7dfcf; font-size: 12px; line-height: 1.35; margin-top: 6px; opacity: .95; }}
      .nv-tags {{ display: flex; flex-wrap: wrap; gap: 6px; margin-top: 10px; }}
      .nv-tag {{
        font-size: 10.5px; font-weight: 600; letter-spacing: .2px;
        padding: 3px 8px; border-radius: 999px; border: 1px solid rgba(118,185,0,.35);
        color: #b9e07d; background: rgba(118,185,0,.12);
      }}
      .nv-cta {{
        margin-top: 10px; display: inline-block; width: 100%; text-align: center;
        color: #0b0d0a; background: #76b900; border-radius: 10px; padding: 7px 10px;
        font-weight: 700; font-size: 12px; letter-spacing: .2px; border: none;
      }}
      .nv-cta:hover {{ filter: brightness(1.05); }}
    </style>
    """

    logo_img = "<span class='nv-wordmark'>NVIDIA</span>"

    card_html = f"""
    <a class="nv-card" href="{vista_url}" target="_blank" rel="noopener noreferrer">
      <div class="nv-hero"></div>
      <div class="nv-body">
        <div class="nv-kicker">FOUNDATION MODEL</div>
        <div class="nv-title">{logo_img}<span class="nv-name">VISTA‑3D</span></div>
        <div class="nv-desc">Specialized interactive model for 3D medical image segmentation.</div>
        <div class="nv-tags">
          <span class="nv-tag">interactive annotation</span>
          <span class="nv-tag">3D segmentation</span>
          <span class="nv-tag">medical imaging</span>
        </div>
        <div class="nv-cta">Open on NVIDIA Build ↗</div>
      </div>
    </a>
    """

    with st.sidebar.container():
        st.markdown(card_css + card_html, unsafe_allow_html=True)


