"""
update_week.py
---------------
"Haftayi guncelle" orkestratoru. Tum haftalik rutini tek komutta
yonetir. Otomatik (kod) adimlar KENDI CALISIR; web-arastirmasi
gerektiren 2 adim icin (API olmadigi icin) seni durdurup ne yapman
gerektigini soyler, sen JSON dosyasini kaydedince devam eder.

AKIS (hafta N icin):
  1. [MANUEL]  Onceki haftanin sonuclarini ingest et (varsa)
               -> ingest_gameweek_results.py
  2. [OTOMATIK] PRIOR_CONFIG'i biriken gercek veriyle kalibre et
               -> calibrate_priors.py  (yeterli veri yoksa atlanir)
  3. [MANUEL]  Bu haftanin fiyat degisikliklerini guncelle (varsa)
               -> ingest_price_updates.py
  4. [MANUEL]  Bu haftanin sakatlik/ceza durumunu guncelle
               -> update_from_web_research.py
  5. [OTOMATIK] xP hesapla + MILP ile kadroyu optimize et
               -> run_gameweek.py

Kullanim:
    python update_week.py <excel_yolu> --gameweek N \\
        [--results sonuclar_gwN-1.json] [--prices fiyat_gwN.json] \\
        [--research web_research_gwN.json] [--apply]

    --apply verilmezse her adim dry-run raporu gosterir, hicbir
    dosyayi degistirmez — once kontrol et, sonra --apply ile gercek
    calistirma yap.
"""

import argparse
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def run(cmd, label):
    print(f"\n{'#'*60}\n# {label}\n{'#'*60}")
    result = subprocess.run([sys.executable] + cmd, cwd=HERE)
    if result.returncode != 0:
        print(f"\n[DURDU] '{label}' adimi hata verdi, sonraki adima gecilmiyor.")
        sys.exit(1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("excel_path")
    ap.add_argument("--gameweek", type=int, required=True)
    ap.add_argument("--results", default=None,
                     help="Onceki haftanin sonuc JSON'u (varsa) — bkz. match_sonuclari_prompti.md")
    ap.add_argument("--prices", default=None,
                     help="Bu haftanin fiyat guncelleme JSON'u (varsa) — bkz. fiyat_guncelleme_prompti.md")
    ap.add_argument("--research", default=None,
                     help="Bu haftanin sakatlik/ceza JSON'u — bkz. web_arastirma_prompti.md")
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    apply_flag = ["--apply"] if args.apply else []

    # 1. Onceki hafta sonuclari (varsa)
    if args.results:
        if not os.path.exists(args.results):
            print(f"[UYARI] {args.results} bulunamadi, adim 1 atlaniyor.")
        else:
            run(["ingest_gameweek_results.py", args.excel_path, args.results] + apply_flag,
                "ADIM 1/5 — Onceki hafta sonuclarini isle")
    else:
        print("\n[BILGI] --results verilmedi, adim 1 (sonuc ingest) atlaniyor. "
              "Ilk hafta icin bu normal.")

    # 2. Otomatik kalibrasyon (her zaman dry-run once, veri varsa --apply ile calisir)
    run(["calibrate_priors.py", args.excel_path] + apply_flag,
        "ADIM 2/5 — PRIOR_CONFIG otomatik kalibrasyon (yeterli veri varsa)")

    # 3. Bu haftanin fiyat guncellemeleri
    if args.prices:
        if not os.path.exists(args.prices):
            print(f"[UYARI] {args.prices} bulunamadi, adim 3 atlaniyor.")
        else:
            run(["ingest_price_updates.py", args.excel_path, args.prices] + apply_flag,
                "ADIM 3/5 — Fiyat guncelle")
    else:
        print(f"\n[BILGI] --prices verilmedi, adim 3 (fiyat guncelleme) atlaniyor. "
              f"Fiyati degismis onemli oyuncu yoksa bu normal — fiyat_guncelleme_prompti.md'ye bak.")

    # 4. Bu haftanin sakatlik/ceza guncellemesi
    if args.research:
        if not os.path.exists(args.research):
            print(f"[UYARI] {args.research} bulunamadi, adim 4 atlaniyor.")
        else:
            run(["update_from_web_research.py", args.excel_path, args.research] + apply_flag,
                "ADIM 4/5 — Sakatlik/ceza (play_probability) guncelle")
    else:
        print(f"\n[MANUEL ADIM GEREKLI] Hafta {args.gameweek} icin sakatlik/ceza arastirmasi "
              f"yapilmadi. web_arastirma_prompti.md'yi bir web AI'ya yapistir, ciktiyi "
              f"web_research_gw{args.gameweek}.json olarak kaydet, sonra bu scripti "
              f"--research web_research_gw{args.gameweek}.json ile tekrar calistir.")

    # 5. Kadro optimizasyonu (her zaman calisir, en guncel veriyle)
    run(["run_gameweek.py", args.excel_path, "--gameweek", str(args.gameweek)],
        "ADIM 5/5 — Kadro optimizasyonu")

    print(f"\n{'='*60}\nHafta {args.gameweek} guncellemesi tamamlandi.\n{'='*60}")


if __name__ == "__main__":
    main()
