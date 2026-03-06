import streamlit as st
import yt_dlp
import sqlite3

# --- 1. BASE DE DATOS (Mantenemos todo intacto) ---
DB_FILE = 'mood_vault_FINAL.db'
def get_connection(): return sqlite3.connect(DB_FILE, check_same_thread=False)

st.set_page_config(page_title="MOOD", layout="wide")

# --- 2. DISEÑO PROFESIONAL Y COMPACTO ---
st.markdown("""
    <style>
    .stApp { background-color: white; }
    /* Navegación superior centrada y limpia */
    .stRadio > div { 
        display: flex !important; justify-content: center !important; 
        gap: 10vw !important; margin-bottom: 30px !important; 
    }
    .stRadio label { font-size: 20px !important; font-weight: bold !important; color: #333 !important; }
    
    /* Input de búsqueda estilo pizarra */
    .stTextInput { max-width: 800px !important; margin: 0 auto !important; }
    
    /* Botones de acción */
    .stButton > button { border-radius: 8px !important; }
    .btn-del-carpeta { background-color: #ff4b4b !important; color: white !important; }
    
    h1, h3 { text-align: center !important; }
    </style>
    """, unsafe_allow_html=True)

if 'recoms' not in st.session_state: st.session_state.recoms = []

# Selector de página
sel_pag = st.radio("", ["DESCUBRIR", "BIBLIOTECA"], horizontal=True, label_visibility="collapsed")

# ---------------------------------------------------------
# PÁGINA: DESCUBRIR (Diseño Centrado)
# ---------------------------------------------------------
if sel_pag == "DESCUBRIR":
    st.markdown("<h1>🎧 MOOD</h1>", unsafe_allow_html=True)
    url_input = st.text_input("", placeholder="Add Link Here...", key="search_final_v21")

    if url_input and url_input != st.session_state.get('last_url'):
        st.session_state.last_url = url_input
        with st.spinner("Filtrando..."):
            with yt_dlp.YoutubeDL({'quiet': True, 'extract_flat': True}) as ydl:
                info = ydl.extract_info(url_input, download=False)
                art = info.get('uploader', '').split('-')[0].strip()
                query = f"ytsearch10:{art} official audio -playlist -mix"
                st.session_state.recoms = ydl.extract_info(query, download=False)['entries']

    if st.session_state.recoms:
        st.markdown("<h3>FOR YOU</h3>", unsafe_allow_html=True)
        conn = get_connection(); c = conn.cursor()
        c.execute('SELECT DISTINCT lista FROM playlist_data'); listas = [r[0] for r in c.fetchall()]; conn.close()
        for vid in st.session_state.recoms:
            c1, c2, c3, c4 = st.columns([4, 1, 1.5, 0.5])
            c1.write(f"**{vid['title']}**")
            c2.link_button("Listen", f"https://www.youtube.com/watch?v={vid['id']}")
            with c3:
                if listas:
                    dest = st.selectbox("A:", listas, key=f"s_{vid['id']}", label_visibility="collapsed")
                    if st.button("💾", key=f"b_{vid['id']}"):
                        conn = get_connection(); c = conn.cursor()
                        c.execute('INSERT INTO playlist_data (lista, cancion, url) VALUES (?, ?, ?)', (dest, vid['title'], f"https://www.youtube.com/watch?v={vid['id']}"))
                        conn.commit(); conn.close(); st.rerun()
            c4.button("🗑️", key=f"t_{vid['id']}")
            st.divider()

# ---------------------------------------------------------
# PÁGINA: BIBLIOTECA (DISEÑO REPARADO)
# ---------------------------------------------------------
else:
    st.markdown("<h1>📂 BIBLIOTECA PERSONAL</h1>", unsafe_allow_html=True)
    
    # Crear carpeta en una línea compacta arriba
    c_in, c_bt = st.columns([3, 1])
    nueva = c_in.text_input("Nombre de nueva carpeta", placeholder="Nueva carpeta...", label_visibility="collapsed")
    if c_bt.button("➕ Crear Carpeta", use_container_width=True):
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
        
        # Expander con diseño de la versión funcional 848b9df0
        with st.expander(f"📁 {l_name} ({len(items)} temas)", expanded=True):
            # Fila de control de carpeta
            col_play, col_del_folder = st.columns([4, 1])
            
            # Botón de reproducción roja (como en tu captura)
            ids = [row[2].split('com/0')[-1] for row in items]
            col_play.link_button(f"▶️ REPRODUCIR: {l_name}", f"https://www.youtube.com/watch_videos?video_ids={','.join(ids)}", type="primary", use_container_width=True)
            
            # NUEVO: Botón para borrar carpeta completa
            if col_del_folder.button(f"🔥 BORRAR CARPETA", key=f"fdel_{l_name}", use_container_width=True):
                c.execute('DELETE FROM playlist_data WHERE lista = ?', (l_name,))
                conn.commit(); st.rerun()

            # Lista de canciones alineada
            for id_db, can, url in items:
                ci, cp, cd = st.columns([5, 1, 1])
                ci.write(f"🎵 {can}")
                cp.link_button("▶️", url)
                if cd.button("🗑️", key=f"del_{id_db}"):
                    c.execute('DELETE FROM playlist_data WHERE id = ?', (id_db,)); conn.commit(); st.rerun()
    conn.close()

