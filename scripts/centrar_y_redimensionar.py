import os
from pathlib import Path
from PIL import Image, ImageFilter
import numpy as np

"""
CENTRAR Y REDIMENSIONAR IMÁGENES
Detecta el contenido (moto/carro) via threshold sobre píxeles no-blancos,
recorta al bounding box, escala manteniendo aspect ratio con padding,
y centra en un canvas blanco cuadrado.
"""

def center_and_resize(
    img_path: Path,
    target_width: int = 1100,
    target_height: int = 1000,
    bg_color: tuple = (255, 255, 255),
    padding_pct: float = 0.05,
    threshold: int = 240,
) -> Image.Image:
    """
    Centra el vehículo en un canvas de target_width x target_height.

    Lógica:
    1. Convierte a escala de grises
    2. Threshold para encontrar píxeles no-blancos (el vehículo)
    3. Calcula bounding box del contenido
    4. Recorta, escala manteniendo aspect ratio con padding
    5. Pega centrado en canvas blanco
    """
    img = Image.open(img_path).convert("RGBA")

    # Crear máscara: píxeles que NO son fondo blanco
    # Componer sobre fondo blanco para que los píxeles transparentes no se detecten como contenido
    white_bg = Image.new("RGB", img.size, bg_color)
    white_bg.paste(img, mask=img.split()[3])  # Usar canal alfa como máscara
    rgb = white_bg

    # Aplicar leve blur para ignorar ruido/artefactos JPEG
    blurred = rgb.filter(ImageFilter.GaussianBlur(radius=2))

    # Encontrar bounding box del contenido con NumPy
    arr = np.array(blurred)
    # Máscara: True donde CUALQUIER canal está por debajo del threshold (= contenido, no fondo)
    mask = np.any(arr < threshold, axis=2)

    if not mask.any():
        # No se encontró contenido, devolver imagen redimensionada tal cual
        return img.convert("RGB").resize((target_width, target_height), Image.LANCZOS)

    # Obtener coordenadas del bounding box desde la máscara
    rows = np.any(mask, axis=1)
    cols = np.any(mask, axis=0)
    min_y, max_y = np.where(rows)[0][[0, -1]]
    min_x, max_x = np.where(cols)[0][[0, -1]]

    # Recortar al bounding box del contenido
    cropped = img.crop((int(min_x), int(min_y), int(max_x) + 1, int(max_y) + 1))

    # Calcular tamaño disponible con padding
    available_w = int(target_width * (1 - 2 * padding_pct))
    available_h = int(target_height * (1 - 2 * padding_pct))

    # Escalar manteniendo aspect ratio
    cw, ch = cropped.size
    scale = min(available_w / cw, available_h / ch)
    new_w = int(cw * scale)
    new_h = int(ch * scale)
    resized = cropped.resize((new_w, new_h), Image.LANCZOS)

    # Crear canvas y pegar centrado
    canvas = Image.new("RGBA", (target_width, target_height), (*bg_color, 255))
    offset_x = (target_width - new_w) // 2
    offset_y = (target_height - new_h) // 2
    canvas.paste(resized, (offset_x, offset_y), resized)

    return canvas.convert("RGB")


def process_images_in_folder(input_folder, output_folder, target_width, target_height, quality=90):
    """
    Procesa todas las imágenes de una carpeta con center_and_resize y las guarda.
    """
    os.makedirs(output_folder, exist_ok=True)

    valid_extensions = ('.png', '.jpg', '.jpeg', '.webp', '.avif')
    files = [
        f for f in os.listdir(input_folder)
        if f.lower().endswith(valid_extensions) and os.path.isfile(os.path.join(input_folder, f))
    ]

    if not files:
        print(f"  No se encontraron imágenes en: {input_folder}")
        return

    print(f"\n  Procesando {len(files)} imágenes en: {input_folder}")

    for filename in files:
        image_path = Path(input_folder) / filename
        # Guardar siempre como .jpg
        output_name = Path(filename).stem + ".jpg"
        output_path = Path(output_folder) / output_name

        try:
            processed = center_and_resize(image_path, target_width=target_width, target_height=target_height)
            processed.save(str(output_path), "JPEG", quality=quality)
            print(f"    [OK] {filename} -> {output_name}")
        except Exception as e:
            print(f"    [ERR] Error procesando {filename}: {e}")


if __name__ == "__main__":
    input_folder = r"C:\Users\JTRUJILLO\Documents\Galgo\Scripts\Otros\scrape_websites_refactorv2\src\data\images\TVS_SPORT 100 KLS"
    output_subfolder_name = "Procesadas_centradas"
    target_width = 1100
    target_height = 1000
    quality = 90         # Calidad JPEG de salida

    print(f"Input: {input_folder}")
    print(f"Target: {target_width}x{target_height} | Calidad JPEG: {quality}")

    # Procesar subcarpetas de primer nivel
    for subfolder_name in os.listdir(input_folder):
        subfolder_path = os.path.join(input_folder, subfolder_name)
        if os.path.isdir(subfolder_path) and subfolder_name != output_subfolder_name:
            subfolder_output = os.path.join(subfolder_path, output_subfolder_name)
            process_images_in_folder(subfolder_path, subfolder_output, target_width, target_height, quality)

    # Procesar la carpeta raíz
    root_output = os.path.join(input_folder, output_subfolder_name)
    process_images_in_folder(input_folder, root_output, target_width, target_height, quality)

    print(f"\nProceso completado. Imagenes guardadas en subcarpetas '{output_subfolder_name}'")
