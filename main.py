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
    # Identitate de browser real pentru a nu fi blocat
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "ro-RO,ro;q=0.9,en-US;q=0.8"
    }
    
    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as client:
            # Încercăm să accesăm pagina
            response = await client.get(request.url, headers=headers)
            
            # Dacă eMAG ne dă eroare temporară, mai așteptăm 2 secunde și mai încercăm o dată
            if response.status_code != 200:
                await asyncio.sleep(2)
                response = await client.get(request.url, headers=headers)

        if response.status_code != 200:
            return {"status": "Error", "message": "eMAG a blocat accesul temporar. Reîncearcă."}

        soup = BeautifulSoup(response.text, "html.parser")
        
        # Extragere Nume
        name_tag = soup.find("h1", {"class": "page-title"})
        product_name = name_tag.get_text(strip=True) if name_tag else "Produs Gentry"
        
        # Extragere Preț
        price = "N/A"
        price_tag = soup.find("p", {"class": "product-new-price"})
        if price_tag:
            # Curățăm prețul să rămână doar cifre și virgulă
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
        return {"status": "Error", "message": "Serverul e ocupat. Mai apasă o dată pe buton."}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=port)
