# Pipeline de Clasificación de Imágenes de Motos

Selecciona automáticamente la mejor foto principal y organiza la galería de imágenes de motocicletas usando similitud visual con CLIP. Puede ejecutarse desde la línea de comandos, desde un notebook Jupyter o desde una interfaz web local con Streamlit.

---

## Tabla de contenidos

1. [Descripción general](#descripción-general)
2. [Qué es CLIP y cómo se usa aquí](#qué-es-clip-y-cómo-se-usa-aquí)
3. [Qué es Streamlit y por qué se usa](#qué-es-streamlit-y-por-qué-se-usa)
4. [Requisitos e instalación](#requisitos-e-instalación)
5. [Estructura del proyecto](#estructura-del-proyecto)
6. [Cómo ejecutar el proyecto](#cómo-ejecutar-el-proyecto)
   - [Opción A — Interfaz web Streamlit (recomendada)](#opción-a--interfaz-web-streamlit-recomendada)
   - [Opción B — Línea de comandos](#opción-b--línea-de-comandos)
   - [Opción C — Notebook Jupyter](#opción-c--notebook-jupyter)
7. [El flujo completo del pipeline](#el-flujo-completo-del-pipeline)
8. [Sistema de referencias](#sistema-de-referencias)
9. [Fórmula de scoring](#fórmula-de-scoring)
10. [Procesamiento de imagen](#procesamiento-de-imagen)
11. [Archivos de salida](#archivos-de-salida)
12. [Formatos de imagen soportados](#formatos-de-imagen-soportados)
13. [Notas y comportamiento](#notas-y-comportamiento)

---

## Descripción general

Un marketplace de motos necesita que cada listado tenga una **imagen principal** clara: la moto fotografiada en tres cuartos frontal (vista desde el frente-izquierdo), sobre fondo blanco, sin recortes. Cuando un proveedor entrega 15 o 20 fotos por modelo, elegir la correcta a mano lleva tiempo y es inconsistente.

Este pipeline automatiza ese proceso en cinco pasos:

1. Preprocesa todas las imágenes (las centra y estandariza el canvas).
2. Carga el modelo CLIP y las imágenes de referencia.
3. Calcula un score numérico para cada imagen comparándola visualmente con las referencias.
4. Selecciona la imagen con mayor score como principal y organiza el resto como galería.
5. Exporta todo a una carpeta `output/` con nombres estandarizados.

---

## Qué es CLIP y cómo se usa aquí

**CLIP** (Contrastive Language–Image Pretraining) es un modelo de visión computacional desarrollado por OpenAI que aprende a relacionar imágenes con texto. Internamente convierte cualquier imagen en un vector numérico de alta dimensión (un "embedding") que representa su contenido visual de forma compacta.

La propiedad clave de estos embeddings es geométrica: dos imágenes visualmente similares producen vectores que apuntan en direcciones parecidas en ese espacio. La **similitud coseno** entre dos vectores mide qué tan parecidas son las imágenes: un valor de 1.0 indica imágenes idénticas; valores cercanos a 0.9 indican imágenes muy similares visualmente.

### Por qué no se usa CLIP con texto (zero-shot)

El enfoque más común con CLIP es comparar imágenes contra descripciones de texto como `"motorcycle in three-quarter front view"`. El problema es que esas descripciones son ambiguas: CLIP no distingue bien entre un tres cuartos frontal izquierdo y uno derecho, ni entiende que la moto debe aparecer completa, centrada y con el faro visible.

### El enfoque que usa este proyecto: similitud imagen-imagen

En vez de comparar contra texto, el pipeline compara cada imagen candidata contra un conjunto de **imágenes de referencia** que ya se sabe que son correctas. Esto funciona mejor porque:

- Las referencias codifican implícitamente todos los criterios al mismo tiempo: ángulo, dirección, fondo limpio, vehículo completo.
- Agregar más referencias al sistema mejora la precisión sin cambiar ninguna línea de código.
- La comparación imagen-imagen captura sutilezas visuales que el texto no puede describir con precisión.

### Modelo utilizado

El proyecto usa **ViT-L-14** preentrenado en el dataset `laion2b_s32b_b82k` a través de la librería `open_clip_torch`. Esta variante grande de CLIP produce embeddings de mayor calidad que la variante ViT-B-32, con el costo de requerir más memoria y tiempo de carga.

---

## Qué es Streamlit y por qué se usa

**Streamlit** es una librería de Python que permite crear aplicaciones web interactivas sin necesidad de escribir HTML, CSS ni JavaScript. Con solo agregar llamadas a funciones como `st.text_input()`, `st.button()` o `st.image()`, Streamlit genera automáticamente una interfaz visual que se ejecuta en el navegador.

La aplicación corre completamente en local — no requiere internet ni servidor externo. Al ejecutar `streamlit run app.py`, Streamlit levanta un servidor local y abre la interfaz en el navegador en `http://localhost:8501`.

### Por qué se agregó Streamlit a este proyecto

El pipeline originalmente se exploraba en un notebook Jupyter y luego se ejecutaba desde la línea de comandos. Streamlit se agregó para:

- Permitir usar el pipeline sin abrir una terminal ni recordar argumentos.
- Ver las imágenes de resultado directamente en el navegador, organizadas en principal y galería.
- Ver los scores CLIP de cada imagen en una tabla expandible.
- Abrir la carpeta `output/` con un clic desde la misma interfaz.
- Que cualquier persona del equipo pueda usar la herramienta sin conocimientos de Python.

---

## Requisitos e instalación

### Prerequisitos

- Python 3.10 o superior
- Git (para clonar el repositorio)

### Instalación

Clona el repositorio y crea un entorno virtual:

```bash
git clone <url-del-repositorio>
cd image_handling

python -m venv venv
```

Activa el entorno virtual:

```bash
# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

Instala las dependencias:

```bash
pip install open-clip-torch torch torchvision pillow pandas numpy streamlit
```

Versiones usadas en este proyecto:

| Librería          | Versión  | Propósito                                      |
|-------------------|----------|------------------------------------------------|
| `open_clip_torch` | 3.3.0    | Modelo CLIP para generar embeddings de imágenes|
| `torch`           | 2.10.0   | Motor de deep learning (CPU o CUDA)            |
| `torchvision`     | 0.25.0   | Utilidades de transformación de imágenes       |
| `pillow`          | 12.1.1   | Lectura, manipulación y guardado de imágenes   |
| `pandas`          | 2.3.3    | Manejo de tablas de scores y rankings          |
| `numpy`           | 2.4.2    | Operaciones sobre arrays de píxeles            |
| `streamlit`       | 1.55.0   | Interfaz web local                             |

> La primera vez que se ejecuta el pipeline, CLIP descarga el modelo desde internet (~900 MB para ViT-L-14). Las ejecuciones siguientes usan la versión en caché.

---

## Estructura del proyecto

```
image_handling/
├── app.py                          # Interfaz web Streamlit
├── launch.bat                      # Lanzador con doble clic (Windows)
├── README.md
├── .env                            # Variables de entorno (no versionado)
├── .gitignore
│
├── notebooks/
│   └── clip_visual_similarity_references.ipynb   # Notebook de exploración original
│
├── scripts/
│   ├── classify_pipeline.py        # Pipeline completo (núcleo del sistema)
│   └── centrar_y_redimensionar.py  # Módulo de preprocesamiento de imágenes
│
└── src/
    └── data/
        └── references/
            ├── positive/           # Imágenes que SÍ son principal correcta
            └── negative/           # Imágenes que NO son principal (ángulos a penalizar)
```

### Descripción de los archivos principales

| Archivo | Descripción |
|---|---|
| `app.py` | Interfaz Streamlit. Llama a `run_pipeline()` y muestra resultados visualmente. |
| `scripts/classify_pipeline.py` | Contiene todos los pasos del pipeline: preprocesamiento, carga de CLIP, scoring, selección y exportación. También puede ejecutarse directamente desde la terminal. |
| `scripts/centrar_y_redimensionar.py` | Función `center_and_resize()` que recorta el vehículo por bounding box y lo centra en un canvas blanco estandarizado. |
| `notebooks/clip_visual_similarity_references.ipynb` | Notebook original donde se desarrolló y validó el enfoque. Útil para experimentar con parámetros o visualizar resultados paso a paso. |
| `src/data/references/positive/` | Imágenes de referencia que el sistema debe imitar: tres cuartos frontal derecho, fondo limpio, vehículo completo. |
| `src/data/references/negative/` | Imágenes que el sistema debe penalizar: laterales, traseras, tres cuartos izquierdo, aereas, etc. |
| `launch.bat` | Script de Windows que activa el entorno virtual y lanza Streamlit con doble clic. |

---

## Cómo ejecutar el proyecto

### Opción A — Interfaz web Streamlit (recomendada)

**Método 1: doble clic (Windows)**

Abre el archivo `launch.bat` con doble clic. Se abrirá una ventana de terminal y luego el navegador en `http://localhost:8501`.

**Método 2: desde la terminal**

```bash
# Desde la carpeta raíz del proyecto, con el entorno virtual activado
streamlit run app.py
```

Una vez abierta la interfaz:

1. En el panel izquierdo (sidebar), escribe la ruta completa a la carpeta que contiene las imágenes a clasificar.
   Ejemplo: `C:\fotos\honda_cb500`
2. Haz clic en el botón **Ejecutar pipeline**.
3. Espera a que la barra de progreso llegue al 100%.
4. Los resultados se muestran en la pantalla principal:
   - **Imagen principal**: la foto seleccionada con su score CLIP.
   - **Galería**: el resto de imágenes, ordenadas por score, en una grilla de 4 columnas.
   - **Tabla completa de scores**: desplegable con todos los valores numéricos.
   - **Botón "Abrir carpeta output"**: abre el explorador de archivos directamente en la carpeta de salida.

### Opción B — Línea de comandos

```bash
python scripts/classify_pipeline.py "C:/ruta/a/la/carpeta"
```

El pipeline imprime el progreso paso a paso y al finalizar muestra el nombre de la imagen principal, el tamaño de la galería y la ruta del output.

Opciones adicionales disponibles al ejecutar directamente el script (editando los valores por defecto en `classify_pipeline.py`):

| Parámetro en el código | Valor por defecto | Descripción |
|---|---|---|
| `target_width` | `1100` | Ancho del canvas de preprocesamiento |
| `target_height` | `1000` | Alto del canvas de preprocesamiento |
| `dup_threshold` | `0.95` | Umbral de similitud para considerar near-duplicates |
| `min_gallery` | `10` | Número mínimo esperado de imágenes en la galería |

### Opción C — Notebook Jupyter

```bash
jupyter notebook notebooks/clip_visual_similarity_references.ipynb
```

El notebook está dividido en secciones numeradas:

| Sección | Contenido |
|---|---|
| 1. Setup | Carga del modelo CLIP y configuración de rutas |
| 2. Cargar referencias | Lee y codifica las imágenes de referencia positivas y negativas |
| 3. Visualizar referencias | Muestra las referencias con borde verde (positivas) y rojo (negativas) |
| 4. Función de scoring | Define `score_image()` con la fórmula completa |
| 5. Probar imagen individual | Celda para probar el score de una sola imagen |
| 6. Procesar carpeta completa | `rank_folder()`: procesa todas las imágenes y muestra la tabla de ranking |
| 7. Visualizar top candidatas | Muestra las 5 mejores candidatas con sus scores |
| 8. Selección de principal y galería | `select_principal_and_gallery()`: elige la imagen final |
| 9. Ajustar el sistema de referencias | Guía para mejorar la precisión del sistema |
| 10. Near-duplicate detection | Detecta imágenes casi idénticas en la carpeta |
| 11. Exportar a output/ | Copia los archivos seleccionados con nombres estandarizados |

Para usar el notebook con tus propias imágenes, cambia la variable `FOLDER` en la celda 3:

```python
FOLDER = r"C:\ruta\a\tu\carpeta\de\fotos"
```

---

## El flujo completo del pipeline

```
Carpeta de entrada (imágenes originales)
         |
         v
  [Paso 1] center_and_resize()
  Detecta bounding box del vehículo,
  recorta fondo sobrante, escala y
  centra en canvas blanco 1100x1000 px
         |
         v
  [Paso 2] Cargar modelo CLIP (ViT-L-14)
  + referencias positivas (n=14)
  + referencias negativas (n=19)
  → embeddings y centroides
         |
         v
  [Paso 3] score_image() por cada imagen
  Calcula: sim_centroide_pos, sim_max_pos,
  sim_centroide_neg → score final
         |
         v
  [Paso 4] Ranking por score descendente
  Principal = rank #1
  Galería = todas las demás
         |
         v
  [Paso 5] export_output()
  output/imagen_principal.jpg
  output/galeria1.jpg
  output/galeria2.jpg
  ...
```

---

## Sistema de referencias

El sistema funciona con dos carpetas de imágenes de referencia ubicadas en `src/data/references/`:

### Referencias positivas (`positive/`)

Son imágenes que ya se sabe que son fotos principales correctas. Características ideales para las referencias positivas:

- Ángulo tres cuartos frontal (el faro y rueda delantera aparecen en el lado derecho de la imagen).
- Vehículo completo en el encuadre.
- Fondo blanco o muy claro.
- Incluir variedad de tipos de moto: scooter, naked, enduro, deportiva, custom.

Actualmente hay **14 referencias positivas**. Con 8-15 imágenes bien curadas el sistema funciona bien.

### Referencias negativas (`negative/`)

Son imágenes de ángulos que se quieren penalizar. Actualmente hay **19 referencias negativas**, que incluyen:

- Tres cuartos frontal izquierdo (orientación invertida).
- Vista lateral pura.
- Vista trasera.
- Tres cuartos trasero.
- Imágenes con fondo oscuro o de color.

### Cómo mejorar el sistema

Para mejorar la selección de la imagen principal:

- Agrega imágenes a `src/data/references/positive/` — no hace falta cambiar ningún código.
- Incluye variedad: distintos modelos, colores, fondos ligeramente distintos.

Para mejorar la penalización de ángulos incorrectos:

- Agrega imágenes a `src/data/references/negative/` con los ángulos que el sistema sigue confundiendo.

Para ajustar la intensidad de la penalización, cambia el parámetro `neg_penalty` en `score_image()` dentro de `scripts/classify_pipeline.py`:

```python
# 0.7 = penalización fuerte (default)
# 0.4-0.5 = penalización moderada
# 0.2-0.3 = penalización suave
neg_penalty: float = 0.7
```

---

## Fórmula de scoring

Para cada imagen candidata se calcula:

```
score_pos = (0.7 × sim_centroide_pos) + (0.3 × sim_max_pos)

score_final = score_pos − (0.7 × sim_centroide_neg)
```

Donde:

| Variable | Descripción |
|---|---|
| `sim_centroide_pos` | Similitud coseno entre la imagen y el centroide (promedio) de las referencias positivas |
| `sim_max_pos` | Similitud coseno máxima contra cualquier referencia positiva individual |
| `sim_centroide_neg` | Similitud coseno entre la imagen y el centroide de las referencias negativas |

Una foto trasera o lateral tiene un `score_pos` moderado pero una penalización alta, resultando en un score final bajo. Una foto tres cuartos frontal correcta tiene un `score_pos` alto y una penalización baja, resultando en el score final más alto.

La tabla completa de scores que muestra la interfaz Streamlit incluye todas estas columnas para facilitar el análisis.

---

## Procesamiento de imagen

Antes de calcular el score CLIP, cada imagen pasa por la función `center_and_resize()` del módulo `scripts/centrar_y_redimensionar.py`. Los pasos son:

1. **Preparación del canal alfa**: convierte la imagen a RGBA y la compone sobre fondo blanco para que los píxeles transparentes no se detecten como contenido.
2. **Reducción de ruido**: aplica un blur gaussiano leve (radio 2) para ignorar artefactos JPEG en los bordes.
3. **Detección de contenido**: marca como contenido cualquier píxel donde al menos un canal RGB sea inferior a 240 (no es fondo blanco puro).
4. **Bounding box**: calcula el rectángulo mínimo que encierra todos los píxeles de contenido.
5. **Recorte**: elimina el fondo sobrante alrededor del vehículo.
6. **Escalado**: redimensiona el recorte al máximo tamaño que quepa en el canvas respetando el aspect ratio, con un margen del 5% en cada lado.
7. **Canvas final**: pega el vehículo centrado sobre un canvas blanco de `1100 × 1000 px` (configurable).

El resultado es una imagen estandarizada que elimina variaciones de encuadre entre fotos de diferentes fuentes antes de pasarlas a CLIP.

> Si la moto tiene un fondo oscuro o de color, la detección de contenido puede no funcionar correctamente, ya que todos los píxeles se interpretarían como contenido. El sistema está optimizado para imágenes con fondo blanco o muy claro.

---

## Archivos de salida

Las imágenes se guardan en la subcarpeta `output/` dentro de la carpeta que se le indica al pipeline:

```
tu_carpeta/
├── foto1.jpg                 # imágenes originales (sin modificar)
├── foto2.jpg
├── ...
└── output/
    ├── imagen_principal.jpg  # la imagen con el mayor score CLIP
    ├── galeria1.jpg          # segunda imagen por score
    ├── galeria2.jpg          # tercera imagen por score
    └── ...
```

- Todas las imágenes de salida están preprocesadas (centradas, fondo blanco, canvas estandarizado).
- Se guardan en formato JPEG con calidad 90.
- La carpeta `output/` se limpia y recrea en cada ejecución del pipeline.

---

## Formatos de imagen soportados

El pipeline procesa archivos con las extensiones `.jpg`, `.jpeg`, `.png`, `.webp` y `.avif`. Los archivos en otros formatos se omiten.

---

## Notas y comportamiento

### Uso de GPU

Si hay una GPU compatible con CUDA disponible, el modelo CLIP la usa automáticamente. En CPU el pipeline es más lento (especialmente la carga del modelo), pero funciona correctamente. El dispositivo detectado se muestra en la consola al inicio de la ejecución.

### Primera ejecución

La primera vez que se ejecuta el pipeline, `open_clip` descarga el modelo ViT-L-14 desde internet (aproximadamente 900 MB). A partir de la segunda ejecución usa la versión en caché y el inicio es mucho más rápido.

### Carpeta temporal

Durante el procesamiento se crea una carpeta temporal en el sistema para almacenar las imágenes preprocesadas. Esta carpeta se elimina automáticamente al finalizar el pipeline, tanto si termina con éxito como si ocurre un error.

### Near-duplicate detection

El módulo `detect_near_duplicates()` en `classify_pipeline.py` puede detectar pares de imágenes con similitud CLIP superior a un umbral (por defecto 0.95). En el notebook esta función se usa como herramienta de análisis. En el pipeline de producción actual, todas las imágenes distintas a la principal se incluyen en la galería sin filtrado de duplicados.

### Imagen principal no encontrada

Si la carpeta de entrada no contiene imágenes válidas, el pipeline lanza un error `FileNotFoundError` con la ruta de la carpeta afectada.
