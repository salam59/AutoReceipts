from io import BytesIO
import os
import base64, hashlib

import openai
from openai import OpenAI
import pypdfium2 as pdfium
from PIL import Image
from dotenv import load_dotenv

from receipts.prompts import RECEIPT_EXTRACT_PROMPT, CLASSIFICATION_PROMPT

load_dotenv()

def convert_pdf_to_images(file_path, file_id, scale=100/72):
        pdf_file = pdfium.PdfDocument(file_path)
        page_indices = [i for i in range(len(pdf_file))]
        num_pages = len(pdf_file)

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

        return f'images/{file_id}', num_pages 

def prepare_prompt(prompt, images_path, num_images):
    prompt_with_images = [
        {'type': 'text', 'text': prompt},
    ]
    for page in range(1, num_images + 1):
        image_path = f"{images_path}/{page}.jpg"
        with open(image_path, 'rb') as image_file:
            image_base64 = base64.b64encode(image_file.read()).decode('utf-8')
            prompt_with_images.append({'type': 'image_url', 'image_url': {'url': f'data:image/jpeg;base64,{image_base64}'}})
    prompt_format = [
        {"role": "system", "content": "You're an expert in analyzing receipts and extracting data from them."},
        {"role": "user", "content": prompt_with_images}
    ]
    return prompt_format

def pre_processing_data(file_path, file_id):
    ext = os.path.splitext(file_path)[1].lower()
    image_exts = ['.jpg', '.jpeg', '.png']

    if ext == '.pdf':
        images_path, num_images = convert_pdf_to_images(file_path, file_id)
    elif ext in image_exts:
        os.makedirs(f'images/{file_id}', exist_ok=True)
        dest_path = os.path.join('images', file_id, '1.jpg')
        with Image.open(file_path) as img:
            rgb_img = img.convert('RGB')
            rgb_img.save(dest_path, format='JPEG', quality=95, optimize=True)
        images_path = f'images/{file_id}'
        num_images = 1

    return images_path, num_images

def create_openai_client():
    client = OpenAI(
        base_url=os.getenv('OPENAI_BASE_URL'),
        api_key=os.getenv('OPENAI_API_KEY')
        )
    return client

def extract_receipt_data(file_path, file_id):
    ext = os.path.splitext(file_path)[1].lower()
    image_exts = ['.jpg', '.jpeg', '.png']
    if ext == '.pdf' or ext in image_exts:
        images_path, num_images = pre_processing_data(file_path, file_id)
    else:
        return {}, "Unsupported file type"
    client = create_openai_client()

    prompt = prepare_prompt(RECEIPT_EXTRACT_PROMPT, images_path, num_images)
    try:
        response = client.chat.completions.create(
            model=os.getenv('LLM_MODEL'),
            messages=[prompt],
            response_format={"type": "json_object"},
        )
        return response.choices[0].message.content
    except openai.error.OpenAIError as e:
        return {'error': str(e), 'status_code': e.http_status}

def classify_receipt_or_not(file_path, file_id):
    images_path, num_images = pre_processing_data(file_path, str(file_id))
    prompt = prepare_prompt(CLASSIFICATION_PROMPT, images_path, num_images)
    
    client = create_openai_client()
    try:
        response = client.chat.completions.create(
            model=os.getenv('LLM_MODEL'),
            messages=[prompt],
            response_format={"type": "json_object"},
        )
        return response.choices[0].message.content
    except openai.error.OpenAIError as e:
        return {'error': str(e), 'status_code': e.http_status}

def generate_file_hash_from_content(file_content):
    """Generate SHA-256 hash from file content"""
    hash_sha256 = hashlib.sha256()
    hash_sha256.update(file_content)
    return hash_sha256.hexdigest()