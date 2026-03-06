import streamlit as st
import yt_dlp

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="MOOD", layout="wide")

# Estilo visual
st.markdown("""
    <style>
    .stApp { background-color: white; }
    .stRadio > div { display: flex !important; justify-content: center !important; gap: 20px !important; }
    .stRadio label { font-size: 20px !important; font-weight: bold !important; color: #333 !important; }
    h1, h3 { text-align: center !important; }
    div.stButton > button { background-color: #df0000 !important; color: white !important; width: 100%; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. MEMORIA DE LA APP (Sustituye a la base de datos) ---
if 'playlists' not in st.session_state:
    st.session_state.playlists = {}
if 'recoms' not in st.session_state:
    st.session_state.recoms = []

# --- 3. NAVEGACIÓN ---
sel = st.radio("", ["DESCUBRIR", "BIBLIOTECA"], horizontal=True, label_visibility="collapsed")

if sel == "DESCUBRIR":
    st.markdown("<h1>🎧 MOOD</h1>", unsafe_allow_html=True)
    url_in = st.text_input("", placeholder="Pega un link de YouTube aquí...")

    if url_in:
        with st.spinner("Buscando..."):
            with yt_dlp.YoutubeDL({'quiet': True, 'extract_flat': True}) as ydl:
                info = ydl.extract_info(url_in, download=False)
                art = info.get('uploader', 'Musica').split('-')[0]
                results = ydl.extract_info(f"ytsearch:5 {art} official audio", download=False)['entries']
                st.session_state.recoms = results

    for v in st.session_state.recoms:
        c1, c2, c3 = st.columns([3, 1, 1.5])
        c1.write(f"**{v['title']}**")
        c2.link_button("Oír", f"https://www.youtube.com/watch?v={v['id']}")
        with c3:
            if st.session_state.playlists:
                dest = st.selectbox("Añadir a:", list(st.session_state.playlists.keys()), key=v['id'])
                if st.button("💾", key=f"b_{v['id']}"):
                    st.session_state.playlists[dest].append({'t': v['title'], 'u': f"https://www.youtube.com/watch?v={v['id']}"})
                    st.toast("¡Guardado!")
        st.divider()

else:
    st.markdown("<h1>📂 BIBLIOTECA</h1>", unsafe_allow_html=True)
    
    # Crear carpeta
    c1, c2 = st.columns([3, 1])
    nueva = c1.text_input("Nueva carpeta...")
    if c2.button("➕"):
        if nueva and nueva not in st.session_state.playlists:
            st.session_state.playlists[nueva] = []
            st.rerun()

    for nombre, canciones in st.session_state.playlists.items():
        with st.expander(f"📁 {nombre} ({len(canciones)})"):
            if canciones:
                # Link para reproducir todo
                ids = [c['u'].split('=')[-1] for c in canciones]
                st.link_button("▶️ REPRODUCIR CARPETA", f"https://www.youtube.com/watch_videos?video_ids={','.join(ids)}")
            
            for i, can in enumerate(canciones):
                col1, col2 = st.columns([4, 1])
                col1.write(f"🎵 {can['t']}")
                col2.link_button("▶️", can['u'])

