# Kişisel Not Defterim - Kurallar

## Proje Yapısı

**GitHub Repository:**
```
alylmz-kisisel-not-defterim/
├── main.py                 # FastAPI backend
├── app.py                  # Eski Streamlit uygulaması (yedek)
├── logo.webp               # BEIREK logosu
├── requirements-fastapi.txt # FastAPI bağımlılıklar
├── requirements.txt        # Streamlit bağımlılıklar (eski)
├── render.yaml             # Render.com deployment config
├── run_local.sh            # Lokal geliştirme scripti (git'e dahil değil)
├── rules.md                # Bu dosya
├── sirketler_projeler.md   # Şirket & Proje indeksi
├── services/
│   ├── __init__.py
│   └── drive.py            # Google Drive API servisleri
├── static/
│   ├── index.html          # SPA frontend (Tailwind + Alpine.js)
│   └── logo.webp           # Logo kopyası
└── .streamlit/
    └── secrets.toml        # Gizli anahtarlar (git'e dahil değil)
```

**Google Workspace Shared Drive (Veri):**
```
aliyilmaz-kisisel-not-defterim/    # Shared Drive ID: 0AFbVhvJLQtOHUk9PVA
├── inbox/                          # 📥 Gelen kutusu
├── notlar/                         # 📝 Notlar
├── gorevler/                       # ✅ Görevler
├── arsiv/                          # 📦 Arşiv (tamamlanan görevler)
├── cop_kutusu/                     # 🗑️ Çöp kutusu (silinen öğeler)
└── export/                         # 📤 Export dosyaları
```

## Mimari

### Yeni Mimari (FastAPI + Tailwind + Alpine.js)

**Backend:** FastAPI (Python)
- REST API endpointleri
- Google Drive API entegrasyonu
- Environment variable ile credentials

**Frontend:** Single Page Application (SPA)
- Tailwind CSS (CDN)
- Alpine.js (reaktif UI)
- Mobile-first tasarım
- iPhone 15 optimizasyonu

### Google Drive API (Single Source of Truth)

Uygulama Google Drive API v3 kullanır. Tüm veri işlemleri Google Workspace Shared Drive üzerinden yapılır.

**Neden Shared Drive?**
- Service Account'lar normal Drive'da storage quota'ya sahip değil
- Workspace Shared Drive bu kısıtlamayı aşar
- info@beirek.com Workspace hesabı üzerinden

**Service Account:**
```
notlarim-drive@aliyilmaz-kisisel-not-defterim.iam.gserviceaccount.com
```

**API Konfigürasyonu:**
```python
SCOPES = ['https://www.googleapis.com/auth/drive']
SHARED_DRIVE_ID = "0AFbVhvJLQtOHUk9PVA"

# Tüm API çağrılarında gerekli parametreler:
supportsAllDrives=True
includeItemsFromAllDrives=True
```

## API Endpointleri

| Method | Endpoint | Açıklama |
|--------|----------|----------|
| GET | `/api/auth?key=xxx` | Authentication |
| GET | `/api/counts?key=xxx` | Tüm klasör sayıları |
| GET | `/api/items/{folder}?key=xxx&filter=Tümü` | Klasör öğeleri |
| POST | `/api/items?key=xxx` | Yeni öğe oluştur |
| PUT | `/api/items/{id}?key=xxx&folder=xxx` | Öğe güncelle |
| POST | `/api/items/{id}/move?key=xxx` | Öğe taşı |
| POST | `/api/items/{id}/pin?key=xxx&folder=xxx` | Sabitleme toggle |
| POST | `/api/items/{id}/proje?key=xxx` | Proje ata |
| DELETE | `/api/items/{id}?key=xxx&folder=xxx` | Öğe sil |
| GET | `/api/companies?key=xxx` | Şirket listesi |
| GET | `/api/projects?key=xxx&company=xxx` | Proje listesi |
| GET | `/api/config?key=xxx` | Şirket-proje config |
| POST | `/api/export?key=xxx` | Filtrelenmiş export |
| POST | `/api/refresh?key=xxx` | Cache temizle |

## Deployment

### Render.com (Aktif)

**URL:** https://alylmz-kisisel-not-defterim.onrender.com

**Erişim:**
- Direkt: https://alylmz-kisisel-not-defterim.onrender.com?key=1102
- Şifreli: https://alylmz-kisisel-not-defterim.onrender.com → `1102` gir

**Build Command:** `pip install -r requirements-fastapi.txt`

**Start Command:** `uvicorn main:app --host 0.0.0.0 --port $PORT`

**Environment Variables:**
- `APP_SECRET_KEY`: Erişim şifresi (1102)
- `GCP_CREDENTIALS`: Service account JSON

**GitHub Repo:** https://github.com/aliyilmazq/alylmz-kisisel-not-defterim (public)

### Streamlit Cloud (Eski - Devre Dışı)

**URL:** https://aliyilmaznotdefterim.streamlit.app/

## Erişim Kontrolü

İki yöntemli authentication:

1. **URL Parametresi:** `?key=1102` - Tarayıcı bookmark için
2. **Şifre Formu:** Ana ekrana eklendiğinde şifre gir, session boyunca hatırla

## UI / UX

### Header

```
[BEIREK Logo]  [🔄 Yenile] [＋ Yeni] (mavi buton)
```

### Tab Menü

```
📥 Gelen (3) | 📝 Not (5) | ✅ Görev (2) | 📦 Arşiv (1) | 🗑️ Çöp (0)
```

| Tab | Açıklama |
|-----|----------|
| 📥 Gelen | Yeni girişler burada bekler |
| 📝 Not | Kalıcı notlar |
| ✅ Görev | Yapılacaklar |
| 📦 Arşiv | Tamamlanan görevler |
| 🗑️ Çöp | Silinen öğeler |

### Kart Görünümü

```
📌 Başlık (sabitlendiyse)                  📁 (proje varsa)
─────────────────────────────────────────
📁 Proje Adı (varsa)
Açıklama (max 2 satır)
─────────────────────────────────────────
[Aksiyon butonları]
```

### Aksiyonlar (Sadece İkon)

- **Gelen Kutusu:** `📝 | ✅ | ✏️ | 🗑️`
- **Notlar:** `📌 | 📥 | ✅ | 📁 | ✏️ | 🗑️`
- **Görevler:** `📌 | ✔️ | 📝 | 📥 | 📁 | ✏️ | 🗑️`
- **Arşiv:** `↩️ | 🗑️`
- **Çöp:** `↩️ | 🗑️`

| İkon | Anlam |
|------|-------|
| 📝 | Not'a taşı |
| 📥 | Gelen'e taşı |
| ✅ | Görev'e taşı |
| ✔️ | Tamamla (Arşiv'e) |
| 📌 | Sabitle/Kaldır |
| 📁 | Proje ata |
| ✏️ | Düzenle |
| 🗑️ | Sil |
| ↩️ | Geri al |

### iPhone 15 Optimizasyonları

- Safe area desteği (notch, home indicator)
- Kompakt padding ve spacing
- Touch-friendly minimum 44px yükseklik
- Inter font ailesi
- viewport-fit=cover
- apple-mobile-web-app-capable

## Dosya Formatı

**Dosya adı:** `2026-02-02-baslik.md`

```markdown
---
proje: "ENVEX - BHP Escondida Sözleşme Yönetimi"
created: 2026-02-02
pinned: false
---

# Başlık

İçerik buraya...
```

## Akış

```
Yeni Giriş → 📥 Gelen Kutusu → 📝 Not veya ✅ Görev
                                      │
                                      ▼
                              📁 Projeye ekle (opsiyonel)
                                      │
                                      ▼
                              Görev tamamlandı
                                      │
                                      ▼
                               📦 Arşiv
```

## Şirket & Proje Yapısı

**10 Şirket, 38 Proje**

```python
SIRKET_PROJE_CONFIG = {
    "ENVEX": [12 proje],
    "COREX": [3 proje],
    "TIS": [7 proje],
    "MIM": [1 proje],
    "TEMROB": [2 proje],
    "PULCHRANI": [2 proje],
    "ALI YILMAZ": [7 proje],
    "EPIOQN": [1 proje],
    "PULPO": [2 proje],
    "OZMEN": [1 proje],
}
```

> Detaylı liste için bkz: `sirketler_projeler.md`

### Filtre UI (Not ve Görev tab'larında)

Hiyerarşik popover filtre (Şirket → Proje):

**Birinci seviye (Şirketler):**
```
[🔽 Tümü]
├── Tümü
├── Projesi Yok
├── ENVEX (12) →
├── COREX (3) →
└── ...
```

**İkinci seviye (Projeler):**
```
[🔽 ENVEX]
├── ← Geri
├── ENVEX (Tümü)     ← Şirketin tüm notları
├── BHP Escondida...
└── ...
```

### Export Özelliği

Filtre yanındaki 📤 butonu ile filtrelenmiş öğeler export edilir:

- Export dosyası Drive'da `export/` klasörüne kaydedilir
- Dosya formatı: `export-YYYYMMDD-HHMM-filtre-adi.md`
- Tüm öğeler tek markdown dosyasında birleştirilir

### Sabitleme (Pin) Özelliği

📌 butonu ile not/görev sabitlenir:
- Sabitli öğeler listenin en üstünde görünür
- Başlıkta 📌 ikonu gösterilir
- Tekrar basınca sabitleme kalkar
- Frontmatter: `pinned: true/false`

## Servis Modülü (services/drive.py)

Tüm Drive işlemleri bu modülde:

```python
# Drive Service
get_drive_service() -> googleapiclient.discovery.Resource
get_credentials() -> Credentials

# Veri Çekme
get_folder_ids() -> dict[str, str]
get_item_count(folder_type: str) -> int
get_items(folder_type: str) -> list[dict]
get_items_filtered(folder_type: str, proje_filter: str) -> list[dict]
get_all_counts() -> dict

# Dosya İşlemleri
save_file(title, content, folder_type, proje=None, file_id=None, pinned=False)
move_file(file_id, from_folder, to_folder)
delete_file(file_id, folder_type)
update_proje(file_id, folder_type, proje)
toggle_pin(file_id, folder_type) -> bool

# Parsing
parse_frontmatter(content: str) -> tuple[dict, str]
create_frontmatter(proje: str = None, pinned: bool = False) -> str
parse_body(body: str, fallback_title: str) -> tuple[str, str]

# Export
export_items(items: list[dict], export_name: str) -> str
get_or_create_export_folder() -> str

# Config
get_sirket_options() -> list[str]
get_proje_options(sirket: str = None) -> list[str]
get_companies_with_counts() -> list[dict]
clear_cache()
```

## Gereksinimler (FastAPI)

```
fastapi>=0.109.0
uvicorn[standard]>=0.27.0
google-api-python-client>=2.100.0
google-auth>=2.23.0
requests>=2.31.0
python-multipart>=0.0.6
```

## Lokal Geliştirme

```bash
cd /Users/alylmztr/Documents/GitHub/alylmz-kisisel-not-defterim

# Environment variables ayarla
export APP_SECRET_KEY="1102"
export GCP_CREDENTIALS='{"type":"service_account",...}'

# Sunucuyu başlat
uvicorn main:app --reload --port 8510
```

**URL:** http://localhost:8510?key=1102

## Git İşlemleri

```bash
# Değişiklikleri geri al
git reset --hard <commit_hash> && git push --force

# Son commit'i geri al
git revert HEAD --no-edit && git push
```
