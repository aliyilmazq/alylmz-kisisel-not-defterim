# Kişisel Not Defterim - Kurallar

## Proje Yapısı

**GitHub Repository:**
```
alylmz-kisisel-not-defterim/
├── main.py                 # FastAPI backend (cookie-based auth, CORS)
├── logo.webp               # BEIREK logosu
├── requirements.txt        # FastAPI bağımlılıklar
├── render.yaml             # Render.com deployment config
├── backup_to_icloud.sh     # iCloud yedekleme scripti
├── com.alylmz.notdefteri.backup.plist  # launchd zamanlayıcı
├── run_local.sh            # Lokal geliştirme scripti (git'e dahil değil)
├── not-defterim.command    # macOS başlatma scripti (çift tıkla)
├── rules.md                # Bu dosya
├── sirketler_projeler.md   # Şirket & Proje indeksi
├── services/
│   ├── __init__.py
│   └── drive.py            # Google Drive API servisleri + error logging
└── static/
    ├── index.html          # SPA frontend (Tailwind + Alpine.js)
    └── logo.webp           # Logo kopyası
```

**Google Workspace Shared Drive (Veri):**
```
aliyilmaz-kisisel-not-defterim/    # Shared Drive ID: 0AFbVhvJLQtOHUk9PVA
├── inbox/                          # 📥 Gelen kutusu
├── notlar/                         # 📝 Notlar
├── gorevler/                       # ✅ Görevler
├── arsiv/                          # 📦 Arşiv (tamamlanan görevler)
├── cop_kutusu/                     # 🗑️ Çöp kutusu (silinen öğeler)
├── export/                         # 📤 Export dosyaları
└── logs/                           # 🔴 Hata logları (otomatik)
```

## Mimari

### Yeni Mimari (FastAPI + Tailwind + Alpine.js)

**Backend:** FastAPI (Python)
- REST API endpointleri
- Google Drive API entegrasyonu
- Environment variable ile credentials

**Frontend:** Single Page Application (SPA)
- Tailwind CSS (CDN + safelist)
- Alpine.js (reaktif UI + store)
- Mobile-first tasarım
- iPhone 15 optimizasyonu
- **CONFIG-driven mimari** (tek kaynak ilkesi)

**Tailwind Safelist (dinamik class'lar için):**
```javascript
tailwind.config = {
    safelist: [
        'grid-cols-1', 'grid-cols-2', 'grid-cols-3', 'grid-cols-4', 'grid-cols-5',
        'line-clamp-1', 'line-clamp-2', 'line-clamp-3', 'line-clamp-4', 'line-clamp-5'
    ]
}
```

### CONFIG-Driven Mimari (Single Source of Truth)

Frontend'de tüm davranışlar tek bir CONFIG objesi üzerinden yönetilir:

```javascript
const CONFIG = {
    // Kart görünüm ayarları
    card: {
        showDate: true,       // Tarih göster
        contentLines: 2,      // Sabit içerik satır sayısı
        expandable: true,     // Genişlet/daralt özelliği
        summaryMaxChars: 200  // Özet karakter limiti (backend ile eşleşir)
    },
    // Tab düzeni
    tabs: {
        row1: 3,              // İlk satır tab sayısı
        row2: 2               // İkinci satır tab sayısı
    },
    // Klasör bazlı aksiyonlar
    actions: {
        inbox: [[...row1_actions...]],
        notlar: [[...row1...], [...row2...]],
        gorevler: [[...row1...], [...row2...]],
        arsiv: [[...actions...]],
        cop_kutusu: [[...actions...]]
    }
};
```

**Avantajları:**
- Yeni aksiyon eklemek için sadece CONFIG'e satır ekle
- Tab düzeni değişikliği: `row1/row2` değerlerini değiştir
- Kart görünümü: `card` ayarlarını değiştir
- Kod tekrarı yok (5 ayrı template yerine tek template)
- 170 satır kod azalması

**Merkezi Fonksiyonlar:**

```javascript
// Tüm API çağrıları tek fonksiyondan (cookie credentials ile)
api(method, url, body = null)  // credentials: 'same-origin'

// Aksiyon butonları CONFIG'den alınır
getActions() → CONFIG.actions[activeTab]

// Tüm aksiyonlar tek dispatcher'dan
executeAction(actionId, item) → switch/case ile yönlendir

// Tab satırları tek fonksiyondan
getTabRows() → [[row1 tabs], [row2 tabs]]

// Tarih formatı Türkçe
formatDate("2026-02-02") → "2 Şubat"

// İçerik genişletme kontrolü (summary/content karşılaştırır)
needsExpand(item) → summary !== content veya satır sayısı > contentLines
```

### Tek Kaynak Bileşenler

Tüm tekrar eden UI pattern'leri tek fonksiyondan üretilir:

```javascript
// Hiyerarşik Dropdown (Filtre + Proje Seçimi)
function hierarchicalDropdown(mode) {
    return {
        selectedCompany: null,
        drillDown(company) { this.selectedCompany = company; },
        goBack() { this.selectedCompany = null; },
        select(value) {
            if (mode === 'filter') this.$store.app.setFilter(value);
            if (mode === 'proje') this.$store.app.setProje(value);
            this.open = false;
        }
    };
}
```

**Tek Kaynak Listesi:**

| Bileşen | Fonksiyon | Kullanım |
|---------|-----------|----------|
| Kartlar | Tek template | Tüm tab'larda aynı kart |
| Tab butonları | `getTabRows()` | 2 satır, CONFIG'den |
| Aksiyonlar | `getActions()` + `executeAction()` | Tab'a göre butonlar |
| Hiyerarşik dropdown | `hierarchicalDropdown(mode)` | Filtre + Proje modal |
| API çağrıları | `api()` | Tüm HTTP istekleri |
| Cache | `getCached()` / `setCached()` | localStorage |

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
SHARED_DRIVE_ID = os.environ.get("SHARED_DRIVE_ID", "0AFbVhvJLQtOHUk9PVA")

# Tüm API çağrılarında gerekli parametreler:
supportsAllDrives=True
includeItemsFromAllDrives=True
```

## API Endpointleri

**Authentication:** Cookie-based (httpOnly, samesite=strict, 30 gün TTL).
Tüm endpointler `notdefteri_key` cookie'si ile korunur.

| Method | Endpoint | Açıklama |
|--------|----------|----------|
| POST | `/api/auth` | Login - cookie set eder (body: `{key}`) |
| GET | `/api/auth` | Cookie doğrulama |
| GET | `/api/counts` | Tüm klasör sayıları |
| GET | `/api/items/{folder}?filter=Tümü` | Klasör öğeleri |
| POST | `/api/items` | Yeni öğe oluştur |
| PUT | `/api/items/{id}?folder=xxx` | Öğe güncelle |
| POST | `/api/items/{id}/move` | Öğe taşı |
| POST | `/api/items/{id}/pin?folder=xxx` | Sabitleme toggle |
| POST | `/api/items/{id}/proje` | Proje ata |
| DELETE | `/api/items/{id}?folder=xxx` | Öğe sil |
| GET | `/api/companies` | Şirket listesi |
| GET | `/api/projects?company=xxx` | Proje listesi |
| GET | `/api/config` | Şirket-proje config |
| POST | `/api/export` | Filtrelenmiş export |
| POST | `/api/refresh` | Cache temizle |

## Deployment

### Render.com (Aktif)

**URL:** https://alylmz-kisisel-not-defterim.onrender.com

**Erişim:** Login formu ile giriş yap (cookie-based auth)

**Build Command:** `pip install -r requirements.txt`

**Start Command:** `uvicorn main:app --host 0.0.0.0 --port $PORT`

**Environment Variables (zorunlu):**
- `APP_SECRET_KEY`: Erişim şifresi (uygulama bu olmadan başlamaz)
- `GCP_CREDENTIALS`: Service account JSON
- `ALLOWED_ORIGINS`: (opsiyonel) CORS izinli origin'ler (virgülle ayrılmış)
- `SHARED_DRIVE_ID`: (opsiyonel) Google Drive ID (varsayılan mevcut)

**GitHub Repo:** https://github.com/aliyilmazq/alylmz-kisisel-not-defterim (public)

## Erişim Kontrolü

**Cookie-based authentication:**

1. **Login formu:** Şifre gir → `POST /api/auth` → httpOnly cookie set edilir
2. **Cookie:** `notdefteri_key` (httpOnly, samesite=strict, 30 gün TTL)
3. **Auto-login:** Sayfa yüklendiğinde cookie varsa otomatik doğrulama
4. **Auth expiry:** Keep-alive ping başarısız olursa login ekranına döner

## UI / UX

### Header

```
[BEIREK Logo]                    [🔄 Yenile]
```

### Hızlı Not Girişi

Uygulama açıldığında direkt metin kutusu:
```
[Hızlı not ekle...                    ] [Kaydet]
```

- İlk satır = başlık, geri kalan = içerik
- **Cmd+Enter** ile hızlı kaydet
- Inbox'a otomatik kaydedilir

### Tab Menü (2 Satır)

```
📥 Gelen (3) | 📝 Not (5) | ✅ Görev (2)
     📦 Arşiv (1)   |   🗑️ Çöp (0)
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
📁 ENVEX - Proje Adı (truncate)  •  2 Şubat
Açıklama metni burada görünür...
[▼ Devamını gör]
─────────────────────────────────────────
[📌 Sabitle] [📁 Proje] [✅ Görev]
[📥 Gelen]   [✏️ Düzenle] [🗑️ Sil]
```

**CONFIG Ayarları:**
```javascript
CONFIG.card = {
    showDate: true,      // Tarih göster (Türkçe format)
    contentLines: 2,     // Kaç satır göster
    expandable: true     // Genişlet butonu
}
```

**Kart Helper Fonksiyonları:**

| Fonksiyon | Açıklama |
|-----------|----------|
| `formatDate(dateStr)` | "2026-02-02" → "2 Şubat" |
| `needsExpand(content)` | Satır/karakter kontrolü |
| `.truncate-proje` | Uzun proje adları için CSS |

**CSS Utilities:**
```css
.line-clamp-1 ... .line-clamp-5  /* İçerik kısıtlama */
.truncate-proje { max-width: 200px; ... }  /* Proje adı */
.whitespace-pre-wrap  /* Satır sonları koru */
.break-words  /* Uzun kelimeler */
```

### Aksiyonlar (İkon + İsim, 2 Satır)

**Gelen Kutusu:**
```
📝 Not | ✅ Görev | ✏️ Düzenle | 🗑️ Sil
```

**Notlar:**
```
📌 Sabitle | 📁 Proje | ✅ Görev
📥 Gelen  | ✏️ Düzenle | 🗑️ Sil
```

**Görevler:**
```
📌 Sabitle | ✔️ Tamam | 📁 Proje | 📝 Not
📥 Gelen  | ✏️ Düzenle | 🗑️ Sil
```

**Arşiv / Çöp:**
```
↩️ Geri Al | 🗑️ Sil
```

### Hiyerarşik Dropdown (Tek Kaynak)

Filtre ve Proje seçimi aynı component'ı kullanır:

```javascript
// Kullanım
x-data="hierarchicalDropdown('filter')"  // Filtre için
x-data="hierarchicalDropdown('proje')"   // Proje seçimi için
```

**Akış:**
1. Önce şirket listesi gösterilir
2. Şirkete tıklayınca projeleri açılır
3. ← Geri ile şirket listesine dön
4. Seçim yapınca mode'a göre `setFilter()` veya `setProje()` çağrılır

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

# Veri Çekme (paralel fetch, pagination)
get_folder_ids() -> dict[str, str]
get_item_count(folder_type: str) -> int
get_items(folder_type: str) -> list[dict]         # ThreadPoolExecutor(5) ile paralel
get_items_filtered(folder_type: str, proje_filter: str) -> list[dict]
get_all_counts() -> dict
_list_all_files(service, folder_id, fields) -> list[dict]  # pageSize=100 + nextPageToken
_fetch_file_content(service, file_info) -> dict

# Dosya İşlemleri (her biri cache invalidation yapar)
save_file(title, content, folder_type, proje=None, file_id=None, pinned=False)
move_file(file_id, from_folder, to_folder)
delete_file(file_id, folder_type)
update_proje(file_id, folder_type, proje)
toggle_pin(file_id, folder_type) -> bool
get_file_parsed(file_id) -> tuple[dict, str, str]  # Dosya oku + parse et

# Parsing & Sanitization
parse_frontmatter(content: str) -> tuple[dict, str]
create_frontmatter(proje: str = None, pinned: bool = False) -> str
parse_body(body: str, fallback_title: str) -> tuple[str, str]
_sanitize_title(title: str) -> str  # Frontmatter injection önlemi

# Cache
_invalidate_items_cache()  # Yazma sonrası seçici cache temizleme

# Klasör & Export
get_or_create_folder(folder_name: str) -> str  # export, logs vb.
export_items(items: list[dict], export_name: str) -> str

# Config
get_sirket_options() -> list[str]
get_proje_options(sirket: str = None) -> list[str]
get_companies_with_counts() -> list[dict]
clear_cache()
```

## Summary Pipeline

Notlar/kartlar için özet (summary) sistemi. Kart önizlemelerinde tam içerik yerine özet gösterilir.

### Backend (services/drive.py)

```python
generate_summary(content: str, max_chars: int = 200) -> str
```

**Strateji:**
1. İçerik paragraflara ayrılır (`\n\n` ile)
2. İlk anlamlı paragraf alınır
3. 200 karakteri aşarsa kelime sınırında kesilir ve "..." eklenir

**API yanıtı:**
```json
{
    "id": "file_id",
    "title": "Başlık",
    "content": "Tam içerik...",
    "summary": "İlk paragraftan üretilen özet...",
    ...
}
```

### Frontend (static/index.html)

**Varsayılan görünüm:** `item.summary` (veya fallback: `item.content`)
**Genişletilmiş görünüm:** `item.content`

```javascript
// Kart body'sinde:
x-text="expanded ? item.content : (item.summary || item.content)"

// Genişletme butonu kontrolü:
needsExpand(item) {
    if (item.summary && item.summary !== item.content) return true;
    // Fallback: satır/karakter kontrolü
}
```

**CONFIG ayarı:**
```javascript
CONFIG.card.summaryMaxChars = 200  // Backend ile eşleşir
```

### quickSave() ile Summary

Hızlı not kaydında client-side summary üretilir (optimistic UI için):

```javascript
const summary = content.length > 200 ? content.substring(0, 197) + '...' : content;
```

API çağrısından sonra backend'den gerçek summary gelir.

## Performans Optimizasyonları

### Backend Cache (TTL + Invalidation)

```python
CACHE_DURATION = 30  # seconds

# Cached fonksiyonlar:
get_items(folder_type)      # 30sn cache
get_all_counts()            # 30sn cache

# Yazma sonrası otomatik cache invalidation:
_invalidate_items_cache()   # save_file, move_file, delete_file sonrası çağrılır

# Manuel cache temizleme:
clear_cache()               # Tüm cache sıfırlanır
```

### Paralel Content Fetch

```python
# N+1 query problemi: Her dosya için ayrı API çağrısı
# Çözüm: ThreadPoolExecutor ile 5 paralel thread
with ThreadPoolExecutor(max_workers=5) as executor:
    futures = {executor.submit(_fetch_file_content, service, f): f for f in all_files}
    for future in as_completed(futures):
        items.append(future.result())
```

### Pagination

```python
# Google Drive API pageSize=100 + nextPageToken döngüsü
# Büyük klasörlerde tüm dosyaların çekilmesini garanti eder
_list_all_files(service, folder_id, fields)
```

### Frontend Cache (localStorage)

```javascript
// Cache-first strateji:
// 1. Önce localStorage'dan göster (anlık)
// 2. API'den çek ve güncelle
// 3. localStorage'a kaydet

getCached(key)              // Cache'den oku
setCached(key, data, ttl)   // Cache'e yaz (30sn TTL)
clearLocalCache()           // Tüm local cache sil
```

### Keep-Alive Ping

```javascript
// Her 5 dakikada bir API'ye ping
// Render.com cold start'ı önler + auth expiry kontrolü
setInterval(() => {
    if (this.authenticated) {
        this.api('GET', '/api/auth').catch(() => {
            this.authenticated = false;
            this.loginError = 'Oturum süresi doldu, tekrar giriş yapın';
        });
    }
}, 5 * 60 * 1000);
```

### Skeleton Loading

Yükleme sırasında animasyonlu placeholder kartlar:

```css
.skeleton {
    background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
    background-size: 200% 100%;
    animation: skeleton-loading 1.5s infinite;
}
```

- "Yükleniyor..." yerine gri kartlar gösterilir
- Kullanıcı içeriğin geleceğini görsel olarak anlar

### Arka Plan Prefetch

```javascript
prefetchTabs() {
    // Aktif tab dışındaki tab'ları arka planda yükle
    const otherTabs = ['inbox', 'notlar', 'gorevler'].filter(t => t !== this.activeTab);
    otherTabs.forEach(tab => {
        this.api('GET', `/api/items/${tab}?filter=Tümü`)
            .then(items => this.setCached(`items_${tab}_Tümü`, items));
    });
}
```

- Giriş yapınca diğer tab'lar arka planda cache'lenir
- Tab geçişi anında olur

### Gzip Sıkıştırma

```python
# main.py
from fastapi.middleware.gzip import GZipMiddleware
app.add_middleware(GZipMiddleware, minimum_size=500)
```

- 500 byte üzeri API yanıtları sıkıştırılır
- Veri transferi azalır

### Optimistic UI

Tüm aksiyonlar anında UI'da yansır, API arka planda çalışır:

```javascript
// Örnek: togglePin
async togglePin(item) {
    // 1. Önce UI güncelle (anlık)
    item.pinned = !item.pinned;
    this.items = [...this.items].sort((a, b) => (b.pinned ? 1 : 0) - (a.pinned ? 1 : 0));

    // 2. API arka planda (hata olursa reload)
    this.api('POST', `/api/items/${item.id}/pin?folder=${this.activeTab}`)
        .catch(e => this.loadItems());
}
```

**Optimistic aksiyonlar:**
- `togglePin`: Anlık toggle ve sıralama
- `moveItem`: Anlık listeden kaldırma + count güncelleme
- `deleteItem`: Anlık listeden kaldırma + count güncelleme
- `setProje`: Anlık proje güncelleme
- `saveItem` (edit): Anlık başlık/içerik güncelleme
- `quickSave`: Anlık listeye ekleme

**Hata durumunda kurtarma:** Tüm optimistic aksiyonlarda API hatası olursa hem `loadItems()` hem `loadCounts()` çağrılarak gerçek duruma geri dönülür.

### Yenile Butonu

- Backend cache temizler
- localStorage cache temizler
- Tüm veriyi yeniden çeker

## Gereksinimler (requirements.txt)

```
fastapi>=0.109.0
uvicorn[standard]>=0.27.0
google-api-python-client>=2.100.0
google-auth>=2.23.0
requests>=2.31.0
python-multipart>=0.0.6
```

## Lokal Geliştirme

### Tek Doğru Başlatma Yöntemi

**Komut dosyası:** `not-defterim.command` (çift tıkla)
- `run_local.sh`'den `APP_SECRET_KEY` ve `GCP_CREDENTIALS` otomatik yüklenir
- Tarayıcı http://localhost:8510 adresine açılır
- Login formu ile giriş yap

veya

**Terminal:**
```bash
cd /Users/alylmztr/Documents/GitHub/alylmz-kisisel-not-defterim
source run_local.sh  # APP_SECRET_KEY ve GCP_CREDENTIALS export eder
uvicorn main:app --host 0.0.0.0 --port 8510
```

**URL:** http://localhost:8510

### Geliştirici Modu (hot-reload)

```bash
uvicorn main:app --reload --port 8510
```

## Error Logging

Tüm hatalar otomatik olarak Google Drive'daki `logs/` klasörüne kaydedilir.

**Dosya formatı:** `error-log-YYYY-MM-DD.md`

```python
# services/drive.py
log_error(error_type, message, details)

# main.py - Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    log_error(type(exc).__name__, str(exc), {...})
```

**Log içeriği:**
- Tarih/saat
- Hata tipi
- Hata mesajı
- URL ve method
- Detaylar (JSON)

## iCloud Yedekleme

Google Drive'dan iCloud'a otomatik sync:

**Script:** `backup_to_icloud.sh`
```bash
# Manuel çalıştır
./backup_to_icloud.sh

# Otomatik (her 30 dk)
cp com.alylmz.notdefteri.backup.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.alylmz.notdefteri.backup.plist
```

**Sync edilen klasörler:**
- inbox/ → iCloud/inbox/
- notlar/ → iCloud/notlar/
- gorevler/ → iCloud/gorevler/
- arsiv/ → iCloud/arsiv/
- export/ → iCloud/export/
- logs/ → iCloud/logs/

**Dizinler:**
```
Google Drive: /Users/alylmztr/Library/CloudStorage/GoogleDrive-.../alylmz-kisisel-not-defterim/
iCloud:       /Users/alylmztr/Library/Mobile Documents/com~apple~CloudDocs/alylmz-kisisel-not-defterim/
```

## Git İşlemleri

```bash
# Değişiklikleri geri al
git reset --hard <commit_hash> && git push --force

# Son commit'i geri al
git revert HEAD --no-edit && git push
```

## Claude Code Tercihleri

**Otomatik İşlemler (sormadan yap):**
- Git commit ve push - değişiklik yapıldığında otomatik commit at ve push et
- Render MCP - deploy durumu kontrolü, log okuma vb. için her zaman MCP kullan
- Bu dosyayı (rules.md) güncel tut
