import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import httpx
from bs4 import BeautifulSoup
from fastapi.middleware.cors import CORSMiddleware
import re

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class ProductRequest(BaseModel):
    url: str

@app.post("/analyze")
async def analyze_product(request: ProductRequest):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "Accept-Language": "ro-RO,ro;q=0.9,en-US;q=0.8,en;q=0.7"
    }
    
    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=20.0) as client:
            response = await client.get(request.url, headers=headers)
            
        if response.status_code != 200:
            raise HTTPException(status_code=400, detail="Pagina eMAG nu poate fi accesată.")

        soup = BeautifulSoup(response.text, "html.parser")
        
        # 1. EXTRAGERE NUME
        name_tag = soup.find("h1", {"class": "page-title"})
        product_name = name_tag.get_text(strip=True) if name_tag else "Produs de Lux"
        
        # 2. EXTRAGERE PREȚ (Metoda de siguranță maximă)
        price = "N/A"
        
        # Căutăm în tag-ul principal de preț
        price_container = soup.find("p", {"class": "product-new-price"})
        if price_container:
            # Eliminăm textul inutil și păstrăm doar cifrele
            raw_text = price_container.get_text(strip=True)
            # Folosim REGEX pentru a extrage doar numerele (ex: 1.250,99 lei devine 1250,99)
            match = re.search(r"(\d+[\d\.,]*)", raw_text)
            if match:
                price = match.group(1)

        # Dacă e încă N/A, verificăm Meta-Tags (datele din spatele paginii)
        if price == "N/A":
            meta_p = soup.find("meta", {"property": "product:price:amount"})
            if meta_p:
                price = meta_p["content"]

        return {
            "status": "Success",
            "product_name": product_name[:45] + "...",
            "price": price
        }

    except Exception as e:
        return {"status": "Error", "message": str(e)}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=port)
