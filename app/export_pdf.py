from PIL import Image, ImageDraw, ImageFont
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
import io
import os

def draw_boxes_on_image(image_path, annotations):
    img = Image.open(image_path).convert("RGB")
    draw = ImageDraw.Draw(img)
    font = None
    try:
        font = ImageFont.truetype("arial.ttf", 18)
    except:
        font = ImageFont.load_default()
    for idx, ann in enumerate(annotations):
        x, y, w, h = ann["left"], ann["top"], ann["width"], ann["height"]
        label = ann.get("label", "")
        comment = ann.get("comment", "")
        color = (255, 0, 0)
        draw.rectangle([x, y, x + w, y + h], outline=color, width=3)
        draw.text((x, y - 20), f"{label}", fill=color, font=font)
    return img

def export_pdf(images_dir, coco_manager, output_path):
    c = canvas.Canvas(output_path, pagesize=A4)
    width, height = A4
    for img_info in coco_manager.coco_data["images"]:
        filename = img_info["file_name"]
        img_path = os.path.join(images_dir, filename)
        annotations = [ann for ann in coco_manager.coco_data["annotations"] if ann["image_id"] == img_info["id"]]
        # Draw boxes on image
        img_with_boxes = draw_boxes_on_image(img_path, annotations)
        # Resize image to fit page width
        img_io = io.BytesIO()
        img_with_boxes.save(img_io, format="PNG")
        img_io.seek(0)
        aspect = img_with_boxes.height / img_with_boxes.width
        img_width = width - 80
        img_height = img_width * aspect
        c.drawImage(ImageReader(img_io), 40, height - img_height - 60, width=img_width, height=img_height)
        # Table of boxes
        y_table = height - img_height - 80
        c.setFont("Helvetica", 12)
        for idx, ann in enumerate(annotations):
            label = ann.get("label", "")
            comment = ann.get("comment", "")
            c.drawString(50, y_table - idx * 20, f"Área {idx+1}: {label} | {comment}")
        c.showPage()
    c.save()
