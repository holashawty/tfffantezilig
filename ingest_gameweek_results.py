"""
ingest_gameweek_results.py
---------------------------
Bir hafta oynandiktan sonra GERCEK performans verisini (dakika, gol,
asist, kart, ve varsa TFF'nin kendi hesapladigi fantasy_points) JSON'dan
okuyup GameweekLog'a EKLER (var olan satirlari degil, yeni satirlar).

IKI VERI KAYNAGI ONERISI (ikisi de ayni JSON semasina cevrilir):
  A) EN GUVENILIR: TFF Fantezi Lig uygulamasindaki "Puanim" ekranini
     ekran goruntusu/PDF olarak belge-erisimi olan bir AI'ya (Gemini)
     ver, "bu ekrandaki oyuncu puanlarini asagidaki JSON semasina
     donustur" de. fantasy_points dogrudan TFF'nin kendi hesabidir,
     bizim tahminimize gerek kalmaz.
  B) TAMAMLAYICI: Web arastirmasiyla (goal.com, sofascore vb.) mac
     istatistikleri (dakika/gol/asist/kart) toplanip PRIOR_CONFIG
     kalibrasyonu icin kullanilir — ama bu kaynak eksik/hatali
     olabilir, o yuzden fantasy_points alaniyla CELISIRSE (A) kaynagi
     esas alinir.

JSON semasi (match_sonuclari_prompti.md'deki prompt bunu uretir):
{
  "gameweek": 1,
  "results": [
    {
      "player_name": "...", "team": "...",
      "minutes": 90, "goals": 1, "assists": 0,
      "yellow_cards": 0, "red_cards": 0,
      "fantasy_points": 12.0,     // TFF'nin kendi puanindan biliniyorsa
      "price_tl": 4500000         // o haftaki fiyat biliniyorsa (opsiyonel)
    }
  ]
}

Kullanim:
    python ingest_gameweek_results.py <excel_yolu> <sonuclar_gwN.json> [--apply]
"""

import argparse
import json
from difflib import SequenceMatcher

import openpyxl

from data_loader import load_players
from validator import validate_match_results

NAME_MATCH_THRESHOLD = 0.82


def _similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, a.lower().strip(), b.lower().strip()).ratio()


def _find_gameweeklog_header(ws):
    for r in range(1, 10):
        if ws.cell(row=r, column=1).value == "player_id":
            return r
    raise RuntimeError("GameweekLog header satiri bulunamadi.")


def _last_data_row(ws, header_row):
    r = header_row + 1
    while ws.cell(row=r, column=1).value not in (None, ""):
        r += 1
    return r  # ilk bos satir


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("excel_path")
    ap.add_argument("json_path")
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    with open(args.json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    gameweek = data["gameweek"]
    results = data.get("results", [])

    players = load_players(args.excel_path)
    name_lookup = players[["player_id", "name", "team"]].to_dict("records")

    quality = validate_match_results(results)
    quality.print_report(f"Hafta {gameweek} mac sonuclari")

    matched, unmatched = [], []
    for res in quality.valid_records:
        best_id, best_score = None, 0.0
        for p in name_lookup:
            score = _similarity(res["player_name"], p["name"])
            if score > best_score:
                best_id, best_score, best_name = p["player_id"], score, p["name"]
        if best_id is None or best_score < NAME_MATCH_THRESHOLD:
            unmatched.append(res)
            continue
        matched.append({
            "player_id": best_id,
            "matched_name": best_name,
            "input_name": res["player_name"],
            "similarity": round(best_score, 3),
            "minutes": res.get("minutes", 0),
            "goals": res.get("goals", 0),
            "assists": res.get("assists", 0),
            "yellow_cards": res.get("yellow_cards", 0),
            "red_cards": res.get("red_cards", 0),
            "fantasy_points": res.get("fantasy_points"),
            "price_tl": res.get("price_tl"),
        })

    print(f"\n=== Hafta {gameweek} eslesme raporu ===")
    print(f"Gecerli kayittan eslesen: {len(matched)}  |  Isim eslesmeyen: {len(unmatched)}\n")
    for m in matched:
        print(f"  {m['input_name']:<28} -> {m['matched_name']:<28} "
              f"dk={m['minutes']:>3} gol={m['goals']} asist={m['assists']} "
              f"puan={m['fantasy_points']}  (benzerlik={m['similarity']})")
    if unmatched:
        print("\n--- ESLESMEYEN (manuel kontrol) ---")
        for u in unmatched:
            print(f"  {u['player_name']} ({u.get('team')})")

    if not args.apply:
        print("\n[DRY-RUN] GameweekLog'a yazilmadi. Onayliyorsan --apply ile tekrar calistir.")
        return

    wb = openpyxl.load_workbook(args.excel_path)
    ws = wb["GameweekLog"]
    header_row = _find_gameweeklog_header(ws)
    r = _last_data_row(ws, header_row)

    for m in matched:
        ws.cell(row=r, column=1).value = m["player_id"]
        ws.cell(row=r, column=2).value = gameweek
        ws.cell(row=r, column=3).value = m["minutes"]
        ws.cell(row=r, column=4).value = m["goals"]
        ws.cell(row=r, column=5).value = m["assists"]
        ws.cell(row=r, column=6).value = m["yellow_cards"]
        ws.cell(row=r, column=7).value = m["red_cards"]
        ws.cell(row=r, column=8).value = m["fantasy_points"]
        if m["price_tl"] is not None:
            ws.cell(row=r, column=9).value = m["price_tl"]
        r += 1

    wb.save(args.excel_path)
    print(f"\n[UYGULANDI] {len(matched)} satir GameweekLog'a eklendi -> {args.excel_path}")


if __name__ == "__main__":
    main()
