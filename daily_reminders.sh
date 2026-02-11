#!/bin/bash
# Günlük Anımsatıcı Senkronizasyonu
# Her gün 09:00'da çalışır, görevleri Anımsatıcılar'a ekler

cd /Users/alylmztr/Documents/GitHub/alylmz-kisisel-not-defterim

# Environment variables'ı yükle (credentials run_local.sh'da tanımlı)
source /Users/alylmztr/Documents/GitHub/alylmz-kisisel-not-defterim/.env.local 2>/dev/null || true

/usr/bin/python3 << 'EOF'
from services.drive import get_items
from services.reminders import add_reminder_with_daily_recurrence, clear_all_reminders, DEFAULT_LIST_NAME

print(f"📋 Günlük Anımsatıcı Senkronizasyonu - {DEFAULT_LIST_NAME}")

# Tüm anımsatıcıları temizle (günlük yenileme)
deleted = clear_all_reminders()
print(f"🗑️  {deleted} eski anımsatıcı silindi")

# Mevcut görevleri yeniden ekle
tasks = get_items('gorevler')
added = 0
for task in tasks:
    title = task.get('title', 'Başlıksız')
    proje = task.get('proje')
    content = task.get('content', '')

    proje_info = f' [{proje}]' if proje else ''
    reminder_title = f'{title}{proje_info}'

    success, _ = add_reminder_with_daily_recurrence(reminder_title, content[:500] if content else '', '09:00')
    if success:
        added += 1

print(f"✅ {added} anımsatıcı eklendi (toplam {len(tasks)} görev)")
EOF
