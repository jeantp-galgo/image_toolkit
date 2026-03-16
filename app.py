"""
app.py — Interfaz Streamlit para el pipeline de clasificación de imágenes.

Ejecutar:
    streamlit run app.py
    (o usar launch.bat para abrir con doble clic)
"""

import subprocess
import sys
from pathlib import Path

import streamlit as st
from PIL import Image

# Agregar scripts/ al path para importar el pipeline
sys.path.insert(0, str(Path(__file__).parent / "scripts"))
from classify_pipeline import run_pipeline  # noqa: E402

# ──────────────────────────────────────────────────────────────────────
# Configuración de página
# ──────────────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Clasificador de Imágenes",
    page_icon="🏍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ──────────────────────────────────────────────────────────────────────
# Sidebar — configuración y control
# ──────────────────────────────────────────────────────────────────────

with st.sidebar:
    st.title("🏍 Clasificador")
    st.caption("Pipeline: CLIP → output")
    st.divider()

    carpeta = st.text_input(
        "Carpeta de imágenes",
        placeholder=r"C:\ruta\a\la\carpeta",
        help="Ruta completa a la carpeta con las imágenes a clasificar",
    )

    st.divider()
    ejecutar = st.button("▶ Ejecutar pipeline", type="primary", use_container_width=True)

    st.divider()
    st.caption("Las imágenes seleccionadas se guardan en `output/` dentro de la carpeta indicada.")

# ──────────────────────────────────────────────────────────────────────
# Estado de sesión
# ──────────────────────────────────────────────────────────────────────

if "resultado" not in st.session_state:
    st.session_state.resultado = None
if "error" not in st.session_state:
    st.session_state.error = None

# ──────────────────────────────────────────────────────────────────────
# Ejecución del pipeline
# ──────────────────────────────────────────────────────────────────────

if ejecutar:
    if not carpeta or not carpeta.strip():
        st.sidebar.error("Ingresa la ruta de la carpeta.")
    elif not Path(carpeta.strip()).exists():
        st.sidebar.error(f"Carpeta no encontrada:\n`{carpeta}`")
    else:
        st.session_state.resultado = None
        st.session_state.error = None

        pasos = [
            "Preprocesando imágenes (centrar y redimensionar)...",
            "Cargando modelo CLIP y referencias...",
            "Calculando scores CLIP...",
            "Seleccionando principal y galería...",
            "Exportando a output/...",
        ]

        progress_bar = st.progress(0, text="Iniciando pipeline...")
        status_placeholder = st.empty()

        def progress_callback(step: int, total: int, msg: str):
            pct = int((step / total) * 100)
            label = pasos[step - 1] if step <= len(pasos) else msg
            progress_bar.progress(pct, text=label)
            status_placeholder.info(f"**Paso {step}/{total}** — {label}")

        try:
            resultado = run_pipeline(
                carpeta.strip(),
                progress_callback=progress_callback,
            )
            progress_bar.progress(100, text="Pipeline completado")
            status_placeholder.success(
                f"Pipeline completado — {1 + len(resultado['gallery'])} imágenes en `output/`"
            )
            st.session_state.resultado = resultado

        except Exception as e:
            progress_bar.empty()
            status_placeholder.empty()
            st.session_state.error = str(e)

# ──────────────────────────────────────────────────────────────────────
# Mostrar error
# ──────────────────────────────────────────────────────────────────────

if st.session_state.error:
    st.error(f"Error durante el pipeline:\n\n```\n{st.session_state.error}\n```")

# ──────────────────────────────────────────────────────────────────────
# Mostrar resultado
# ──────────────────────────────────────────────────────────────────────

if st.session_state.resultado:
    res = st.session_state.resultado
    output_dir: Path = res["output_dir"]
    principal: str = res["principal"]
    gallery: list = res["gallery"]
    df = res["df"]

    st.divider()

    # — Imagen principal —
    st.subheader("Imagen principal")

    principal_path = output_dir / "imagen_principal.jpg"
    principal_score = df[df["archivo"] == principal]["score"].values[0] if not df.empty else None

    col_img, col_info = st.columns([2, 1])
    with col_img:
        if principal_path.exists():
            st.image(str(principal_path), use_container_width=True)
    with col_info:
        st.metric("Score CLIP", f"{principal_score:.4f}" if principal_score is not None else "—")
        st.caption(f"Archivo original: `{principal}`")
        st.caption(f"Output: `imagen_principal.jpg`")

    st.divider()

    # — Galería —
    st.subheader(f"Galería ({len(gallery)} imágenes)")

    COLS = 4
    gallery_files = sorted(output_dir.glob("galeria*.jpg"))

    if gallery_files:
        rows = [gallery_files[i:i + COLS] for i in range(0, len(gallery_files), COLS)]
        for row in rows:
            cols = st.columns(COLS)
            for col, gfile in zip(cols, row):
                with col:
                    # Buscar el nombre original correspondiente a este archivo de galería
                    idx = int(gfile.stem.replace("galeria", "")) - 1
                    original_name = gallery[idx] if idx < len(gallery) else gfile.name
                    score_val = df[df["archivo"] == original_name]["score"].values
                    score_str = f"{score_val[0]:.4f}" if len(score_val) > 0 else "—"

                    st.image(str(gfile), use_container_width=True)
                    st.caption(f"`{gfile.name}` · score: {score_str}")
    else:
        st.warning("No se encontraron imágenes de galería en la carpeta output/.")

    st.divider()

    # — Tabla de scores completa —
    with st.expander("Ver tabla completa de scores"):
        st.dataframe(
            df[["archivo", "score", "score_pos", "sim_centroide_pos", "sim_centroide_neg", "penalizacion"]],
            use_container_width=True,
        )

    # — Botón para abrir carpeta output —
    st.divider()
    col_btn, col_path = st.columns([1, 3])
    with col_btn:
        if st.button("📂 Abrir carpeta output"):
            subprocess.Popen(f'explorer "{output_dir}"')
    with col_path:
        st.code(str(output_dir), language=None)

# ──────────────────────────────────────────────────────────────────────
# Estado inicial (sin resultado)
# ──────────────────────────────────────────────────────────────────────

elif not ejecutar and st.session_state.resultado is None and not st.session_state.error:
    st.markdown(
        """
        ## Clasificador de imágenes de motos

        Selecciona una carpeta en el panel izquierdo y haz clic en **Ejecutar pipeline**.

        ### Qué hace el pipeline:
        1. **Clasifica** usando CLIP (ViT-L-14) comparando contra referencias positivas y negativas
        2. **Selecciona** la imagen principal (mayor score) y una galería con todas las imágenes restantes
        3. **Exporta** todo a una carpeta `output/` dentro de la carpeta indicada

        ### Output generado:
        ```
        tu_carpeta/
        └── output/
            ├── imagen_principal.jpg
            ├── galeria1.jpg
            ├── galeria2.jpg
            └── ...
        ```
        """
    )
