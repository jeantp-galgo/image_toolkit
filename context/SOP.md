# SOP — image_handling

## Proposito

Seleccionar automaticamente la imagen principal de un conjunto de fotos de motocicletas y organizar la galeria, usando similitud visual con CLIP.

## Instalacion

```bash
cd image_handling
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate

pip install open-clip-torch torch torchvision pillow pandas numpy streamlit
```

La primera ejecucion descarga el modelo CLIP ViT-L-14 (~900 MB desde internet). Las ejecuciones siguientes usan la version en cache.

## Ejecucion — Opcion A: Interfaz Streamlit (recomendada)

**Con doble clic (Windows):**

Abrir el archivo `launch.bat`.

**Desde la terminal:**

```bash
streamlit run app.py
```

Una vez abierta la interfaz en `http://localhost:8501`:

1. En el panel lateral, escribir la ruta completa a la carpeta de imagenes. Ejemplo: `C:\fotos\honda_cb500`
2. Hacer clic en "Ejecutar pipeline"
3. Esperar la barra de progreso
4. Ver resultados: imagen principal con su score, galeria ordenada por score, tabla completa de scores

## Ejecucion — Opcion B: Linea de comandos

```bash
python scripts/classify_pipeline.py "C:/ruta/a/la/carpeta"
```

## Ejecucion — Opcion C: Notebook Jupyter

```bash
jupyter notebook notebooks/clip_visual_similarity_references.ipynb
```

Cambiar la variable `FOLDER` en la celda 3:

```python
FOLDER = r"C:\ruta\a\tu\carpeta\de\fotos"
```

## Ajustar la intensidad de penalizacion

Editar el parametro `neg_penalty` en `scripts/classify_pipeline.py`:

```python
# 0.7 = penalizacion fuerte (default)
# 0.4-0.5 = penalizacion moderada
# 0.2-0.3 = penalizacion suave
neg_penalty: float = 0.7
```

## Mejorar el sistema de referencias

Para mejorar la seleccion de la imagen principal:
- Agregar imagenes correctas a `src/data/references/positive/`
- Incluir variedad: distintos modelos, colores, fondos ligeramente distintos
- No se requieren cambios en el codigo

Para mejorar la penalizacion de angulos incorrectos:
- Agregar imagenes a `src/data/references/negative/` con los angulos que el sistema sigue confundiendo

## Formatos de imagen soportados

`.jpg`, `.jpeg`, `.png`, `.webp`, `.avif`

## Notas operativas

- Si hay GPU con CUDA disponible, el modelo la usa automaticamente
- Si la carpeta de entrada no contiene imagenes validas, el pipeline lanza `FileNotFoundError`
- El sistema esta optimizado para imagenes con fondo blanco o muy claro
- Las imagenes de salida se guardan en formato JPEG con calidad 90
- La carpeta `output/` se limpia y recrea en cada ejecucion
