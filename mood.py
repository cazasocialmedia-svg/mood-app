import streamlit as st
import yt_dlp
import sqlite3
import os

# --- 1. CONFIGURACIÓN DE BASE DE DATOS (BLINDADA PARA LA NUBE) ---
DB_FILE = 'mood_vault_FINAL.db'

def get_connection():
    return sqlite3.connect(DB_FILE, check_same_thread=False)

def init_db():
    conn = get_connection()
    c = conn.cursor()
    # Crea la tabla si no existe (esto elimina el error de tu captura)
    c.execute('''CREATE TABLE IF NOT EXISTS playlist_data 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  lista TEXT, 
                  cancion TEXT, 
                  url TEXT)''')
    conn.commit()
    conn.close()

# EJECUTAR INICIALIZACIÓN AL ABRIR LA APP
init_db()

# --- 2. CONFIGURACIÓN DE PÁGINA Y DISEÑO ---
st.set_page_config(page_title="MOOD", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: white; }
    .stRadio > div { display: flex !important; justify-content: center !important; gap: 10vw !important; margin-bottom: 20px !important; }
    .stRadio label { font-size: 20px !important; font-weight: bold !important; color: #333 !important; }
    .stTextInput { max-width: 800px !important; margin: 0 auto !important; }
    div.stButton > button:first-child { background-color: #df0000 !important; color: white !important; border-radius: 8px !important; font-weight: bold !important; }
    h1, h3 { text-align: center !important; }
    [data-testid="stHorizontalBlock"] { align-items: center !important; }
    </style>
    """, unsafe_allow_html=True)

if 'recoms' not in st.session_state: st.session_state.recoms = []

sel_pag = st.radio("", ["DESCUBRIR", "BIBLIOTECA"], horizontal=True, label_visibility="collapsed")

if sel_pag == "DESCUBRIR":
    st.markdown("<h1>🎧 MOOD</h1>", unsafe_allow_html=True)
    url_input = st.text_input("", placeholder="Pega un link de YouTube aquí...", key="search_v22")

    if url_input and url_input != st.session_state.get('last_url'):
        st.session_state.last_url = url_input
        with st.spinner("Buscando música..."):
            with yt_dlp.YoutubeDL({'quiet': True, 'extract_flat': True}) as ydl:
                info = ydl.extract_info(url_input, download=False)
                artista = info.get('uploader', '').split('-')[0].strip()
                query = f"ytsearch10:{artista} official audio -playlist -mix"
                st.session_state.recoms = ydl.extract_info(query, download=False)['entries']

    if st.session_state.recoms:
        st.markdown("<h3>RECOMENDADOS</h3>", unsafe_allow_html=True)
        conn = get_connection(); c = conn.cursor()
        c.execute('SELECT DISTINCT lista FROM playlist_data'); listas = [r[0] for r in c.fetchall()]; conn.close()
        for vid in st.session_state.recoms:
            c1, c2, c3, c4 = st.columns([4, 1, 1.5, 0.5])
            l_vid = f"https://www.youtube.com/watch?v={vid['id']}"
            c1.write(f"**{vid['title']}**")
            c2.link_button("Oír", l_vid)
            with c3:
                if listas:
                    dest = st.selectbox("Carpeta:", listas, key=f"s_{vid['id']}", label_visibility="collapsed")
                    if st.button("💾", key=f"b_{vid['id']}"):
                        conn = get_connection(); c = conn.cursor()
                        c.execute('INSERT INTO playlist_data (lista, cancion, url) VALUES (?, ?, ?)', (dest, vid['title'], l_vid))
                        conn.commit(); conn.close(); st.rerun()
            c4.button("🗑️", key=f"t_{vid['id']}")
            st.divider()
else:
    st.markdown("<h1>📂 MI BIBLIOTECA</h1>", unsafe_allow_html=True)
    c_in, c_bt = st.columns([3, 1])
    nueva_c = c_in.text_input("Nombre", placeholder="Nueva carpeta...", label_visibility="collapsed")
    if c_bt.button("➕ Crear", use_container_width=True):
        if nueva_c:
            conn = get_connection(); c = conn.cursor()
            c.execute('INSERT INTO playlist_data (lista, cancion, url) VALUES (?, ?, ?)', (nueva_c, "DB_INIT", "NONE"))
            conn.commit(); conn.close(); st.rerun()
    st.divider()
    conn = get_connection(); c = conn.cursor()
    c.execute('SELECT DISTINCT lista FROM playlist_data')
    for l_name in [r[0] for r in c.fetchall()]:
        c.execute('SELECT id, cancion, url FROM playlist_data WHERE lista = ? AND cancion != "DB_INIT"', (l_name,))
        canciones = c.fetchall()
        with st.expander(f"📁 {l_name} ({len(canciones)} temas)", expanded=True):
            col_p, col_d = st.columns([4, 1])
            if canciones:
                ids = [r[2].split('com/0')[-1] for r in canciones]
                col_p.link_button(f"▶️ REPRODUCIR TODO", f"https://www.youtube.com/watch_videos?video_ids={','.join(ids)}", use_container_width=True)
            if col_d.button("🔥 Borrar", key=f"fdel_{l_name}"):
                c.execute('DELETE FROM playlist_data WHERE lista = ?', (l_name,))
                conn.commit(); st.rerun()
            for id_db, nom, url in canciones:
                ci, cp, cd = st.columns([5, 1, 1])
                ci.write(f"🎵 {nom}")
                cp.link_button("▶️", url)
                if cd.button("🗑️", key=f"del_{id_db}"):
                    c.execute('DELETE FROM playlist_data WHERE id = ?', (id_db,)); conn.commit(); st.rerun()
    conn.close()

