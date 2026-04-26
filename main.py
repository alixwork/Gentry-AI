import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import httpx
from bs4 import BeautifulSoup
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Permitem site-ului tău de pe GitHub să vorbească cu acest server
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
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=15.0) as client:
            response = await client.get(request.url, headers=headers)
            
        if response.status_code != 200:
            raise HTTPException(status_code=400, detail="Nu am putut accesa pagina eMAG.")

        soup = BeautifulSoup(response.text, "html.parser")
        
        # EXTRAGERE NUME PRODUS
        name_tag = soup.find("h1", {"class": "page-title"})
        product_name = name_tag.get_text(strip=True) if name_tag else "Produs Necunoscut"
        
        # EXTRAGERE PREȚ (Metodă multiplă pentru siguranță)
        price = "N/A"
        
        # Încercăm prima metodă (clasa principală de preț)
        price_tag = soup.find("p", {"class": "product-new-price"})
        if price_tag:
            # Luăm doar textul, eliminăm "lei" și curățăm spațiile
            price_text = price_tag.get_text(strip=True).lower().replace("lei", "").replace(".", "")
            # Dacă există zecimale în tag-uri separate, le unim
            sup = price_tag.find("sup")
            if sup:
                main_price = price_text.replace(sup.get_text(strip=True).lower(), "")
                price = f"{main_price},{sup.get_text(strip=True)}"
            else:
                price = price_text

        # Dacă prima metodă a eșuat, căutăm în meta tag-uri (invizibile, dar precise)
        if price == "N/A":
            meta_price = soup.find("meta", {"property": "product:price:amount"})
            if meta_price:
                price = meta_price["content"]

        return {
            "status": "Success",
            "product_name": product_name[:50] + "...",
            "price": price
        }

    except Exception as e:
        return {"status": "Error", "message": str(e)}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=port)
