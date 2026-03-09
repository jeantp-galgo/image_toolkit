#!/usr/bin/env python3
"""
Script para redimensionar imágenes manteniendo proporciones y añadiendo fondo blanco.
Usado por la SKILL identify-principal para procesar imágenes después de la selección.
"""
import os
import sys
from PIL import Image


def resize_image(image_path, output_path, target_width, target_height):
    """
    Redimensiona una imagen manteniendo las proporciones y deja el fondo blanco.

    Args:
        image_path: Ruta de la imagen de entrada
        output_path: Ruta donde guardar la imagen redimensionada
        target_width: Ancho objetivo
        target_height: Alto objetivo

    Returns:
        bool: True si se procesó correctamente, False en caso contrario
    """
    try:
        # Abrir la imagen con PIL para el procesamiento
        img = Image.open(image_path).convert("RGBA")

        # Calcular la relación de aspecto
        target_ratio = target_width / target_height
        img_ratio = img.width / img.height

        # Determinar nuevas dimensiones manteniendo la proporción
        if img_ratio > target_ratio:
            new_width = target_width
            new_height = int(target_width / img_ratio)
        else:
            new_width = int(target_height * img_ratio)
            new_height = target_height

        # Redimensionar la imagen
        img_resized = img.resize((new_width, new_height), Image.LANCZOS)

        # Crear un lienzo del tamaño objetivo y centrar la imagen redimensionada
        # Fondo blanco: (255, 255, 255)
        background = Image.new("RGB", (target_width, target_height), (255, 255, 255))
        paste_x = (target_width - new_width) // 2
        paste_y = (target_height - new_height) // 2
        # Pegar la imagen redimensionada sobre el fondo blanco usando el canal alfa como máscara
        background.paste(img_resized.convert("RGBA"), (paste_x, paste_y), img_resized)

        # Guardar la imagen redimensionada (siempre fondo blanco)
        background.save(output_path, "JPEG", quality=90)
        return True
    except Exception as e:
        print(f"Error procesando {os.path.basename(image_path)}: {e}", file=sys.stderr)
        return False


def process_output_folder(output_folder, target_width=1100, target_height=1000):
    """
    Procesa todas las imágenes en la carpeta output/ redimensionándolas.

    Args:
        output_folder: Ruta de la carpeta output/ que contiene las imágenes
        target_width: Ancho objetivo (default: 1100)
        target_height: Alto objetivo (default: 1000)

    Returns:
        tuple: (número de imágenes procesadas, número de errores)
    """
    if not os.path.isdir(output_folder):
        print(f"Error: La carpeta no existe: {output_folder}", file=sys.stderr)
        return 0, 1

    processed = 0
    errors = 0

    # Procesar cada archivo de imagen en la carpeta output/
    for filename in os.listdir(output_folder):
        if not filename.lower().endswith(('.png', '.jpg', '.jpeg', '.webp', '.avif')):
            continue

        image_path = os.path.join(output_folder, filename)

        # Crear ruta temporal para la imagen redimensionada
        # Guardamos con extensión .jpg siempre (formato de salida estándar)
        base_name = os.path.splitext(filename)[0]
        output_path = os.path.join(output_folder, f"{base_name}.jpg")

        try:
            success = resize_image(
                image_path,
                output_path,
                target_width,
                target_height
            )
            if success:
                # Si la imagen original no era .jpg, eliminar el archivo original
                if not filename.lower().endswith('.jpg'):
                    os.remove(image_path)
                processed += 1
                print(f"Procesada: {filename} → {base_name}.jpg")
            else:
                errors += 1
        except Exception as e:
            print(f"Error procesando {filename}: {e}", file=sys.stderr)
            errors += 1

    return processed, errors


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: resize-images.py <output_folder> [target_width] [target_height]", file=sys.stderr)
        print("  output_folder: Carpeta output/ que contiene las imágenes a redimensionar", file=sys.stderr)
        print("  target_width: Ancho objetivo (default: 1100)", file=sys.stderr)
        print("  target_height: Alto objetivo (default: 1000)", file=sys.stderr)
        sys.exit(1)

    output_folder = sys.argv[1]
    target_width = int(sys.argv[2]) if len(sys.argv) > 2 else 1100
    target_height = int(sys.argv[3]) if len(sys.argv) > 3 else 1000

    processed, errors = process_output_folder(output_folder, target_width, target_height)

    if errors > 0:
        print(f"\nProcesadas: {processed}, Errores: {errors}", file=sys.stderr)
        sys.exit(1)
    else:
        print(f"\n✓ {processed} imágenes redimensionadas correctamente")
        sys.exit(0)
