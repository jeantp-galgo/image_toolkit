import io
import sys
import requests
import pandas as pd
import numpy as np
from pathlib import Path
from PIL import Image, ImageFilter

"""
COMPOSICION DE MOTO SOBRE PLANTILLA
Lee un CSV con URLs de imágenes de motos, descarga cada imagen, detecta
el bounding box del vehículo, lo escala y lo centra en el área disponible
de una plantilla local fija.
"""

# ---------------------------------------------------------------------------
# PARAMETROS CONFIGURABLES
# ---------------------------------------------------------------------------

RUTA_CSV       = r"C:\Users\JTRUJILLO\Desktop\utiles\Reportes\historical_data\src\data\lifestyle_base\BaseCO.csv"       # CSV con columna imagen_link
RUTA_PLANTILLA = "./MARCO-ANUNCIO-DINAMICO-MARZO.jpg"       # Imagen plantilla local (.png)
CARPETA_OUTPUT = "./src/data/imagenes_con_marcos"                # Carpeta donde se guardan los resultados

COLUMNA_URL    = "image_link"   # Nombre de la columna con la URL
COLUMNA_ID     = "code"            # Columna para nombrar el archivo de salida (None = usar índice)

ESCALA_MOTO    = 0.65   # % del ancho disponible de la plantilla que ocupa la moto
HEADER_PCT     = 0.22   # % de la altura de la plantilla reservado para el header (logo + texto)
FOOTER_PCT     = 0.12   # % de la altura de la plantilla reservado para la barra inferior
PADDING_PCT    = 0.04   # Padding interno al recortar el bounding box del vehículo
THRESHOLD      = 240    # Umbral de luminosidad para detectar contenido (< = contenido)

TIMEOUT_DESC   = 15     # Segundos máximos para descargar cada imagen

# ---------------------------------------------------------------------------
# FUNCIONES
# ---------------------------------------------------------------------------

def descargar_imagen(url: str, timeout: int = TIMEOUT_DESC) -> Image.Image:
    """Descarga una imagen desde una URL y la retorna como objeto PIL."""
    response = requests.get(url, timeout=timeout)
    response.raise_for_status()
    return Image.open(io.BytesIO(response.content))


def eliminar_fondo_blanco(img_rgba: Image.Image, threshold: int = THRESHOLD) -> Image.Image:
    """
    Convierte los píxeles cercanos al blanco en transparentes.
    Útil cuando la imagen fuente tiene fondo blanco sólido (no transparente).
    """
    arr = np.array(img_rgba.convert("RGBA"), dtype=np.uint8)

    # Píxeles donde los 3 canales RGB son >= threshold → fondo blanco → alpha = 0
    es_blanco = np.all(arr[:, :, :3] >= threshold, axis=2)
    arr[es_blanco, 3] = 0

    return Image.fromarray(arr, "RGBA")


def detectar_bbox(img_rgba: Image.Image, threshold: int = THRESHOLD, padding_pct: float = PADDING_PCT):
    """
    Detecta el bounding box del contenido no-blanco/no-transparente de la imagen.
    Retorna (min_x, min_y, max_x, max_y) o None si no encuentra contenido.
    """
    # Componer sobre fondo blanco para unificar transparencia y fondo blanco
    bg_blanco = Image.new("RGB", img_rgba.size, (255, 255, 255))
    bg_blanco.paste(img_rgba, mask=img_rgba.split()[3])

    # Leve blur para ignorar artefactos JPEG/PNG
    blurred = bg_blanco.filter(ImageFilter.GaussianBlur(radius=2))
    arr = np.array(blurred)

    # Máscara: True donde algún canal está por debajo del threshold
    mask = np.any(arr < threshold, axis=2)

    if not mask.any():
        return None

    rows = np.any(mask, axis=1)
    cols = np.any(mask, axis=0)
    min_y, max_y = np.where(rows)[0][[0, -1]]
    min_x, max_x = np.where(cols)[0][[0, -1]]

    # Aplicar padding interno al bounding box
    w, h = img_rgba.size
    pad_x = int((max_x - min_x) * padding_pct)
    pad_y = int((max_y - min_y) * padding_pct)

    min_x = max(0, min_x - pad_x)
    min_y = max(0, min_y - pad_y)
    max_x = min(w - 1, max_x + pad_x)
    max_y = min(h - 1, max_y + pad_y)

    return int(min_x), int(min_y), int(max_x) + 1, int(max_y) + 1


def escalar_a_area(img: Image.Image, ancho_max: int, alto_max: int) -> Image.Image:
    """Escala la imagen para que quepa en el área dada manteniendo aspect ratio."""
    ratio = min(ancho_max / img.width, alto_max / img.height)
    return img.resize((int(img.width * ratio), int(img.height * ratio)), Image.LANCZOS)


def componer_sobre_plantilla(
    img_moto: Image.Image,
    ruta_plantilla: str,
    escala: float = ESCALA_MOTO,
    header_pct: float = HEADER_PCT,
    footer_pct: float = FOOTER_PCT,
) -> Image.Image:
    """
    Coloca la moto centrada en el área disponible de la plantilla.

    El área disponible se calcula excluyendo el header (logo/texto) y el footer
    (barra inferior morada). La moto nunca superpasa ninguno de los dos.
    """
    plantilla = Image.open(ruta_plantilla).convert("RGBA")
    pw, ph = plantilla.size

    # Límites del área disponible (en píxeles)
    y_inicio = int(ph * header_pct)
    y_fin    = int(ph * (1 - footer_pct))
    alto_disponible = y_fin - y_inicio
    ancho_disponible = int(pw * escala)

    # Convertir a RGBA y eliminar fondo blanco
    moto = img_moto.convert("RGBA")
    moto = eliminar_fondo_blanco(moto)

    # Recortar al bounding box del contenido real
    bbox = detectar_bbox(moto)
    if bbox:
        moto = moto.crop(bbox)

    # Escalar para que quepa en el área disponible
    moto = escalar_a_area(moto, ancho_disponible, alto_disponible)

    # Centrar horizontalmente dentro del área disponible
    x = (pw - moto.width) // 2

    # Centrar verticalmente dentro del área disponible
    y = y_inicio + (alto_disponible - moto.height) // 2

    # Pegar respetando canal alfa
    plantilla.paste(moto, (x, y), moto)

    return plantilla.convert("RGB")


def nombre_archivo(row: pd.Series, indice: int, columna_id: str | None) -> str:
    """Genera el nombre del archivo de salida a partir del ID o del índice."""
    if columna_id and columna_id in row.index and pd.notna(row[columna_id]):
        nombre = str(row[columna_id]).strip().replace(" ", "_").replace("/", "-")
        return f"{nombre}-feed.jpg"
    return f"moto_{indice:04d}-feed.jpg"


# ---------------------------------------------------------------------------
# EJECUCION PRINCIPAL
# ---------------------------------------------------------------------------

def main():
    ruta_csv       = Path(RUTA_CSV)
    ruta_plantilla = Path(RUTA_PLANTILLA)
    carpeta_output = Path(CARPETA_OUTPUT)

    # Validaciones previas
    if not ruta_csv.exists():
        print(f"[ERROR] No se encontró el CSV: {ruta_csv}")
        sys.exit(1)

    if not ruta_plantilla.exists():
        print(f"[ERROR] No se encontró la plantilla: {ruta_plantilla}")
        sys.exit(1)

    carpeta_output.mkdir(parents=True, exist_ok=True)


     # Filtrar acá qué se le pondrá marco
    df = pd.read_csv(ruta_csv)
    # df = df[df]

    if COLUMNA_URL not in df.columns:
        print(f"[ERROR] El CSV no tiene la columna '{COLUMNA_URL}'.")
        print(f"        Columnas disponibles: {list(df.columns)}")
        sys.exit(1)

    total   = len(df)
    ok      = 0
    errores = 0

    print(f"\nPlantilla : {ruta_plantilla.name}")
    print(f"CSV       : {ruta_csv.name}  ({total} filas)")
    print(f"Output    : {carpeta_output}\n")

    for idx, row in df.iterrows():
        url = row[COLUMNA_URL]
        nombre = nombre_archivo(row, idx, COLUMNA_ID)
        ruta_salida = carpeta_output / nombre

        # Saltar URLs vacías o nulas
        if pd.isna(url) or str(url).strip() == "":
            print(f"  [{idx:04d}] SKIP  — URL vacía")
            errores += 1
            continue

        try:
            img_moto  = descargar_imagen(str(url))
            resultado = componer_sobre_plantilla(img_moto, str(ruta_plantilla))
            resultado.save(str(ruta_salida), "JPEG", quality=92)
            print(f"  [{idx:04d}] OK    — {nombre}")
            ok += 1
        except requests.exceptions.RequestException as e:
            print(f"  [{idx:04d}] ERROR — URL inaccesible: {e}")
            errores += 1
        except Exception as e:
            print(f"  [{idx:04d}] ERROR — {nombre}: {e}")
            errores += 1

    print(f"\nFinalizado: {ok} OK | {errores} errores | {total} total")
    print(f"Imágenes guardadas en: {carpeta_output}")


if __name__ == "__main__":
    main()
