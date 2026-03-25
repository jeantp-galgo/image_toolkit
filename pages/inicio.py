import streamlit as st

st.title("🛠️ Image Toolkit")
st.caption("Herramientas de procesamiento de imágenes para Marketplace")

st.divider()

col1, col2, col3 = st.columns(3, gap="large")

with col1:
    st.subheader("Clasificador de imágenes")
    st.markdown(
        """
        Clasifica un set de imágenes usando **CLIP (ViT-L-14)** y selecciona
        automáticamente la imagen principal y la galería.

        - Compara contra referencias positivas y negativas
        - Genera scores por imagen
        - Exporta `imagen_principal.jpg` + `galeria*.jpg`
        """
    )
    st.info("Selecciona **Clasificador** en el menú lateral")

with col2:
    st.subheader("Centrar y Redimensionar")
    st.markdown(
        """
        Detecta el vehículo en cada imagen y lo **centra en un canvas limpio**
        con las dimensiones que necesites.

        - Detección automática de bounding box
        - Padding y threshold configurables
        - Descarga masiva en ZIP
        """
    )
    st.info("Selecciona **Centrar y Redimensionar** en el menú lateral")

with col3:
    st.subheader("Comprimir Imágenes")
    st.markdown(
        """
        Reduce el **peso de tus imágenes** sin pérdida de calidad visible,
        con control total sobre el formato y el tamaño objetivo.

        - Salida en JPEG o WebP
        - Ajuste automático de calidad si supera el límite de MB
        - Procesamiento recursivo de subcarpetas
        """
    )
    st.info("Selecciona **Comprimir Imágenes** en el menú lateral")

st.divider()
st.caption("Usa el menú lateral para navegar entre herramientas.")
