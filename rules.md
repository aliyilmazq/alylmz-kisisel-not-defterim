# Kişisel Not Defterim - Kurallar

## Proje Yapısı

**GitHub (Uygulama):**
```
alylmz-kisisel-not-defterim/
├── app.py                  # Streamlit uygulaması
├── requirements.txt        # Bağımlılıklar
├── rules.md                # Bu dosya
├── sirketler_projeler.md   # Şirket & Proje indeksi
└── not-defterim.command    # Tıkla-çalıştır dosyası
```

**iCloud & Google Drive (Veri):**
```
alylmz-kisisel-not-defterim/
├── inbox/                  # 📥 Gelen kutusu
├── notlar/                 # 📝 Notlar
├── gorevler/               # ✅ Görevler
├── arsiv/                  # 📦 Arşiv (tamamlanan görevler)
└── cop_kutusu/             # 🗑️ Çöp kutusu (silinen öğeler)
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

## Giriş Formatı

Tek metin kutusu:
- **İlk satır** → Başlık
- **Geri kalan satırlar** → Açıklama/içerik

### Dosya Formatı (.md)

**Dosya adı:** `2026-02-02-baslik.md` (tarih-baslik formatı)

```markdown
---
proje: "ENVEX - BHP Escondida Sözleşme Yönetimi"
created: 2026-02-02
---

# Başlık

İçerik buraya...
```

- `proje`: `"SIRKET - Proje Adı"` formatında veya `null`
- `created`: Oluşturulma tarihi (YYYY-MM-DD)

## Kart Görünümü

Tüm tablarda aynı kart yapısı kullanılır:

```
▶ Başlık (ilk satır, CSS ile tek satır)
  ─────────────────────────────
  Açıklama (geri kalan satırlar, CSS ile max 3 satır)
  ─────────────────────────────
  [Aksiyon butonları]  ← Segmented control
```

**Aksiyonlar:**
- **Gelen Kutusu:** `📝Not | ✅Görev | ✏️Düzenle | 🗑️Sil`
- **Notlar:** `📥Gelen | ✅Görev | 📁Proje | ✏️Düzenle | 🗑️Sil`
- **Görevler:** `✅Tamamla | 📝Not | 📁Proje | 📥Gelen | ✏️Düzenle | 🗑️Sil`
- **Arşiv:** `↩️Geri | 🗑️Sil`
- **Çöp:** `↩️Geri | ×Sil`

- Segmented control her zaman yan yana kalır (responsive)

## Üst Menü (Tabs)

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

- Tab'larda sayaç gösterilir (örn: "📥 Gelen (3)")
- Mobile-friendly: Yatay scroll ile erişilebilir

## Klasör Yapısı

**Uygulama (GitHub):**
`/Users/alylmztr/Documents/GitHub/alylmz-kisisel-not-defterim/`

**Veri (iCloud + Google Drive):**
```
iCloud (MAIN_FOLDER) ──sync──► Google Drive
```

1. **iCloud:** `/Users/alylmztr/Library/Mobile Documents/com~apple~CloudDocs/alylmz-kisisel-not-defterim/`
2. **Google Drive:** `/Users/alylmztr/Library/CloudStorage/GoogleDrive-831590@gmail.com/Drive'ım/alylmz-kisisel-not-defterim/`

> ⚠️ **KURAL:** iCloud ve Google Drive her zaman entegre çalışmalı. Tüm veri işlemleri her iki lokasyona da senkronize edilmeli.

## Çalıştırma

**Dock'tan:** `not-defterim.command` tıkla

**Terminal:**
```bash
cd /Users/alylmztr/Documents/GitHub/alylmz-kisisel-not-defterim
streamlit run app.py --server.port 8510
```

**URL:** http://localhost:8510

## Tasarım

- Mobile-first iOS benzeri arayüz
- Inter font
- Touch-friendly (min 44px)
- Segmented control (her zaman yan yana)
- Satır bazlı sınırlama (responsive)

## Tek Yerden Yönetim

### Klasör Değişkenleri
```python
APP_FOLDER = Path("/.../GitHub/alylmz-kisisel-not-defterim")  # Uygulama
DATA_FOLDERS = [iCloud, Google Drive]  # Veri
MAIN_FOLDER = DATA_FOLDERS[0]  # iCloud ana kaynak
```

### FOLDER_CONFIG - Alt Klasör Yönetimi
```python
FOLDER_CONFIG = {
    "inbox": "inbox",
    "notlar": "notlar",
    "gorevler": "gorevler",
    "arsiv": "arsiv",
    "cop_kutusu": "cop_kutusu",
}

def get_folder_path(folder: Path, folder_type: str) -> Path:
    return folder / FOLDER_CONFIG[folder_type]
```

### get_items() - Tek Veri Çekme
```python
def get_items(folder_type: str) -> list[dict]:
    return get_items_from_folder(get_folder_path(MAIN_FOLDER, folder_type))
```

### CSS_STYLES - Stil Değişkeni
```python
CSS_STYLES = """<style>...</style>"""
st.markdown(CSS_STYLES, unsafe_allow_html=True)
```

### TAB_CONFIG - Tab Yönetimi
```python
TAB_CONFIG = {
    "folder_name": {
        "options": [...],
        "actions": {...},
        "empty_msg": "..."
    }
}
```

## Şirket & Proje Yapısı

> **Kaynak dosya:** `sirketler_projeler.md` - Şirket ve proje listesi burada tutulur.

### Konfigürasyon
```python
# sirketler_projeler.md dosyasından okunur veya hardcoded:
SIRKET_PROJE_CONFIG = {
    "ENVEX": [...],      # 12 proje
    "COREX": [...],      # 3 proje
    "TIS": [...],        # 7 proje
    "MIM": [...],        # 1 proje
    "TEMROB": [...],     # 2 proje
    "PULCHRANI": [...],  # 2 proje
    "ALI YILMAZ": [...], # 7 proje
    "EPIOQN": [...],     # 1 proje
    "PULPO": [...],      # 2 proje
    "OZMEN": [...],      # 1 proje
}
# Toplam: 10 şirket, 38 proje
```

> Detaylı liste için bkz: `sirketler_projeler.md`

### Frontmatter Formatı
```markdown
---
proje: "ENVEX - BHP Escondida Sözleşme Yönetimi"
created: 2026-02-02
---

# Başlık

İçerik...
```

- Her not/görev **tek projeye** ait olabilir
- `proje: null` = projesi yok
- Proje formatı: `"SIRKET - Proje Adı"`

### Filtre UI (Not ve Görev tab'larında)
```
┌─────────────────────────────────┐
│ 🔽 Filtre: Tümü                 │
├─────────────────────────────────┤
│ ▶ Kart 1                        │
│ ▶ Kart 2                        │
└─────────────────────────────────┘
```

### Dropdown Seçenekleri
```
Tümü
Projesi Yok
ENVEX - BHP Escondida Sözleşme Yönetimi
ENVEX - ABD ENVEX Satış Ağı
...
COREX - Corpus Christi Güneş Enerjisi Santrali
...
```

### Aksiyonlar (Güncel)
- **Notlar:** `📥Gelen | ✅Görev | 📁Proje | ✏️Düzenle | 🗑️Sil`
- **Görevler:** `✅Tamamla | 📝Not | 📁Proje | 📥Gelen | ✏️Düzenle | 🗑️Sil`

### Proje Fonksiyonları
```python
def get_proje_options() -> list[str]:
    """Dropdown için proje seçenekleri: ['Tümü', 'Projesi Yok', 'SIRKET - Proje', ...]"""

def get_items_filtered(folder_type: str, proje: str = None) -> list[dict]:
    """Projeye göre filtrelenmiş öğeler"""

def update_proje(filename: str, folder: str, proje: str):
    """Dosyanın projesini güncelle"""
```

### Parsing Fonksiyonları (Single Source of Truth)
```python
def parse_frontmatter(content: str) -> tuple[dict, str]:
    """Frontmatter ve içeriği ayır"""

def create_frontmatter(proje: str = None) -> str:
    """Yeni frontmatter oluştur"""

def parse_body(body: str, fallback_title: str = "") -> tuple[str, str]:
    """Body'den başlık ve içerik ayır - kod tekrarını önler"""
```

### UI Render Fonksiyonları (Single Source of Truth)
```python
def render_card(item, folder, key_prefix):
    """Tek kart yapısı - tüm tablar için aynı"""

def render_tab(items, folder, key_prefix):
    """Tab içeriği render"""

def render_filter(folder_type, filter_state_key, select_key):
    """Proje filtresi render - kod tekrarını önler"""
```

### Session State (Filtreler)
```python
st.session_state.notlar_filter = "Tümü"    # Notlar tab filtresi
st.session_state.gorevler_filter = "Tümü"  # Görevler tab filtresi
st.session_state.proje_mode = False        # Proje seçim modu
st.session_state.proje_item = None         # Proje atanacak öğe
```

## Performans Stratejisi (YAGNI)

**Şu an:** Pure Frontmatter
- Her dosyadan YAML frontmatter okunur
- Basit ve yeterli performans

**İleride (gerekirse):** Frontmatter + SQLite Cache
- Frontmatter = Source of Truth
- SQLite = Arama/Filtre indeksi
- 10,000+ not için düşünülebilir
