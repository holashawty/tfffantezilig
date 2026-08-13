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
    5. Sonucu ekrana yaz + xlsx olarak disari ver (biçimli)
"""

import argparse
import sys
import pandas as pd
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

from data_loader import load_players, load_gameweek_log
from xp_model import compute_xp
from optimizer import optimize_squad


# === Excel biçimlendirme sabitleri ===
HEADER_FILL = PatternFill(start_color="404040", end_color="404040", fill_type="solid")
HEADER_FONT = Font(bold=True, color="FFFFFF", size=11)
HEADER_ALIGN = Alignment(horizontal="center", vertical="center", wrap_text=True)

CAPTAIN_FILL = PatternFill(start_color="FFEB3B", end_color="FFEB3B", fill_type="solid")  # sari
VICE_FILL    = PatternFill(start_color="FFF59D", end_color="FFF59D", fill_type="solid")  # acik sari
BENCH_FILL   = PatternFill(start_color="EEEEEE", end_color="EEEEEE", fill_type="solid")  # gri

THIN_BORDER = Border(
    left=Side(style="thin", color="CCCCCC"),
    right=Side(style="thin", color="CCCCCC"),
    top=Side(style="thin", color="CCCCCC"),
    bottom=Side(style="thin", color="CCCCCC"),
)

# Pozisyon siralama onceligi (GK -> DEF -> MID -> FWD)
POS_ORDER = {"GK": 1, "DEF": 2, "MID": 3, "FWD": 4}
# Rol onceligi (CAPTAIN ve VICE once, sonra STARTER, en son BENCH)
ROLE_ORDER = {"CAPTAIN": 1, "VICE_CAPTAIN": 2, "STARTER": 3, "BENCH": 4}

PRICE_FORMAT = '#,##0" TL"'
XP_FORMAT = "0.00"
PROB_FORMAT = "0%"


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
    """Kadro onerisini biçimli Excel olarak disari verir.

    Biçimlendirme:
      - Baslik satiri: kalin, gri arka plan, beyaz yazi
      - price_tl: #,##0" TL" formati (9.000.000 TL)
      - xp: 2 ondalik (3.84)
      - play_probability: yuzde (95%)
      - role=CAPTAIN satiri: sari arka plan
      - role=VICE_CAPTAIN: acik sari
      - role=BENCH: gri arka plan
      - Satirlar pozisyona (GK->DEF->MID->FWD) ve role (CAPTAIN->VICE->STARTER->BENCH) gore sirali
    """
    squad = result.squad.copy()
    squad["gameweek"] = gameweek
    squad["role"] = squad["is_starter"].map({True: "STARTER", False: "BENCH"})
    squad.loc[squad["player_id"] == result.captain["player_id"], "role"] = "CAPTAIN"
    squad.loc[squad["player_id"] == result.vice_captain["player_id"], "role"] = "VICE_CAPTAIN"

    out_cols = ["player_id", "name", "position_code", "team", "price_tl",
                "play_probability", "xp", "role"]
    squad_out = squad[out_cols].copy()

    # Siralama: once pozisyon (GK->DEF->MID->FWD), sonra role (CAPTAIN->VICE->STARTER->BENCH),
    # sonra xp'ye gore azalan (ayni pozisyon+role icinde yüksek xP basta)
    squad_out["_pos_order"] = squad_out["position_code"].map(POS_ORDER)
    squad_out["_role_order"] = squad_out["role"].map(ROLE_ORDER)
    squad_out = squad_out.sort_values(
        ["_pos_order", "_role_order", "xp"], ascending=[True, True, False]
    ).drop(columns=["_pos_order", "_role_order"]).reset_index(drop=True)

    # openpyxl workbook olustur, biçimlendirme uygula
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = f"GW{gameweek}_Kadro"

    # Baslik satiri
    headers_tr = ["Oyuncu ID", "Ad", "Pozisyon", "Takim", "Fiyat",
                  "Oynama %", "xP", "Rol"]
    for c, h in enumerate(headers_tr, start=1):
        cell = ws.cell(row=1, column=c, value=h)
        cell.fill = HEADER_FILL
        cell.font = HEADER_FONT
        cell.alignment = HEADER_ALIGN
        cell.border = THIN_BORDER

    # Veri satirlari
    for r_idx, row in squad_out.iterrows():
        r = r_idx + 2  # baslik satirindan sonra
        values = [row["player_id"], row["name"], row["position_code"],
                  row["team"], row["price_tl"], row["play_probability"],
                  row["xp"], row["role"]]
        for c, v in enumerate(values, start=1):
            cell = ws.cell(row=r, column=c, value=v)
            cell.border = THIN_BORDER
            cell.alignment = Alignment(vertical="center")

        # Hucre bicimlendirme: sayi formatlari
        ws.cell(row=r, column=5).number_format = PRICE_FORMAT   # Fiyat
        ws.cell(row=r, column=6).number_format = PROB_FORMAT    # Oynama %
        ws.cell(row=r, column=7).number_format = XP_FORMAT      # xP

        # Rol bazli arka plan rengi
        role = row["role"]
        if role == "CAPTAIN":
            row_fill = CAPTAIN_FILL
        elif role == "VICE_CAPTAIN":
            row_fill = VICE_FILL
        elif role == "BENCH":
            row_fill = BENCH_FILL
        else:
            row_fill = None
        if row_fill is not None:
            for c in range(1, len(values) + 1):
                ws.cell(row=r, column=c).fill = row_fill

        # Kaptan/vice satirinda "Ad" kalin
        if role in ("CAPTAIN", "VICE_CAPTAIN"):
            ws.cell(row=r, column=2).font = Font(bold=True)

    # Kolon genislikleri
    col_widths = {
        1: 12,  # Oyuncu ID
        2: 30,  # Ad
        3: 10,  # Pozisyon
        4: 18,  # Takim
        5: 16,  # Fiyat
        6: 12,  # Oynama %
        7: 10,  # xP
        8: 14,  # Rol
    }
    for c, w in col_widths.items():
        ws.column_dimensions[get_column_letter(c)].width = w

    # Baslik satiri yuksekligi
    ws.row_dimensions[1].height = 32

    # Freeze panes - baslik sabit kalsin
    ws.freeze_panes = "A2"

    wb.save(path)
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
