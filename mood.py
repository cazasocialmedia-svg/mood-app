import streamlit as st
import yt_dlp
import sqlite3
import os

# --- 1. CONFIGURACIÓN DE BASE DE DATOS (VERSION NUBE CORREGIDA) ---
# Usamos un nombre nuevo para forzar a la nube a crear el archivo desde cero
DB_FILE = 'mood_database_v23.db'

def get_connection():
    return sqlite3.connect(DB_FILE, check_same_thread=False)

def init_db():
    try:
        conn = get_connection()
        c = conn.cursor()
        # Crea la tabla necesaria para que no de error al buscar carpetas
        c.execute('''CREATE TABLE IF NOT EXISTS playlist_data 
                     (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                      lista TEXT, 
                      cancion TEXT, 
                      url TEXT)''')
        conn.commit()
        conn.close()
    except Exception as e:
        st.error(f"Error al iniciar base de datos: {e}")

# EJECUTAR INICIALIZACIÓN ANTES DE MOSTRAR LA APP
init_db()

# --- 2. DISEÑO Y ESTILO ---
st.set_page_config(page_title="MOOD", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: white; }
    /* Pestañas navegación */
    .stRadio > div { display: flex !important; justify-content: center !important; gap: 8vw !important; margin-bottom: 20px !important; }
    .stRadio label { font-size: 18px !important; font-weight: bold !important; color: #444 !important; }
    /* Buscador */
    .stTextInput { max-width: 700px !important; margin: 0 auto !important; }
    /* Botón Reproducir Rojo */
    div.stButton > button:first-child { background-color: #df0000 !important; color: white !important; border-radius: 8px !important; }
    h1, h3 { text-align: center !important; }
    </style>
    """, unsafe_allow_html=True)

if 'recoms' not in st.session_state: st.session_state.recoms = []

# Navegación
sel_pag = st.radio("", ["DESCUBRIR", "BIBLIOTECA"], horizontal=True, label_visibility="collapsed")

# ---------------------------------------------------------
# SECCIÓN: DESCUBRIR
# ---------------------------------------------------------
if sel_pag == "DESCUBRIR":
    st.markdown("<h1>🎧 MOOD</h1>", unsafe_allow_html=True)
    url_in = st.text_input("", placeholder="Pega un link de YouTube aquí...", key="search_phone")

    if url_in and url_in != st.session_state.get('last_url'):
        st.session_state.last_url = url_in
        with st.spinner("Buscando similares..."):
            with yt_dlp.YoutubeDL({'quiet': True, 'extract_flat': True}) as ydl:
                info = ydl.extract_info(url_in, download=False)
                art = info.get('uploader', '').split('-')[0].strip()
                query = f"ytsearch10:{art} official audio -playlist -mix"
                st.session_state.recoms = ydl.extract_info(query, download=False)['entries']

    if st.session_state.recoms:
        st.markdown("<h3>FOR YOU</h3>", unsafe_allow_html=True)
        conn = get_connection(); c = conn.cursor()
        c.execute('SELECT DISTINCT lista FROM playlist_data'); 
        listas = [r[0] for r in c.fetchall() if r[0] != 'DB_INIT']; conn.close()
        
        for vid in st.session_state.recoms:
            c1, c2, c3 = st.columns([4, 1.5, 2])
            c1.write(f"**{vid['title']}**")
            c2.link_button("Oír", f"https://www.youtube.com/watch?v={vid['id']}")
            with c3:
                if listas:
                    dest = st.selectbox("A:", listas, key=f"s_{vid['id']}", label_visibility="collapsed")
                    if st.button("💾 Guardar", key=f"b_{vid['id']}"):
                        conn = get_connection(); c = conn.cursor()
                        c.execute('INSERT INTO playlist_data (lista, cancion, url) VALUES (?, ?, ?)', (dest, vid['title'], f"https://www.youtube.com/watch?v={vid['id']}"))
                        conn.commit(); conn.close(); st.success("Guardado!"); st.rerun()
            st.divider()

# ---------------------------------------------------------
# SECCIÓN: BIBLIOTECA
# ---------------------------------------------------------
else:
    st.markdown("<h1>📂 BIBLIOTECA</h1>", unsafe_allow_html=True)
    
    # Crear carpeta
    c_in, c_bt = st.columns([3, 1])
    nueva = c_in.text_input("Nueva...", placeholder="Nombre de carpeta...", label_visibility="collapsed")
    if c_bt.button("➕ Crear"):
        if nueva:
            conn = get_connection(); c = conn.cursor()
            c.execute('INSERT INTO playlist_data (lista, cancion, url) VALUES (?, ?, ?)', (nueva, "DB_INIT", "NONE"))
            conn.commit(); conn.close(); st.rerun()
    
    st.divider()

    conn = get_connection(); c = conn.cursor()
    c.execute('SELECT DISTINCT lista FROM playlist_data')
    for l_name in [r[0] for r in c.fetchall()]:
        c.execute('SELECT id, cancion, url FROM playlist_data WHERE lista = ? AND cancion != "DB_INIT"', (l_name,))
        items = c.fetchall()
        
        with st.expander(f"📁 {l_name} ({len(items)})", expanded=True):
            col_play, col_del = st.columns([4, 1])
            if items:
                ids = [r[2].split('v=')[-1] for r in items]
                col_play.link_button(f"▶️ REPRODUCIR: {l_name}", f"https://www.youtube.com/watch_videos?video_ids={','.join(ids)}", use_container_width=True)
            
            if col_del.button("🗑️", key=f"fdel_{l_name}"):
                c.execute('DELETE FROM playlist_data WHERE lista = ?', (l_name,))
                conn.commit(); conn.close(); st.rerun()

            for id_db, can, url in items:
                ci, cp, cd = st.columns([5, 1, 1])
                ci.write(f"🎵 {can}")
                cp.link_button("▶️", url)
                if cd.button("❌", key=f"del_{id_db}"):
                    c.execute('DELETE FROM playlist_data WHERE id = ?', (id_db,)); conn.commit(); conn.close(); st.rerun()
    conn.close()

