
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests
from bs4 import BeautifulSoup
import re
import os
import uvicorn

app = FastAPI()

# Configurare CORS - Permite aplicației tale să fie accesată de pe orice domeniu
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_methods=["*"],
    allow_headers=["*"],
)

class ProductLink(BaseModel):
    url: str

def extract_price(soup):
    """Funcție care scanează codul paginii pentru a găsi prețul în lei/RON."""
    text_content = soup.get_text()
    # Căutăm tipare numerice urmate de lei sau RON
    price_pattern = re.findall(r'(\d+[\d\s.,]*)\s*(?:lei|RON)', text_content, re.IGNORECASE)
    if price_pattern:
        # Curățăm caracterele invizibile și spațiile extra
        clean_price = price_pattern[0].replace('\xa0', ' ').strip()
        return clean_price
    return "N/A"

@app.post("/analyze")
async def analyze_link(data: ProductLink):
    try:
        # User-Agent-ul păcălește site-urile să creadă că ești un browser real, nu un robot
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
        }
        
        response = requests.get(data.url, headers=headers, timeout=15)
        response.raise_for_status() # Verifică dacă pagina s-a încărcat corect
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extragem titlul paginii și îl scurtăm pentru cardurile de wishlist
        full_title = soup.title.string if soup.title else "Produs Necunoscut"
        short_title = full_title.split('-')[0].split('|')[0].strip()[:45] + "..."
        
        # Extragem prețul folosind funcția de mai sus
        price = extract_price(soup)
        
        return {
            "status": "Success",
            "product_name": short_title,
            "price": price,
            "url": data.url,
            "agent_message": "Analiză Gentry finalizată cu succes."
        }
    except Exception as e:
        return {
            "status": "Error", 
            "message": f"Gentry nu a putut accesa link-ul. Motiv: {str(e)}"
        }

# Această parte este esențială pentru serverele de hosting (Railway, Render, Heroku)
if __name__ == "__main__":
    # Citim portul de la server, sau folosim 8000 dacă rulăm local
    port = int(os.environ.get("PORT", 8000))
    # Rulăm pe 0.0.0.0 pentru a fi vizibil pe internet
    uvicorn.run(app, host="0.0.0.0", port=port)