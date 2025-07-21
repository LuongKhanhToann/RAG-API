from sentence_transformers import SentenceTransformer   #HuggingFace Model 
from core.config import api_embedded_key
import google.generativeai as genai
import openai
import os
import requests
from bs4 import BeautifulSoup
import json
import re
def embedding_model():
    model = SentenceTransformer('paraphrase-mpnet-base-v2')
    return model

#Open AI
# openai.api_key = api_embedded_key
# def embedding_model(text: str) -> list:
#     response = openai.embeddings.create(
#         model="text-embedding-3-small",  
#         input=text
#     )
#     return response.data[0].embedding


#Gemini
# genai.configure(api_key=api_embedded_key)
# def embedding_model(text: str) -> list:
#     response = genai.embed_content(
#         model="models/embedding-gecko-001",
#         content=text,
#         task_type="retrieval_document"
#     )
#     return response['embedding']


def is_valid_price(price_text):
    return bool(re.search(r'\d{1,3}(?:[\.,]\d{1,3})*(₫|\$|€|£)?', price_text.strip()))

def extract_product_data(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    product_data = {}

    product_name = soup.find('title') or soup.find('meta', {'property': 'og:title'})
    product_data['name'] = product_name.get_text(strip=True) if product_name else 'N/A'

    product_description = soup.find('meta', {'name': 'description'}) or soup.find('meta', {'property': 'og:description'})
    product_data['description'] = product_description.get('content', 'N/A') if product_description else 'N/A'

    product_image = soup.find('meta', {'property': 'og:image'})
    product_data['image'] = product_image.get('content', 'N/A') if product_image else 'N/A'

    price_elements = soup.find_all(class_=re.compile(r'.*price.*', re.IGNORECASE))
    prices = []
    existing_class_names = set() 
    max_prices = 3
    
    for price_element in price_elements:
        price_text = price_element.get_text(strip=True)
        class_name = price_element.get('class', [])

        class_name_str = ', '.join(class_name)
        if class_name_str not in existing_class_names:
            if is_valid_price(price_text):
                if len(prices) < max_prices:
                    prices.append({
                        'price': price_text,
                        'class_name': class_name_str 
                    })
                    existing_class_names.add(class_name_str)  

    if prices:
        product_data['prices'] = prices
    else:
        product_data['prices'] = 'N/A'

    return [product_data]

def save_to_json(products, output_file_path):
    with open(output_file_path, 'w', encoding='utf-8') as f:
        json.dump(products, f, ensure_ascii=False, indent=4)

def process_html_to_json(url, output_file_path):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  

        if response.status_code == 200:
            html_content = response.content

            products_data = extract_product_data(html_content)  
            save_to_json(products_data, output_file_path)
            print(f"Save successfully {output_file_path}")
        else:
            print(f"Cannot access url {url}. Error: {response.status_code}")

    except requests.exceptions.RequestException as e:
        print(f"Error HTTP: {e}")

## Test
# tgdd_url = 'https://www.thegioididong.com/dong-ho-deo-tay/elio-es172-02-nu?utm_flashsale=1'
# cellphone_url = 'https://cellphones.com.vn/iphone-14-pro.html'
# hoanghamobile_url = 'https://hoanghamobile.com/dien-thoai/redmi-note-14?gad_source=1&gad_campaignid=22799315212&gbraid=0AAAAADfCGpa6XtQQT6QZ3KioAsizwBzfk&gclid=CjwKCAjwp_LDBhBCEiwAK7FnktFRWSedfw70V5cidCJtQK88YD0x_f3NZSI5u2XY6Ph8I-WRwsm8QRoCUfoQAvD_BwE'
# apple_url = 'https://www.apple.com/vn/shop/product/MDFX4FE/A/ốp-lưng-silicon-magsafe-cho-iphone-16-pro-hồng-mẫu-đơn'

# output_file_path_tgdd = 'tgdd_product.json'
# output_file_path_cellphone = 'cellphone_product.json'
# output_file_path_hoanghamobile = 'hoanghamobile_product.json'
# output_file_path_apple = 'app_product.json'

# process_html_to_json(tgdd_url, output_file_path_tgdd)
# process_html_to_json(cellphone_url, output_file_path_cellphone)
# process_html_to_json(hoanghamobile_url, output_file_path_hoanghamobile)
# process_html_to_json(apple_url, output_file_path_apple)