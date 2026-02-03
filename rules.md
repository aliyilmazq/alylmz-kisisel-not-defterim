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
- **CONFIG-driven mimari** (tek kaynak ilkesi)

### CONFIG-Driven Mimari (Single Source of Truth)

Frontend'de tüm davranışlar tek bir CONFIG objesi üzerinden yönetilir:

```javascript
const CONFIG = {
    // Kart görünüm ayarları
    card: {
        showDate: true,       // Tarih göster
        contentLines: 2,      // Sabit içerik satır sayısı
        expandable: true      // Genişlet/daralt özelliği
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
// Tüm API çağrıları tek fonksiyondan
api(method, url, body = null)

// Aksiyon butonları CONFIG'den alınır
getActions() → CONFIG.actions[activeTab]

// Tüm aksiyonlar tek dispatcher'dan
executeAction(actionId, item) → switch/case ile yönlendir
```

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
📁 Proje Adı (varsa)
📅 Tarih (CONFIG.card.showDate)
Açıklama (max 2 satır, genişletilebilir)  [▼/▲]
─────────────────────────────────────────
[Aksiyon butonları - 2 satır]
```

**Kart Özellikleri:**
- Tarih gösterimi: `CONFIG.card.showDate`
- İçerik satır limiti: `CONFIG.card.contentLines`
- Genişlet/daralt: `CONFIG.card.expandable` (uzun içerikler için)

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

### Proje Seçimi (Hiyerarşik)

Filtre ile aynı mantık:
1. Önce şirket listesi gösterilir
2. Şirkete tıklayınca projeleri açılır
3. ← Geri ile şirket listesine dön

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

## Performans Optimizasyonları

### Backend Cache (TTL)

```python
CACHE_DURATION = 30  # seconds

# Cached fonksiyonlar:
get_items(folder_type)      # 30sn cache
get_all_counts()            # 30sn cache

# Cache temizleme:
clear_cache()               # Tüm cache sıfırlanır
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
// Render.com cold start'ı önler
setInterval(() => fetch('/api/auth?key=...'), 5 * 60 * 1000);
```

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
- `moveItem`: Anlık listeden kaldırma
- `deleteItem`: Anlık listeden kaldırma
- `setProje`: Anlık proje güncelleme
- `saveItem` (edit): Anlık başlık/içerik güncelleme
- `quickSave`: Anlık listeye ekleme

### Yenile Butonu

- Backend cache temizler
- localStorage cache temizler
- Tüm veriyi yeniden çeker

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
