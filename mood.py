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
    /* Navegación superior centrada */
    .stRadio > div { 
        display: flex !important; justify-content: center !important; 
        gap: 10vw !important; margin-bottom: 20px !important; 
    }
    .stRadio label { font-size: 20px !important; font-weight: bold !important; color: #333 !important; }
    
    /* Buscador centrado */
    .stTextInput { max-width: 800px !important; margin: 0 auto !important; }
    
    /* Botón de Reproducir Carpeta (Rojo) */
    div.stButton > button:first-child {
        background-color: #df0000 !important; color: white !important;
        border-radius: 8px !important; font-weight: bold !important;
    }
    
    h1, h3 { text-align: center !important; }
    [data-testid="stHorizontalBlock"] { align-items: center !important; }
    </style>
    """, unsafe_allow_html=True)

if 'recoms' not in st.session_state: st.session_state.recoms = []

# Navegación Pestañas
sel_pag = st.radio("", ["DESCUBRIR", "BIBLIOTECA"], horizontal=True, label_visibility="collapsed")

# ---------------------------------------------------------
# PÁGINA: DESCUBRIR
# ---------------------------------------------------------
if sel_pag == "DESCUBRIR":
    st.markdown("<h1>🎧 MOOD</h1>", unsafe_allow_html=True)
    url_input = st.text_input("", placeholder="Pega un link de YouTube aquí...", key="search_v22")

    if url_input and url_input != st.session_state.get('last_url'):
        st.session_state.last_url = url_input
        with st.spinner("Buscando música similar (sin mixes)..."):
            ydl_opts = {'quiet': True, 'extract_flat': True}
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url_input, download=False)
                artista = info.get('uploader', '').split('-')[0].strip()
                # Filtro para evitar contenido basura
                query = f"ytsearch10:{artista} official audio -playlist -mix -compilation"
                st.session_state.recoms = ydl.extract_info(query, download=False)['entries']

    if st.session_state.recoms:
        st.markdown("<h3>RECOMENDADOS</h3>", unsafe_allow_html=True)
        conn = get_connection(); c = conn.cursor()
        c.execute('SELECT DISTINCT lista FROM playlist_data'); listas = [r[0] for r in c.fetchall()]; conn.close()
        
        for vid in st.session_state.recoms:
            c1, c2, c3, c4 = st.columns([4, 1, 1.5, 0.5])
            link_vid = f"https://www.youtube.com/watch?v={vid['id']}"
            c1.write(f"**{vid['title']}**")
            c2.link_button("Oír", link_vid)
            with c3:
                if listas:
                    dest = st.selectbox("Carpeta:", listas, key=f"s_{vid['id']}", label_visibility="collapsed")
                    if st.button("💾", key=f"b_{vid['id']}"):
                        conn = get_connection(); c = conn.cursor()
                        c.execute('INSERT INTO playlist_data (lista, cancion, url) VALUES (?, ?, ?)', (dest, vid['title'], link_vid))
                        conn.commit(); conn.close(); st.rerun()
            c4.button("🗑️", key=f"t_{vid['id']}")
            st.divider()

# ---------------------------------------------------------
# PÁGINA: BIBLIOTECA (REPARADA PARA EL CELULAR)
# ---------------------------------------------------------
else:
    st.markdown("<h1>📂 MI BIBLIOTECA</h1>", unsafe_allow_html=True)
    
    # Crear Carpeta (Arriba y compacto)
    c_in, c_bt = st.columns([3, 1])
    nueva_c = c_in.text_input("Nombre de carpeta", placeholder="Nombre de nueva carpeta...", label_visibility="collapsed")
    if c_bt.button("➕ Crear", use_container_width=True):
        if nueva_c:
            conn = get_connection(); c = conn.cursor()
            c.execute('INSERT INTO playlist_data (lista, cancion, url) VALUES (?, ?, ?)', (nueva_c, "DB_INIT", "NONE"))
            conn.commit(); conn.close(); st.rerun()
    
    st.divider()

    conn = get_connection(); c = conn.cursor()
    c.execute('SELECT DISTINCT lista FROM playlist_data')
    listas_existentes = [r[0] for r in c.fetchall()]
    
    for l_name in listas_existentes:
        c.execute('SELECT id, cancion, url FROM playlist_data WHERE lista = ? AND cancion != "DB_INIT"', (l_name,))
        canciones = c.fetchall()
        
        with st.expander(f"📁 {l_name} ({len(canciones)} temas)", expanded=True):
            col_play_all, col_del_folder = st.columns([4, 1])
            
            # Botón de reproducción de carpeta
            if canciones:
                ids = [r[2].split('v=')[-1] for r in canciones]
                p_url = f"https://www.youtube.com/watch_videos?video_ids={','.join(ids)}"
                col_play_all.link_button(f"▶️ REPRODUCIR TODO: {l_name}", p_url, use_container_width=True)
            
            if col_del_folder.button("🔥 Borrar", key=f"fdel_{l_name}", use_container_width=True):
                c.execute('DELETE FROM playlist_data WHERE lista = ?', (l_name,))
                conn.commit(); conn.close(); st.rerun()

            for id_db, nom, url in canciones:
                ci, cp, cd = st.columns([5, 1, 1])
                ci.write(f"🎵 {nom}")
                cp.link_button("▶️", url)
                if cd.button("🗑️", key=f"del_{id_db}"):
                    c.execute('DELETE FROM playlist_data WHERE id = ?', (id_db,)); conn.commit(); st.rerun()
    conn.close()