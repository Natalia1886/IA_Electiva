"""Punto de entrada principal de la API REST (FastAPI) para la tienda de artículos religiosos."""

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

# Asegurar registro de agentes y skills al importar
import agents
import skills

from core.database.connection import init_db
from core.database.seed_data import seed_database
from interfaces.api.routes_auth import router as auth_router
from interfaces.api.routes_products import router as products_router
from interfaces.api.routes_sales import router as sales_router
from interfaces.api.routes_inventory import router as inventory_router
from interfaces.api.routes_festivities import router as festivities_router
from interfaces.api.routes_recommendations import router as recommendations_router
from interfaces.api.routes_dashboard import router as dashboard_router

# Inicializar base de datos y siembra automática
init_db()
seed_database()

app = FastAPI(
    title="Sistema Inteligente de Ventas, Inventario y Recomendaciones Religiosas",
    description="Backend en capas con arquitectura de agentes, skills y ML para tienda de artículos religiosos.",
    version="1.0.0"
)

# Configuración CORS para interfaz de usuario (RNF01, RNF02)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inclusión de routers modulares
app.include_router(auth_router, prefix="/api")
app.include_router(products_router, prefix="/api")
app.include_router(sales_router, prefix="/api")
app.include_router(inventory_router, prefix="/api")
app.include_router(festivities_router, prefix="/api")
app.include_router(recommendations_router, prefix="/api")
app.include_router(dashboard_router, prefix="/api")


# Montar carpeta estática de la interfaz web (RNF01)
WEB_UI_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web_ui")
if os.path.exists(WEB_UI_DIR):
    app.mount("/static", StaticFiles(directory=WEB_UI_DIR), name="static")

    @app.get("/", include_in_schema=False)
    def serve_ui():
        return FileResponse(os.path.join(WEB_UI_DIR, "index.html"))


@app.get("/api/health", tags=["Salud"])
def health_check():
    return {
        "status": "healthy",
        "app": "Tienda Religiosa MilanFramework",
        "version": "1.0.0"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("interfaces.api.main:app", host="0.0.0.0", port=8000, reload=True)
