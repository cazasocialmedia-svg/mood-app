import streamlit as st
from streamlit_gsheets import GSheetsConnection
import yt_dlp
import pandas as pd

st.set_page_config(page_title="MOOD", layout="wide")

# CONEXIÓN
conn = st.connection("gsheets", type=GSheetsConnection)
SHEET = "https://docs.google.com/spreadsheets/d/1JxKBKcggTIB2sjzpqmdrxqFh8OIWp7Z1BiAivfPLWH0/edit#gid=0"

def get_data():
    try: return conn.read(spreadsheet=SHEET, ttl=0)
    except: return pd.DataFrame(columns=["lista", "cancion", "url"])

def save_data(df): conn.update(spreadsheet=SHEET, data=df)

# NAVEGACIÓN
df = get_data()
sel = st.radio("", ["DESCUBRIR", "BIBLIOTECA"], horizontal=True, label_visibility="collapsed")

if sel == "DESCUBRIR":
    st.markdown("<h1 style='text-align: center;'>🎧 MOOD</h1>", unsafe_allow_html=True)
    u = st.text_input("", placeholder="Pega link aquí...")
    if u:
        with st.spinner("Buscando..."):
            with yt_dlp.YoutubeDL({'quiet':True}) as ydl:
                info = ydl.extract_info(u, download=False)
                art = info.get('uploader','').split('-')[0]
                recoms = ydl.extract_info(f"ytsearch5:{art} official audio", download=False)['entries']
                for v in recoms:
                    c1, c2, c3 = st.columns([3, 1, 1.5])
                    c1.write(f"**{v['title']}**")
                    c2.link_button("Oír", f"https://www.youtube.com/watch?v={v['id']}")
                    with c3:
                        listas = df['lista'].unique().tolist()
                        if listas:
                            cat = st.selectbox("A:", listas, key=v['id'])
                            if st.button("💾", key=f"s_{v['id']}"):
                                new = pd.DataFrame([{"lista":cat, "cancion":v['title'], "url":f"https://www.youtube.com/watch?v={v['id']}"}])
                                save_data(pd.concat([df, new], ignore_index=True))
                                st.rerun()
else:
    st.markdown("<h1 style='text-align: center;'>📂 BIBLIOTECA</h1>", unsafe_allow_html=True)
    n = st.text_input("Nueva carpeta...")
    if st.button("➕"):
        save_data(pd.concat([df, pd.DataFrame([{"lista":n, "cancion":"INIT", "url":"NONE"}])], ignore_index=True))
        st.rerun()
    for l in df['lista'].unique():
        with st.expander(f"📁 {l}"):
            items = df[(df['lista']==l) & (df['cancion']!="INIT")]
            for i, r in items.iterrows():
                col1, col2, col3 = st.columns([4,1,1])
                col1.write(r['cancion'])
                col2.link_button("▶️", r['url'])
                if col3.button("🗑️", key=f"d_{i}"):
                    save_data(df.drop(i))
                    st.rerun()

