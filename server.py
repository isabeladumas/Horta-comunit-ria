from fastapi import FastAPI, Query, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional
import uvicorn
import io

from database import init_db, insert_leitura, add_intervencao, get_todas_leituras, get_ultima_leitura, get_intervencoes
from report_generator import generate_csv_buffer, generate_pdf_bytes

# Inicializa banco de dados ao iniciar
init_db()

app = FastAPI(
    title="API de Ingestão e Controle IoT - Horta Comunitária",
    description="Servidor de Ingestão de Dados de Sensores (ESP32/Arduino) e Gestão de Intervenções Agronômicas.",
    version="1.0.0"
)

# Habilita CORS para permitir visualizações de qualquer dashboard web
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class LeituraPayload(BaseModel):
    valor_ph: float = Field(..., description="Valor medido do pH (ex: 6.5)")
    valor_umidade: int = Field(..., description="Valor percentual da umidade do solo (ex: 60)")
    status_solo: Optional[str] = Field("Ideal", description="Diagnóstico preliminar (ex: 'Ideal', 'Ácido', 'Seco')")
    intervencao: Optional[str] = Field("", description="Anotação de intervenção humana (opcional)")

class IntervencaoPayload(BaseModel):
    intervencao: str = Field(..., description="Descrição da ação de manejo (ex: 'Calagem com 200g calcário')")
    data_hora: Optional[str] = Field(None, description="Data/Hora opcional no formato 'YYYY-MM-DD HH:MM:SS'")

@app.get("/")
def home():
    return {
        "status": "online",
        "projeto": "Monitoramento IoT de Horta Comunitária",
        "endpoints": {
            "post_leitura_json": "POST /api/leituras",
            "get_leitura_url": "GET /api/leituras?valor_ph=6.5&valor_umidade=60&status_solo=Ideal",
            "post_intervencao": "POST /api/intervencao",
            "listar_leituras": "GET /api/leituras/todas",
            "ultima_leitura": "GET /api/leituras/ultima",
            "exportar_csv": "GET /api/export/csv",
            "exportar_pdf": "GET /api/export/pdf",
            "documentacao_interativa": "/docs"
        }
    }

# Endpoint POST (Recomendado para ESP32 enviando JSON)
@app.post("/api/leituras", status_code=201)
def receber_leitura_post(payload: LeituraPayload):
    try:
        registro = insert_leitura(
            valor_ph=payload.valor_ph,
            valor_umidade=payload.valor_umidade,
            status_solo=payload.status_solo or "Ideal",
            intervencao=payload.intervencao or ""
        )
        return {
            "status": "sucesso",
            "mensagem": "Leitura recebida e persistida com sucesso.",
            "registro": registro
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Endpoint GET (Fallback para microcontroladores simples com parâmetros na URL)
@app.get("/api/leituras")
def receber_leitura_get(
    valor_ph: float = Query(..., description="pH lido pelo sensor"),
    valor_umidade: int = Query(..., description="Umidade em %"),
    status_solo: Optional[str] = Query("Ideal", description="Diagnóstico"),
    intervencao: Optional[str] = Query("", description="Anotação de manejo")
):
    try:
        registro = insert_leitura(
            valor_ph=valor_ph,
            valor_umidade=valor_umidade,
            status_solo=status_solo or "Ideal",
            intervencao=intervencao or ""
        )
        return {
            "status": "sucesso",
            "metodo": "GET",
            "registro": registro
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Endpoint para registrar intervenções agronômicas humanas
@app.post("/api/intervencao")
def registrar_intervencao(payload: IntervencaoPayload):
    try:
        sucesso = add_intervencao(payload.intervencao, payload.data_hora)
        return {
            "status": "sucesso",
            "mensagem": f"Intervenção '{payload.intervencao}' registrada no banco de dados."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Endpoint para consultar a última leitura instantânea (Scorecards)
@app.get("/api/leituras/ultima")
def obter_ultima():
    leitura = get_ultima_leitura()
    if not leitura:
        raise HTTPException(status_code=404, detail="Nenhuma leitura cadastrada.")
    return leitura

# Endpoint para obter todas as leituras históricas
@app.get("/api/leituras/todas")
def obter_todas():
    return get_todas_leituras()

# Endpoint para exportação em CSV
@app.get("/api/export/csv")
def exportar_csv():
    csv_buf = generate_csv_buffer()
    return Response(
        content=csv_buf.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=horta_leituras.csv"}
    )

# Endpoint para exportação em PDF
@app.get("/api/export/pdf")
def exportar_pdf():
    pdf_bytes = generate_pdf_bytes()
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=relatorio_horta_comunitaria.pdf"}
    )

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
