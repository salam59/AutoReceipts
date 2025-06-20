from io import BytesIO
import os
import shutil, base64, json

from openai import OpenAI
import pypdfium2 as pdfium
from PIL import Image
from dotenv import load_dotenv

from .prompts import RECEIPT_EXTRACT_PROMPT

load_dotenv()

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

def prepare_prompt(images_path, num_images):
    prompt_with_images = [
        {'type': 'text', 'text': RECEIPT_EXTRACT_PROMPT},
    ]
    for page in range(1, num_images + 1):
        with open(images_path, 'rb') as image_file:
            image_base64 = base64.b64encode(image_file.read()).decode('utf-8')
            prompt_with_images.append({'type': 'image_url', 'image_url': {'url': f'data:image/jpeg;base64,{image_base64}'}})
    prompt_format = [
        {"role": "system", "content": "You're an expert in analyzing receipts and extracting data from them."},
        {"role": "user", "content": prompt_with_images}
    ]
    return prompt_format

def extract_receipt_data(file_path, file_id):
    images_path = convert_pdf_to_images(file_path, file_id)

    client = OpenAI(
        base_url=os.getenv('OPENAI_BASE_URL'),
        api_key=os.getenv('OPENAI_API_KEY')
        )

    images_path, num_images = f'images/{file_id}'
    prompt = prepare_prompt(images_path, num_images)

    response = client.chat.completions.create(
        model=os.getenv('LLM_MODEL'),
        messages=[{"role": "user", "content": RECEIPT_EXTRACT_PROMPT}],
        response_format={"type": "json_object"},
    )
    return response.choices[0].message.content