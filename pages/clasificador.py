import subprocess
import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).parent.parent / "src" / "core"))
from classify_pipeline import run_pipeline  # noqa: E402

# ── Sidebar ────────────────────────────────────────────────────────────

with st.sidebar:
    st.header("Configuración")
    carpeta = st.text_input(
        "Carpeta de imágenes",
        placeholder=r"C:\ruta\a\la\carpeta",
        help="Ruta completa a la carpeta con las imágenes a clasificar.",
    )
    st.divider()
    ejecutar = st.button("Ejecutar pipeline", type="primary", use_container_width=True)
    st.caption("Las imágenes se guardan en `output/` dentro de la carpeta indicada.")

# ── Validación temprana ────────────────────────────────────────────────

st.title("Clasificador de imágenes")

if not ejecutar and not st.session_state.get("clf_resultado"):
    st.markdown(
        """
        Selecciona una carpeta en el panel izquierdo y haz clic en **Ejecutar pipeline**.

        ### Qué hace el pipeline:
        1. **Preprocesa** centrando y redimensionando cada imagen
        2. **Clasifica** con CLIP (ViT-L-14) contra referencias positivas y negativas
        3. **Selecciona** la imagen principal (mayor score) y la galería restante
        4. **Exporta** todo a `output/` dentro de la carpeta indicada

        ```
        tu_carpeta/
        └── output/
            ├── imagen_principal.jpg
            ├── galeria1.jpg
            └── ...
        ```
        """
    )
    st.stop()

# ── Ejecución ─────────────────────────────────────────────────────────

if ejecutar:
    if not carpeta or not carpeta.strip():
        st.sidebar.error("Ingresa la ruta de la carpeta.")
        st.stop()
    if not Path(carpeta.strip()).exists():
        st.sidebar.error(f"Carpeta no encontrada: `{carpeta}`")
        st.stop()

    pasos = [
        "Preprocesando imágenes...",
        "Cargando modelo CLIP y referencias...",
        "Calculando scores CLIP...",
        "Seleccionando principal y galería...",
        "Exportando a output/...",
    ]

    progress = st.progress(0, text="Iniciando pipeline...")
    log = st.empty()

    def progress_callback(step: int, total: int, msg: str):
        pct = int((step / total) * 100)
        label = pasos[step - 1] if step <= len(pasos) else msg
        progress.progress(pct, text=label)
        log.info(f"**Paso {step}/{total}** — {label}")

    try:
        resultado = run_pipeline(carpeta.strip(), progress_callback=progress_callback)
        progress.progress(100, text="Pipeline completado")
        log.success(f"Listo — {1 + len(resultado['gallery'])} imágenes en `output/`")
        st.session_state["clf_resultado"] = resultado
        st.session_state["clf_error"] = None
    except Exception as e:
        progress.empty()
        log.empty()
        st.session_state["clf_error"] = str(e)
        st.session_state["clf_resultado"] = None

# ── Mostrar error ──────────────────────────────────────────────────────

if st.session_state.get("clf_error"):
    st.error(f"Error durante el pipeline:\n\n```\n{st.session_state['clf_error']}\n```")
    st.stop()

# ── Mostrar resultados ─────────────────────────────────────────────────

if not st.session_state.get("clf_resultado"):
    st.stop()

res = st.session_state["clf_resultado"]
output_dir: Path = res["output_dir"]
principal: str   = res["principal"]
gallery: list    = res["gallery"]
df               = res["df"]

st.divider()

# Imagen principal
st.subheader("Imagen principal")
principal_path  = output_dir / "imagen_principal.jpg"
principal_score = df[df["archivo"] == principal]["score"].values[0] if not df.empty else None

col_img, col_info = st.columns([2, 1])
with col_img:
    if principal_path.exists():
        st.image(str(principal_path), use_container_width=True)
with col_info:
    st.metric("Score CLIP", f"{principal_score:.4f}" if principal_score is not None else "—")
    st.caption(f"Archivo original: `{principal}`")

st.divider()

# Galería
st.subheader(f"Galería ({len(gallery)} imágenes)")
COLS = 4
gallery_files = sorted(output_dir.glob("galeria*.jpg"))

if gallery_files:
    for row in [gallery_files[i:i + COLS] for i in range(0, len(gallery_files), COLS)]:
        cols = st.columns(COLS)
        for col, gfile in zip(cols, row):
            with col:
                idx = int(gfile.stem.replace("galeria", "")) - 1
                original_name = gallery[idx] if idx < len(gallery) else gfile.name
                score_val = df[df["archivo"] == original_name]["score"].values
                score_str = f"{score_val[0]:.4f}" if len(score_val) > 0 else "—"
                st.image(str(gfile), use_container_width=True)
                st.caption(f"`{gfile.name}` · score: {score_str}")
else:
    st.warning("No se encontraron imágenes de galería en output/.")

st.divider()

with st.expander("Ver tabla completa de scores"):
    st.dataframe(
        df[["archivo", "score", "score_pos", "sim_centroide_pos", "sim_centroide_neg", "penalizacion"]],
        use_container_width=True,
    )

st.divider()
col_btn, col_path = st.columns([1, 3])
with col_btn:
    if st.button("Abrir carpeta output"):
        subprocess.Popen(f'explorer "{output_dir}"')
with col_path:
    st.code(str(output_dir), language=None)
