"""
classify_pipeline.py
--------------------
Pipeline completo de clasificación de imágenes de motos/scooters.

Uso:
    python classify_pipeline.py "C:/ruta/a/carpeta"
    python classify_pipeline.py "C:/ruta/a/carpeta" --width 1100 --height 1000

Pasos:
    1. Preprocesar imágenes: centrar contenido en canvas blanco
    2. Cargar modelo CLIP y referencias positivas/negativas
    3. Calcular score de cada imagen contra referencias
    4. Seleccionar imagen principal (rank 1) y galería (top N, sin near-duplicates)
    5. Exportar versiones preprocesadas a output/ con nombres estandarizados
"""

import argparse
import io
import shutil
import sys
import tempfile
from pathlib import Path

import numpy as np
import open_clip
import pandas as pd
import torch
from PIL import Image

# Importar la función de preprocesamiento desde el módulo existente
# Funciona tanto al ejecutar desde scripts/ como al importar desde la raíz del proyecto
import sys as _sys
_sys.path.insert(0, str(Path(__file__).parent))
from centrar_y_redimensionar import center_and_resize

# ──────────────────────────────────────────────────────────────────────
# Configuración de rutas y modelo
# ──────────────────────────────────────────────────────────────────────

# Directorio base del proyecto (sube un nivel desde scripts/ → image_handling/)
BASE_DIR = Path(__file__).parent.parent

# Referencias para CLIP
REFERENCES_BASE = BASE_DIR / "src" / "data" / "references"
REFERENCES_POS  = REFERENCES_BASE / "positive"
REFERENCES_NEG  = REFERENCES_BASE / "negative"

# Modelo CLIP
MODEL_NAME = "ViT-L-14"
PRETRAINED  = "laion2b_s32b_b82k"

# Extensiones de imagen soportadas
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".avif"}


# ──────────────────────────────────────────────────────────────────────
# Paso 1: Preprocesar imágenes
# ──────────────────────────────────────────────────────────────────────

def preprocess_images(
    input_folder: Path,
    target_width: int,
    target_height: int,
) -> tuple[Path, dict[str, str]]:
    """
    Centra y redimensiona todas las imágenes de input_folder en una carpeta temporal.

    Retorna:
        tmp_dir: Path a la carpeta temporal con las imágenes procesadas
        name_map: dict {nombre_original_sin_ext: nombre_procesado.jpg}
    """
    tmp_dir = Path(tempfile.mkdtemp(prefix="clip_pipeline_"))
    name_map: dict[str, str] = {}  # original_stem -> nombre en tmp_dir

    images = sorted([
        f for f in input_folder.iterdir()
        if f.suffix.lower() in IMAGE_EXTENSIONS
    ])

    if not images:
        raise FileNotFoundError(f"No se encontraron imágenes en: {input_folder}")

    print(f"\n[1/5] Preprocesando {len(images)} imágenes...")

    for img_path in images:
        try:
            processed = center_and_resize(img_path, target_width=target_width, target_height=target_height)
            out_name = img_path.stem + ".jpg"
            out_path = tmp_dir / out_name
            processed.save(str(out_path), "JPEG", quality=90)
            name_map[img_path.name] = out_name
            print(f"  [OK] {img_path.name}")
        except Exception as e:
            print(f"  [ERR] Error en {img_path.name}: {e}", file=sys.stderr)

    print(f"  {len(name_map)} imagenes preprocesadas en carpeta temporal")
    return tmp_dir, name_map


# ──────────────────────────────────────────────────────────────────────
# Paso 2: Cargar modelo CLIP y referencias
# ──────────────────────────────────────────────────────────────────────

def load_model() -> tuple:
    """Carga el modelo CLIP y retorna (model, preprocess, device)."""
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"\n[2/5] Cargando modelo CLIP ({MODEL_NAME})... [device: {device}]")
    model, _, preprocess = open_clip.create_model_and_transforms(MODEL_NAME, pretrained=PRETRAINED)
    model = model.to(device).eval()
    print(f"  Modelo cargado")
    return model, preprocess, device


def encode_image(img_path: str, model, preprocess, device: str) -> torch.Tensor:
    """Genera el embedding CLIP normalizado de una imagen."""
    img = Image.open(img_path).convert("RGB")
    tensor = preprocess(img).unsqueeze(0).to(device)
    with torch.no_grad():
        features = model.encode_image(tensor)
        features /= features.norm(dim=-1, keepdim=True)
    return features.squeeze(0)


def load_references(
    ref_folder: Path,
    model,
    preprocess,
    device: str,
    label: str = "",
) -> tuple[torch.Tensor, torch.Tensor]:
    """
    Carga y codifica las imágenes de referencia de una carpeta.

    Retorna:
        embeddings: tensor (N, dim) con embeddings individuales
        centroid: vector promedio normalizado
    """
    paths = sorted([p for p in ref_folder.iterdir() if p.suffix.lower() in IMAGE_EXTENSIONS])

    if not paths:
        raise FileNotFoundError(f"No se encontraron referencias en: {ref_folder}")

    tag = f" [{label}]" if label else ""
    print(f"  Referencias{tag}: {len(paths)} imágenes")

    embeddings = []
    for p in paths:
        emb = encode_image(str(p), model, preprocess, device)
        embeddings.append(emb)

    ref_embeddings = torch.stack(embeddings)
    centroid = ref_embeddings.mean(dim=0)
    centroid /= centroid.norm()

    return ref_embeddings, centroid


# ──────────────────────────────────────────────────────────────────────
# Paso 3: Scoring y ranking
# ──────────────────────────────────────────────────────────────────────

def score_image(
    img_path: str,
    ref_embeddings_pos: torch.Tensor,
    ref_centroid_pos: torch.Tensor,
    ref_centroid_neg: torch.Tensor,
    model,
    preprocess,
    device: str,
    centroid_weight: float = 0.7,
    max_sim_weight: float = 0.3,
    neg_penalty: float = 0.7,
) -> dict:
    """
    Calcula el score de una imagen contra referencias positivas/negativas.

    score = (0.7 * sim_centroide_pos + 0.3 * sim_max_pos) - (0.7 * sim_centroide_neg)
    """
    img_emb = encode_image(img_path, model, preprocess, device)

    sims_pos = (ref_embeddings_pos @ img_emb).cpu().numpy()
    centroid_sim_pos = (ref_centroid_pos @ img_emb).item()
    max_sim = float(sims_pos.max())
    positive_score = (centroid_weight * centroid_sim_pos) + (max_sim_weight * max_sim)

    centroid_sim_neg = (ref_centroid_neg @ img_emb).item()
    final_score = positive_score - (neg_penalty * centroid_sim_neg)

    return {
        "archivo": Path(img_path).name,
        "score": round(final_score, 6),
        "score_pos": round(positive_score, 6),
        "sim_centroide_pos": round(centroid_sim_pos, 6),
        "sim_centroide_neg": round(centroid_sim_neg, 6),
        "penalizacion": round(neg_penalty * centroid_sim_neg, 6),
        "sim_max": round(max_sim, 6),
    }


def rank_folder(
    folder: Path,
    ref_embeddings_pos: torch.Tensor,
    ref_centroid_pos: torch.Tensor,
    ref_centroid_neg: torch.Tensor,
    model,
    preprocess,
    device: str,
) -> pd.DataFrame:
    """Procesa todas las imágenes de una carpeta y retorna DataFrame rankeado por score."""
    images = sorted([f for f in folder.iterdir() if f.suffix.lower() in IMAGE_EXTENSIONS])

    print(f"\n[3/5] Calculando scores CLIP para {len(images)} imágenes...")

    results = []
    for img_path in images:
        try:
            result = score_image(
                str(img_path),
                ref_embeddings_pos, ref_centroid_pos, ref_centroid_neg,
                model, preprocess, device,
            )
            results.append(result)
            print(f"  {result['archivo']:<45} score: {result['score']:+.4f}")
        except Exception as e:
            print(f"  ERROR en {img_path.name}: {e}", file=sys.stderr)

    df = pd.DataFrame(results)
    df = df.sort_values("score", ascending=False).reset_index(drop=True)
    df.index = df.index + 1
    df.index.name = "rank"
    return df


# ──────────────────────────────────────────────────────────────────────
# Paso 4: Selección de principal + galería
# ──────────────────────────────────────────────────────────────────────

def detect_near_duplicates(
    folder: Path,
    file_names: list[str],
    model,
    preprocess,
    device: str,
    threshold: float = 0.95,
) -> set[frozenset]:
    """
    Detecta pares de near-duplicates entre las imágenes de la galería.
    Retorna un set de frozensets {nombre_a, nombre_b} con similitud >= threshold.
    """
    embeddings = []
    names = []
    for name in file_names:
        path = folder / name
        if path.exists():
            emb = encode_image(str(path), model, preprocess, device)
            embeddings.append(emb)
            names.append(name)

    if len(embeddings) < 2:
        return set()

    all_emb = torch.stack(embeddings)
    sim_matrix = (all_emb @ all_emb.T).cpu().numpy()

    dup_pairs = set()
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            if sim_matrix[i, j] >= threshold:
                dup_pairs.add(frozenset({names[i], names[j]}))

    return dup_pairs


def select_principal_and_gallery(
    df: pd.DataFrame,
    folder: Path,
    model,
    preprocess,
    device: str,
    min_gallery: int = 10,
    dup_threshold: float = 0.95,
) -> tuple[str, list[str]]:
    """
    Selecciona la imagen principal (rank 1) y una galería.
    Comportamiento igual al notebook: incluye todas las imágenes excepto la principal.

    Retorna:
        principal: nombre del archivo de la imagen principal
        gallery: lista ordenada de nombres de archivo para la galería
    """
    principal = df.iloc[0]["archivo"]
    print(f"  Imagen principal: {principal} (score: {df.iloc[0]['score']:.4f})")

    # Galería: resto de imágenes (comportamiento del notebook - incluir todas)
    gallery = list(df.iloc[1:]["archivo"])

    print(f"  Galería: {len(gallery)} imágenes seleccionadas")
    if len(gallery) < min_gallery:
        print(f"  [AVISO] Solo se encontraron {len(gallery)} imagenes validas (minimo deseado: {min_gallery})")

    return principal, gallery


# ──────────────────────────────────────────────────────────────────────
# Paso 5: Exportar a output/
# ──────────────────────────────────────────────────────────────────────

def export_output(
    source_folder: Path,
    dest_parent: Path,
    principal: str,
    gallery: list[str],
) -> Path:
    """
    Copia las imágenes procesadas al output/ de la carpeta de destino.

    Args:
        source_folder: carpeta con las imágenes procesadas (tmp_dir)
        dest_parent: carpeta original del usuario (donde se crea output/)
        principal: nombre del archivo de la imagen principal
        gallery: lista de nombres de archivo de la galería

    Retorna la ruta de la carpeta output/.
    """
    output_dir = dest_parent / "output"

    # Limpiar y recrear output/
    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir()

    # Copiar imagen principal (ya es .jpg por el preprocesamiento)
    src_principal = source_folder / principal
    if not src_principal.exists():
        raise FileNotFoundError(f"Imagen principal no encontrada: {src_principal}")

    dst_principal = output_dir / f"imagen_principal.jpg"
    shutil.copy2(src_principal, dst_principal)
    print(f"  [OK] imagen_principal.jpg  <-  {principal}")

    # Copiar galería
    for i, filename in enumerate(gallery, start=1):
        src_file = source_folder / filename
        if not src_file.exists():
            print(f"  [ERR] No encontrada, omitida: {filename}", file=sys.stderr)
            continue
        dst_file = output_dir / f"galeria{i}.jpg"
        shutil.copy2(src_file, dst_file)
        print(f"  [OK] galeria{i}.jpg  <-  {filename}")

    print(f"\n  {1 + len(gallery)} imagenes exportadas")
    return output_dir


# ──────────────────────────────────────────────────────────────────────
# Pipeline principal
# ──────────────────────────────────────────────────────────────────────

def run_pipeline(
    input_folder: str,
    progress_callback=None,
) -> dict:
    """
    Ejecuta el pipeline completo y retorna un dict con los resultados.

    Args:
        input_folder: ruta a la carpeta con imágenes
        progress_callback: función opcional llamada con (paso: int, total: int, mensaje: str)
                           para reportar progreso (usada por la UI Streamlit)

    Returns:
        dict con claves: principal, gallery, df, output_dir, input_folder
        Lanza Exception si hay error.
    """
    folder = Path(input_folder)
    if not folder.exists() or not folder.is_dir():
        raise FileNotFoundError(f"Carpeta no encontrada: {folder}")

    def _progress(step, msg):
        print(msg)
        if progress_callback:
            progress_callback(step, 5, msg)

    print("=" * 60)
    print(f"Carpeta: {folder}")
    print("=" * 60)

    tmp_dir = None
    try:
        # Paso 1: Preprocesar imágenes (centrar y redimensionar)
        _progress(1, f"[1/5] Preprocesando imágenes...")
        tmp_dir, name_map = preprocess_images(folder, target_width=1100, target_height=1000)

        # Paso 2: Cargar modelo y referencias
        _progress(2, f"[2/5] Cargando modelo CLIP y referencias...")
        model, preprocess, device = load_model()
        ref_emb_pos, ref_centroid_pos = load_references(REFERENCES_POS, model, preprocess, device, label="positivas")
        ref_emb_neg, ref_centroid_neg = load_references(REFERENCES_NEG, model, preprocess, device, label="negativas")

        # Paso 3: Ranking sobre imágenes procesadas
        _progress(3, f"[3/5] Calculando scores CLIP...")
        df = rank_folder(tmp_dir, ref_emb_pos, ref_centroid_pos, ref_centroid_neg, model, preprocess, device)

        if df.empty:
            raise RuntimeError("No se pudieron procesar imágenes.")

        # Paso 4: Selección
        _progress(4, f"[4/5] Seleccionando principal y galería...")
        principal, gallery = select_principal_and_gallery(df, tmp_dir, model, preprocess, device)

        # Paso 5: Exportar imágenes procesadas a output/
        _progress(5, f"[5/5] Exportando a output/...")
        output_dir = export_output(tmp_dir, folder, principal, gallery)

    finally:
        # Limpiar carpeta temporal
        if tmp_dir and tmp_dir.exists():
            shutil.rmtree(tmp_dir, ignore_errors=True)

    print(f"\n{'=' * 60}")
    print(f"Pipeline completado")
    print(f"  Output: {output_dir}")
    print(f"  Principal: {principal}")
    print(f"  Galería: {len(gallery)} imágenes")
    print(f"{'=' * 60}")

    return {
        "principal": principal,
        "gallery": gallery,
        "df": df,
        "output_dir": output_dir,
        "input_folder": folder,
    }


# ──────────────────────────────────────────────────────────────────────
# Entry point
# ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    # Forzar UTF-8 en stdout/stderr para evitar errores de encoding en Windows
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(
        description="Pipeline de clasificación de imágenes de motos: CLIP → output"
    )
    parser.add_argument("carpeta", help="Ruta a la carpeta con imágenes a clasificar")

    args = parser.parse_args()
    try:
        result = run_pipeline(args.carpeta)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
