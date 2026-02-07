"""
Kişisel Not Defterim - FastAPI Backend
"""
import os
from fastapi import FastAPI, HTTPException, Query, Request, Response
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

from services.drive import (
    get_items, get_items_filtered, get_all_counts,
    save_file, move_file, delete_file, update_proje, toggle_pin,
    export_items, get_sirket_options, get_proje_options,
    get_companies_with_counts, clear_cache, SIRKET_PROJE_CONFIG,
    log_error
)

app = FastAPI(title="Kişisel Not Defterim API")


# Global Exception Handler - Hataları Drive'a logla
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Tüm hataları yakala ve Drive'a logla"""
    error_details = {
        "url": str(request.url),
        "method": request.method,
        "error_type": type(exc).__name__,
        "error_message": str(exc)
    }

    # Drive'a logla (arka planda, hata olsa bile devam et)
    try:
        log_error(
            error_type=type(exc).__name__,
            message=str(exc),
            details=error_details
        )
    except Exception:
        pass  # Loglama hatası olursa sessizce geç

    # HTTPException ise orijinal yanıtı döndür
    if isinstance(exc, HTTPException):
        raise exc

    # Diğer hatalar için 500 döndür
    raise HTTPException(status_code=500, detail="Internal server error")

# CORS - sadece bilinen origin'lere izin ver
ALLOWED_ORIGINS = os.environ.get("ALLOWED_ORIGINS", "").split(",")
ALLOWED_ORIGINS = [o.strip() for o in ALLOWED_ORIGINS if o.strip()]
if not ALLOWED_ORIGINS:
    # Varsayılan: sadece kendi domain'imiz ve localhost
    ALLOWED_ORIGINS = [
        "https://alylmz-kisisel-not-defterim.onrender.com",
        "http://localhost:8510",
    ]
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Gzip sıkıştırma (500 byte üzeri yanıtlar için)
app.add_middleware(GZipMiddleware, minimum_size=500)

# Static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Secret key - default olmadan, env zorunlu
SECRET_KEY = os.environ.get("APP_SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError("APP_SECRET_KEY environment variable is required")


# Pydantic Models
class ItemCreate(BaseModel):
    title: str
    content: str = ""
    folder: str
    proje: Optional[str] = None


class ItemUpdate(BaseModel):
    title: str
    content: str = ""
    proje: Optional[str] = None
    pinned: bool = False


class MoveRequest(BaseModel):
    from_folder: str
    to_folder: str


class ProjeUpdate(BaseModel):
    folder: str
    proje: Optional[str] = None


class ExportRequest(BaseModel):
    folder: str
    filter: str = "Tümü"
    name: str


# Auth - cookie tabanlı
COOKIE_NAME = "notdefteri_key"


def check_auth(request: Request):
    """Cookie'den veya query param'dan auth kontrol et"""
    key = request.cookies.get(COOKIE_NAME) or request.query_params.get("key")
    if key != SECRET_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")


# Routes
@app.get("/")
async def root():
    return FileResponse("static/index.html")


@app.post("/api/auth")
async def authenticate(request: Request, response: Response):
    """Authenticate - key'i cookie'ye yaz"""
    body = await request.json()
    key = body.get("key", "")
    if key == SECRET_KEY:
        response.set_cookie(
            key=COOKIE_NAME,
            value=key,
            httponly=True,
            samesite="strict",
            max_age=30 * 24 * 60 * 60,  # 30 gün
        )
        return {"success": True}
    raise HTTPException(status_code=401, detail="Invalid key")


@app.get("/api/auth")
async def verify_auth(request: Request):
    """Cookie auth doğrula"""
    check_auth(request)
    return {"success": True}


@app.get("/api/counts")
async def get_counts(request: Request):
    """Get all folder counts"""
    check_auth(request)
    return get_all_counts()


@app.get("/api/items/{folder}")
async def get_folder_items(
    folder: str,
    request: Request,
    filter: str = Query("Tümü")
):
    """Get items from a folder with optional filter"""
    check_auth(request)
    if filter == "Tümü":
        return get_items(folder)
    return get_items_filtered(folder, filter)


@app.post("/api/items")
async def create_item(item: ItemCreate, request: Request):
    """Create a new item"""
    check_auth(request)
    file_id = save_file(item.title, item.content, item.folder, item.proje)
    return {"success": True, "id": file_id}


@app.put("/api/items/{file_id}")
async def update_item(
    file_id: str,
    item: ItemUpdate,
    request: Request,
    folder: str = Query(...)
):
    """Update an existing item"""
    check_auth(request)
    save_file(item.title, item.content, folder, item.proje, file_id, item.pinned)
    return {"success": True}


@app.post("/api/items/{file_id}/move")
async def move_item(file_id: str, move: MoveRequest, request: Request):
    """Move item between folders"""
    check_auth(request)
    move_file(file_id, move.from_folder, move.to_folder)
    return {"success": True}


@app.post("/api/items/{file_id}/pin")
async def pin_item(file_id: str, request: Request, folder: str = Query(...)):
    """Toggle pin status"""
    check_auth(request)
    new_status = toggle_pin(file_id, folder)
    return {"success": True, "pinned": new_status}


@app.post("/api/items/{file_id}/proje")
async def set_proje(file_id: str, proje: ProjeUpdate, request: Request):
    """Update item's project"""
    check_auth(request)
    update_proje(file_id, proje.folder, proje.proje)
    return {"success": True}


@app.delete("/api/items/{file_id}")
async def delete_item(file_id: str, request: Request, folder: str = Query(...)):
    """Delete or trash an item"""
    check_auth(request)
    delete_file(file_id, folder)
    return {"success": True}


@app.get("/api/companies")
async def get_companies(request: Request):
    """Get companies with project counts"""
    check_auth(request)
    return get_companies_with_counts()


@app.get("/api/projects")
async def get_projects(request: Request, company: str = Query(None)):
    """Get project options"""
    check_auth(request)
    return get_proje_options(company)


@app.get("/api/sirketler")
async def get_sirketler(request: Request):
    """Get company options for filter"""
    check_auth(request)
    return get_sirket_options()


@app.get("/api/config")
async def get_config(request: Request):
    """Get full company-project config"""
    check_auth(request)
    return SIRKET_PROJE_CONFIG


@app.post("/api/export")
async def export(export_req: ExportRequest, request: Request):
    """Export filtered items to a file"""
    check_auth(request)
    items = get_items_filtered(export_req.folder, export_req.filter)
    filename = export_items(items, export_req.name)
    return {"success": True, "filename": filename}


@app.post("/api/refresh")
async def refresh(request: Request):
    """Clear cache"""
    check_auth(request)
    clear_cache()
    return {"success": True}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8510)
