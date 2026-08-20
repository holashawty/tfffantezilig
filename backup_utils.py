"""
backup_utils.py
---------------
Excel dosyasina yazmadan once otomatik yedek alan ortak yardimci.

Neden var:
  oyuncu_veritabani.xlsx tek canli hafiza — GameweekLog gecmisi
  burada. Bir hata (yanlis player_id, ws.max_row+1 bug, vs.) veriyi
  geri donusmez bozabilir. Bu yuzden her --apply oncesi yedek alinir.

Kullanim:
    from backup_utils import backup_excel
    backup_excel("oyuncu_veritabani.xlsx")  # --apply oncesi cagir

Yedek konumu:
    backups/oyuncu_veritabani_YYYYMMDD_HHMMSS.xlsx
    (Excel dosyasiyla ayni klasorde backups/ altinda)

.gitignore:
    backups/ klasoru repoya ALINMAZ (kullanici-local, buyuk olabilir).
"""

import os
import shutil
from datetime import datetime


def backup_excel(excel_path: str) -> str:
    """Excel dosyasinin tarih damgali yedeğini alir.

    Args:
        excel_path: Yedeklenecek Excel dosyasinin yolu.

    Returns:
        Olusturulan yedek dosyasinin tam yolu. Hata olursa bos string.

    Side effect:
        backups/ klasoru yoksa olusturulur (excel dosyasinin yaninda).
    """
    if not os.path.exists(excel_path):
        # Dosya yoksa yedek alinamaz — sessiz gec, cagiran zaten hata verir
        return ""

    excel_dir = os.path.dirname(os.path.abspath(excel_path))
    excel_name = os.path.basename(excel_path)
    stem, ext = os.path.splitext(excel_name)
    # .xlsx -> .xlsx (ext korunsun), stem'e timestamp ekle

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = os.path.join(excel_dir, "backups")
    os.makedirs(backup_dir, exist_ok=True)

    backup_name = f"{stem}_{timestamp}{ext}"
    backup_path = os.path.join(backup_dir, backup_name)

    try:
        shutil.copy2(excel_path, backup_path)
        print(f"[YEDEK] {excel_name} -> backups/{backup_name}")
        return backup_path
    except Exception as e:
        # Yedek alinamazsa uygulama durdurulmali — ama bu fonksiyon
        # sadece uyarir, cagiran kararı versin. Biz yine de devam
        # etmesinin risky oldugunu soyleyelim.
        print(f"[UYARI] Yedek alinamadi: {e}")
        print(f"        Devam etmek riskli — Excel'e yazmadan once kontrol et.")
        return ""


def safe_save_excel(wb, excel_path: str):
    """Excel dosyasini kaydeder. Eger dosya baska bir programda aciksa
    ve PermissionError verirse kullaniciya kapatmasi icin bekleme firsati tanir."""
    while True:
        try:
            wb.save(excel_path)
            break
        except PermissionError:
            print(f"\n[UYARI] '{os.path.basename(excel_path)}' dosyasi su anda Microsoft Excel veya baska bir programda ACIK!")
            print(f"        Windows dosya acikken uzerine yazilmasina izin vermiyor.")
            input("        Lutfen Excel'i KAPATIP Enter tusuna basin (tekrar denenecek)... ")
        except Exception as e:
            print(f"[HATA] Excel kaydedilirken hata olustu: {e}")
            raise
