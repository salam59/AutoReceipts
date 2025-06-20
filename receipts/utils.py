from io import BytesIO
import os
import shutil, base64, json

from openai import OpenAI
import pypdfium2 as pdfium
from PIL import Image

def convert_pdf_to_images(file_path, file_id, scale=100/72):
        pdf_file = pdfium.PdfDocument(file_path)
        page_indices = [i for i in range(len(pdf_file))]

        renderer = pdf_file.render(
            pdfium.PdfBitmap.to_pil,
            page_indices=page_indices,
            scale=scale,
        )

        os.makedirs(f'images/{file_id}', exist_ok=True)
        for i, image in zip(page_indices, renderer):
            image_byte_array = BytesIO()

            max_dimension = 1536  
            if image.width > max_dimension or image.height > max_dimension:
                ratio = min(max_dimension/image.width,
                            max_dimension/image.height)
                new_size = (int(image.width * ratio),
                            int(image.height * ratio))
                image = image.resize(new_size, Image.Resampling.LANCZOS)

            # Optimize JPEG quality
            image.save(image_byte_array, format='JPEG',
                       quality=95,  
                       optimize=True)
            image_byte_array = image_byte_array.getvalue()

            image_path = os.path.join('images', file_id, f"{i+1}.jpg")
            Image.open(BytesIO(image_byte_array)).save(image_path)

        return f'images/{file_id}'