#!/bin/bash
# ===========================================
# iCloud Backup Script
# Google Drive -> iCloud sync
# ===========================================

# Kaynak: Google Drive (Mac'te mount edilmiş)
GDRIVE_SOURCE="/Users/alylmztr/Library/CloudStorage/GoogleDrive-831590@gmail.com/Drive'ım/alylmz-kisisel-not-defterim"

# Hedef: iCloud Drive
ICLOUD_DEST="/Users/alylmztr/Library/Mobile Documents/com~apple~CloudDocs/alylmz-kisisel-not-defterim"

# Log dosyası
LOG_FILE="$ICLOUD_DEST/backup-log.txt"

# Tarih
DATE=$(date '+%Y-%m-%d %H:%M:%S')

echo "[$DATE] Backup başlıyor..." >> "$LOG_FILE"

# Klasör yoksa oluştur
mkdir -p "$ICLOUD_DEST/inbox"
mkdir -p "$ICLOUD_DEST/notlar"
mkdir -p "$ICLOUD_DEST/gorevler"
mkdir -p "$ICLOUD_DEST/arsiv"
mkdir -p "$ICLOUD_DEST/export"
mkdir -p "$ICLOUD_DEST/logs"

# rsync ile sync (sadece değişenleri kopyala)
rsync -av --delete \
    "$GDRIVE_SOURCE/inbox/" "$ICLOUD_DEST/inbox/" 2>> "$LOG_FILE"

rsync -av --delete \
    "$GDRIVE_SOURCE/notlar/" "$ICLOUD_DEST/notlar/" 2>> "$LOG_FILE"

rsync -av --delete \
    "$GDRIVE_SOURCE/gorevler/" "$ICLOUD_DEST/gorevler/" 2>> "$LOG_FILE"

rsync -av --delete \
    "$GDRIVE_SOURCE/arsiv/" "$ICLOUD_DEST/arsiv/" 2>> "$LOG_FILE"

rsync -av --delete \
    "$GDRIVE_SOURCE/export/" "$ICLOUD_DEST/export/" 2>> "$LOG_FILE"

rsync -av --delete \
    "$GDRIVE_SOURCE/logs/" "$ICLOUD_DEST/logs/" 2>> "$LOG_FILE"

END_DATE=$(date '+%Y-%m-%d %H:%M:%S')
echo "[$END_DATE] Backup tamamlandı." >> "$LOG_FILE"
echo "---" >> "$LOG_FILE"

echo "Backup tamamlandı: $END_DATE"
