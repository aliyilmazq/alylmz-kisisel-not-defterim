# Kişisel Not Defterim - Kurallar

## Proje Yapısı

**GitHub Repository:**
```
alylmz-kisisel-not-defterim/
├── app.py                  # Streamlit uygulaması
├── logo.webp               # BEIREK logosu
├── requirements.txt        # Bağımlılıklar
├── rules.md                # Bu dosya
├── sirketler_projeler.md   # Şirket & Proje indeksi
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
└── cop_kutusu/                     # 🗑️ Çöp kutusu (silinen öğeler)
```

## Mimari

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

### SSL Sorunu Çözümü

Python httplib2 ile SSL hatası oluşuyordu. Çözüm: Custom HTTP adapter ile requests kullanımı.

```python
from google.auth.transport.requests import AuthorizedSession

class RequestsHttpAdapter:
    def __init__(self, session):
        self.session = session

    def request(self, uri, method='GET', body=None, headers=None, **kwargs):
        response = self.session.request(method, uri, data=body, headers=headers)
        return type('Response', (), {
            'status': response.status_code,
            'reason': response.reason
        })(), response.content

# Kullanım:
authed_session = AuthorizedSession(credentials)
service = build('drive', 'v3', http=RequestsHttpAdapter(authed_session))
```

## Deployment

### Streamlit Cloud

**URL:** https://aliyilmaznotdefterim.streamlit.app/

**GitHub Repo:** https://github.com/aliyilmazq/alylmz-kisisel-not-defterim (public)

**Secrets (Streamlit Cloud > Settings > Secrets):**
```toml
app_secret_key = "***"  # Gizli anahtar

[gcp_service_account]
type = "service_account"
project_id = "aliyilmaz-kisisel-not-defterim"
private_key_id = "..."
private_key = """
-----BEGIN PRIVATE KEY-----
...
-----END PRIVATE KEY-----
"""
client_email = "notlarim-drive@aliyilmaz-kisisel-not-defterim.iam.gserviceaccount.com"
# ... diğer alanlar
```

### Erişim Kontrolü

İki yöntemli authentication:

1. **URL Parametresi:** `?key=***` - Tarayıcı bookmark için
2. **Şifre Formu:** Ana ekrana eklendiğinde şifre gir, session boyunca hatırla

```python
SECRET_KEY = st.secrets.get("app_secret_key", "notlarim2024")

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

# URL ile giriş
if st.query_params.get("key") == SECRET_KEY:
    st.session_state.authenticated = True

# Şifre formu (URL parametresi yoksa)
if not st.session_state.authenticated:
    entered_key = st.text_input("Erişim anahtarı", type="password")
    if st.button("Giriş"):
        if entered_key == SECRET_KEY:
            st.session_state.authenticated = True
            st.rerun()
```

## Performans Optimizasyonları

### Caching

```python
@st.cache_resource
def get_drive_service():
    """Drive service - uygulama başına bir kez"""

@st.cache_data(ttl=60)
def get_folder_ids():
    """Klasör ID'leri - 60 saniye cache"""

@st.cache_data(ttl=30)
def get_items(folder_type: str):
    """Dosya listesi ve içerikleri - 30 saniye cache"""

@st.cache_data(ttl=30)
def get_item_count(folder_type: str):
    """Hızlı dosya sayısı (içerik okumadan) - 30 saniye cache"""
```

### Lazy Loading

Tab sayıları için hızlı count API kullanılır, içerikler sadece ilgili tab görüntülendiğinde yüklenir:

```python
# Başlangıçta sadece sayılar
inbox_count = get_item_count("inbox")
notes_count = get_item_count("notlar")
# ...

# Tab içeriği görüntülendiğinde
with tab1:
    inbox = get_items("inbox")  # Şimdi yükle
```

## UI / UX

### Header

```
[BEIREK Logo 112px]  [＋ Yeni] (mavi buton)
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
▶ Başlık 📁 (proje varsa)
  ─────────────────────────────
  📁 Proje Adı (varsa)
  Açıklama (max 2 satır)
  ─────────────────────────────
  [Aksiyon butonları - Segmented Control]
```

### Aksiyonlar (Sadece İkon)

- **Gelen Kutusu:** `📝 | ✅ | ✏️ | 🗑️`
- **Notlar:** `📥 | ✅ | 📁 | ✏️ | 🗑️`
- **Görevler:** `✔️ | 📝 | 📁 | 📥 | ✏️ | 🗑️`
- **Arşiv:** `↩️ | 🗑️`
- **Çöp:** `↩️ | 🗑️`

| İkon | Anlam |
|------|-------|
| 📝 | Not'a taşı |
| 📥 | Gelen'e taşı |
| ✅ | Görev'e taşı |
| ✔️ | Tamamla (Arşiv'e) |
| 📁 | Proje ata |
| ✏️ | Düzenle |
| 🗑️ | Sil |
| ↩️ | Geri al |

### iPhone 15 Optimizasyonları (CSS)

- Safe area desteği (notch, home indicator)
- Kompakt padding ve spacing
- iOS segment control stili tab'lar
- Touch-friendly minimum 32-44px yükseklik
- Streamlit header/footer gizleme
- Inter font ailesi

```css
/* Örnek optimizasyonlar */
.main .block-container {
    padding: 0.5rem 0.75rem 1rem 0.75rem !important;
    padding-bottom: env(safe-area-inset-bottom, 1rem) !important;
}

[data-testid="stHeader"],
[data-testid="stToolbar"],
footer { display: none !important; }
```

## Dosya Formatı

**Dosya adı:** `2026-02-02-baslik.md`

```markdown
---
proje: "ENVEX - BHP Escondida Sözleşme Yönetimi"
created: 2026-02-02
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

```
🔽 Filtre: [Tümü ▼]
├── Tümü
├── Projesi Yok
├── ENVEX - Proje 1
├── ENVEX - Proje 2
└── ...
```

## Session State

```python
st.session_state.authenticated = False    # Giriş durumu
st.session_state.edit_mode = False        # Düzenleme modu
st.session_state.selected_item = None     # Düzenlenen öğe
st.session_state.proje_mode = False       # Proje seçim modu
st.session_state.proje_item = None        # Proje atanacak öğe
st.session_state.notlar_filter = "Tümü"   # Notlar tab filtresi
st.session_state.gorevler_filter = "Tümü" # Görevler tab filtresi
```

## Önemli Fonksiyonlar

```python
# Drive Service
get_drive_service() -> googleapiclient.discovery.Resource

# Veri Çekme
get_folder_ids() -> dict[str, str]
get_item_count(folder_type: str) -> int
get_items(folder_type: str) -> list[dict]
get_items_filtered(folder_type: str, proje_filter: str) -> list[dict]

# Dosya İşlemleri
save_file(title, content, folder_type, proje=None, file_id=None)
move_file(file_id, from_folder, to_folder)
delete_file(file_id, folder_type)
update_proje(file_id, folder_type, proje)

# Parsing
parse_frontmatter(content: str) -> tuple[dict, str]
create_frontmatter(proje: str = None) -> str
parse_body(body: str, fallback_title: str) -> tuple[str, str]

# UI Rendering
render_card(item, folder, key_prefix)
render_tab(items, folder, key_prefix)
render_filter(folder_type, filter_state_key, select_key)
```

## Gereksinimler

```
streamlit>=1.28.0
google-api-python-client>=2.100.0
google-auth>=2.23.0
google-auth-oauthlib>=1.1.0
```

## Lokal Geliştirme

```bash
cd /Users/alylmztr/Documents/GitHub/alylmz-kisisel-not-defterim
streamlit run app.py --server.port 8510
```

**URL:** http://localhost:8510?key=***

## Git İşlemleri

```bash
# Değişiklikleri geri al
git reset --hard <commit_hash> && git push --force

# Son commit'i geri al
git revert HEAD --no-edit && git push
```
