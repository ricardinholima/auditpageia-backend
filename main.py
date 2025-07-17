from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests
from bs4 import BeautifulSoup
import openai
import os

# Configure sua chave da OpenAI
openai.api_key = os.getenv("OPENAI_API_KEY")

app = FastAPI()

# Liberar CORS para frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class SiteInput(BaseModel):
    url: str

@app.post("/renderizar")
async def renderizar_diagnostico(input: SiteInput):
    try:
        res = requests.get(input.url, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")

        title = soup.title.string if soup.title else "Sem título"
        h1 = soup.find("h1").text.strip() if soup.find("h1") else "Sem H1"
        ctas = [a.text.strip() for a in soup.find_all("a") if 'comprar' in a.text.lower() or 'saiba mais' in a.text.lower()]
        texto_total = soup.get_text(separator=' ').strip()[0:3000]  # Limite para prompt

        prompt = f"""
Você é um especialista em conversão de sites. Abaixo estão os elementos principais da página analisada:

Título: {title}
H1: {h1}
CTAs: {ctas}
Texto da Página:
{texto_total}

Com base nesses elementos, escreva um relatório direto e prático com:
1. Pontos positivos da estrutura
2. O que está prejudicando a conversão
3. Sugestões de melhorias (copy, layout, CTAs)
4. Nota geral de 0 a 10 com justificativa.

Use linguagem acessível.
"""

        completion = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Você é um consultor de UX e Copy para páginas de vendas."},
                {"role": "user", "content": prompt}
            ]
        )

        texto_final = completion.choices[0].message.content
        return {"relatorio": texto_final}

    except Exception as e:
        return {"relatorio": f"Erro na análise: {str(e)}"}
