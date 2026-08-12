"""
calibrate_priors.py
--------------------
PRIOR_CONFIG katsayilarini (xp_model.py) gercek GameweekLog verisiyle
otomatik yeniden tahmin eder.

NEDEN BU BIR LLM/PROMPT ISI DEGIL:
Bu bir istatistiksel tahmin (regresyon) problemi: "price_percentile
ile gercek gol/asist/kart oranlari arasindaki iliski nedir?" sorusunun
tek dogru cevabi verideki sayilardan cikar. Bir web AI'ya "yeni
katsayilari tahmin et" diye sormak once GameweekLog verisini tam ve
dogru okumasini, sonra da kafadan regresyon yapmasini gerektirir —
ikisi de kod her zaman daha hizli, daha dogru ve tekrarlanabilir
sekilde yapar. LLM'in rolu (web arastirmasi) burada yok; bu yuzden bu
script tamamen otonom calisir, hicbir web AI promptuna ihtiyac duymaz.

YONTEM: Her (pozisyon, istatistik) cifti icin, o pozisyondaki
oyunculari price_percentile'a karsi gozlenen orana (agirliksiz
dogrusal regresyon, np.polyfit derece=1) oturtur. Yeterli veri
olmayan pozisyon/istatistik kombinasyonlari ATLANIR ve eski deger
korunur (az veriyle asiri uydurma / overfitting'den kacinmak icin).

Kullanim:
    python calibrate_priors.py <excel_yolu> [--min-games 2] [--min-players 8] [--apply]

    --apply verilmezse sadece ESKI vs YENI karsilastirma raporu basar,
    prior_config_calibrated.json'a yazmaz (dry-run).
"""

import argparse
import json
import os

import numpy as np
import pandas as pd

from data_loader import load_players, load_gameweek_log
from xp_model import PRIOR_CONFIG, get_active_prior_config, CALIBRATED_CONFIG_PATH

STATS_TO_CALIBRATE = [
    "start_prob", "goals_per_match", "assists_per_match",
    "clean_sheet_prob", "yellow_prob", "red_prob",
]


def _player_level_observations(players: pd.DataFrame, log: pd.DataFrame) -> pd.DataFrame:
    """Her oyuncu icin: oynadigi hafta sayisi, mac basi gol/asist,
    60dk+ oynama orani, sari/kirmizi kart orani."""
    if log.empty:
        return pd.DataFrame()

    g = log.groupby("player_id").agg(
        n_games=("gameweek", "count"),
        avg_minutes=("minutes", "mean"),
        goals_per_match=("goals", "mean"),
        assists_per_match=("assists", "mean"),
        yellow_prob=("yellow_cards", "mean"),
        red_prob=("red_cards", "mean"),
        start_prob=("minutes", lambda s: (s >= 60).mean()),
    ).reset_index()

    merged = g.merge(
        players[["player_id", "position_code", "price_tl"]],
        on="player_id", how="left",
    )
    merged["price_pct"] = merged.groupby("position_code")["price_tl"].rank(pct=True)
    return merged


def _fit_stat(obs: pd.DataFrame, stat: str, min_players: int):
    """Bir (pozisyon icindeki) istatistik icin (base, spread) tahmini.
    Yeterli veri yoksa None doner (eski deger korunur demek)."""
    sub = obs.dropna(subset=[stat, "price_pct"])
    if len(sub) < min_players:
        return None
    x = sub["price_pct"].values
    y = sub[stat].values
    if np.std(x) < 1e-6:
        return None
    slope, intercept = np.polyfit(x, y, 1)
    base = float(np.clip(intercept, 0.0, None))
    spread = float(slope)
    return round(base, 4), round(spread, 4)


def calibrate(players: pd.DataFrame, log: pd.DataFrame, min_games: int, min_players: int):
    obs = _player_level_observations(players, log)
    if obs.empty:
        return {}, "GameweekLog bos — kalibre edilecek veri yok."

    obs = obs[obs["n_games"] >= min_games]
    if obs.empty:
        return {}, f"Hicbir oyuncu min_games={min_games} sartini saglamiyor — henuz erken."

    current = get_active_prior_config()
    new_config, report_lines = {}, []

    for pos in ["GK", "DEF", "MID", "FWD"]:
        pos_obs = obs[obs["position_code"] == pos]
        pos_updates = {}
        for stat in STATS_TO_CALIBRATE:
            # clean_sheet_prob observed veriden dogrudan cikmiyor (GameweekLog'da
            # yok), o yuzden atla — bu istatistik icin manuel/baska kaynak gerekir.
            if stat == "clean_sheet_prob":
                continue
            fit = _fit_stat(pos_obs, stat, min_players)
            if fit is None:
                continue
            old = current[pos][stat]
            if fit != old:
                pos_updates[stat] = fit
                report_lines.append(
                    f"  [{pos}] {stat:<20} eski={old}  ->  yeni={fit}  (n_oyuncu={len(pos_obs.dropna(subset=[stat]))})"
                )
        if pos_updates:
            new_config[pos] = pos_updates

    summary = "\n".join(report_lines) if report_lines else "Degisen bir katsayi yok / yeterli veri yok."
    return new_config, summary


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("excel_path")
    ap.add_argument("--min-games", type=int, default=2,
                     help="Bir oyuncunun sayilmasi icin gereken min oynanan hafta")
    ap.add_argument("--min-players", type=int, default=8,
                     help="Bir pozisyon/istatistik icin gereken min oyuncu sayisi")
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    players = load_players(args.excel_path)
    log = load_gameweek_log(args.excel_path)

    new_config, summary = calibrate(players, log, args.min_games, args.min_players)

    print("\n=== PRIOR_CONFIG kalibrasyon raporu ===")
    print(summary)

    if not new_config:
        print("\nUygulanacak degisiklik yok.")
        return

    if not args.apply:
        print("\n[DRY-RUN] prior_config_calibrated.json yazilmadi. Onayliyorsan --apply.")
        return

    existing = {}
    if os.path.exists(CALIBRATED_CONFIG_PATH):
        with open(CALIBRATED_CONFIG_PATH, "r", encoding="utf-8") as f:
            existing = json.load(f)
    for pos, stats in new_config.items():
        existing.setdefault(pos, {})
        existing[pos].update(stats)

    with open(CALIBRATED_CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(existing, f, ensure_ascii=False, indent=2)
    print(f"\n[UYGULANDI] {CALIBRATED_CONFIG_PATH} guncellendi. "
          f"xp_model.py bir sonraki calistirmada bunu otomatik kullanacak.")


if __name__ == "__main__":
    main()
