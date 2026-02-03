"""
Kişisel Not Defterim - FastAPI Backend
"""
import os
import json
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel
from typing import Optional

from services.drive import (
    get_items, get_items_filtered, get_all_counts, get_item_count,
    save_file, move_file, delete_file, update_proje, toggle_pin,
    export_items, get_sirket_options, get_proje_options,
    get_companies_with_counts, clear_cache, SIRKET_PROJE_CONFIG
)

app = FastAPI(title="Kişisel Not Defterim API")

# Static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Secret key
SECRET_KEY = os.environ.get("APP_SECRET_KEY", "1102")


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


# Auth middleware
def check_auth(key: str = None):
    if key != SECRET_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")


# Routes
@app.get("/")
async def root():
    return FileResponse("static/index.html")


@app.get("/api/auth")
async def authenticate(key: str = Query(...)):
    """Authenticate with secret key"""
    if key == SECRET_KEY:
        return {"success": True}
    raise HTTPException(status_code=401, detail="Invalid key")


@app.get("/api/counts")
async def get_counts(key: str = Query(...)):
    """Get all folder counts"""
    check_auth(key)
    return get_all_counts()


@app.get("/api/items/{folder}")
async def get_folder_items(
    folder: str,
    key: str = Query(...),
    filter: str = Query("Tümü")
):
    """Get items from a folder with optional filter"""
    check_auth(key)
    if filter == "Tümü":
        return get_items(folder)
    return get_items_filtered(folder, filter)


@app.post("/api/items")
async def create_item(item: ItemCreate, key: str = Query(...)):
    """Create a new item"""
    check_auth(key)
    file_id = save_file(item.title, item.content, item.folder, item.proje)
    return {"success": True, "id": file_id}


@app.put("/api/items/{file_id}")
async def update_item(
    file_id: str,
    item: ItemUpdate,
    folder: str = Query(...),
    key: str = Query(...)
):
    """Update an existing item"""
    check_auth(key)
    save_file(item.title, item.content, folder, item.proje, file_id, item.pinned)
    return {"success": True}


@app.post("/api/items/{file_id}/move")
async def move_item(file_id: str, move: MoveRequest, key: str = Query(...)):
    """Move item between folders"""
    check_auth(key)
    move_file(file_id, move.from_folder, move.to_folder)
    return {"success": True}


@app.post("/api/items/{file_id}/pin")
async def pin_item(file_id: str, folder: str = Query(...), key: str = Query(...)):
    """Toggle pin status"""
    check_auth(key)
    new_status = toggle_pin(file_id, folder)
    return {"success": True, "pinned": new_status}


@app.post("/api/items/{file_id}/proje")
async def set_proje(file_id: str, proje: ProjeUpdate, key: str = Query(...)):
    """Update item's project"""
    check_auth(key)
    update_proje(file_id, proje.folder, proje.proje)
    return {"success": True}


@app.delete("/api/items/{file_id}")
async def delete_item(file_id: str, folder: str = Query(...), key: str = Query(...)):
    """Delete or trash an item"""
    check_auth(key)
    delete_file(file_id, folder)
    return {"success": True}


@app.get("/api/companies")
async def get_companies(key: str = Query(...)):
    """Get companies with project counts"""
    check_auth(key)
    return get_companies_with_counts()


@app.get("/api/projects")
async def get_projects(key: str = Query(...), company: str = Query(None)):
    """Get project options"""
    check_auth(key)
    return get_proje_options(company)


@app.get("/api/sirketler")
async def get_sirketler(key: str = Query(...)):
    """Get company options for filter"""
    check_auth(key)
    return get_sirket_options()


@app.get("/api/config")
async def get_config(key: str = Query(...)):
    """Get full company-project config"""
    check_auth(key)
    return SIRKET_PROJE_CONFIG


@app.post("/api/export")
async def export(export_req: ExportRequest, key: str = Query(...)):
    """Export filtered items to a file"""
    check_auth(key)
    items = get_items_filtered(export_req.folder, export_req.filter)
    filename = export_items(items, export_req.name)
    return {"success": True, "filename": filename}


@app.post("/api/refresh")
async def refresh(key: str = Query(...)):
    """Clear cache"""
    check_auth(key)
    clear_cache()
    return {"success": True}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8510)
