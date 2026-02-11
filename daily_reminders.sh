#!/bin/bash
# Günlük Anımsatıcı Senkronizasyonu
# Her gün 09:00'da çalışır, görevleri Anımsatıcılar'a ekler

cd /Users/alylmztr/Documents/GitHub/alylmz-kisisel-not-defterim

# Environment variables'ı yükle (credentials run_local.sh'da tanımlı)
source /Users/alylmztr/Documents/GitHub/alylmz-kisisel-not-defterim/.env.local 2>/dev/null || true

/usr/bin/python3 << 'EOF'
from services.drive import get_items
from services.reminders import (
    add_reminder_with_daily_recurrence,
    clear_all_reminders,
    get_list_for_project,
    DEFAULT_LIST_NAME,
    PROJECT_LIST_MAPPING
)

print(f"📋 Günlük Anımsatıcı Senkronizasyonu")

# Tüm listelerdeki anımsatıcıları temizle
all_lists = set([DEFAULT_LIST_NAME] + list(PROJECT_LIST_MAPPING.values()))
total_deleted = 0
for list_name in all_lists:
    deleted = clear_all_reminders(list_name)
    if deleted > 0:
        print(f"🗑️  {list_name}: {deleted} silindi")
        total_deleted += deleted

# Mevcut görevleri yeniden ekle
tasks = get_items('gorevler')
added = 0
for task in tasks:
    title = task.get('title', 'Başlıksız')
    proje = task.get('proje')
    content = task.get('content', '')

    # Projeye göre uygun listeyi bul
    target_list = get_list_for_project(proje)

    # Proje bilgisi başlığa eklenmeyecek (zaten doğru listede)
    reminder_title = title

    success, _ = add_reminder_with_daily_recurrence(reminder_title, content[:500] if content else '', '09:00', target_list)
    if success:
        added += 1
        print(f"  ✅ {target_list}: {title[:40]}...")

print(f"\n📊 Toplam: {added} anımsatıcı eklendi ({len(tasks)} görev)")
EOF
