import streamlit as st
from streamlit_gsheets import GSheetsConnection
import yt_dlp
import pandas as pd

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="MOOD", layout="wide")

SHEET_ID = "1JxKBKcggTIB2sjzpqmdrxqFh8OIWp7Z1BiAivfPLWH0"
SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/edit#gid=0"

conn = st.connection("gsheets", type=GSheetsConnection)

def get_data():
    try:
        return conn.read(spreadsheet=SHEET_URL, ttl=0)
    except:
        return pd.DataFrame(columns=["lista", "cancion", "url"])

def save_data(new_df):
    conn.update(spreadsheet=SHEET_URL, data=new_df)

# --- ESTILO ---
st.markdown("""
    <style>
    .stApp { background-color: white; }
    div.stButton > button { border-radius: 8px; font-weight: bold; }
    .btn-del { background-color: #ff4b4b !important; color: white !important; }
    h1 { text-align: center; }
    </style>
    """, unsafe_allow_html=True)

if 'recoms' not in st.session_state: st.session_state.recoms = []

df = get_data()
sel = st.radio("", ["DESCUBRIR", "BIBLIOTECA"], horizontal=True, label_visibility="collapsed")

# --- PÁGINA: DESCUBRIR ---
if sel == "DESCUBRIR":
    st.markdown("<h1>🎧 MOOD</h1>", unsafe_allow_html=True)
    url_in = st.text_input("", placeholder="Pega un link de YouTube aquí...")

    if url_in and url_in != st.session_state.get('last_url'):
        st.session_state.last_url = url_in
        with st.spinner("Buscando similares..."):
            with yt_dlp.YoutubeDL({'quiet': True, 'extract_flat': True}) as ydl:
                info = ydl.extract_info(url_in, download=False)
                art = info.get('uploader', 'Musica').split('-')[0].strip()
                st.session_state.recoms = ydl.extract_info(f"ytsearch:5 {art} official audio", download=False)['entries']

    for v in st.session_state.recoms:
        c1, c2, c3 = st.columns([3, 1, 1.5])
        c1.write(f"**{v['title']}**")
        c2.link_button("Oír", f"https://www.youtube.com/watch?v={v['id']}")
        with c3:
            listas = [l for l in df['lista'].unique().tolist() if l != "INIT_DB"]
            if listas:
                dest = st.selectbox("Carpeta:", listas, key=f"sel_{v['id']}", label_visibility="collapsed")
                if st.button("💾 Guardar", key=f"save_{v['id']}"):
                    new_row = pd.DataFrame([{"lista": dest, "cancion": v['title'], "url": f"https://www.youtube.com/watch?v={v['id']}"}])
                    df = pd.concat([df, new_row], ignore_index=True)
                    save_data(df)
                    st.toast("¡Guardado!")
        st.divider()

# --- PÁGINA: BIBLIOTECA ---
else:
    st.markdown("<h1>📂 BIBLIOTECA</h1>", unsafe_allow_html=True)
    c_in, c_bt = st.columns([3, 1])
    nueva = c_in.text_input("Nueva carpeta...", label_visibility="collapsed")
    if c_bt.button("➕ Crear"):
        if nueva and nueva not in df['lista'].values:
            df = pd.concat([df, pd.DataFrame([{"lista": nueva, "cancion": "INIT_DB", "url": "NONE"}])], ignore_index=True)
            save_data(df); st.rerun()

    for l_name in df['lista'].unique():
        canciones = df[(df['lista'] == l_name) & (df['cancion'] != "INIT_DB")]
        with st.expander(f"📁 {l_name} ({len(canciones)})"):
            # Botón para borrar carpeta completa
            if st.button(f"🔥 Borrar Carpeta {l_name}", key=f"fdel_{l_name}"):
                df = df[df['lista'] != l_name]
                save_data(df); st.rerun()

            for index, row in canciones.iterrows():
                col1, col2, col3 = st.columns([4, 1, 1])
                col1.write(f"🎵 {row['cancion']}")
                col2.link_button("▶️", row['url'])
                # BOTÓN DE BORRAR CANCIÓN INDIVIDUAL
                if col3.button("🗑️", key=f"del_{index}"):
                    df = df.drop(index)
                    save_data(df); st.rerun()

