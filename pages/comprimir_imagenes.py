import subprocess
from pathlib import Path

import streamlit as st

from src.core.compress_images import compress_images_in_folder

# ── Sidebar ────────────────────────────────────────────────────────────────

with st.sidebar:
    st.header("Configuración")

    carpeta_input = st.text_input(
        "Carpeta de imágenes",
        placeholder=r"C:\ruta\a\imagenes",
        help="Ruta completa a la carpeta con las imágenes a comprimir.",
    )

    st.divider()
    st.subheader("Parámetros de compresión")

    formato = st.selectbox(
        "Formato de salida",
        options=["JPEG", "WEBP"],
        help="JPEG es el más compatible. WEBP puede lograr mayor reducción.",
    )

    quality = st.slider(
        "Calidad",
        min_value=60,
        max_value=100,
        value=85,
        help="Calidad inicial. Si el resultado supera el tamaño máximo, se reduce automáticamente hasta 70.",
    )

    max_size_mb = st.number_input(
        "Tamaño máximo objetivo (MB)",
        min_value=0.1,
        max_value=10.0,
        value=0.5,
        step=0.1,
        format="%.1f",
        help="Si la imagen comprimida supera este peso, se reduce la calidad progresivamente.",
    )

    st.divider()
    st.subheader("Opciones adicionales")

    recursive = st.checkbox(
        "Procesar subcarpetas (recursivo)",
        value=False,
        help="Si está activo, procesa también todas las subcarpetas dentro de la carpeta indicada.",
    )

    replace_original = st.checkbox(
        "Reemplazar original (mismo formato)",
        value=False,
        help="Si el formato de salida coincide con el original, sobreescribe el archivo. "
             "Cuando cambia el formato (ej: PNG → JPEG), el original siempre se elimina.",
    )

    st.divider()
    ejecutar = st.button("Comprimir imágenes", type="primary", use_container_width=True)

# ── Estado inicial ─────────────────────────────────────────────────────────

st.title("Comprimir Imágenes")

if not ejecutar and not st.session_state.get("ci_resultados"):
    st.markdown(
        """
        Reduce el peso de tus imágenes sin perder calidad visible.

        ### Qué hace:
        1. **Detecta** todas las imágenes en la carpeta (`.png`, `.jpg`, `.jpeg`, `.webp`)
        2. **Convierte** a JPEG o WebP con la calidad indicada
        3. **Ajusta automáticamente** la calidad si el resultado supera el tamaño máximo
        4. **Elimina el original** cuando el formato de salida es diferente (ej: PNG → JPEG)

        Configura los parámetros en el panel izquierdo y haz clic en **Comprimir imágenes**.
        """
    )
    st.stop()

# ── Ejecución ──────────────────────────────────────────────────────────────

if ejecutar:
    if not carpeta_input or not carpeta_input.strip():
        st.sidebar.error("Ingresa la ruta de la carpeta.")
        st.stop()

    carpeta_path = Path(carpeta_input.strip())
    if not carpeta_path.exists() or not carpeta_path.is_dir():
        st.sidebar.error(f"Carpeta no encontrada: `{carpeta_input}`")
        st.stop()

    progress_bar = st.progress(0, text="Iniciando...")
    log = st.container()

    def on_progress(current: int, total: int, filename: str) -> None:
        progress_bar.progress(
            int(current / total * 100),
            text=f"[{current}/{total}] {filename}",
        )
        resultados_parciales = st.session_state.get("ci_resultados", [])
        ultimo = resultados_parciales[-1] if resultados_parciales else None
        if ultimo:
            if not ultimo["success"]:
                log.error(f"Error en **{ultimo['filename']}**: {ultimo.get('error')}")
            elif ultimo.get("skipped"):
                log.info(f"Saltada (ya existe): **{ultimo['filename']}**")
            else:
                log.success(
                    f"OK: **{ultimo['filename']}** — "
                    f"{ultimo['original_size_mb']} MB → {ultimo['new_size_mb']} MB "
                    f"({ultimo['reduction_percent']}% reducción)"
                )

    resultados = compress_images_in_folder(
        folder_path=carpeta_path,
        quality=quality,
        format=formato,
        max_size_mb=max_size_mb,
        replace_original=replace_original,
        recursive=recursive,
        on_progress=on_progress,
    )

    # Log de los resultados (on_progress llega un paso tarde, cerrar el último)
    for r in resultados:
        if not r["success"]:
            log.error(f"Error en **{r['filename']}**: {r.get('error')}")
        elif r.get("skipped"):
            log.info(f"Saltada (ya existe): **{r['filename']}**")
        else:
            log.success(
                f"OK: **{r['filename']}** — "
                f"{r['original_size_mb']} MB → {r['new_size_mb']} MB "
                f"({r['reduction_percent']}% reducción)"
            )

    progress_bar.empty()

    exitosas = [r for r in resultados if r["success"] and not r.get("skipped")]
    st.toast(f"Completado. {len(exitosas)}/{len(resultados)} imágenes comprimidas.")

    st.session_state["ci_resultados"] = resultados
    st.session_state["ci_carpeta"] = carpeta_path
    st.rerun()

# ── Resultados ─────────────────────────────────────────────────────────────

if not st.session_state.get("ci_resultados"):
    st.stop()

resultados   = st.session_state["ci_resultados"]
carpeta_path = st.session_state["ci_carpeta"]

exitosas  = [r for r in resultados if r["success"] and not r.get("skipped")]
saltadas  = [r for r in resultados if r.get("skipped")]
fallidas  = [r for r in resultados if not r["success"]]

c1, c2, c3, c4 = st.columns(4)
c1.metric("Total", len(resultados))
c2.metric("Comprimidas", len(exitosas))
c3.metric("Saltadas", len(saltadas))
c4.metric("Errores", len(fallidas))

if exitosas:
    total_original = sum(r["original_size_mb"] for r in exitosas)
    total_nuevo    = sum(r["new_size_mb"] for r in exitosas)
    reduccion_mb   = total_original - total_nuevo
    reduccion_pct  = (reduccion_mb / total_original * 100) if total_original > 0 else 0

    st.divider()
    ca, cb, cc = st.columns(3)
    ca.metric("Tamaño original total", f"{total_original:.2f} MB")
    cb.metric("Tamaño final total",    f"{total_nuevo:.2f} MB")
    cc.metric("Reducción total",       f"{reduccion_mb:.2f} MB ({reduccion_pct:.1f}%)")

if fallidas:
    with st.expander(f"{len(fallidas)} errores", expanded=True):
        for r in fallidas:
            st.error(f"`{r['filename']}` — {r.get('error', 'Error desconocido')}")

st.divider()

if st.button("Abrir carpeta"):
    subprocess.Popen(f'explorer "{carpeta_path}"')
