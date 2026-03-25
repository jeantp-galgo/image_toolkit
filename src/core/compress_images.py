"""
compress_images.py — Lógica de compresión de imágenes sin dependencias de Streamlit.

Funciones principales:
    compress_image()              → Comprime una sola imagen
    compress_images_in_folder()  → Comprime todas las imágenes de una carpeta
"""

import os
from pathlib import Path
from PIL import Image

SUPPORTED_EXTENSIONS = (".png", ".jpg", ".jpeg", ".webp")


def compress_image(
    input_path: Path,
    output_path: Path,
    quality: int = 85,
    format: str = "JPEG",
    max_size_mb: float = 0.5,
) -> dict:
    """
    Comprime una imagen reduciendo su peso sin perder mucha calidad.
    Si el resultado sigue siendo mayor a max_size_mb, reduce la calidad
    progresivamente en pasos de 5 hasta llegar a calidad 70 como mínimo.

    Args:
        input_path:  Ruta de la imagen original.
        output_path: Ruta donde guardar la imagen comprimida.
        quality:     Calidad inicial (1-100). Recomendado 85-90.
        format:      Formato de salida: 'JPEG' o 'WEBP'.
        max_size_mb: Tamaño máximo objetivo en MB (0.5 = 500 KB).

    Returns:
        dict con claves: success, original_size_mb, new_size_mb,
        reduction_percent, final_quality y (en caso de error) error.
    """
    try:
        img = Image.open(input_path)

        # JPEG no soporta transparencia → convertir a RGB con fondo blanco
        if img.mode in ("RGBA", "LA", "P"):
            background = Image.new("RGB", img.size, (255, 255, 255))
            if img.mode == "P":
                img = img.convert("RGBA")
            mask = img.split()[-1] if img.mode == "RGBA" else None
            background.paste(img, mask=mask)
            img = background
        elif img.mode != "RGB":
            img = img.convert("RGB")

        original_size = os.path.getsize(input_path)
        original_size_mb = original_size / (1024 * 1024)

        def _save(q: int) -> None:
            if format == "WEBP":
                img.save(output_path, "WEBP", quality=q, method=6)
            else:
                img.save(output_path, "JPEG", quality=q, optimize=True)

        _save(quality)
        new_size = os.path.getsize(output_path)
        new_size_mb = new_size / (1024 * 1024)

        # Reducir calidad progresivamente si el resultado sigue siendo grande
        current_quality = quality
        while new_size_mb > max_size_mb and current_quality > 70:
            current_quality -= 5
            _save(current_quality)
            new_size = os.path.getsize(output_path)
            new_size_mb = new_size / (1024 * 1024)

        reduction_percent = ((original_size - new_size) / original_size) * 100

        return {
            "success": True,
            "original_size_mb": round(original_size_mb, 2),
            "new_size_mb": round(new_size_mb, 2),
            "reduction_percent": round(reduction_percent, 1),
            "final_quality": current_quality,
        }

    except Exception as e:
        return {"success": False, "error": str(e)}


def compress_images_in_folder(
    folder_path: Path | str,
    quality: int = 85,
    format: str = "JPEG",
    max_size_mb: float = 0.5,
    replace_original: bool = False,
    recursive: bool = False,
    on_progress=None,
) -> list[dict]:
    """
    Comprime todas las imágenes de una carpeta (y opcionalmente subcarpetas).

    Cuando el formato de salida difiere del original (ej: PNG → JPEG), el archivo
    original se elimina automáticamente para conservar solo la versión optimizada.

    Args:
        folder_path:      Carpeta raíz con las imágenes.
        quality:          Calidad de compresión inicial (85-90 recomendado).
        format:           Formato de salida: 'JPEG' o 'WEBP'.
        max_size_mb:      Tamaño máximo objetivo en MB.
        replace_original: Si True y el formato coincide, sobreescribe el original.
        recursive:        Si True, procesa también todas las subcarpetas.
        on_progress:      Callable opcional(current, total, filename) para feedback externo.

    Returns:
        Lista de dicts por imagen con claves: filename, success, original_size_mb,
        new_size_mb, reduction_percent, error.
    """
    folder_path = Path(folder_path)

    # Recopilar archivos a procesar
    if recursive:
        files = [
            f for f in folder_path.rglob("*")
            if f.is_file() and f.suffix.lower() in SUPPORTED_EXTENSIONS
        ]
    else:
        files = [
            f for f in folder_path.iterdir()
            if f.is_file() and f.suffix.lower() in SUPPORTED_EXTENSIONS
        ]

    results = []
    total = len(files)

    for i, input_path in enumerate(files, start=1):
        ext_out = ".webp" if format == "WEBP" else ".jpg"
        output_path = input_path.with_suffix(ext_out)

        # Saltar si ya existe una versión comprimida diferente al original
        if output_path.exists() and output_path != input_path:
            results.append({
                "filename": input_path.name,
                "success": True,
                "skipped": True,
                "original_size_mb": None,
                "new_size_mb": None,
                "reduction_percent": None,
                "error": None,
            })
            if on_progress:
                on_progress(i, total, input_path.name)
            continue

        result = compress_image(input_path, output_path, quality, format, max_size_mb)

        row = {
            "filename": input_path.name,
            "skipped": False,
            **result,
        }

        if result["success"]:
            # Eliminar original si la extensión cambió, o si se pidió reemplazar
            same_ext = input_path.suffix.lower() == output_path.suffix.lower()
            if not same_ext and input_path.exists():
                input_path.unlink()
            elif same_ext and replace_original and output_path != input_path:
                input_path.unlink()

        results.append(row)

        if on_progress:
            on_progress(i, total, input_path.name)

    return results
