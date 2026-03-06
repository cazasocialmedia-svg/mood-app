import streamlit as st
from streamlit_gsheets import GSheetsConnection
import yt_dlp
import pandas as pd

# --- 1. CONFIGURACIÓN Y CONEXIÓN ---
st.set_page_config(page_title="MOOD", layout="wide")

SHEET_ID = "1JxKBKcggTIB2sjzpqmdrxqFh8OIWp7Z1BiAivfPLWH0"
SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/edit#gid=0"
conn = st.connection("gsheets", type=GSheetsConnection)

def get_data():
    try: return conn.read(spreadsheet=SHEET_URL, ttl=0)
    except: return pd.DataFrame(columns=["lista", "cancion", "url"])

def save_data(df):
    conn.update(spreadsheet=SHEET_URL, data=df)

# --- 2. MEMORIA DE SESIÓN (Para que no se borre al cambiar pestaña) ---
if 'recoms' not in st.session_state: st.session_state.recoms = []
if 'last_query' not in st.session_state: st.session_state.last_query = ""

# --- 3. DISEÑO ---
st.markdown("""
    <style>
    .stApp { background-color: white; }
    div.stButton > button { border-radius: 8px; font-weight: bold; width: 100%; }
    h1 { text-align: center; margin-bottom: 0; }
    </style>
    """, unsafe_allow_html=True)

df = get_data()
sel = st.radio("", ["DESCUBRIR", "BIBLIOTECA"], horizontal=True, label_visibility="collapsed")

# --- PÁGINA: DESCUBRIR ---
if sel == "DESCUBRIR":
    st.markdown("<h1>🎧 MOOD</h1>", unsafe_allow_html=True)
    url_in = st.text_input("", placeholder="Pega un link de YouTube aquí...", key="search_bar")

    # Solo busca si el link cambió
    if url_in and url_in != st.session_state.last_query:
        with st.spinner("Buscando similares..."):
            with yt_dlp.YoutubeDL({'quiet': True, 'extract_flat': True}) as ydl:
                info = ydl.extract_info(url_in, download=False)
                art = info.get('uploader', 'Musica').split('-')[0].strip()
                st.session_state.recoms = ydl.extract_info(f"ytsearch5:{art} official audio", download=False)['entries']
                st.session_state.last_query = url_in

    # Mostrar recomendaciones guardadas en memoria
    if st.session_state.recoms:
        for v in st.session_state.recoms:
            c1, c2, c3 = st.columns([3, 1, 1.5])
            c1.write(f"**{v['title']}**")
            c2.link_button("Oír", f"https://www.youtube.com/watch?v={v['id']}")
            with c3:
                listas = [l for l in df['lista'].unique().tolist() if l != "INIT_DB"]
                if listas:
                    dest = st.selectbox("A:", listas, key=f"s_{v['id']}", label_visibility="collapsed")
                    if st.button("💾 Guardar", key=f"b_{v['id']}"):
                        new_row = pd.DataFrame([{"lista": dest, "cancion": v['title'], "url": f"https://www.youtube.com/watch?v={v['id']}"}])
                        save_data(pd.concat([df, new_row], ignore_index=True))
                        st.toast("¡Guardado!")
            st.divider()

# --- PÁGINA: BIBLIOTECA ---
else:
    st.markdown("<h1>📂 BIBLIOTECA</h1>", unsafe_allow_html=True)
    
    col_n1, col_n2 = st.columns([3, 1])
    nueva = col_n1.text_input("Nueva carpeta...", label_visibility="collapsed")
    if col_n2.button("➕ Crear"):
        if nueva and nueva not in df['lista'].values:
            init_df = pd.concat([df, pd.DataFrame([{"lista": nueva, "cancion": "INIT_DB", "url": "NONE"}])], ignore_index=True)
            save_data(init_df)
            st.rerun()

    for l_name in df['lista'].unique():
        canciones = df[(df['lista'] == l_name) & (df['cancion'] != "INIT_DB")]
        with st.expander(f"📁 {l_name} ({len(canciones)})"):
            if not canciones.empty:
                ids = [r.split('=')[-1] for r in canciones['url']]
                st.link_button("▶️ REPRODUCIR TODO", f"https://www.youtube.com/watch_videos?video_ids={','.join(ids)}")
                
                for index, row in canciones.iterrows():
                    b1, b2, b3 = st.columns([4, 1, 1])
                    b1.write(f"🎵 {row['cancion']}")
                    b2.link_button("▶️", row['url'])
                    # ELIMINAR CANCIÓN
                    if b3.button("🗑️", key=f"del_{index}"):
                        new_df = df.drop(index)
                        save_data(new_df)
                        st.rerun()
            
            if st.button(f"🔥 Eliminar Carpeta {l_name}", key=f"fdel_{l_name}"):
                save_data(df[df['lista'] != l_name])
                st.rerun()

