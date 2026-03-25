"""
app.py — Entry point del toolkit de imágenes.

Ejecutar:
    streamlit run app.py
"""

import streamlit as st

st.set_page_config(
    page_title="Image Toolkit",
    page_icon=":material/photo_library:",
    layout="wide",
    initial_sidebar_state="expanded",
)

inicio              = st.Page("pages/inicio.py",               title="Inicio",                  icon=":material/home:",            default=True)
clasificador        = st.Page("pages/clasificador.py",         title="Clasificador",             icon=":material/auto_awesome:")
centrar_redim       = st.Page("pages/centrar_redimensionar.py",title="Centrar y Redimensionar",  icon=":material/crop_free:")
comprimir           = st.Page("pages/comprimir_imagenes.py",   title="Comprimir Imágenes",       icon=":material/compress:")

nav = st.navigation([inicio, clasificador, centrar_redim, comprimir])
nav.run()
