import streamlit as st
import os
import json
import zipfile
import tempfile
import shutil
from datetime import datetime
from streamlit_img_label import st_img_label
from streamlit_img_label.manage import ImageManager, ImageDirManager
from PIL import Image
import xml.etree.ElementTree as ET
import io

class COCOAnnotationManager:
    def __init__(self):
        self.coco_data = {
            "images": [],
            "annotations": [],
            "categories": []
        }
        self.annotation_id_counter = 1
        self.image_id_counter = 1
        self.category_id_counter = 1
        self.category_name_to_id = {}
        self.image_annotations = {}  # filename -> annotations

    def add_category(self, name):
        if name not in self.category_name_to_id:
            self.category_name_to_id[name] = self.category_id_counter
            self.coco_data["categories"].append({
                "id": self.category_id_counter,
                "name": name,
                "supercategory": ""
            })
            self.category_id_counter += 1
        return self.category_name_to_id[name]

    def get_image_id_by_filename(self, filename):
        for img in self.coco_data["images"]:
            if img["file_name"] == filename:
                return img["id"]
        return None

    def add_or_update_image_annotations(self, filename, width, height, annotations):
        """Agregar o actualizar anotaciones para una imagen específica"""
        # Buscar si la imagen ya existe
        image_id = self.get_image_id_by_filename(filename)
        
        if image_id is None:
            # Crear nueva imagen
            image_info = {
                "id": self.image_id_counter,
                "file_name": filename,
                "width": width,
                "height": height
            }
            self.coco_data["images"].append(image_info)
            image_id = self.image_id_counter
            self.image_id_counter += 1
        else:
            # Actualizar dimensiones si es necesario
            for img in self.coco_data["images"]:
                if img["id"] == image_id:
                    img["width"] = width
                    img["height"] = height
                    break

        # Remover anotaciones existentes para esta imagen
        self.coco_data["annotations"] = [
            ann for ann in self.coco_data["annotations"] 
            if ann["image_id"] != image_id
        ]

        # Agregar nuevas anotaciones
        for ann in annotations:
            category_id = self.add_category(ann["label"])
            x, y, w, h = ann["left"], ann["top"], ann["width"], ann["height"]
            annotation = {
                "id": self.annotation_id_counter,
                "image_id": image_id,
                "category_id": category_id,
                "bbox": [x, y, w, h],
                "area": w * h,
                "iscrowd": 0
            }
            self.coco_data["annotations"].append(annotation)
            self.annotation_id_counter += 1

        # Actualizar cache local
        self.image_annotations[filename] = annotations

    def get_annotations_for_image(self, filename):
        """Obtener anotaciones para una imagen específica"""
        if filename in self.image_annotations:
            return self.image_annotations[filename]
        
        # Buscar en COCO data
        image_id = self.get_image_id_by_filename(filename)
        if image_id is None:
            return []

        annotations = []
        for ann in self.coco_data["annotations"]:
            if ann["image_id"] == image_id:
                # Encontrar el nombre de la categoría
                category_name = "Unknown"
                for cat in self.coco_data["categories"]:
                    if cat["id"] == ann["category_id"]:
                        category_name = cat["name"]
                        break
                
                x, y, w, h = ann["bbox"]
                annotations.append({
                    "label": category_name,
                    "left": x,
                    "top": y,
                    "width": w,
                    "height": h
                })
        
        self.image_annotations[filename] = annotations
        return annotations

    def load_from_json(self, json_data):
        self.coco_data = json_data
        
        # Rebuild counters
        if self.coco_data["images"]:
            self.image_id_counter = max([img["id"] for img in self.coco_data["images"]]) + 1
        if self.coco_data["annotations"]:
            self.annotation_id_counter = max([ann["id"] for ann in self.coco_data["annotations"]]) + 1
        if self.coco_data["categories"]:
            self.category_id_counter = max([cat["id"] for cat in self.coco_data["categories"]]) + 1
            self.category_name_to_id = {cat["name"]: cat["id"] for cat in self.coco_data["categories"]}
        
        # Rebuild image annotations cache
        self.image_annotations = {}
        for img in self.coco_data["images"]:
            filename = img["file_name"]
            self.image_annotations[filename] = self.get_annotations_for_image(filename)

def save_xml_annotation(img_path, filename, annotations, img_width, img_height):
    """Guardar anotaciones en formato XML (para persistencia temporal)"""
    if not annotations:
        # Si no hay anotaciones, eliminar XML si existe
        xml_filename = os.path.splitext(filename)[0] + ".xml"
        xml_path = os.path.join(os.path.dirname(img_path), xml_filename)
        if os.path.exists(xml_path):
            os.remove(xml_path)
        return None
    
    root = ET.Element("annotation")
    
    folder = ET.SubElement(root, "folder")
    folder.text = "images"
    
    filename_elem = ET.SubElement(root, "filename")
    filename_elem.text = filename
    
    size = ET.SubElement(root, "size")
    width = ET.SubElement(size, "width")
    width.text = str(img_width)
    height = ET.SubElement(size, "height")
    height.text = str(img_height)
    depth = ET.SubElement(size, "depth")
    depth.text = "3"
    
    for ann in annotations:
        obj = ET.SubElement(root, "object")
        name = ET.SubElement(obj, "name")
        name.text = ann["label"]
        
        bndbox = ET.SubElement(obj, "bndbox")
        xmin = ET.SubElement(bndbox, "xmin")
        xmin.text = str(int(ann["left"]))
        ymin = ET.SubElement(bndbox, "ymin")
        ymin.text = str(int(ann["top"]))
        xmax = ET.SubElement(bndbox, "xmax")
        xmax.text = str(int(ann["left"] + ann["width"]))
        ymax = ET.SubElement(bndbox, "ymax")
        ymax.text = str(int(ann["top"] + ann["height"]))
    
    xml_filename = os.path.splitext(filename)[0] + ".xml"
    xml_path = os.path.join(os.path.dirname(img_path), xml_filename)
    
    tree = ET.ElementTree(root)
    tree.write(xml_path, encoding='utf-8', xml_declaration=True)
    return xml_path

def load_xml_annotation(xml_path):
    """Cargar anotaciones desde archivo XML"""
    if not os.path.exists(xml_path):
        return []
    
    tree = ET.parse(xml_path)
    root = tree.getroot()
    
    annotations = []
    for obj in root.findall("object"):
        name = obj.find("name").text
        bndbox = obj.find("bndbox")
        
        left = int(bndbox.find("xmin").text)
        top = int(bndbox.find("ymin").text)
        right = int(bndbox.find("xmax").text)
        bottom = int(bndbox.find("ymax").text)
        
        annotations.append({
            "label": name,
            "left": left,
            "top": top,
            "width": right - left,
            "height": bottom - top
        })
    
    return annotations

def extract_zip_to_temp(uploaded_zip):
    """Extraer ZIP a directorio temporal"""
    temp_dir = tempfile.mkdtemp()
    
    with zipfile.ZipFile(uploaded_zip, 'r') as zip_ref:
        zip_ref.extractall(temp_dir)
    
    # Buscar directorio con imágenes
    image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff'}
    image_dir = None
    
    for root, dirs, files in os.walk(temp_dir):
        image_files = [f for f in files if os.path.splitext(f.lower())[1] in image_extensions]
        if image_files:
            image_dir = root
            break
    
    return image_dir if image_dir else temp_dir

def create_download_zip(image_dir, annotations_data, format_type="both"):
    """Crear ZIP para descarga con imágenes y anotaciones"""
    zip_buffer = io.BytesIO()
    
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        # Agregar imágenes
        for file in os.listdir(image_dir):
            if file.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp', '.tiff')):
                file_path = os.path.join(image_dir, file)
                zip_file.write(file_path, f"images/{file}")
        
        # Agregar archivos XML si existen
        if format_type in ["both", "xml"]:
            for file in os.listdir(image_dir):
                if file.lower().endswith('.xml'):
                    file_path = os.path.join(image_dir, file)
                    zip_file.write(file_path, f"annotations_xml/{file}")
        
        # Agregar archivo COCO JSON
        if format_type in ["both", "coco"] and annotations_data:
            coco_json = json.dumps(annotations_data.coco_data, indent=2)
            zip_file.writestr("annotations_coco.json", coco_json)
    
    zip_buffer.seek(0)
    return zip_buffer.getvalue()

def initialize_session_state():
    """Inicializa las variables de session_state si no existen."""
    defaults = {
        "temp_dir": None,
        "files": [],
        "annotation_files": [],
        "image_index": 0,
        "custom_labels": ["Default Label"],
        "coco_manager": COCOAnnotationManager(),
        "unsaved_changes": False,
        "current_rects": [],
        "last_processed_image": None
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

def save_current_changes_if_needed():
    """Guarda cambios temporales antes de navegar o cambiar imagen."""
    if st.session_state.last_processed_image and st.session_state.current_rects is not None:
        current_file = st.session_state.last_processed_image
        img_path = os.path.join(st.session_state.temp_dir, current_file)
        img = Image.open(img_path)
        st.session_state.coco_manager.add_or_update_image_annotations(
            current_file, img.width, img.height, st.session_state.current_rects
        )
        save_xml_annotation(img_path, current_file, st.session_state.current_rects, img.width, img.height)
        xml_filename = os.path.splitext(current_file)[0] + ".xml"
        if st.session_state.current_rects and xml_filename not in st.session_state.annotation_files:
            st.session_state.annotation_files.append(xml_filename)
        elif not st.session_state.current_rects and xml_filename in st.session_state.annotation_files:
            st.session_state.annotation_files.remove(xml_filename)

def sidebar_config():
    st.image("src/grafico4.png", use_column_width=True)
    st.header("⚙️ Configuración")
    uploaded_zip = st.file_uploader(
        "Subir ZIP con imágenes", 
        type=['zip'],
        help="Sube un archivo ZIP que contenga las imágenes a clasificar"
    )
    if uploaded_zip is not None:
        if st.button("📁 Cargar Imágenes"):
            with st.spinner("Extrayendo imágenes..."):
                if st.session_state.temp_dir and os.path.exists(st.session_state.temp_dir):
                    shutil.rmtree(st.session_state.temp_dir)
                st.session_state.temp_dir = extract_zip_to_temp(uploaded_zip)
                idm = ImageDirManager(st.session_state.temp_dir)
                st.session_state.files = sorted(idm.get_all_files())
                st.session_state.annotation_files = []
                for file in st.session_state.files:
                    xml_file = os.path.splitext(file)[0] + ".xml"
                    xml_path = os.path.join(st.session_state.temp_dir, xml_file)
                    if os.path.exists(xml_path):
                        st.session_state.annotation_files.append(xml_file)
                        annotations = load_xml_annotation(xml_path)
                        if annotations:
                            img_path = os.path.join(st.session_state.temp_dir, file)
                            img = Image.open(img_path)
                            st.session_state.coco_manager.add_or_update_image_annotations(
                                file, img.width, img.height, annotations
                            )
                st.session_state.image_index = 0
                st.session_state.current_rects = []
                st.session_state.last_processed_image = None
            st.success(f"✅ Cargadas {len(st.session_state.files)} imágenes")
            st.rerun()
    st.subheader("📋 Cargar Anotaciones")
    uploaded_annotations = st.file_uploader(
        "Cargar archivo COCO JSON", 
        type=['json'],
        help="Cargar anotaciones existentes en formato COCO"
    )
    if uploaded_annotations is not None:
        if st.button("📥 Cargar Anotaciones"):
            try:
                coco_data = json.load(uploaded_annotations)
                st.session_state.coco_manager.load_from_json(coco_data)
                labels = [cat["name"] for cat in coco_data["categories"]]
                if labels:
                    st.session_state.custom_labels = labels
                if st.session_state.temp_dir:
                    for img_info in coco_data["images"]:
                        filename = img_info["file_name"]
                        annotations = st.session_state.coco_manager.get_annotations_for_image(filename)
                        if annotations:
                            img_path = os.path.join(st.session_state.temp_dir, filename)
                            if os.path.exists(img_path):
                                save_xml_annotation(
                                    img_path, filename, annotations,
                                    img_info["width"], img_info["height"]
                                )
                                xml_filename = os.path.splitext(filename)[0] + ".xml"
                                if xml_filename not in st.session_state.annotation_files:
                                    st.session_state.annotation_files.append(xml_filename)
                st.success("✅ Anotaciones cargadas correctamente")
                st.rerun()
            except Exception as e:
                st.error(f"❌ Error al cargar anotaciones: {str(e)}")
    st.markdown("---")
    st.subheader("🏷️ Etiquetas Personalizadas")
    st.write("**Etiquetas actuales:**")
    for i, label in enumerate(st.session_state.custom_labels):
        col1, col2 = st.columns([3, 1])
        with col1:
            st.text(f"• {label}")
        with col2:
            if st.button("🗑️", key=f"del_{i}", help="Eliminar etiqueta"):
                if len(st.session_state.custom_labels) > 1:
                    st.session_state.custom_labels.pop(i)
                    st.rerun()
                else:
                    st.warning("Debe mantener al menos una etiqueta")
    new_label = st.text_input("Nueva etiqueta:")
    if st.button("➕ Agregar Etiqueta"):
        if new_label and new_label not in st.session_state.custom_labels:
            st.session_state.custom_labels.append(new_label)
            st.success(f"Etiqueta '{new_label}' agregada")
            st.rerun()
        elif new_label in st.session_state.custom_labels:
            st.warning("Esta etiqueta ya existe")

def show_stats():
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total de imágenes", len(st.session_state.files))
    with col2:
        st.metric("Anotadas", len(st.session_state.annotation_files))
    with col3:
        st.metric("Pendientes", len(st.session_state.files) - len(st.session_state.annotation_files))
    with col4:
        st.metric("Imagen actual", st.session_state.image_index + 1)

def navigation_controls():
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        if st.button("⬅️ Anterior"):
            if st.session_state.image_index > 0:
                save_current_changes_if_needed()
                st.session_state.image_index -= 1
                st.session_state.unsaved_changes = False
                st.rerun()
            else:
                st.warning("Esta es la primera imagen")
    with col2:
        if st.button("➡️ Siguiente"):
            if st.session_state.image_index < len(st.session_state.files) - 1:
                save_current_changes_if_needed()
                st.session_state.image_index += 1
                st.session_state.unsaved_changes = False
                st.rerun()
            else:
                st.warning("Esta es la última imagen")
    with col3:
        if st.button("⏭️ Siguiente sin anotar"):
            save_current_changes_if_needed()
            found = False
            for i in range(st.session_state.image_index + 1, len(st.session_state.files)):
                file = st.session_state.files[i]
                xml_file = os.path.splitext(file)[0] + ".xml"
                if xml_file not in st.session_state.annotation_files:
                    st.session_state.image_index = i
                    found = True
                    st.rerun()
                    break
            if not found:
                st.info("Todas las imágenes restantes están anotadas")
    with col4:
        selected_index = st.selectbox(
            "Ir a imagen:",
            range(len(st.session_state.files)),
            index=st.session_state.image_index,
            format_func=lambda x: f"{x+1}: {st.session_state.files[x]}",
            key="file_selector"
        )
        if selected_index != st.session_state.image_index:
            save_current_changes_if_needed()
            st.session_state.image_index = selected_index
            st.session_state.unsaved_changes = False
            st.rerun()
    with col5:
        if st.button("💾 Guardar Todo"):
            save_current_changes_if_needed()
            for file in st.session_state.files:
                xml_file = os.path.splitext(file)[0] + ".xml"
                xml_path = os.path.join(st.session_state.temp_dir, xml_file)
                if os.path.exists(xml_path):
                    annotations = load_xml_annotation(xml_path)
                    if annotations:
                        img_path = os.path.join(st.session_state.temp_dir, file)
                        img = Image.open(img_path)
                        st.session_state.coco_manager.add_or_update_image_annotations(
                            file, img.width, img.height, annotations
                        )
            zip_data = create_download_zip(
                st.session_state.temp_dir, 
                st.session_state.coco_manager,
                "both"
            )
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            st.download_button(
                "📦 Descargar ZIP completo",
                data=zip_data,
                file_name=f"anotaciones_completas_{timestamp}.zip",
                mime="application/zip",
                key="download_all"
            )
            st.success("✅ Todas las anotaciones han sido guardadas")

def main():
    st.set_page_config(page_title="Clasificador de Imágenes con Bounding Box", layout="wide")
    import streamlit.components.v1 as components
    components.html("""
    <script>
    window.onbeforeunload = function() {
        return "⚠️ Estás a punto de salir o refrescar. ¿Seguro que quieres continuar?";
    };
    </script>
    """, height=0, width=0)
    st.title("Clasificador de Imágenes con Bounding Box")
    st.markdown("---")
    initialize_session_state()
    with st.sidebar:
        sidebar_config()
    if not st.session_state.files:
        st.info("👆 Por favor, sube un archivo ZIP con imágenes para comenzar")
        return
    show_stats()
    st.markdown("---")
    navigation_controls()
    if st.button("🔄 Recargar Bounding Boxes"):
        st.session_state.last_processed_image = None
    current_file = st.session_state.files[st.session_state.image_index]
    img_path = os.path.join(st.session_state.temp_dir, current_file)
    st.subheader(f"🖼️ {current_file}")
    im = ImageManager(img_path)
    img = im.get_img()
    resized_img = im.resizing_img()
    col_left, col_center, col_right = st.columns([1,2,1])
    with col_center:
        # Siempre sincronizar current_rects con el COCO manager al cambiar de imagen o tras cargar COCO
        annotations = st.session_state.coco_manager.get_annotations_for_image(current_file)
        scale_x = resized_img.width / img.width
        scale_y = resized_img.height / img.height
        st.session_state.current_rects = []
        for ann in annotations:
            st.session_state.current_rects.append({
                "left": int(ann["left"] * scale_x),
                "top": int(ann["top"] * scale_y),
                "width": int(ann["width"] * scale_x),
                "height": int(ann["height"] * scale_y),
                "label": ann.get("label", "Default Label")
            })
        st.session_state.last_processed_image = current_file
        st.session_state.unsaved_changes = False
        rects = st_img_label(resized_img, box_color="red", rects=st.session_state.current_rects, key=f"img_label_{current_file}")
    
    # Detectar cambios
    if rects != st.session_state.current_rects:
        st.session_state.current_rects = rects
        st.session_state.unsaved_changes = True
        
        # Auto-guardar cambios temporales (sin rerun para evitar bucles)
        if rects:
            # Convertir coordenadas de vuelta al tamaño original
            scale_x = img.width / resized_img.width
            scale_y = img.height / resized_img.height
            
            original_annotations = []
            for rect in rects:
                original_annotations.append({
                    "label": rect.get("label", "Default Label"),
                    "left": rect["left"] * scale_x,
                    "top": rect["top"] * scale_y,
                    "width": rect["width"] * scale_x,
                    "height": rect["height"] * scale_y
                })
            
            # Guardar temporalmente (en memoria)
            st.session_state.coco_manager.image_annotations[current_file] = original_annotations
        else:
            # Sin anotaciones, limpiar cache
            if current_file in st.session_state.coco_manager.image_annotations:
                del st.session_state.coco_manager.image_annotations[current_file]
    
    # Interfaz de etiquetado
    if st.session_state.current_rects:
        st.subheader("🏷️ Asignar Etiquetas")
        
        for i, rect in enumerate(st.session_state.current_rects):
            col1, col2 = st.columns([1, 2])
            
            with col1:
                # Mostrar miniatura del área seleccionada
                try:
                    scale_x = img.width / resized_img.width
                    scale_y = img.height / resized_img.height
                    
                    left = int(rect["left"] * scale_x)
                    top = int(rect["top"] * scale_y)
                    right = int((rect["left"] + rect["width"]) * scale_x)
                    bottom = int((rect["top"] + rect["height"]) * scale_y)
                    
                    cropped = img.crop((left, top, right, bottom))
                    cropped.thumbnail((150, 150))
                    st.image(cropped, caption=f"Área {i+1}")
                except:
                    st.text(f"Área {i+1}")
            
            with col2:
                current_label = rect.get("label", "Default Label")
                default_index = 0
                if current_label in st.session_state.custom_labels:
                    default_index = st.session_state.custom_labels.index(current_label)
                
                selected_label = st.selectbox(
                    f"Etiqueta para área {i+1}:",
                    st.session_state.custom_labels,
                    index=default_index,
                    key=f"label_select_{current_file}_{i}"
                )
                
                # Actualizar etiqueta si cambió
                if selected_label != current_label:
                    st.session_state.current_rects[i]["label"] = selected_label
                    st.session_state.unsaved_changes = True
                    # No hacer rerun aquí para evitar bucles
    
    # Botones de acción
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("💾 Guardar Imagen Actual", type="primary"):
            try:
                # Convertir coordenadas a tamaño original
                scale_x = img.width / resized_img.width
                scale_y = img.height / resized_img.height
                
                final_annotations = []
                for rect in st.session_state.current_rects:
                    final_annotations.append({
                        "label": rect.get("label", "Default Label"),
                        "left": rect["left"] * scale_x,
                        "top": rect["top"] * scale_y,
                        "width": rect["width"] * scale_x,
                        "height": rect["height"] * scale_y
                    })
                
                # Guardar en COCO manager y XML
                st.session_state.coco_manager.add_or_update_image_annotations(
                    current_file, img.width, img.height, final_annotations
                )
                save_xml_annotation(img_path, current_file, final_annotations, img.width, img.height)
                
                # Actualizar lista de archivos anotados
                xml_filename = os.path.splitext(current_file)[0] + ".xml"
                if final_annotations and xml_filename not in st.session_state.annotation_files:
                    st.session_state.annotation_files.append(xml_filename)
                elif not final_annotations and xml_filename in st.session_state.annotation_files:
                    st.session_state.annotation_files.remove(xml_filename)
                
                st.session_state.unsaved_changes = False
                st.success("✅ Imagen guardada correctamente")
                
            except Exception as e:
                st.error(f"❌ Error al guardar: {str(e)}")
    
    with col2:
        if st.button("🗑️ Limpiar Imagen Actual"):
            try:
                # Limpiar anotaciones de la imagen actual
                st.session_state.current_rects = []
                st.session_state.coco_manager.add_or_update_image_annotations(
                    current_file, img.width, img.height, []
                )
                
                # Eliminar archivo XML si existe
                xml_filename = os.path.splitext(current_file)[0] + ".xml"
                xml_path = os.path.join(st.session_state.temp_dir, xml_filename)
                if os.path.exists(xml_path):
                    os.remove(xml_path)
                
                # Remover de lista de anotados
                if xml_filename in st.session_state.annotation_files:
                    st.session_state.annotation_files.remove(xml_filename)
                
                st.session_state.unsaved_changes = False
                st.success("🗑️ Anotaciones de la imagen eliminadas")
                
            except Exception as e:
                st.error(f"❌ Error al limpiar: {str(e)}")
    
    with col3:
        # Descargar solo anotaciones COCO JSON
        if st.button("📄 Descargar COCO JSON"):
            save_current_changes_if_needed()
            
            # Asegurar que todas las anotaciones estén en el COCO manager
            for file in st.session_state.files:
                xml_file = os.path.splitext(file)[0] + ".xml"
                xml_path = os.path.join(st.session_state.temp_dir, xml_file)
                if os.path.exists(xml_path):
                    annotations = load_xml_annotation(xml_path)
                    if annotations:
                        img_path_temp = os.path.join(st.session_state.temp_dir, file)
                        img_temp = Image.open(img_path_temp)
                        st.session_state.coco_manager.add_or_update_image_annotations(
                            file, img_temp.width, img_temp.height, annotations
                        )
            
            coco_json = json.dumps(st.session_state.coco_manager.coco_data, indent=2)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            st.download_button(
                "📥 Descargar archivo COCO JSON",
                data=coco_json,
                file_name=f"annotations_coco_{timestamp}.json",
                mime="application/json",
                key="download_coco"
            )
    
    # Indicador de cambios no guardados
    if st.session_state.unsaved_changes:
        st.warning("⚠️ **Cambios detectados - se auto-guardan temporalmente para navegación**")
        st.info("💡 Usa 'Guardar Imagen Actual' para confirmar y guardar permanentemente")
    
    # Información adicional sobre la imagen actual
    with st.expander("ℹ️ Información de la imagen"):
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Ancho original", f"{img.width}px")
        with col2:
            st.metric("Alto original", f"{img.height}px")
        with col3:
            st.metric("Bounding boxes", len(st.session_state.current_rects))
        with col4:
            xml_filename = os.path.splitext(current_file)[0] + ".xml"
            status = "✅ Guardada" if xml_filename in st.session_state.annotation_files else "⏳ Pendiente"
            st.metric("Estado", status)
    
    # Progreso general
    if st.session_state.files:
        progress = len(st.session_state.annotation_files) / len(st.session_state.files)
        st.progress(progress, text=f"Progreso: {len(st.session_state.annotation_files)}/{len(st.session_state.files)} imágenes anotadas ({progress:.1%})")
    
    # Debug info (opcional - se puede ocultar en producción)
    with st.expander("🔧 Información de Debug", expanded=False):
        st.json({
            "Imagen actual": current_file,
            "Índice actual": st.session_state.image_index,
            "Total rectángulos actuales": len(st.session_state.current_rects),
            "Cambios sin guardar": st.session_state.unsaved_changes,
            "Total imágenes en COCO": len(st.session_state.coco_manager.coco_data["images"]),
            "Total anotaciones in COCO": len(st.session_state.coco_manager.coco_data["annotations"]),
            "Total categorías en COCO": len(st.session_state.coco_manager.coco_data["categories"])
        })

if __name__ == "__main__":
    main()