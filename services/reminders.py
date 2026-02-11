"""
macOS Reminders (Anımsatıcılar) Entegrasyonu
osascript kullanarak Anımsatıcılar uygulamasına görev ekler
"""
import subprocess
from datetime import datetime, timedelta


# Varsayılan Anımsatıcılar listesi adı
DEFAULT_LIST_NAME = "Kişisel Not Defterim Anımsatıcılar"

# Proje bazlı liste eşleştirmesi
PROJECT_LIST_MAPPING = {
    "TYPEFULLY - LinkedIn - Makale Konuları": "LinkedIn - Makale Konuları",
    "TYPEFULLY - X - Makale Konuları": "X - Makale Konuları",
}


def get_list_for_project(proje: str = None) -> str:
    """Projeye göre uygun Anımsatıcılar listesini döndür"""
    if proje and proje in PROJECT_LIST_MAPPING:
        return PROJECT_LIST_MAPPING[proje]
    return DEFAULT_LIST_NAME


def _run_applescript(script: str) -> tuple[bool, str]:
    """AppleScript çalıştır"""
    try:
        result = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            return True, result.stdout.strip()
        return False, result.stderr.strip()
    except subprocess.TimeoutExpired:
        return False, "Timeout"
    except Exception as e:
        return False, str(e)


def ensure_reminders_list(list_name: str = DEFAULT_LIST_NAME) -> bool:
    """Anımsatıcılar listesinin var olduğundan emin ol, yoksa oluştur"""
    script = f'''
    tell application "Reminders"
        if not (exists list "{list_name}") then
            make new list with properties {{name:"{list_name}"}}
        end if
    end tell
    '''
    success, _ = _run_applescript(script)
    return success


def reminder_exists(title: str, list_name: str = DEFAULT_LIST_NAME, check_completed: bool = False) -> bool:
    """Belirtilen başlıkta anımsatıcı var mı kontrol et"""
    title_escaped = title.replace('"', '\\"')[:200]

    if check_completed:
        # Hem tamamlanmış hem tamamlanmamış kontrol et
        condition = f'name contains "{title_escaped}"'
    else:
        # Sadece tamamlanmamış kontrol et
        condition = f'name contains "{title_escaped}" and completed is false'

    script = f'''
    tell application "Reminders"
        tell list "{list_name}"
            set matchingReminders to (every reminder whose {condition})
            return (count of matchingReminders) > 0
        end tell
    end tell
    '''

    success, output = _run_applescript(script)
    return success and output.lower() == "true"


def reset_completed_reminders(list_name: str = DEFAULT_LIST_NAME) -> int:
    """Tamamlanmış anımsatıcıları sil (günlük yenileme için)"""
    script = f'''
    tell application "Reminders"
        tell list "{list_name}"
            set completedReminders to (every reminder whose completed is true)
            set deletedCount to count of completedReminders
            repeat with r in completedReminders
                delete r
            end repeat
            return deletedCount
        end tell
    end tell
    '''

    success, output = _run_applescript(script)
    if success:
        try:
            return int(output)
        except:
            return 0
    return 0


def clear_all_reminders(list_name: str = DEFAULT_LIST_NAME) -> int:
    """Listedeki tüm anımsatıcıları sil (günlük yenileme için)"""
    script = f'''
    tell application "Reminders"
        tell list "{list_name}"
            set allReminders to every reminder
            set deletedCount to count of allReminders
            repeat with r in allReminders
                delete r
            end repeat
            return deletedCount
        end tell
    end tell
    '''

    success, output = _run_applescript(script)
    if success:
        try:
            return int(output)
        except:
            return 0
    return 0


def add_reminder_with_daily_recurrence(
    title: str,
    notes: str = "",
    remind_time: str = "09:00",
    list_name: str = DEFAULT_LIST_NAME
) -> tuple[bool, str]:
    """
    macOS Anımsatıcılar uygulamasına günlük tekrarlayan görev ekle
    Aynı başlıkta anımsatıcı varsa tekrar eklemez.
    """
    # Zaten varsa ekleme
    if reminder_exists(title, list_name):
        return True, f"Anımsatıcı zaten mevcut: {title}"

    ensure_reminders_list(list_name)

    # Hatırlatma saatini parse et
    try:
        hour, minute = remind_time.split(":")
        hour, minute = int(hour), int(minute)
    except:
        hour, minute = 9, 0

    # Escape
    title_escaped = title.replace('"', '\\"').replace('\n', ' ')[:200]
    notes_escaped = notes.replace('"', '\\"').replace('\n', '\\n')[:500] if notes else ""

    # Locale-independent tarih hesaplama (AppleScript içinde)
    script = f'''
    tell application "Reminders"
        set reminderDate to current date
        set hours of reminderDate to {hour}
        set minutes of reminderDate to {minute}
        set seconds of reminderDate to 0

        -- Eğer saat geçtiyse yarına ayarla
        if reminderDate < (current date) then
            set reminderDate to reminderDate + (1 * days)
        end if

        tell list "{list_name}"
            set newReminder to make new reminder with properties {{name:"{title_escaped}", body:"{notes_escaped}"}}
            set due date of newReminder to reminderDate
            set remind me date of newReminder to reminderDate
        end tell
    end tell
    '''

    success, message = _run_applescript(script)
    if success:
        return True, f"Anımsatıcı eklendi: {title}"
    return False, f"Anımsatıcı eklenemedi: {message}"


def complete_reminder(title: str, list_name: str = DEFAULT_LIST_NAME) -> tuple[bool, str]:
    """Belirtilen başlıktaki anımsatıcıyı tamamlandı olarak işaretle"""
    title_escaped = title.replace('"', '\\"')[:200]

    script = f'''
    tell application "Reminders"
        tell list "{list_name}"
            set matchingReminders to (every reminder whose name contains "{title_escaped}" and completed is false)
            repeat with r in matchingReminders
                set completed of r to true
            end repeat
        end tell
    end tell
    '''

    success, message = _run_applescript(script)
    return success, message


def delete_reminder(title: str, list_name: str = DEFAULT_LIST_NAME) -> tuple[bool, str]:
    """Belirtilen başlıktaki anımsatıcıyı sil"""
    title_escaped = title.replace('"', '\\"')[:200]

    script = f'''
    tell application "Reminders"
        tell list "{list_name}"
            set matchingReminders to (every reminder whose name contains "{title_escaped}")
            repeat with r in matchingReminders
                delete r
            end repeat
        end tell
    end tell
    '''

    success, message = _run_applescript(script)
    return success, message
