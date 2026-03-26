# SOP — image_toolkit

## Proposito

Procesar imagenes de vehiculos para Marketplace usando cualquiera de las tres herramientas del toolkit:
clasificar y seleccionar imagen principal, centrar y redimensionar imagenes en canvas estandar, o comprimir imagenes reduciendo su peso sin perdida visual significativa.

## Configuracion inicial

### Instalacion

```bash
cd image_toolkit
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate

pip install -r requirements.txt
```

La primera vez que se ejecuta el **Clasificador**, se descarga el modelo CLIP ViT-L-14 (~900 MB).
Las herramientas de centrado y compresion no requieren descarga adicional.

---

## Ejecucion

### Opcion A: Interfaz Streamlit (recomendada)

**Con doble clic (Windows):**

Abrir el archivo `Toolkit de imagenes.bat`.

**Desde la terminal:**

```bash
streamlit run app.py
```

La aplicacion abre en `http://localhost:8501`. Usar el menu lateral para navegar entre herramientas.

---

## Herramienta 1: Clasificador de Imagenes

Selecciona automaticamente la imagen principal de un set de fotos de motos/scooters y organiza la galeria.

**Pagina Streamlit:** `Clasificador` (menu lateral)

### Pasos en la UI

1. En el panel lateral, ingresar la ruta completa a la carpeta con las imagenes. Ejemplo: `C:\fotos\honda_cb500`
2. Hacer clic en **Ejecutar pipeline**
3. Esperar la barra de progreso (5 pasos: preprocesar → cargar modelo → calcular scores → seleccionar → exportar)
4. Revisar resultados:
   - **Imagen principal** con su score CLIP
   - **Galeria** ordenada por score (grilla de 4 columnas)
   - **Tabla completa de scores** (expandible)
5. Usar el boton **Abrir carpeta output** para acceder a los archivos exportados

### Output

```
<carpeta_indicada>/
└── output/
    ├── imagen_principal.jpg
    ├── galeria1.jpg
    ├── galeria2.jpg
    └── ...
```

Todas las imagenes de output estan preprocesadas (centradas, canvas 1100x1000 px, fondo blanco, JPEG calidad 90).
La carpeta `output/` se limpia y recrea en cada ejecucion.

### Ejecucion desde linea de comandos (alternativa)

```bash
python scripts/classify_pipeline.py "C:/ruta/a/la/carpeta"
```

### Ejecucion desde notebook (alternativa)

```bash
jupyter notebook notebooks/clip_visual_similarity_references.ipynb
```

Cambiar la variable `FOLDER` en la celda correspondiente:

```python
FOLDER = r"C:\ruta\a\tu\carpeta\de\fotos"
```

### Formula de scoring

```
score_pos   = (0.7 * sim_centroide_pos) + (0.3 * sim_max_pos)
score_final = score_pos - (0.7 * sim_centroide_neg)
```

Para ajustar la penalizacion de angulos incorrectos, editar `neg_penalty` en `src/core/classify_pipeline.py`:

```python
neg_penalty: float = 0.7  # 0.7 = fuerte | 0.4-0.5 = moderada | 0.2-0.3 = suave
```

### Mejorar el sistema de referencias

Para mejorar la seleccion (sin cambiar codigo):
- Agregar imagenes correctas (tres cuartos frontal derecho, fondo blanco) a `src/data/references/positive/`
- Agregar angulos que el sistema confunde a `src/data/references/negative/`

---

## Herramienta 2: Centrar y Redimensionar

Detecta el vehiculo en cada imagen, lo recorta al bounding box y lo centra en un canvas limpio.

**Pagina Streamlit:** `Centrar y Redimensionar` (menu lateral)

### Pasos en la UI

1. En el panel lateral, ingresar la ruta completa a la carpeta con las imagenes
2. Configurar los parametros de salida:

| Parametro | Descripcion | Valor por defecto |
|---|---|---|
| Ancho (px) | Ancho del canvas de salida | 1100 |
| Alto (px) | Alto del canvas de salida | 1000 |
| Padding interno (%) | Espacio libre alrededor del vehiculo | 5% |
| Calidad JPEG | Calidad de compresion de salida | 90 |
| Threshold deteccion | Pixeles >= este valor se consideran fondo blanco | 240 |
| Guardar en subcarpeta 'Procesadas/' | Crea subcarpeta dentro de la carpeta de entrada | Activo |

3. Hacer clic en **Procesar imagenes**
4. Revisar la vista previa en grilla (4 columnas)
5. Usar **Descargar ZIP** para descarga masiva, o **Abrir carpeta output** para acceder directamente

### Output

```
<carpeta_indicada>/
└── Procesadas/
    ├── imagen1.jpg
    ├── imagen2.jpg
    └── ...
```

Si se desactiva la opcion de subcarpeta, los archivos se guardan en la misma carpeta de entrada.

---

## Herramienta 3: Comprimir Imagenes

Reduce el peso de imagenes sin perdida visible, con ajuste automatico de calidad si el resultado supera el tamano objetivo.

**Pagina Streamlit:** `Comprimir Imagenes` (menu lateral)

### Pasos en la UI

1. En el panel lateral, ingresar la ruta completa a la carpeta con las imagenes
2. Configurar los parametros de compresion:

| Parametro | Descripcion | Valor por defecto |
|---|---|---|
| Formato de salida | JPEG o WebP | JPEG |
| Calidad | Calidad inicial (se reduce automaticamente si es necesario) | 85 |
| Tamano maximo objetivo (MB) | Limite de peso por imagen | 0.5 MB |
| Procesar subcarpetas (recursivo) | Incluye todas las subcarpetas | No |
| Reemplazar original | Sobreescribe el original si el formato coincide | No |

3. Hacer clic en **Comprimir imagenes**
4. Revisar las metricas: total / comprimidas / saltadas / errores
5. Revisar la reduccion total en MB y porcentaje
6. Usar el boton **Abrir carpeta** para ver los archivos resultantes

### Comportamiento sobre los archivos originales

| Situacion | Comportamiento |
|---|---|
| Formato de salida diferente al original (ej: PNG → JPEG) | El original se elimina automaticamente |
| Formato de salida igual al original + "Reemplazar original" activo | El original se sobreescribe |
| Formato igual + "Reemplazar original" inactivo | Se crea el archivo nuevo; el original se conserva |
| El archivo comprimido ya existe | Se salta (skipped), no se reprocesa |

---

## Formatos de imagen soportados

| Herramienta | Formatos de entrada |
|---|---|
| Clasificador | `.jpg`, `.jpeg`, `.png`, `.webp`, `.avif` |
| Centrar y Redimensionar | `.jpg`, `.jpeg`, `.png`, `.webp`, `.avif` |
| Comprimir Imagenes | `.jpg`, `.jpeg`, `.png`, `.webp` |

---

## Notas operativas

| Situacion | Comportamiento | Solucion |
|---|---|---|
| GPU con CUDA disponible | El clasificador la usa automaticamente | Ninguna, es automatico |
| Sin GPU | El clasificador corre en CPU (mas lento) | Esperar; funciona igual |
| Carpeta sin imagenes validas | El pipeline lanza error y lo muestra en la UI | Verificar la ruta y el contenido de la carpeta |
| Primera ejecucion del clasificador | Descarga modelo CLIP ViT-L-14 (~900 MB) | Requiere conexion a internet; las siguientes usan cache |
| Imagen sin contenido detectable (fondo completamente blanco) | `center_and_resize` devuelve la imagen redimensionada tal cual | Esperado; no es un error |
| Imagen con canal de transparencia (RGBA/PNG) | Se compone sobre fondo blanco antes de procesar | Automatico en todas las herramientas |
