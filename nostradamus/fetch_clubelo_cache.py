"""
fetch_clubelo_cache.py
----------------------
Tüm Süper Lig takımları için ClubElo derece geçmişini bir kez indirip
yerel CSV olarak saklar. docs/01'in "kendi ELO algoritmanı yazma,
soccerdata kullan" kuralının uygulamasıdır.

İndirme maliyeti: ~15s/takım × 25 takım ≈ 6-7 dakika. Bu yüzden
cache'lenir — backtest script'leri her çalıştığında yeniden indirmez.

Kullanım:
    python fetch_clubelo_cache.py <superlig_odds.db> <cache.csv>
"""

import argparse
import logging
import os
import sqlite3
import sys
import time

import pandas as pd
import soccerdata as sd


# bizim DB'deki canonical_name → ClubElo'daki takım adı
# (deneme-yanılma ile bulunan eşlemeler)
TEAM_NAME_MAP = {
    "Ad. Demirspor":     "Adana Demirspor",
    "Alanyaspor":        "Alanyaspor",
    "Ankaragucu":        "MKE Ankaragucu",
    "Antalyaspor":       "Antalyaspor",
    "Besiktas":          "Besiktas",
    "Bodrumspor":        "Bodrum",
    "Buyuksehyr":        "Istanbul Basaksehir",
    "Eyupspor":          "Eyupspor",
    "Fenerbahce":        "Fenerbahce",
    "Galatasaray":       "Galatasaray",
    "Gaziantep":         "Gaziantepspor",
    "Genclerbirligi":    "Genclerbirligi",
    "Goztep":            "Goztep",
    "Hatayspor":         "Hatayspor",
    "Istanbulspor":      "Istanbulspor",
    "Karagumruk":        "Fatih Karagumruk",
    "Kasimpasa":         "Kasimpasa",
    "Kayserispor":       "Kayseri",
    "Kocaelispor":       "Kocaelispor",
    "Konyaspor":         "Konyaspor",
    "Pendikspor":        "Pendikspor",
    "Rizespor":          "Rizespor",
    "Samsunspor":        "Samsunspor",
    "Sivasspor":         "Sivasspor",
    "Trabzonspor":       "Trabzonspor",
    # 8 sezonda görünen ama son 3'te olmayan takımlar (cache tamam olsun)
    "Akhisar Belediyespor": "Akhisarspor",
    "Altay":             "Altay",
    "Bursaspor":         "Bursaspor",
    "Denizlispor":       "Denizlispor",
    "Erzurum BB":        "BB Erzurumspor",
    "Giresunspor":       "Giresunspor",
    "Yeni Malatyaspor":  "Yeni Malatyaspor",
}


def fetch_all(db_path, cache_path):
    logging.disable(logging.INFO)
    if os.path.exists(cache_path):
        existing = pd.read_csv(cache_path)
        print(f"Mevcut cache: {len(existing)} satır, {existing['team'].nunique()} takım")
        have = set(existing["team"].unique())
    else:
        existing = pd.DataFrame()
        have = set()

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("SELECT team_id, canonical_name FROM teams ORDER BY canonical_name;")
    teams = cur.fetchall()
    conn.close()

    cl = sd.ClubElo()
    all_dfs = [existing] if not existing.empty else []
    fetched, failed = 0, []

    for tid, cname in teams:
        elo_name = TEAM_NAME_MAP.get(cname, cname)
        if elo_name in have:
            print(f"  SKIP {cname:25} -> {elo_name}  (zaten cache'de)")
            continue
        t0 = time.time()
        try:
            df = cl.read_team_history(elo_name)
            if df is None or df.empty:
                raise RuntimeError("boş sonuç")
            df = df.reset_index().rename(columns={"from": "from_date"})
            df["team_id"] = tid
            df["our_name"] = cname
            df["clubelo_name"] = elo_name
            all_dfs.append(df)
            fetched += 1
            print(f"  OK   {cname:25} -> {elo_name:30}  {len(df)} rows  ({time.time()-t0:.1f}s)")
            have.add(elo_name)
        except Exception as e:
            failed.append((cname, elo_name, str(e)))
            print(f"  ERR  {cname:25} -> {elo_name:30}  {type(e).__name__}: {e}  ({time.time()-t0:.1f}s)")

    if all_dfs:
        combined = pd.concat(all_dfs, ignore_index=True)
        combined.to_csv(cache_path, index=False)
        print(f"\n[TAMAM] {cache_path}: {len(combined)} satır, "
              f"{combined['clubelo_name'].nunique()} takım")

    if failed:
        print(f"\n[UYARI] {len(failed)} takım başarısız — manuel düzeltme gerek:")
        for cname, ename, err in failed:
            print(f"  {cname:25} -> {ename:30}  ({err})")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("db_path")
    ap.add_argument("cache_path")
    args = ap.parse_args()
    fetch_all(args.db_path, args.cache_path)
