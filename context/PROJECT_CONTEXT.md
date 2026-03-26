# image_toolkit — Contexto del Proyecto

## Que es

Toolkit de procesamiento de imagenes para Marketplace, con interfaz web local construida en Streamlit.
Agrupa en una sola aplicacion tres herramientas independientes: clasificacion automatica de imagenes de vehiculos usando similitud visual con CLIP, centrado y redimensionado con deteccion de bounding box, y compresion de imagenes con control de calidad y formato.

El proyecto evolucion a partir de un pipeline unico de clasificacion (image_handling) hacia un toolkit
multi-herramienta donde cada pagina de Streamlit encapsula una capacidad distinta de procesamiento de imagenes.

## Estado (2026-03-26)

### Completado
- Clasificador de imagenes con CLIP (ViT-L-14): seleccion automatica de imagen principal y galeria
- Centrar y Redimensionar: deteccion de bounding box y exportacion con parametros configurables
- Comprimir Imagenes: reduccion de peso con control de calidad, formato JPEG/WebP y descarga masiva

### En progreso
- (ninguno activo)

### Por hacer
- Identificacion de tipo de moto (Naked, Doble proposito, etc.)

## Que hace

Cada herramienta del toolkit opera de forma independiente sobre una carpeta de imagenes:

1. **Clasificador**: usa CLIP para comparar imagenes contra referencias positivas/negativas y seleccionar la imagen principal (tres cuartos frontal, fondo claro) y ordenar la galeria por score
2. **Centrar y Redimensionar**: detecta el vehiculo en cada imagen via threshold de pixeles no-blancos, recorta al bounding box, escala manteniendo aspect ratio y centra en un canvas blanco con dimensiones configurables
3. **Comprimir Imagenes**: convierte imagenes a JPEG o WebP, reduce calidad progresivamente si el resultado supera el tamano maximo objetivo, y elimina el original cuando cambia el formato

## Flujo por herramienta

### Clasificador

```text
Carpeta de imagenes
  → Preprocesamiento: center_and_resize (1100x1000 px, carpeta temporal)
  → Carga modelo CLIP ViT-L-14 + referencias positivas + referencias negativas
  → Score por imagen: (0.7 * sim_centroide_pos + 0.3 * sim_max_pos) - (0.7 * sim_centroide_neg)
  → Rank por score → imagen principal (rank 1) + galeria (resto)
  → output/imagen_principal.jpg + output/galeria1.jpg, galeria2.jpg, ...
```

### Centrar y Redimensionar

```text
Carpeta de imagenes
  → Convertir a RGBA, componer sobre fondo blanco
  → GaussianBlur(radius=2) para suavizar ruido
  → Threshold sobre array NumPy → bounding box del vehiculo
  → Recortar → escalar con aspect ratio + padding configurable
  → Centrar en canvas blanco de target_width x target_height
  → Guardar JPEG en carpeta/Procesadas/ (o en la misma carpeta)
  → Descarga masiva en ZIP
```

### Comprimir Imagenes

```text
Carpeta de imagenes (con opcion recursiva)
  → Convertir modo RGBA/P a RGB con fondo blanco (para JPEG)
  → Guardar en JPEG u WebP con calidad inicial (85 recomendado)
  → Si peso > max_size_mb: reducir calidad en pasos de 5 hasta minimo 70
  → Eliminar original si cambio el formato (ej: PNG → JPEG)
  → Reporte: total / comprimidas / saltadas / errores + reduccion total en MB
```

## Arquitectura

```
image_toolkit/
├── app.py                              # Entry point Streamlit — navegacion entre paginas
├── Toolkit de imagenes.bat             # Lanzador con doble clic (Windows)
├── requirements.txt
├── context/
│   ├── PROJECT_CONTEXT.md
│   └── SOP.md
├── pages/                              # Paginas de la app Streamlit
│   ├── inicio.py                       # Pantalla de bienvenida con descripcion de herramientas
│   ├── clasificador.py                 # UI del clasificador CLIP
│   ├── centrar_redimensionar.py        # UI de centrar y redimensionar
│   └── comprimir_imagenes.py           # UI de comprimir imagenes
├── src/
│   ├── core/                           # Logica de negocio sin dependencias de Streamlit
│   │   ├── classify_pipeline.py        # Pipeline completo CLIP (preprocesar → score → exportar)
│   │   ├── centrar_y_redimensionar.py  # Funcion center_and_resize
│   │   └── compress_images.py          # Funciones compress_image y compress_images_in_folder
│   └── data/
│       ├── references/
│       │   ├── positive/               # Imagenes de referencia correctas (tres cuartos frontal)
│       │   └── negative/               # Imagenes de referencia incorrectas (lateral, trasera, etc.)
│       └── imagenes_con_marcos/        # [uso especifico — ver scripts/]
├── scripts/                            # Scripts de linea de comandos (alternativos a la UI)
│   ├── classify_pipeline.py
│   ├── centrar_y_redimensionar.py
│   └── componer_sobre_plantilla.py
└── notebooks/
    └── clip_visual_similarity_references.ipynb
```

| Archivo | Funcion |
|---|---|
| `app.py` | Configura la app Streamlit y registra las paginas de navegacion |
| `pages/clasificador.py` | Interfaz del clasificador: input, barra de progreso, vista de imagen principal, galeria y tabla de scores |
| `pages/centrar_redimensionar.py` | Interfaz de centrado: parametros de salida (ancho, alto, padding, threshold), preview en grilla, descarga ZIP |
| `pages/comprimir_imagenes.py` | Interfaz de compresion: formato, calidad, tamano maximo, modo recursivo, metricas de reduccion |
| `src/core/classify_pipeline.py` | Pipeline CLIP: preprocesar → cargar modelo → score → seleccionar → exportar a output/ |
| `src/core/centrar_y_redimensionar.py` | `center_and_resize()`: deteccion de contenido via threshold NumPy, recorte y centrado en canvas |
| `src/core/compress_images.py` | `compress_image()` y `compress_images_in_folder()`: compresion con ajuste automatico de calidad |

## Output por herramienta

| Herramienta | Salida |
|---|---|
| Clasificador | `<carpeta>/output/imagen_principal.jpg` + `galeria1.jpg`, `galeria2.jpg`, ... |
| Centrar y Redimensionar | `<carpeta>/Procesadas/*.jpg` (o en la misma carpeta si se desactiva subcarpeta); descarga ZIP disponible en UI |
| Comprimir Imagenes | Archivos `.jpg` o `.webp` en la misma ubicacion del original; originales eliminados si cambia el formato |

## Stack tecnico

| Tecnologia | Uso |
|---|---|
| Python 3.10+ | Lenguaje principal |
| Streamlit 1.55.0 | Interfaz web local multi-pagina |
| open_clip_torch 3.3.0 | Modelo CLIP ViT-L-14 para similitud visual |
| torch 2.11.0 | Motor de deep learning (CLIP) |
| torchvision 0.26.0 | Transformaciones de imagenes para CLIP |
| Pillow 12.1.1 | Lectura, transformacion y guardado de imagenes |
| NumPy 2.4.3 | Deteccion de bounding box via operaciones sobre arrays |
| pandas 2.3.3 | Tabla de scores del clasificador |

## Requisitos

- Python 3.10+
- GPU con CUDA opcional (mejora la velocidad del clasificador; funciona en CPU)
- Primera ejecucion del clasificador descarga el modelo CLIP ViT-L-14 (~900 MB desde internet)
- Las herramientas de centrado y compresion no requieren descarga de modelos
