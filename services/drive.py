"""
Google Drive API Service
Tüm Drive işlemleri bu modülde
"""
import os
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaInMemoryUpload
from google.auth.transport.requests import AuthorizedSession
from datetime import datetime
import time

# Config
SCOPES = ['https://www.googleapis.com/auth/drive']
SHARED_DRIVE_ID = os.environ.get("SHARED_DRIVE_ID", "0AFbVhvJLQtOHUk9PVA")

# Şirket ve Proje Konfigürasyonu
SIRKET_PROJE_CONFIG = {
    "ENVEX": [
        "BHP Escondida Sözleşme Yönetimi",
        "ABD ENVEX Satış Ağı",
        "Kazakistan ENVEX Satış Ağı",
        "Satış Ekibi Yapılanması",
        "Umman ENVEX Satış Ağı",
        "Kuveyt ENVEX Satış Ağı",
        "WIPO ENVEX Raporlama Süreci",
        "Kurumsal Kimlik",
        "ABD ENVEX Relocation Projesi",
        "ENVEX-COREX Ortaklık Görüşmeleri",
        "ENVEX Yatırımcı Sunum Dosyası",
        "ENVEX Sözleşme Yönetimi Eğitimi",
    ],
    "COREX": [
        "Corpus Christi Güneş Enerjisi Santrali",
        "Corpus Christi Bakır Geri Dönüşüm Tesisi",
        "ENVEX - COREX Ortaklık Projesi",
    ],
    "TIS": [
        "Satış Süreç Yönetimi Projesi",
        "Resmi İlişkiler Yönetimi Projesi",
        "Kültürel Dönüşüm Projesi",
        "İmalat Tasarım Dijitalleşme Projesi",
        "İslam Kalkınma Bankası İşbirliği",
        "Kazakistan Yapılanması",
        "EBRD Projesi",
    ],
    "MIM": [
        "Kore KEXIM Tedarik Zinciri Finansmanı Projesi",
    ],
    "TEMROB": [
        "Ankara Teknopark Akıllı Ayna Projesi",
        "Ankara Teknopark Yapay Zeka Finansal Yazılım Projesi",
    ],
    "PULCHRANI": [
        "Shopify Eticaret Platformu Geliştirme Projesi",
        "ETSY Eticaret Platformu Geliştirme Projesi",
    ],
    "ALI YILMAZ": [
        "CAPITAL ONE US Kredi Kartı",
        "BOFA US Kredi Kartı",
        "BOFA US Banka Kartı",
        "CHASE US Kredi Kartı",
        "EQUIFAX Kredi Bürosu İletişimi",
        "NAV Kredi Skoru Projesi",
        "TOMO Kredi Skoru Projesi",
    ],
    "EPIOQN": [
        "EQONE Akıllı Ayna Ürün Geliştirme Projesi",
    ],
    "PULPO": [
        "Debt Finance Projesi",
        "Convertible Note Yatırımı Projesi",
    ],
    "OZMEN": [
        "Manisa JES Satış Süreci Projesi",
    ],
}

FOLDER_CONFIG = {
    "inbox": "inbox",
    "notlar": "notlar",
    "gorevler": "gorevler",
    "arsiv": "arsiv",
    "cop_kutusu": "cop_kutusu",
}

# Drive Service Singleton
_drive_service = None
_folder_ids_cache = None

# TTL Cache
_cache = {}
_cache_ttl = {}
CACHE_DURATION = 30  # seconds


def get_cached(key):
    """Get cached value if not expired"""
    if key in _cache and key in _cache_ttl:
        if time.time() < _cache_ttl[key]:
            return _cache[key]
    return None


def set_cached(key, value, ttl=CACHE_DURATION):
    """Set cache with TTL"""
    _cache[key] = value
    _cache_ttl[key] = time.time() + ttl


def get_credentials():
    """Environment'tan credentials al"""
    creds_json = os.environ.get("GCP_CREDENTIALS")
    if creds_json:
        creds_info = json.loads(creds_json)
        return service_account.Credentials.from_service_account_info(creds_info, scopes=SCOPES)
    raise ValueError("GCP_CREDENTIALS environment variable not set")


def get_drive_service():
    """Google Drive API servisi - singleton"""
    global _drive_service
    if _drive_service is None:
        credentials = get_credentials()
        authed_session = AuthorizedSession(credentials)

        class RequestsHttpAdapter:
            def __init__(self, session):
                self.session = session

            def request(self, uri, method='GET', body=None, headers=None, **kwargs):
                response = self.session.request(method, uri, data=body, headers=headers)
                return type('Response', (), {
                    'status': response.status_code,
                    'reason': response.reason
                })(), response.content

        _drive_service = build('drive', 'v3', http=RequestsHttpAdapter(authed_session))
    return _drive_service


def get_folder_ids() -> dict:
    """Alt klasör ID'lerini al - cached"""
    global _folder_ids_cache
    if _folder_ids_cache is None:
        service = get_drive_service()
        results = service.files().list(
            q=f"'{SHARED_DRIVE_ID}' in parents and mimeType='application/vnd.google-apps.folder' and trashed=false",
            fields="files(id, name)",
            supportsAllDrives=True,
            includeItemsFromAllDrives=True,
            corpora="drive",
            driveId=SHARED_DRIVE_ID
        ).execute()

        _folder_ids_cache = {}
        for folder in results.get('files', []):
            _folder_ids_cache[folder['name']] = folder['id']
    return _folder_ids_cache


def clear_cache():
    """Cache'i temizle"""
    global _folder_ids_cache, _cache, _cache_ttl
    _folder_ids_cache = None
    _cache = {}
    _cache_ttl = {}


def parse_frontmatter(content: str) -> tuple[dict, str]:
    """Frontmatter ve içeriği ayır"""
    frontmatter = {"proje": None, "created": None, "pinned": False}
    body = content

    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            fm_text = parts[1].strip()
            body = parts[2].strip()

            for line in fm_text.split("\n"):
                if ":" in line:
                    key, value = line.split(":", 1)
                    key = key.strip()
                    value = value.strip().strip('"').strip("'")
                    if key == "pinned":
                        frontmatter[key] = value.lower() == "true"
                    elif value.lower() in ("null", "none", ""):
                        frontmatter[key] = None if key != "pinned" else False
                    elif key in frontmatter:
                        frontmatter[key] = value

    return frontmatter, body


def create_frontmatter(proje: str = None, pinned: bool = False) -> str:
    """Yeni frontmatter oluştur"""
    today = datetime.now().strftime("%Y-%m-%d")
    proje_str = f'"{proje}"' if proje else "null"
    pinned_str = "true" if pinned else "false"
    return f"""---
proje: {proje_str}
created: {today}
pinned: {pinned_str}
---"""


def parse_body(body: str, fallback_title: str = "") -> tuple[str, str]:
    """Body'den başlık ve içerik ayır"""
    lines = body.split("\n")
    title = lines[0].replace("# ", "").strip() if lines and lines[0].strip() else fallback_title
    content = "\n".join(lines[1:]).strip() if len(lines) > 1 else ""
    return title, content


def generate_summary(content: str, max_chars: int = 200) -> str:
    """
    İçerikten özet üret.
    Strateji: İlk anlamlı paragraf + karakter limiti.
    """
    if not content or not content.strip():
        return ""

    # Paragraflarına ayır
    paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]

    if not paragraphs:
        paragraphs = [p.strip() for p in content.split('\n') if p.strip()]

    if not paragraphs:
        return ""

    summary = paragraphs[0]

    if len(summary) > max_chars:
        truncate_at = summary[:max_chars].rfind(' ')
        if truncate_at == -1:
            truncate_at = max_chars
        summary = summary[:truncate_at].rstrip('.,;:!?') + "..."

    return summary


def _fetch_file_content(service, file_info: dict) -> dict:
    """Tek dosyanın içeriğini çek ve parse et"""
    content = service.files().get_media(fileId=file_info['id']).execute().decode('utf-8')
    frontmatter, body = parse_frontmatter(content)
    title, body_content = parse_body(body, file_info['name'].replace('.md', ''))
    return {
        "id": file_info['id'],
        "filename": file_info['name'],
        "title": title,
        "content": body_content,
        "summary": generate_summary(body_content),
        "proje": frontmatter.get("proje"),
        "created": frontmatter.get("created"),
        "modified": file_info['modifiedTime'],
        "pinned": frontmatter.get("pinned", False),
    }


def _list_all_files(service, folder_id: str, fields: str = "nextPageToken, files(id, name, modifiedTime)") -> list[dict]:
    """Klasördeki tüm dosyaları pagination ile çek"""
    all_files = []
    page_token = None
    while True:
        results = service.files().list(
            q=f"'{folder_id}' in parents and trashed=false",
            fields=fields,
            orderBy="modifiedTime desc",
            pageSize=100,
            pageToken=page_token,
            supportsAllDrives=True,
            includeItemsFromAllDrives=True
        ).execute()
        all_files.extend(results.get('files', []))
        page_token = results.get('nextPageToken')
        if not page_token:
            break
    return all_files


def get_items(folder_type: str) -> list[dict]:
    """Google Drive'dan dosyaları çek (cached, paralel fetch)"""
    cache_key = f"items_{folder_type}"
    cached = get_cached(cache_key)
    if cached is not None:
        return cached

    service = get_drive_service()
    folder_ids = get_folder_ids()

    if folder_type not in folder_ids:
        return []

    folder_id = folder_ids[folder_type]
    all_files = _list_all_files(service, folder_id)

    # İçerikleri paralel çek (5 thread)
    items = []
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(_fetch_file_content, service, f): f for f in all_files}
        for future in as_completed(futures):
            items.append(future.result())

    # Sabitlenmiş öğeler üstte
    items.sort(key=lambda x: (not x.get("pinned", False)))
    set_cached(cache_key, items)
    return items


def get_item_count(folder_type: str) -> int:
    """Klasördeki dosya sayısını hızlıca al"""
    service = get_drive_service()
    folder_ids = get_folder_ids()

    if folder_type not in folder_ids:
        return 0

    all_files = _list_all_files(service, folder_ids[folder_type], fields="nextPageToken, files(id)")
    return len(all_files)


def get_all_counts() -> dict:
    """Tüm klasörlerin sayıları (cached)"""
    cache_key = "all_counts"
    cached = get_cached(cache_key)
    if cached is not None:
        return cached

    counts = {
        "inbox": get_item_count("inbox"),
        "notlar": get_item_count("notlar"),
        "gorevler": get_item_count("gorevler"),
        "arsiv": get_item_count("arsiv"),
        "cop_kutusu": get_item_count("cop_kutusu"),
    }
    set_cached(cache_key, counts)
    return counts


def get_items_filtered(folder_type: str, proje_filter: str = "Tümü") -> list[dict]:
    """Projeye göre filtrelenmiş öğeler"""
    items = get_items(folder_type)
    if proje_filter == "Tümü":
        return items
    elif proje_filter == "Projesi Yok":
        return [item for item in items if not item.get("proje")]
    elif proje_filter.endswith(" (Tümü)"):
        sirket = proje_filter.replace(" (Tümü)", "")
        return [item for item in items if item.get("proje") and item.get("proje").startswith(f"{sirket} - ")]
    else:
        return [item for item in items if item.get("proje") == proje_filter]


def _sanitize_title(title: str) -> str:
    """Başlıktan frontmatter injection'ı engelle"""
    # Satır sonlarını kaldır (frontmatter injection önlemi)
    return title.replace('\n', ' ').replace('\r', ' ').strip()


def _invalidate_items_cache():
    """Yazma işlemlerinden sonra item cache'lerini temizle"""
    keys_to_remove = [k for k in _cache if k.startswith("items_") or k == "all_counts"]
    for k in keys_to_remove:
        _cache.pop(k, None)
        _cache_ttl.pop(k, None)


def save_file(title: str, content: str, folder_type: str, proje: str = None, file_id: str = None, pinned: bool = False):
    """Dosya kaydet veya güncelle"""
    service = get_drive_service()
    folder_ids = get_folder_ids()

    title = _sanitize_title(title)
    frontmatter = create_frontmatter(proje, pinned)
    md_content = f"{frontmatter}\n\n# {title}\n\n{content}"

    media = MediaInMemoryUpload(md_content.encode('utf-8'), mimetype='text/markdown')

    if file_id:
        service.files().update(
            fileId=file_id,
            media_body=media,
            supportsAllDrives=True
        ).execute()
        _invalidate_items_cache()
        return file_id
    else:
        date_prefix = datetime.now().strftime("%Y-%m-%d")
        safe_title = "".join(c if c.isalnum() or c in (' ', '-', '_') else '_' for c in title)
        safe_title = safe_title[:50].strip().replace(" ", "-").lower()
        filename = f"{date_prefix}-{safe_title}.md"

        file_metadata = {
            'name': filename,
            'parents': [folder_ids[folder_type]],
            'mimeType': 'text/markdown'
        }
        result = service.files().create(
            body=file_metadata,
            media_body=media,
            supportsAllDrives=True
        ).execute()
        _invalidate_items_cache()
        return result.get('id')


def move_file(file_id: str, from_folder: str, to_folder: str):
    """Dosyayı klasörler arası taşı"""
    service = get_drive_service()
    folder_ids = get_folder_ids()

    service.files().update(
        fileId=file_id,
        addParents=folder_ids[to_folder],
        removeParents=folder_ids[from_folder],
        supportsAllDrives=True
    ).execute()
    _invalidate_items_cache()


def delete_file(file_id: str, folder_type: str):
    """Dosyayı çöp kutusuna taşı veya kalıcı sil"""
    service = get_drive_service()

    if folder_type == "cop_kutusu":
        service.files().delete(fileId=file_id, supportsAllDrives=True).execute()
        _invalidate_items_cache()
    else:
        move_file(file_id, folder_type, "cop_kutusu")


def get_file_parsed(file_id: str) -> tuple[dict, str, str]:
    """Dosyayı oku ve parse et: (frontmatter, title, body_content)"""
    service = get_drive_service()
    content = service.files().get_media(fileId=file_id).execute().decode('utf-8')
    frontmatter, body = parse_frontmatter(content)
    title, body_content = parse_body(body)
    return frontmatter, title, body_content


def update_proje(file_id: str, folder_type: str, proje: str):
    """Dosyanın projesini güncelle"""
    frontmatter, title, body_content = get_file_parsed(file_id)
    save_file(title, body_content, folder_type, proje, file_id, frontmatter.get("pinned", False))


def toggle_pin(file_id: str, folder_type: str) -> bool:
    """Dosyanın sabitleme durumunu değiştir, yeni durumu döndür"""
    frontmatter, title, body_content = get_file_parsed(file_id)
    new_pinned = not frontmatter.get("pinned", False)
    save_file(title, body_content, folder_type, frontmatter.get("proje"), file_id, new_pinned)
    return new_pinned


def get_or_create_folder(folder_name: str) -> str:
    """Klasörü al veya oluştur (export, logs vb.)"""
    service = get_drive_service()
    folder_ids = get_folder_ids()

    if folder_name in folder_ids:
        return folder_ids[folder_name]

    file_metadata = {
        'name': folder_name,
        'mimeType': 'application/vnd.google-apps.folder',
        'parents': [SHARED_DRIVE_ID]
    }
    folder = service.files().create(
        body=file_metadata,
        supportsAllDrives=True,
        fields='id'
    ).execute()

    # Cache güncelle
    global _folder_ids_cache
    if _folder_ids_cache:
        _folder_ids_cache[folder_name] = folder.get('id')

    return folder.get('id')


def export_items(items: list[dict], export_name: str) -> str:
    """Öğeleri tek bir markdown dosyasına export et"""
    service = get_drive_service()
    export_folder_id = get_or_create_folder("export")

    today = datetime.now().strftime("%Y-%m-%d %H:%M")
    content_lines = [f"# Export: {export_name}", f"Tarih: {today}", f"Toplam: {len(items)} öğe", "", "---", ""]

    for item in items:
        pinned_mark = "📌 " if item.get('pinned') else ""
        proje_mark = f" 📁 {item.get('proje')}" if item.get('proje') else ""
        content_lines.append(f"## {pinned_mark}{item['title']}{proje_mark}")
        content_lines.append("")
        if item.get('content'):
            content_lines.append(item['content'])
            content_lines.append("")
        content_lines.append("---")
        content_lines.append("")

    md_content = "\n".join(content_lines)

    safe_name = "".join(c if c.isalnum() or c in (' ', '-', '_') else '_' for c in export_name)
    filename = f"export-{datetime.now().strftime('%Y%m%d-%H%M')}-{safe_name[:30]}.md"

    media = MediaInMemoryUpload(md_content.encode('utf-8'), mimetype='text/markdown')
    file_metadata = {
        'name': filename,
        'parents': [export_folder_id],
        'mimeType': 'text/markdown'
    }
    service.files().create(
        body=file_metadata,
        media_body=media,
        supportsAllDrives=True
    ).execute()

    return filename


def get_sirket_options() -> list[str]:
    """Şirket listesi"""
    return ["Tümü", "Projesi Yok"] + list(SIRKET_PROJE_CONFIG.keys())


def get_proje_options(sirket: str = None) -> list[str]:
    """Proje seçenekleri"""
    if sirket and sirket in SIRKET_PROJE_CONFIG:
        options = [f"{sirket} (Tümü)"]
        for proje in SIRKET_PROJE_CONFIG[sirket]:
            options.append(f"{sirket} - {proje}")
        return options
    else:
        options = ["Tümü", "Projesi Yok"]
        for sirket, projeler in SIRKET_PROJE_CONFIG.items():
            for proje in projeler:
                options.append(f"{sirket} - {proje}")
        return options


def get_companies_with_counts() -> list[dict]:
    """Şirketler ve proje sayıları"""
    return [
        {"name": sirket, "count": len(projeler)}
        for sirket, projeler in SIRKET_PROJE_CONFIG.items()
    ]


# ============================================
# ERROR LOGGING - Google Drive'a kaydet
# ============================================

def log_error(error_type: str, message: str, details: dict = None):
    """Hatayı Drive'daki logs klasörüne kaydet"""
    try:
        service = get_drive_service()
        logs_folder_id = get_or_create_folder("logs")

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        date_str = datetime.now().strftime("%Y-%m-%d")

        log_entry = f"""## {timestamp} - {error_type}

**Message:** {message}

"""
        if details:
            log_entry += "**Details:**\n```json\n"
            log_entry += json.dumps(details, indent=2, ensure_ascii=False)
            log_entry += "\n```\n"

        log_entry += "\n---\n\n"

        # Bugünün log dosyasını bul veya oluştur
        filename = f"error-log-{date_str}.md"

        # Mevcut dosyayı ara
        results = service.files().list(
            q=f"'{logs_folder_id}' in parents and name='{filename}' and trashed=false",
            fields="files(id)",
            supportsAllDrives=True,
            includeItemsFromAllDrives=True
        ).execute()

        files = results.get('files', [])

        if files:
            # Mevcut dosyaya ekle
            file_id = files[0]['id']
            existing_content = service.files().get_media(fileId=file_id).execute().decode('utf-8')
            new_content = existing_content + log_entry
            media = MediaInMemoryUpload(new_content.encode('utf-8'), mimetype='text/markdown')
            service.files().update(
                fileId=file_id,
                media_body=media,
                supportsAllDrives=True
            ).execute()
        else:
            # Yeni dosya oluştur
            header = f"# Error Log - {date_str}\n\n"
            content = header + log_entry
            media = MediaInMemoryUpload(content.encode('utf-8'), mimetype='text/markdown')
            file_metadata = {
                'name': filename,
                'parents': [logs_folder_id],
                'mimeType': 'text/markdown'
            }
            service.files().create(
                body=file_metadata,
                media_body=media,
                supportsAllDrives=True
            ).execute()

        return True
    except Exception as e:
        # Log yazarken hata olursa sessizce geç
        print(f"Error logging failed: {e}")
        return False
