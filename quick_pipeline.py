"""
quick_pipeline.py
-----------------
Haftalık operasyonları (Hafta Öncesi Hazırlık ve Hafta Sonrası Sonuç Girişi)
tek bir komutla uçtan uca çalıştıran hızlı otomasyon aracı.

KULLANIM:
  1. Hafta Öncesi Hazırlık (Sakatlık + Fiyat + Nostradamus + Kadro Optimizasyonu):
     python quick_pipeline.py --gameweek 2 --apply

  2. Hafta Sonrası Sonuçlar (Maç Sonuçları + GameweekLog Güncellemesi):
     python quick_pipeline.py --gameweek 2 --results --apply
"""

import argparse
import os
import subprocess
import sys
import openpyxl

from backup_utils import backup_excel


def run_pre_gameweek(excel_path, gameweek, apply_changes):
    print("=" * 65)
    print(f"  TFF FANTEZI LIG - HAFTA {gameweek} HAZIRLIK PIPELINE'I")
    print("=" * 65)

    injury_file = f"web_research_gw{gameweek}.json"
    price_file = f"fiyat_gw{gameweek}.json"
    fixtures_file = f"nostradamus_fixtures_gw{gameweek}.json"

    files_found = {
        "Sakatlık/Ceza": (injury_file, os.path.exists(injury_file)),
        "Fiyatlar": (price_file, os.path.exists(price_file)),
        "Nostradamus Oranları": (fixtures_file, os.path.exists(fixtures_file)),
    }

    print("\n[DURUM KONTROLU]")
    for label, (fname, exists) in files_found.items():
        status = "[MEVCUT]" if exists else "[BULUNAMADI - Atlanacak]"
        print(f"  {label:<22} : {fname:<32} {status}")

    # 1. Sakatlık güncellemesi
    if files_found["Sakatlık/Ceza"][1]:
        print("\n" + "-" * 50)
        print("1. Sakatlık ve Cezalar İşleniyor...")
        cmd = [sys.executable, "update_from_web_research.py", excel_path, injury_file]
        if apply_changes:
            cmd.append("--apply")
        subprocess.run(cmd)
    else:
        print("\n[BILGI] Sakatlık JSON dosyası bulunamadı, mevcut sakatlık durumlarıyla devam ediliyor.")

    # 2. Fiyat güncellemesi
    if files_found["Fiyatlar"][1]:
        print("\n" + "-" * 50)
        print("2. Güncel Fiyatlar İşleniyor...")
        cmd = [sys.executable, "ingest_price_updates.py", excel_path, price_file]
        if apply_changes:
            cmd.append("--apply")
        subprocess.run(cmd)
    else:
        print("\n[BILGI] Fiyat JSON dosyası bulunamadı, mevcut fiyatlarla devam ediliyor.")

    # 3. Nostradamus tahmin üretimi
    if files_found["Nostradamus Oranları"][1]:
        print("\n" + "-" * 50)
        print("3. Nostradamus Tahminleri Hesaplanıyor...")
        subprocess.run([sys.executable, "nostradamus_predict.py", fixtures_file])
    else:
        print("\n[BILGI] Nostradamus fixtures JSON dosyası bulunamadı.")

    # 4. Kadro optimizasyonu
    print("\n" + "=" * 50)
    print(f"4. Kadro Optimizasyonu Başlatılıyor (Hafta {gameweek})...")
    print("=" * 50)
    subprocess.run([sys.executable, "run_gameweek.py", excel_path, "--gameweek", str(gameweek)])

    output_kadro = f"gw{gameweek}_kadro_onerisi.xlsx"
    if os.path.exists(output_kadro):
        print(f"\n[TAMAMLANDI] En iyi kadro oluşturuldu: {output_kadro}")
        try:
            os.startfile(output_kadro)
        except Exception:
            pass
    else:
        print("\n[UYARI] Kadro dosyası oluşturulamadı.")


def run_post_gameweek(excel_path, gameweek, apply_changes):
    print("=" * 65)
    print(f"  TFF FANTEZI LIG - HAFTA {gameweek} SONUC VE PUAN ISLEME")
    print("=" * 65)

    results_file = f"match_sonuclari_gw{gameweek}.json"
    if not os.path.exists(results_file):
        print(f"\n[HATA] Sonuç dosyası bulunamadı: {results_file}")
        print("Lütfen tff_fantezi_export.js kullanarak veya Gemini ile dosyanızı oluşturun.")
        return

    print(f"\n1. {results_file} dosyası sisteme işleniyor...")
    cmd = [sys.executable, "ingest_gameweek_results.py", excel_path, results_file]
    if apply_changes:
        cmd.append("--apply")
    subprocess.run(cmd)


def main():
    parser = argparse.ArgumentParser(description="TFF Fantezi Lig Hızlı Pipeline")
    parser.add_argument("--excel", default="oyuncu_veritabani.xlsx", help="Excel veritabanı yolu")
    parser.add_argument("--gameweek", type=int, default=1, help="İşlenecek hafta no")
    parser.add_argument("--apply", action="store_true", help="Değişiklikleri Excel'e kaydet")
    parser.add_argument("--results", action="store_true", help="Hafta sonu maç sonuçlarını işle")

    args = parser.parse_args()

    if args.results:
        run_post_gameweek(args.excel, args.gameweek, args.apply)
    else:
        run_pre_gameweek(args.excel, args.gameweek, args.apply)


if __name__ == "__main__":
    main()
