import streamlit as st
from streamlit_gsheets import GSheetsConnection
import yt_dlp
import pandas as pd

st.set_page_config(page_title="MOOD", layout="wide")

# CONEXIÓN DIRECTA
SHEET_URL = "https://docs.google.com/spreadsheets/d/1JxKBKcggTIB2sjzpqmdrxqFh8OIWp7Z1BiAivfPLWH0/edit#gid=0"
conn = st.connection("gsheets", type=GSheetsConnection)

def cargar():
    try:
        return conn.read(spreadsheet=SHEET_URL, ttl=0)
    except:
        return pd.DataFrame(columns=["lista", "cancion", "url"])

def guardar(df_nuevo):
    # Esto solo funcionará si pusiste "Editor" en el Google Sheet
    conn.update(spreadsheet=SHEET_URL, data=df_nuevo)

# MEMORIA
if 'recoms' not in st.session_state: st.session_state.recoms = []

df = cargar()
menu = st.radio("", ["DESCUBRIR", "BIBLIOTECA"], horizontal=True, label_visibility="collapsed")

if menu == "DESCUBRIR":
    st.markdown("<h1 style='text-align:center;'>🎧 MOOD</h1>", unsafe_allow_html=True)
    link = st.text_input("", placeholder="Pega el link aquí...")
    
    if link and link != st.session_state.get('last'):
        with st.spinner("Buscando..."):
            with yt_dlp.YoutubeDL({'quiet':True}) as ydl:
                info = ydl.extract_info(link, download=False)
                art = info.get('uploader','').split('-')[0]
                st.session_state.recoms = ydl.extract_info(f"ytsearch5:{art} audio", download=False)['entries']
                st.session_state.last = link

    for v in st.session_state.recoms:
        c1, c2, c3 = st.columns([3, 1, 1.5])
        c1.write(v['title'])
        c2.link_button("Oír", f"https://www.youtube.com/watch?v={v['id']}")
        with c3:
            listas = [l for l in df['lista'].unique().tolist() if l != "INIT"]
            if listas:
                dest = st.selectbox("A:", listas, key=v['id'])
                if st.button("💾", key="b"+v['id']):
                    nueva_fila = pd.DataFrame([{"lista": dest, "cancion": v['title'], "url": f"https://www.youtube.com/watch?v={v['id']}"}])
                    guardar(pd.concat([df, nueva_fila], ignore_index=True))
                    st.success("¡Guardado!")

else:
    st.markdown("<h1 style='text-align:center;'>📂 BIBLIOTECA</h1>", unsafe_allow_html=True)
    
    # SECCIÓN PARA CREAR PLAYLIST
    c_in, c_bt = st.columns([3, 1])
    n_p = c_in.text_input("Nombre de playlist...")
    if c_bt.button("➕ Crear"):
        if n_p:
            df = pd.concat([df, pd.DataFrame([{"lista": n_p, "cancion": "INIT", "url": "NONE"}])], ignore_index=True)
            guardar(df)
            st.rerun()

    # LISTADO CON BOTÓN DE BORRAR
    for lista in df['lista'].unique():
        with st.expander(f"📁 {lista}"):
            songs = df[(df['lista'] == lista) & (df['cancion'] != "INIT")]
            for idx, r in songs.iterrows():
                b1, b2, b3 = st.columns([4, 1, 1])
                b1.write(r['cancion'])
                b2.link_button("▶️", r['url'])
                # EL BOTÓN DE BORRAR QUE FALTABA
                if b3.button("🗑️", key=f"del_{idx}"):
                    df = df.drop(idx)
                    guardar(df)
                    st.rerun()

