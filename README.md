# Clasificador de Imágenes con Bounding Box

Este proyecto es una aplicación web desarrollada con Streamlit para clasificar imágenes y generar anotaciones de bounding boxes en formato COCO y XML. Permite cargar imágenes en lote, crear y editar anotaciones visualmente, gestionar etiquetas personalizadas y exportar los resultados.

## Características

- Carga de imágenes desde un archivo ZIP.
- Visualización y anotación de bounding boxes sobre las imágenes.
- Soporte para etiquetas personalizadas.
- Exportación de anotaciones en formato COCO (JSON) y Pascal VOC (XML).
- Importación de anotaciones COCO existentes.
- Barra lateral con configuración y logo personalizado.
- Estadísticas de progreso y navegación eficiente entre imágenes.
- Sincronización automática de anotaciones y guardado temporal.

## Requisitos

- Python 3.8+
- Streamlit
- Pillow
- streamlit_img_label

Instala las dependencias con:

```bash
pip install -r requirements.txt
```

## Uso

1. Ejecuta la aplicación:
   ```bash
   streamlit run app/clasificador.py
   ```
2. En la interfaz web:
   - Sube un archivo ZIP con tus imágenes.
   - Anota las imágenes dibujando bounding boxes y asignando etiquetas.
   - Descarga las anotaciones en formato COCO o XML cuando termines.

## Estructura del Proyecto

- `app/clasificador.py`: Código principal de la aplicación Streamlit.
- `requirements.txt`: Dependencias del proyecto.
- `annotations_coco.json`: Archivo de anotaciones COCO generado/exportado.

## Créditos

Desarrollado por UrielM.
