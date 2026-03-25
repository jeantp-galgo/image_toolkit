import io
import subprocess
import sys
import zipfile
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).parent.parent / "src" / "core"))
from centrar_y_redimensionar import center_and_resize  # noqa: E402

VALID_EXTENSIONS = (".png", ".jpg", ".jpeg", ".webp", ".avif")

# ── Sidebar ────────────────────────────────────────────────────────────

with st.sidebar:
    st.header("Configuración")

    carpeta_input = st.text_input(
        "Carpeta de imágenes",
        placeholder=r"C:\ruta\a\imagenes",
        help="Ruta completa a la carpeta con las imágenes a procesar.",
    )

    st.divider()
    st.subheader("Parámetros de salida")

    col_w, col_h = st.columns(2)
    with col_w:
        target_width = st.number_input("Ancho (px)", min_value=100, max_value=5000, value=1100, step=50)
    with col_h:
        target_height = st.number_input("Alto (px)", min_value=100, max_value=5000, value=1000, step=50)

    padding_pct = st.slider(
        "Padding interno (%)",
        min_value=0, max_value=20, value=5,
        help="Espacio libre alrededor del vehículo, como % del lado.",
    )
    quality = st.slider("Calidad JPEG", min_value=50, max_value=100, value=90)
    threshold = st.slider(
        "Threshold detección",
        min_value=180, max_value=255, value=240,
        help="Píxeles >= este valor se consideran fondo blanco.",
    )

    st.divider()
    usar_subcarpeta = st.checkbox(
        "Guardar en subcarpeta 'Procesadas/'",
        value=True,
        help="Si está activo, crea 'Procesadas/' dentro de la carpeta de entrada.",
    )

    st.divider()
    ejecutar = st.button("Procesar imágenes", type="primary", use_container_width=True)

# ── Validación temprana ────────────────────────────────────────────────

st.title("Centrar y Redimensionar")

if not ejecutar and not st.session_state.get("cr_resultados"):
    st.markdown(
        """
        Detecta automáticamente el vehículo en cada imagen y lo centra en un canvas limpio.

        ### Qué hace:
        1. **Detecta** el bounding box del vehículo (ignora fondo blanco)
        2. **Recorta** al contenido relevante
        3. **Escala** manteniendo aspect ratio con padding configurable
        4. **Centra** en un canvas blanco del tamaño indicado
        5. **Exporta** a JPEG con la calidad elegida

        ```
        tu_carpeta/
        └── Procesadas/
            ├── imagen1.jpg
            └── ...
        ```

        Configura los parámetros en el panel izquierdo y haz clic en **Procesar imágenes**.
        """
    )
    st.stop()

# ── Ejecución ─────────────────────────────────────────────────────────

if ejecutar:
    if not carpeta_input or not carpeta_input.strip():
        st.sidebar.error("Ingresa la ruta de la carpeta.")
        st.stop()

    carpeta_path = Path(carpeta_input.strip())
    if not carpeta_path.exists() or not carpeta_path.is_dir():
        st.sidebar.error(f"Carpeta no encontrada: `{carpeta_input}`")
        st.stop()

    archivos = [
        f for f in carpeta_path.iterdir()
        if f.is_file() and f.suffix.lower() in VALID_EXTENSIONS
    ]

    if not archivos:
        st.sidebar.warning("No se encontraron imágenes en la carpeta indicada.")
        st.stop()

    output_dir = carpeta_path / "Procesadas" if usar_subcarpeta else carpeta_path
    output_dir.mkdir(parents=True, exist_ok=True)

    resultados = []
    progress = st.progress(0, text="Iniciando...")
    log = st.container()
    total = len(archivos)

    for i, archivo in enumerate(archivos, start=1):
        progress.progress(int(i / total * 100), text=f"Procesando {archivo.name}...")
        output_path = output_dir / (archivo.stem + ".jpg")
        try:
            procesada = center_and_resize(
                archivo,
                target_width=target_width,
                target_height=target_height,
                padding_pct=padding_pct / 100,
                threshold=threshold,
            )
            procesada.save(str(output_path), "JPEG", quality=quality)
            resultados.append({"nombre": archivo.name, "path": output_path, "ok": True, "error": None})
            log.success(f"OK: **{archivo.name}**")
        except Exception as e:
            resultados.append({"nombre": archivo.name, "path": None, "ok": False, "error": str(e)})
            log.error(f"Error en {archivo.name}: {e}")

    progress.empty()
    st.toast(f"Proceso completado. {sum(r['ok'] for r in resultados)}/{total} imágenes OK.")

    st.session_state["cr_resultados"] = resultados
    st.session_state["cr_output_dir"] = output_dir
    st.rerun()

# ── Mostrar resultados ─────────────────────────────────────────────────

if not st.session_state.get("cr_resultados"):
    st.stop()

resultados  = st.session_state["cr_resultados"]
output_dir  = st.session_state["cr_output_dir"]
ok_list     = [r for r in resultados if r["ok"]]
err_list    = [r for r in resultados if not r["ok"]]

# Métricas resumen
c1, c2, c3 = st.columns(3)
c1.metric("Total", len(resultados))
c2.metric("Exitosas", len(ok_list))
c3.metric("Con error", len(err_list))

if err_list:
    with st.expander(f"{len(err_list)} errores", expanded=True):
        for r in err_list:
            st.error(f"`{r['nombre']}` — {r['error']}")

if not ok_list:
    st.stop()

st.divider()

# Vista previa
st.subheader(f"Vista previa — {len(ok_list)} imágenes procesadas")
COLS = 4
for row in [ok_list[i:i + COLS] for i in range(0, len(ok_list), COLS)]:
    cols = st.columns(COLS)
    for col, r in zip(cols, row):
        with col:
            st.image(str(r["path"]), use_container_width=True)
            st.caption(r["nombre"])

st.divider()

# Acciones
zip_buffer = io.BytesIO()
with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
    for r in ok_list:
        zf.write(r["path"], arcname=r["path"].name)
zip_buffer.seek(0)

col_btn, col_zip, col_path = st.columns([1, 1, 2])
with col_btn:
    if st.button("Abrir carpeta output"):
        subprocess.Popen(f'explorer "{output_dir}"')
with col_zip:
    st.download_button(
        label="Descargar ZIP",
        data=zip_buffer,
        file_name="imagenes_procesadas.zip",
        mime="application/zip",
        use_container_width=True,
    )
with col_path:
    st.code(str(output_dir), language=None)
