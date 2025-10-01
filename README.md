# OllinTag - Guided Image Label

Herramienta web para clasificación y anotación de imágenes con bounding boxes y etiquetas personalizadas. Compatible con formato COCO JSON para entrenamiento de modelos de visión computarizada.

## Características

- Clasificación visual interactiva con bounding boxes
- Etiquetas personalizadas y comentarios por anotación
- Importación de lotes de imágenes vía ZIP
- Exportación en formato COCO JSON o XML
- Navegación inteligente entre imágenes
- Auto-guardado temporal durante la sesión

## Requisitos

**Navegadores soportados:**
- Google Chrome 90+ (recomendado)
- Mozilla Firefox 88+
- Microsoft Edge 90+
- Safari 14+ (macOS)

**Límites de archivos:**
- ZIP: máximo 200 MB
- Formatos: JPG, JPEG, PNG, BMP, TIFF
- JSON COCO: máximo 200 MB

## Instalación

### Clonar el repositorio

```bash
git clone https://github.com/UrieelM/Image_Sorter.git
cd Image_Sorter
```

### Instalar dependencias

```bash
pip install -r requirements.txt
```

### Ejecutar la aplicación

```bash
streamlit run OllinTag.py
```

La aplicación se abrirá automáticamente en tu navegador en `http://localhost:8501`

### Configuración recomendada del navegador

- Chrome/Edge: Habilitar cookies y almacenamiento local en Configuración → Privacidad y seguridad
- Firefox: Permitir cookies en Preferencias → Privacidad y seguridad
- Safari: Desactivar "Evitar seguimiento entre sitios" si hay problemas

## Guía de Uso

### Flujo de Trabajo Básico

#### 1. Preparar y cargar imágenes

1. Comprime tus imágenes en un archivo ZIP (máx. 200 MB)
2. En el panel "Configuración", haz clic en "Browse files"
3. Selecciona tu archivo ZIP
4. Haz clic en "Cargar Imágenes"
5. Verifica las métricas en la parte superior (Total, Anotadas, Pendientes)

#### 2. Configurar etiquetas personalizadas

1. Ve a "Etiquetas Personalizadas" en el panel izquierdo
2. Elimina "Default Label" si no la necesitas
3. Escribe el nombre de tu categoría en "Nueva etiqueta"
4. Haz clic en "Agregar Etiqueta"
5. Repite para cada categoría necesaria

**Ejemplo:** Stenosis, Normal, Calcificación, Oclusión

#### 3. Anotar imágenes

1. Haz clic y arrastra sobre la imagen para crear un bounding box
2. Suelta el mouse para finalizar
3. En "Asignar Etiquetas y Comentarios":
   - Selecciona la etiqueta del dropdown
   - Añade comentarios opcionales
4. **Importante:** Haz clic en "Guardar Imagen Actual" antes de cambiar de imagen

#### 4. Navegar entre imágenes

- **Anterior/Siguiente:** Navegación secuencial
- **Siguiente sin anotar:** Salta a la próxima imagen pendiente
- **Ir a imagen:** Selección directa desde el dropdown

#### 5. Monitorear progreso

La barra superior muestra:
- Total de imágenes cargadas
- Imágenes anotadas
- Imágenes pendientes
- Imagen actual en trabajo

#### 6. Exportar resultados

**Opción A - Solo JSON:**
1. Haz clic en "Descargar COCO JSON"
2. Úsalo para entrenar modelos o importar en otras herramientas

**Opción B - Paquete completo:**
1. Haz clic en "Guardar Todo"
2. Haz clic en "Descargar ZIP completo"
3. Obtendrás:
   - Carpeta `images/`: imágenes originales
   - `annotations_coco.json`: archivo COCO principal
   - Carpeta `annotations_xml/`: archivos XML individuales

### Cargar proyecto existente

Si ya tienes anotaciones previas:

1. **Primero:** Carga el ZIP de imágenes
2. **Después:** En "Cargar Anotaciones", selecciona tu archivo JSON COCO
3. Haz clic en "Cargar Anotaciones"

Las imágenes aparecerán con sus bounding boxes, etiquetas y comentarios intactos.

## Solución de Problemas Comunes

### Los bounding boxes desaparecen

**Causa:** No guardar antes de navegar

**Solución:**
- Siempre usa "Guardar Imagen Actual" antes de cambiar de imagen
- Verifica el mensaje "Imagen guardada correctamente"
- Usa "Recargar Bounding Boxes" si es necesario

### Error al cargar JSON

**Problema:** JSON inválido o imágenes no coinciden

**Solución:**
1. Valida el JSON en jsonlint.com
2. Verifica que cargaste las imágenes primero
3. Asegura que los nombres de archivo coinciden exactamente

### El ZIP no se carga

**Solución:**
1. Verifica que el archivo sea menor a 200 MB
2. Confirma que solo contiene formatos soportados
3. Evita estructuras de carpetas profundas (máx. 2 niveles)
4. Divide datasets grandes en múltiples ZIPs pequeños

### Rendimiento lento

**Solución:**
1. Cierra pestañas innecesarias del navegador
2. Reduce la resolución de imágenes antes de crear el ZIP
3. Trabaja con lotes más pequeños (<500 imágenes por sesión)
4. Reinicia el navegador cada 2-3 horas en sesiones largas
5. Usa modo incógnito para evitar interferencia de extensiones

## Errores Críticos a Evitar

- **Cargar JSON antes que las imágenes:** El JSON no encontrará las referencias
- **No guardar antes de navegar:** Perderás las anotaciones de la imagen actual
- **Cerrar el navegador sin descargar:** Perderás todo el trabajo no exportado

## Privacidad

- Procesamiento local: todas las imágenes se procesan en tu navegador
- Sin envío de datos: no se transmiten imágenes a servidores externos
- Datos temporales: los archivos se eliminan al cerrar la ventana

## Licencia

MIT License - Copyright (c) 2025 Uriel Mendoza Rodríguez

### Atribuciones

Este proyecto utiliza código de [streamlit-img-label](https://github.com/lit26/streamlit-img-label) por **Tianning Li (lit26)**, bajo MIT License.

---

**Versión:** 1.0 | **Fecha:** Septiembre 2025 | **Autor:** Uriel Mendoza Rodríguez