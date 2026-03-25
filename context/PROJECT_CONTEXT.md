# image_handling — Contexto del Proyecto

## Que es

Pipeline automatizado que selecciona la mejor foto principal y organiza la galeria de imagenes de motocicletas usando similitud visual con el modelo CLIP (ViT-L-14). Puede ejecutarse desde la linea de comandos, desde un notebook Jupyter o desde una interfaz web local con Streamlit.

## Problema que resuelve

Cuando un proveedor entrega 15 o 20 fotos por modelo, elegir manualmente la imagen principal correcta (moto en tres cuartos frontal derecho, fondo blanco, sin recortes) lleva tiempo y es inconsistente. Este pipeline automatiza ese proceso.

## Como funciona

El sistema usa **similitud imagen-imagen** con CLIP: cada imagen candidata se compara contra un conjunto de imagenes de referencia que ya se sabe que son correctas. Esto captura sutilezas visuales (angulo, fondo limpio, encuadre) que el texto no puede describir con precision.

### Flujo del pipeline

1. Preprocesa todas las imagenes (centra y estandariza el canvas a 1100x1000 px)
2. Carga el modelo CLIP ViT-L-14 y las imagenes de referencia
3. Calcula un score numerico para cada imagen comparandola visualmente con las referencias
4. Selecciona la imagen con mayor score como principal
5. Exporta todo a una carpeta `output/` con nombres estandarizados

### Formula de scoring

```
score_pos   = (0.7 x sim_centroide_pos) + (0.3 x sim_max_pos)
score_final = score_pos - (0.7 x sim_centroide_neg)
```

## Arquitectura

```
image_handling/
├── app.py                          # Interfaz web Streamlit
├── launch.bat                      # Lanzador con doble clic (Windows)
├── notebooks/
│   └── clip_visual_similarity_references.ipynb
├── scripts/
│   ├── classify_pipeline.py        # Pipeline completo (nucleo del sistema)
│   └── centrar_y_redimensionar.py  # Preprocesamiento de imagenes
└── src/
    └── data/
        └── references/
            ├── positive/           # Imagenes que SI son principal correcta (14 refs)
            └── negative/           # Imagenes que NO son principal (19 refs)
```

## Referencias del sistema

- **Positivas** (`positive/`): tres cuartos frontal derecho, vehiculo completo, fondo blanco o claro. Actualmente 14 imagenes.
- **Negativas** (`negative/`): laterales, traseras, tres cuartos izquierdo, fondos oscuros. Actualmente 19 imagenes.

Para mejorar la precision: agregar imagenes a cualquiera de las carpetas de referencias sin cambiar codigo.

## Requisitos

- Python 3.10+
- GPU con CUDA (opcional, mejora velocidad)
- Primera ejecucion descarga el modelo ViT-L-14 (~900 MB)

## Dependencias

| Libreria | Version | Proposito |
|---|---|---|
| `open_clip_torch` | 3.3.0 | Modelo CLIP |
| `torch` | 2.10.0 | Motor de deep learning |
| `torchvision` | 0.25.0 | Transformaciones de imagenes |
| `pillow` | 12.1.1 | Lectura y guardado de imagenes |
| `pandas` | 2.3.3 | Tablas de scores |
| `streamlit` | 1.55.0 | Interfaz web local |

## Output

Las imagenes se guardan en la subcarpeta `output/` dentro de la carpeta procesada:

```
output/
├── imagen_principal.jpg  # imagen con el mayor score CLIP
├── galeria1.jpg
├── galeria2.jpg
└── ...
```

Todas las imagenes de salida estan preprocesadas (centradas, fondo blanco, canvas estandarizado). La carpeta `output/` se limpia y recrea en cada ejecucion.
