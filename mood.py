import streamlit as st
from streamlit_gsheets import GSheetsConnection
import yt_dlp
import pandas as pd

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="MOOD", layout="wide")

# CONEXIÓN A TU GOOGLE SHEET
# Este es el ID que encontraste en tu captura
SHEET_ID = "1JxKBKcggTIB2sjzpqmdrxqFh8OIWp7Z1BiAivfPLWH0"
SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/edit#gid=0"

conn = st.connection("gsheets", type=GSheetsConnection)

def get_data():
    try:
        # Intentamos leer la hoja
        return conn.read(spreadsheet=SHEET_URL, ttl=0)
    except:
        # Si falla (hoja vacía), creamos la estructura base
        return pd.DataFrame(columns=["lista", "cancion", "url"])

def save_data(new_df):
    conn.update(spreadsheet=SHEET_URL, data=new_df)

# --- ESTILO ---
st.markdown("""
    <style>
    .stApp { background-color: white; }
    .stRadio > div { display: flex !important; justify-content: center !important; gap: 20px !important; }
    div.stButton > button { background-color: #df0000 !important; color: white !important; border-radius: 8px; width: 100%; }
    h1, h3 { text-align: center !important; }
    </style>
    """, unsafe_allow_html=True)

# Memoria temporal para recomendaciones
if 'recoms' not in st.session_state: st.session_state.recoms = []

sel = st.radio("", ["DESCUBRIR", "BIBLIOTECA"], horizontal=True, label_visibility="collapsed")

# Cargamos los datos actuales de Google Sheets
df = get_data()

# --- PÁGINA: DESCUBRIR ---
if sel == "DESCUBRIR":
    st.markdown("<h1>🎧 MOOD</h1>", unsafe_allow_html=True)
    url_in = st.text_input("", placeholder="Pega un link de YouTube aquí...")

    if url_in and url_in != st.session_state.get('last_url'):
        st.session_state.last_url = url_in
        with st.spinner("Buscando similares..."):
            with yt_dlp.YoutubeDL({'quiet': True, 'extract_flat': True}) as ydl:
                info = ydl.extract_info(url_in, download=False)
                art = info.get('uploader', 'Music').split('-')[0]
                st.session_state.recoms = ydl.extract_info(f"ytsearch:5 {art} official audio", download=False)['entries']

    for v in st.session_state.recoms:
        c1, c2, c3 = st.columns([3, 1, 1.5])
        c1.write(f"**{v['title']}**")
        c2.link_button("Oír", f"https://www.youtube.com/watch?v={v['id']}")
        with c3:
            listas_existentes = df['lista'].unique().tolist()
            if listas_existentes:
                dest = st.selectbox("Carpeta:", listas_existentes, key=v['id'])
                if st.button("💾", key=f"b_{v['id']}"):
                    new_row = pd.DataFrame([{"lista": dest, "cancion": v['title'], "url": f"https://www.youtube.com/watch?v={v['id']}"}])
                    df = pd.concat([df, new_row], ignore_index=True)
                    save_data(df)
                    st.toast("¡Guardado en Google Sheets!")
        st.divider()

# --- PÁGINA: BIBLIOTECA ---
else:
    st.markdown("<h1>📂 BIBLIOTECA</h1>", unsafe_allow_html=True)
    
    col_n1, col_n2 = st.columns([3, 1])
    nueva = col_n1.text_input("Nueva carpeta...")
    if col_n2.button("➕"):
        if nueva and nueva not in df['lista'].values:
            # Añadimos fila de inicialización
            new_folder = pd.DataFrame([{"lista": nueva, "cancion": "INIT_DB", "url": "NONE"}])
            df = pd.concat([df, new_folder], ignore_index=True)
            save_data(df)
            st.rerun()

    for l_name in df['lista'].unique():
        canciones = df[(df['lista'] == l_name) & (df['cancion'] != "INIT_DB")]
        with st.expander(f"📁 {l_name} ({len(canciones)})"):
            if not canciones.empty:
                # Botón de reproducción de carpeta (Google Mirror)
                ids = [r.split('=')[-1] for r in canciones['url']]
                st.link_button("▶️ REPRODUCIR CARPETA", f"https://www.youtube.com/watch_videos?video_ids={','.join(ids)}")
                
                for _, row in canciones.iterrows():
                    b1, b2 = st.columns([4, 1])
                    b1.write(f"🎵 {row['cancion']}")
                    b2.link_button("▶️", row['url'])
