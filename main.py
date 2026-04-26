import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import httpx
from bs4 import BeautifulSoup
from fastapi.middleware.cors import CORSMiddleware
import re
import asyncio

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
    # Folosim o identitate de browser foarte comună (Chrome pe Windows)
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "ro-RO,ro;q=0.9,en-US;q=0.8",
        "Cache-Control": "no-cache"
    }
    
    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=25.0) as client:
            # Prima încercare
            response = await client.get(request.url, headers=headers)
            
            # Dacă suntem blocați (eroare 403 sau 503), mai încercăm o dată după 2 secunde
            if response.status_code != 200:
                await asyncio.sleep(2.5)
                response = await client.get(request.url, headers=headers)

        if response.status_code != 200:
            return {"status": "Error", "message": "eMAG verifică conexiunea. Mai apasă o dată pe buton."}

        soup = BeautifulSoup(response.text, "html.parser")
        
        # Extragere Nume
        name_tag = soup.find("h1", {"class": "page-title"})
        product_name = name_tag.get_text(strip=True) if name_tag else "Produs Gentry"
        
        # Extragere Preț
        price = "N/A"
        price_tag = soup.find("p", {"class": "product-new-price"})
        if price_tag:
            raw_price = price_tag.get_text(strip=True)
            match = re.search(r"(\d+[\d\.,]*)", raw_price)
            if match:
                price = match.group(1)

        return {
            "status": "Success",
            "product_name": product_name[:40] + "...",
            "price": price
        }

    except Exception as e:
        return {"status": "Error", "message": "Conexiune resetată. Reîncearcă scanarea."}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=port)
