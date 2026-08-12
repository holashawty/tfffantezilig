"""
run_gameweek.py
----------------
Haftalik calistirilacak ana script.

Kullanim:
    python run_gameweek.py <excel_yolu> [--gameweek N] [--out cikti.xlsx]

Akis:
    1. Players / GameweekLog sheet'lerini oku
    2. Fiyatlari guncelle (GameweekLog'da o haftaya ait fiyat varsa)
    3. xP hesapla (price-prior + shrinkage + play_probability)
    4. MILP ile kesin en iyi 15 / ilk 11 / kaptan / yedek sirasi
    5. Sonucu ekrana yaz + xlsx olarak disari ver
"""

import argparse
import sys
import pandas as pd

from data_loader import load_players, load_gameweek_log
from xp_model import compute_xp
from optimizer import optimize_squad


def format_tl(x: float) -> str:
    return f"{x:,.0f} TL".replace(",", ".")


def print_result(result, gameweek: int):
    print(f"\n{'='*60}")
    print(f"  HAFTA {gameweek} - ONERILEN KADRO")
    print(f"{'='*60}")
    print(f"Toplam maliyet: {format_tl(result.total_budget_used)} / 100.000.000 TL")
    print(f"Ilk 11 toplam xP: {result.total_starting_xp:.2f}")

    print("\n--- ILK 11 ---")
    cols = ["name", "position_code", "team", "price_tl", "xp"]
    for pos in ["GK", "DEF", "MID", "FWD"]:
        rows = result.starters[result.starters["position_code"] == pos]
        for _, r in rows.sort_values("xp", ascending=False).iterrows():
            tag = ""
            if r["player_id"] == result.captain["player_id"]:
                tag = "  <- KAPTAN (2x)"
            elif r["player_id"] == result.vice_captain["player_id"]:
                tag = "  <- YEDEK KAPTAN"
            print(f"  [{pos}] {r['name']:<28} {r['team']:<16} "
                  f"{format_tl(r['price_tl']):>14}  xP={r['xp']:.2f}{tag}")

    print("\n--- YEDEKLER (oncelik sirasina gore) ---")
    if result.bench_gk is not None:
        print(f"  [GK]  {result.bench_gk['name']:<28} xP={result.bench_gk['xp']:.2f}")
    for i, (_, r) in enumerate(result.bench_outfield.iterrows(), start=1):
        print(f"  [{i}]   {r['name']:<28} ({r['position_code']}) xP={r['xp']:.2f}")


def export_result(result, path: str, gameweek: int):
    squad = result.squad.copy()
    squad["gameweek"] = gameweek
    squad["role"] = squad["is_starter"].map({True: "STARTER", False: "BENCH"})
    squad.loc[squad["player_id"] == result.captain["player_id"], "role"] = "CAPTAIN"
    squad.loc[squad["player_id"] == result.vice_captain["player_id"], "role"] = "VICE_CAPTAIN"

    out_cols = ["player_id", "name", "position_code", "team", "price_tl",
                "play_probability", "xp", "role"]
    squad[out_cols].sort_values(
        ["role", "position_code"], ascending=[False, True]
    ).to_excel(path, index=False, sheet_name=f"GW{gameweek}_Kadro")
    print(f"\nSonuc yazildi: {path}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("excel_path")
    ap.add_argument("--gameweek", type=int, default=1)
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    players = load_players(args.excel_path)
    log = load_gameweek_log(args.excel_path)

    players = compute_xp(players, log)
    result = optimize_squad(players)

    print_result(result, args.gameweek)

    out_path = args.out or f"gw{args.gameweek}_kadro_onerisi.xlsx"
    export_result(result, out_path, args.gameweek)


if __name__ == "__main__":
    main()
