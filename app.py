import streamlit as st
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaInMemoryUpload
from google.auth.transport.requests import Request
from datetime import datetime
import requests
import io

# Erişim kontrolü
SECRET_KEY = st.secrets.get("app_secret_key", "notlarim2024")

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

# URL parametresi ile giriş
if st.query_params.get("key") == SECRET_KEY:
    st.session_state.authenticated = True

# Giriş kontrolü
if not st.session_state.authenticated:
    st.title("🔒 Notlarım")
    entered_key = st.text_input("Erişim anahtarı", type="password")
    if st.button("Giriş", use_container_width=True):
        if entered_key == SECRET_KEY:
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("Yanlış anahtar")
    st.stop()

# Google Drive API Setup
SCOPES = ['https://www.googleapis.com/auth/drive']
SHARED_DRIVE_ID = "0AFbVhvJLQtOHUk9PVA"  # Workspace Shared Drive

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

# Klasör konfigürasyonu
FOLDER_CONFIG = {
    "inbox": "inbox",
    "notlar": "notlar",
    "gorevler": "gorevler",
    "arsiv": "arsiv",
    "cop_kutusu": "cop_kutusu",
}


@st.cache_resource
def get_drive_service():
    """Google Drive API servisi oluştur - requests transport kullanır"""
    from google.auth.transport.requests import AuthorizedSession

    credentials = service_account.Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=SCOPES
    )

    # requests tabanlı transport - SSL sorununu çözer
    authed_session = AuthorizedSession(credentials)

    # googleapiclient için custom http adapter
    class RequestsHttpAdapter:
        def __init__(self, session):
            self.session = session

        def request(self, uri, method='GET', body=None, headers=None, **kwargs):
            response = self.session.request(method, uri, data=body, headers=headers)
            return type('Response', (), {
                'status': response.status_code,
                'reason': response.reason
            })(), response.content

    return build('drive', 'v3', http=RequestsHttpAdapter(authed_session))


@st.cache_data(ttl=60)
def get_folder_ids():
    """Alt klasör ID'lerini al - Shared Drive desteği"""
    service = get_drive_service()
    folder_ids = {}

    results = service.files().list(
        q=f"'{SHARED_DRIVE_ID}' in parents and mimeType='application/vnd.google-apps.folder' and trashed=false",
        fields="files(id, name)",
        supportsAllDrives=True,
        includeItemsFromAllDrives=True,
        corpora="drive",
        driveId=SHARED_DRIVE_ID
    ).execute()

    for folder in results.get('files', []):
        folder_ids[folder['name']] = folder['id']

    return folder_ids


def get_proje_options() -> list[str]:
    """Dropdown için proje seçenekleri oluştur"""
    options = ["Tümü", "Projesi Yok"]
    for sirket, projeler in SIRKET_PROJE_CONFIG.items():
        for proje in projeler:
            options.append(f"{sirket} - {proje}")
    return options


def parse_frontmatter(content: str) -> tuple[dict, str]:
    """Frontmatter ve içeriği ayır"""
    frontmatter = {"proje": None, "created": None}
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
                    if value.lower() in ("null", "none", ""):
                        value = None
                    if key in frontmatter:
                        frontmatter[key] = value

    return frontmatter, body


def create_frontmatter(proje: str = None) -> str:
    """Yeni frontmatter oluştur"""
    today = datetime.now().strftime("%Y-%m-%d")
    proje_str = f'"{proje}"' if proje else "null"
    return f"""---
proje: {proje_str}
created: {today}
---"""


def parse_body(body: str, fallback_title: str = "") -> tuple[str, str]:
    """Body'den başlık ve içerik ayır"""
    lines = body.split("\n")
    title = lines[0].replace("# ", "").strip() if lines and lines[0].strip() else fallback_title
    content = "\n".join(lines[1:]).strip() if len(lines) > 1 else ""
    return title, content


@st.cache_data(ttl=30)
def get_items(folder_type: str) -> list[dict]:
    """Google Drive'dan dosyaları çek - Shared Drive desteği + 30sn cache"""
    service = get_drive_service()
    folder_ids = get_folder_ids()

    if folder_type not in folder_ids:
        return []

    folder_id = folder_ids[folder_type]
    items = []

    results = service.files().list(
        q=f"'{folder_id}' in parents and trashed=false",
        fields="files(id, name, modifiedTime)",
        orderBy="modifiedTime desc",
        supportsAllDrives=True,
        includeItemsFromAllDrives=True
    ).execute()

    for file in results.get('files', []):
        # Dosya içeriğini oku
        content = service.files().get_media(fileId=file['id']).execute().decode('utf-8')
        frontmatter, body = parse_frontmatter(content)
        title, body_content = parse_body(body, file['name'].replace('.md', ''))

        items.append({
            "id": file['id'],
            "filename": file['name'],
            "title": title,
            "content": body_content,
            "proje": frontmatter.get("proje"),
            "created": frontmatter.get("created"),
            "modified": file['modifiedTime'],
        })

    return items


def get_items_filtered(folder_type: str, proje_filter: str = "Tümü") -> list[dict]:
    """Projeye göre filtrelenmiş öğeler"""
    items = get_items(folder_type)
    if proje_filter == "Tümü":
        return items
    elif proje_filter == "Projesi Yok":
        return [item for item in items if not item.get("proje")]
    else:
        return [item for item in items if item.get("proje") == proje_filter]


def save_file(title: str, content: str, folder_type: str, proje: str = None, file_id: str = None):
    """Dosya kaydet veya güncelle - Shared Drive desteği"""
    service = get_drive_service()
    folder_ids = get_folder_ids()

    frontmatter = create_frontmatter(proje)
    md_content = f"{frontmatter}\n\n# {title}\n\n{content}"

    media = MediaInMemoryUpload(md_content.encode('utf-8'), mimetype='text/markdown')

    if file_id:
        # Mevcut dosyayı güncelle
        service.files().update(
            fileId=file_id,
            media_body=media,
            supportsAllDrives=True
        ).execute()
    else:
        # Yeni dosya oluştur
        date_prefix = datetime.now().strftime("%Y-%m-%d")
        safe_title = "".join(c if c.isalnum() or c in (' ', '-', '_') else '_' for c in title)
        safe_title = safe_title[:50].strip().replace(" ", "-").lower()
        filename = f"{date_prefix}-{safe_title}.md"

        file_metadata = {
            'name': filename,
            'parents': [folder_ids[folder_type]],
            'mimeType': 'text/markdown'
        }
        service.files().create(
            body=file_metadata,
            media_body=media,
            supportsAllDrives=True
        ).execute()


def move_file(file_id: str, from_folder: str, to_folder: str):
    """Dosyayı klasörler arası taşı - Shared Drive desteği"""
    service = get_drive_service()
    folder_ids = get_folder_ids()

    service.files().update(
        fileId=file_id,
        addParents=folder_ids[to_folder],
        removeParents=folder_ids[from_folder],
        supportsAllDrives=True
    ).execute()


def delete_file(file_id: str, folder_type: str):
    """Dosyayı çöp kutusuna taşı veya kalıcı sil - Shared Drive desteği"""
    service = get_drive_service()
    folder_ids = get_folder_ids()

    if folder_type == "cop_kutusu":
        # Kalıcı sil
        service.files().delete(fileId=file_id, supportsAllDrives=True).execute()
    else:
        # Çöp kutusuna taşı
        move_file(file_id, folder_type, "cop_kutusu")


def update_proje(file_id: str, folder_type: str, proje: str):
    """Dosyanın projesini güncelle"""
    service = get_drive_service()

    content = service.files().get_media(fileId=file_id).execute().decode('utf-8')
    _, body = parse_frontmatter(content)
    title, body_content = parse_body(body)

    save_file(title, body_content, folder_type, proje, file_id)


# Streamlit Arayüzü
st.set_page_config(
    page_title="Notlarım",
    page_icon="📝",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# CSS Stilleri
CSS_STYLES = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    * {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        -webkit-tap-highlight-color: transparent;
    }
    .stApp { background: #f2f2f7; }
    .main .block-container {
        padding: 0.5rem 1rem 2rem 1rem !important;
        max-width: 100% !important;
    }
    [data-testid="stSidebar"] { display: none; }
    .stTabs [data-baseweb="tab-list"] {
        gap: 0;
        background: #ffffff;
        border-radius: 12px;
        padding: 4px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    .stTabs [data-baseweb="tab"] {
        flex: 1;
        justify-content: center;
        padding: 8px 4px;
        font-size: 0.7rem;
        font-weight: 500;
        color: #8e8e93;
        border-radius: 8px;
        min-height: 44px;
    }
    .stTabs [data-baseweb="tab"][aria-selected="true"] {
        background: #007aff;
        color: white;
    }
    .stTabs [data-baseweb="tab-panel"] {
        padding-top: 1rem;
    }
    h1 { font-weight: 600 !important; font-size: 1.3rem !important; color: #1c1c1e !important; margin-bottom: 0.5rem !important; }
    h2 { font-weight: 600 !important; font-size: 1.1rem !important; color: #1c1c1e !important; }
    h3 { font-weight: 600 !important; font-size: 1rem !important; color: #1c1c1e !important; }
    .stButton > button {
        background: #007aff !important;
        color: white !important;
        border: none !important;
        border-radius: 10px !important;
        padding: 0.7rem 1rem !important;
        font-weight: 500 !important;
        font-size: 0.875rem !important;
        min-height: 44px !important;
        touch-action: manipulation;
    }
    .stButton > button:hover { background: #0056b3 !important; }
    .stButton > button:active { transform: scale(0.95); }
    .stTextArea > div > div > textarea {
        background: #ffffff !important;
        border: 1px solid #e5e5ea !important;
        border-radius: 12px !important;
        padding: 0.75rem 1rem !important;
        font-size: 16px !important;
        line-height: 1.5 !important;
    }
    .stTextArea > div > div > textarea:focus {
        border-color: #007aff !important;
        box-shadow: 0 0 0 3px rgba(0, 122, 255, 0.15) !important;
    }
    hr { border: none !important; height: 1px !important; background: #e5e5ea !important; margin: 0.8rem 0 !important; }
    .stCaption { color: #8e8e93 !important; font-size: 0.7rem !important; }
    p { font-size: 0.875rem !important; }
    ::-webkit-scrollbar { width: 0px; height: 0px; }
    .streamlit-expanderContent { padding: 0.5rem !important; }
    .streamlit-expanderContent .stCaption {
        display: -webkit-box !important;
        -webkit-line-clamp: 3 !important;
        -webkit-box-orient: vertical !important;
        overflow: hidden !important;
    }
    .streamlit-expanderHeader p {
        white-space: nowrap !important;
        overflow: hidden !important;
        text-overflow: ellipsis !important;
    }
    .streamlit-expanderContent [data-testid="stSegmentedControl"] {
        display: flex !important;
        justify-content: center !important;
    }
    .streamlit-expanderContent [data-testid="stSegmentedControl"] > div {
        width: 100% !important;
        max-width: 360px !important;
    }
    .streamlit-expanderContent [data-testid="stSegmentedControl"] button {
        flex: 1 !important;
        min-height: 44px !important;
        font-size: 0.75rem !important;
        padding: 0.4rem 0.2rem !important;
    }
    @media (min-width: 768px) {
        .main .block-container { padding: 1rem 3rem !important; max-width: 800px !important; }
    }
</style>
"""

st.markdown(CSS_STYLES, unsafe_allow_html=True)

# Session state
if "edit_mode" not in st.session_state:
    st.session_state.edit_mode = False
if "selected_item" not in st.session_state:
    st.session_state.selected_item = None
if "proje_mode" not in st.session_state:
    st.session_state.proje_mode = False
if "proje_item" not in st.session_state:
    st.session_state.proje_item = None
if "notlar_filter" not in st.session_state:
    st.session_state.notlar_filter = "Tümü"
if "gorevler_filter" not in st.session_state:
    st.session_state.gorevler_filter = "Tümü"

# Tab sayıları için hızlı count fonksiyonu
@st.cache_data(ttl=30)
def get_item_count(folder_type: str) -> int:
    """Klasördeki dosya sayısını hızlıca al (içerik okumadan)"""
    service = get_drive_service()
    folder_ids = get_folder_ids()

    if folder_type not in folder_ids:
        return 0

    results = service.files().list(
        q=f"'{folder_ids[folder_type]}' in parents and trashed=false",
        fields="files(id)",
        supportsAllDrives=True,
        includeItemsFromAllDrives=True
    ).execute()

    return len(results.get('files', []))

# Lazy loading - sadece sayıları al, içerikleri sonra yükle
inbox_count = get_item_count("inbox")
notes_count = get_item_count("notlar")
tasks_count = get_item_count("gorevler")
archive_count = get_item_count("arsiv")
trash_count = get_item_count("cop_kutusu")

# Başlık ve Yeni Giriş butonu
col1, col2 = st.columns([3, 1])
with col1:
    st.image("logo.webp", width=120)
with col2:
    if st.button("+ Yeni", use_container_width=True):
        st.session_state.edit_mode = True
        st.session_state.selected_item = None
        st.rerun()

# Düzenleme modu
if st.session_state.edit_mode:
    default_content = ""
    if st.session_state.selected_item:
        default_content = st.session_state.selected_item["title"]
        if st.session_state.selected_item["content"]:
            default_content += "\n\n" + st.session_state.selected_item["content"]

    content = st.text_area("", value=default_content, height=200, placeholder="Bir şeyler yazın...", label_visibility="collapsed")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Kaydet", use_container_width=True, type="primary"):
            if content.strip():
                lines = content.strip().split('\n')
                title = lines[0].strip()
                full_content = '\n'.join(lines[1:]).strip()

                if st.session_state.selected_item:
                    folder = st.session_state.selected_item["folder"]
                    file_id = st.session_state.selected_item["id"]
                    proje = st.session_state.selected_item.get("proje")
                    save_file(title, full_content, folder, proje, file_id)
                else:
                    save_file(title, full_content, "inbox")

                st.session_state.edit_mode = False
                st.session_state.selected_item = None
                st.cache_data.clear()
                st.rerun()
    with col2:
        if st.button("İptal", use_container_width=True):
            st.session_state.edit_mode = False
            st.session_state.selected_item = None
            st.rerun()

elif st.session_state.proje_mode:
    item = st.session_state.proje_item
    st.subheader(f"📁 Proje Ata: {item['title']}")

    proje_options = get_proje_options()
    current_proje = item.get('proje') or "Projesi Yok"
    if current_proje not in proje_options:
        current_proje = "Projesi Yok"

    current_index = proje_options.index(current_proje) if current_proje in proje_options else 1

    selected_proje = st.selectbox(
        "Proje Seç",
        options=proje_options[1:],
        index=current_index - 1 if current_index > 0 else 0,
        label_visibility="collapsed"
    )

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Kaydet", use_container_width=True, type="primary"):
            proje_value = None if selected_proje == "Projesi Yok" else selected_proje
            update_proje(item['id'], item['folder'], proje_value)
            st.session_state.proje_mode = False
            st.session_state.proje_item = None
            st.cache_data.clear()
            st.rerun()
    with col2:
        if st.button("İptal", use_container_width=True, key="proje_iptal"):
            st.session_state.proje_mode = False
            st.session_state.proje_item = None
            st.rerun()

else:
    # Tab konfigürasyonu
    TAB_CONFIG = {
        "inbox": {
            "options": ["📝Not", "✅Görev", "✏️Düzenle", "🗑️Sil"],
            "actions": {
                "📝Not": lambda item: move_file(item['id'], "inbox", "notlar"),
                "✅Görev": lambda item: move_file(item['id'], "inbox", "gorevler"),
                "🗑️Sil": lambda item: delete_file(item['id'], "inbox"),
            },
            "empty_msg": "Gelen kutusu boş."
        },
        "notlar": {
            "options": ["📥Gelen", "✅Görev", "📁Proje", "✏️Düzenle", "🗑️Sil"],
            "actions": {
                "📥Gelen": lambda item: move_file(item['id'], "notlar", "inbox"),
                "✅Görev": lambda item: move_file(item['id'], "notlar", "gorevler"),
                "🗑️Sil": lambda item: delete_file(item['id'], "notlar"),
            },
            "empty_msg": "Henüz not yok."
        },
        "gorevler": {
            "options": ["✅Tamamla", "📝Not", "📁Proje", "📥Gelen", "✏️Düzenle", "🗑️Sil"],
            "actions": {
                "✅Tamamla": lambda item: move_file(item['id'], "gorevler", "arsiv"),
                "📝Not": lambda item: move_file(item['id'], "gorevler", "notlar"),
                "📥Gelen": lambda item: move_file(item['id'], "gorevler", "inbox"),
                "🗑️Sil": lambda item: delete_file(item['id'], "gorevler"),
            },
            "empty_msg": "Henüz görev yok."
        },
        "arsiv": {
            "options": ["↩️Geri", "🗑️Sil"],
            "actions": {
                "↩️Geri": lambda item: move_file(item['id'], "arsiv", "gorevler"),
                "🗑️Sil": lambda item: delete_file(item['id'], "arsiv"),
            },
            "empty_msg": "Arşiv boş."
        },
        "cop_kutusu": {
            "options": ["↩️Geri", "×Sil"],
            "actions": {
                "↩️Geri": lambda item: move_file(item['id'], "cop_kutusu", "inbox"),
                "×Sil": lambda item: delete_file(item['id'], "cop_kutusu"),
            },
            "empty_msg": "Çöp kutusu boş."
        },
    }

    def render_card(item: dict, folder: str, key_prefix: str):
        config = TAB_CONFIG[folder]
        title_display = item['title']
        if item.get('proje'):
            title_display = f"{item['title']} 📁"

        with st.expander(title_display, expanded=False):
            if item.get('proje'):
                st.caption(f"📁 {item['proje']}")
            if item['content']:
                st.caption(item['content'])

            action = st.segmented_control(
                "Aksiyon",
                options=config["options"],
                key=f"{key_prefix}_{item['id']}",
                label_visibility="collapsed"
            )
            if action == "✏️Düzenle":
                st.session_state.selected_item = {**item, "folder": folder}
                st.session_state.edit_mode = True
                st.rerun()
            elif action == "📁Proje":
                st.session_state.proje_mode = True
                st.session_state.proje_item = {**item, "folder": folder}
                st.rerun()
            elif action and action in config["actions"]:
                config["actions"][action](item)
                st.cache_data.clear()
                st.rerun()

    def render_tab(items: list, folder: str, key_prefix: str):
        if items:
            for item in items:
                render_card(item, folder, key_prefix)
        else:
            st.caption(TAB_CONFIG[folder]["empty_msg"])

    def render_filter(folder_type: str, filter_state_key: str, select_key: str) -> str:
        proje_options = get_proje_options()
        current_filter = getattr(st.session_state, filter_state_key)
        selected_filter = st.selectbox(
            "🔽 Filtre",
            options=proje_options,
            index=proje_options.index(current_filter) if current_filter in proje_options else 0,
            key=select_key
        )
        if selected_filter != current_filter:
            setattr(st.session_state, filter_state_key, selected_filter)
            st.rerun()
        return selected_filter

    # Tab menü
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        f"📥 Gelen ({inbox_count})",
        f"📝 Not ({notes_count})",
        f"✅ Görev ({tasks_count})",
        f"📦 Arşiv ({archive_count})",
        f"🗑️ Çöp ({trash_count})"
    ])

    with tab1:
        inbox = get_items("inbox")
        render_tab(inbox, "inbox", "inbox")

    with tab2:
        render_filter("notlar", "notlar_filter", "notlar_filter_select")
        filtered_notes = get_items_filtered("notlar", st.session_state.notlar_filter)
        render_tab(filtered_notes, "notlar", "note")

    with tab3:
        render_filter("gorevler", "gorevler_filter", "gorevler_filter_select")
        filtered_tasks = get_items_filtered("gorevler", st.session_state.gorevler_filter)
        render_tab(filtered_tasks, "gorevler", "task")

    with tab4:
        archive = get_items("arsiv")
        render_tab(archive, "arsiv", "archive")

    with tab5:
        trash = get_items("cop_kutusu")
        render_tab(trash, "cop_kutusu", "trash")
