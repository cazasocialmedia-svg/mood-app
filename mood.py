import streamlit as st
from streamlit_gsheets import GSheetsConnection
import yt_dlp
import pandas as pd

st.set_page_config(page_title="MOOD", layout="wide")

# CONEXIÓN
conn = st.connection("gsheets", type=GSheetsConnection)

def cargar():
    try: return conn.read(ttl=0)
    except: return pd.DataFrame(columns=["lista", "cancion", "url"])

def guardar(df):
    conn.update(data=df)
    st.rerun()

# INTERFAZ
df = cargar()
tab1, tab2 = st.tabs(["🎧 DESCUBRIR", "📂 BIBLIOTECA"])

# --- DESCUBRIR ---
with tab1:
    st.markdown("<h1 style='text-align:center;'>MOOD</h1>", unsafe_allow_html=True)
    link = st.text_input("Pega el link aquí...")
    if link:
        with st.spinner("Buscando..."):
            with yt_dlp.YoutubeDL({'quiet':True}) as ydl:
                info = ydl.extract_info(link, download=False)
                art = info.get('uploader','').split('-')[0]
                recoms = ydl.extract_info(f"ytsearch5:{art} audio", download=False)['entries']
                for v in recoms:
                    c1, c2, c3 = st.columns([3, 1, 1.5])
                    c1.write(v['title'])
                    c2.link_button("Oír", f"https://www.youtube.com/watch?v={v['id']}")
                    with c3:
                        listas = [l for l in df['lista'].unique().tolist() if l != "INIT"]
                        if listas:
                            dest = st.selectbox("A:", listas, key=v['id'])
                            if st.button("💾", key="s_"+v['id']):
                                row = pd.DataFrame([{"lista":dest, "cancion":v['title'], "url":f"https://www.youtube.com/watch?v={v['id']}"}])
                                guardar(pd.concat([df, row], ignore_index=True))

# --- BIBLIOTECA (Aquí están tus opciones de crear y borrar) ---
with tab2:
    st.markdown("<h1 style='text-align:center;'>BIBLIOTECA</h1>", unsafe_allow_html=True)
    
    # SECCIÓN CREAR (Lo que decías que no aparecía)
    c_in, c_bt = st.columns([3, 1])
    nueva = c_in.text_input("Nombre de nueva playlist...")
    if c_bt.button("➕ CREAR"):
        if nueva:
            guardar(pd.concat([df, pd.DataFrame([{"lista":nueva, "cancion":"INIT", "url":"NONE"}])], ignore_index=True))

    st.divider()

    # LISTADO Y BORRADO
    for l_name in df['lista'].unique():
        with st.expander(f"📁 {l_name}"):
            # Borrar playlist entera
            if st.button(f"🗑️ BORRAR PLAYLIST", key="fdel_"+l_name):
                guardar(df[df['lista'] != l_name])
            
            canciones = df[(df['lista'] == l_name) & (df['cancion'] != "INIT")]
            for i, r in canciones.iterrows():
                b1, b2, b3 = st.columns([4, 1, 1])
                b1.write(r['cancion'])
                b2.link_button("▶️", r['url'])
                # BOTÓN BORRAR ARCHIVO INDIVIDUAL
                if b3.button("❌", key=f"del_{i}"):
                    guardar(df.drop(i))
