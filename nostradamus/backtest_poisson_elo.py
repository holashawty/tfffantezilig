"""
backtest_poisson_elo.py
-----------------------
docs/03 Adım 3: Devig baseline'a Poisson (Dixon-Coles) ve Elo (ClubElo)
katmanlarını ekleyip Brier score iyileşmesi olup olmadığını ölçer.

Kural (docs/03): iyileşme YOKSA katman EKLENMEZ.

Test edilen varyantlar:
  A) devig-only (baseline, 0.5557)
  B) devig + ClubElo (ağırlık 0.3, 0.5, 0.7 — en iyisini seç)
  C) devig + Dixon-Coles Poisson (sezon başında fit, ağırlık 0.3, 0.5, 0.7)
  D) devig + Elo + Poisson (çeşitli kombinasyonlar)

Elo kaynağı: ClubElo (cache/clubelo_history.csv). 4 takım eksik
(Basaksehir, Karagumruk, Ankaragucu, Goztep) — bu takımların maçlarında
Elo katmanı atlanır, sadece devig kullanılır.

Poisson kaynağı: penaltyblog.models.DixonColesGoalModel. Her sezon
başında, o sezonun başlangıç tarihinden önceki tüm maçlarla fit edilir
(look-ahead bias yok).

Kullanım:
    python backtest_poisson_elo.py <superlig_odds.db> <clubelo_cache.csv>
"""

import argparse
import sqlite3
import sys
from collections import defaultdict
from datetime import datetime, timedelta
from statistics import median

import pandas as pd

from shin import calculate_implied_probabilities
from penaltyblog.models import DixonColesGoalModel


SELECTION_ORDER = ["H", "D", "A"]


# ============================================================
# DEVIG (baseline ile aynı)
# ============================================================

def _proportional_devig(odds_3):
    invs = [1.0 / o for o in odds_3]
    s = sum(invs)
    return [v / s for v in invs]


def _shin_devig(odds_3):
    try:
        probs = calculate_implied_probabilities(odds_3)
        probs = [max(0.0, min(1.0, p)) for p in probs]
        s = sum(probs)
        if s <= 0:
            return _proportional_devig(odds_3)
        return [p / s for p in probs]
    except Exception:
        return _proportional_devig(odds_3)


def _aggregate_bookmaker_probs(prob_vectors):
    if not prob_vectors:
        return None
    by_class = [[v[c] for v in prob_vectors] for c in range(3)]
    med = [median(col) for col in by_class]
    s = sum(med)
    if s <= 0:
        return None
    return [p / s for p in med]


def devig_probs_for_match(odds_by_bookmaker):
    """{bookmaker: [H, D, A]} → [p_H, p_D, p_A] veya None."""
    per_bk = []
    for bk, odds_3 in odds_by_bookmaker.items():
        if any(o is None or o <= 1.0 for o in odds_3):
            continue
        per_bk.append(_shin_devig(odds_3))
    return _aggregate_bookmaker_probs(per_bk) if per_bk else None


# ============================================================
# ELO (ClubElo cache)
# ============================================================

def load_elo_cache(csv_path):
    """ClubElo CSV'sini oku, {team_id: DataFrame(from, to, elo)} döndür."""
    df = pd.read_csv(csv_path)
    df["from_date"] = pd.to_datetime(df["from_date"])
    df["to"] = pd.to_datetime(df["to"])
    by_team = {}
    for tid, g in df.groupby("team_id"):
        by_team[int(tid)] = g.sort_values("from_date").reset_index(drop=True)
    return by_team


def elo_lookup(by_team, team_id, match_date):
    """Verilen takım için match_date (excluded — bir gün öncesi) içindeki
    en güncel ClubElo rating'ini döndür. Yoksa None."""
    if team_id not in by_team:
        return None
    md = pd.to_datetime(match_date) - timedelta(days=1)
    g = by_team[team_id]
    # rating where from_date <= md < to (match_date-1)
    sel = g[(g["from_date"] <= md) & (g["to"] > md)]
    if sel.empty:
        # en eski kayıt maç tarihinden sonraysa, en eskisini al
        if g["from_date"].iloc[0] > md:
            return float(g["elo"].iloc[0])
        return None
    return float(sel["elo"].iloc[-1])


def elo_match_probs(home_elo, away_elo, home_adv=100.0):
    """ClubElo rating'lerini 1X2 olasılığına çevir.
    Standart lojistik dönüşüm:
      p_home = 1 / (1 + 10^(-(home_elo - away_elo + home_adv) / 400))
      p_away = 1 / (1 + 10^(-(away_elo - home_elo - home_adv) / 400))
      p_draw = (1 - p_home - p_away) clipped
    penaltyblog.ratings.Elo'nun calculate_match_probabilities metoduyla
    aynı yaklaşım — kafadan formül yazılmadı."""
    if home_elo is None or away_elo is None:
        return None
    diff = (home_elo - away_elo + home_adv) / 400.0
    p_home = 1.0 / (1.0 + 10 ** (-diff))
    p_away = 1.0 / (1.0 + 10 ** (diff))
    p_draw = 1.0 - p_home - p_away
    if p_draw < 0:
        # rating farkı çok büyükse p_draw negatif olabilir — yeniden dağıt
        if p_home > p_away:
            p_home += p_draw
        else:
            p_away += p_draw
        p_draw = 0.0
    return [p_home, p_draw, p_away]


# ============================================================
# POISSON (Dixon-Coles, sezon başında fit)
# ============================================================

def fit_dc_for_season(db_path, season_start_date):
    """Verilen tarihten ÖNCE oynanmış tüm Süper Lig maçlarıyla
    Dixon-Coles fit et. Model döndürür."""
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("""
        SELECT home_team_id, away_team_id, home_goals, away_goals
        FROM matches
        WHERE match_date < ? AND home_goals IS NOT NULL
        ORDER BY match_date
    """, (season_start_date,))
    rows = cur.fetchall()
    conn.close()
    if len(rows) < 50:
        return None
    goals_home = [r[2] for r in rows]
    goals_away = [r[3] for r in rows]
    teams_home = [f"T{r[0]}" for r in rows]
    teams_away = [f"T{r[1]}" for r in rows]
    weights = [1.0] * len(rows)
    try:
        dc = DixonColesGoalModel(goals_home, goals_away, teams_home, teams_away, weights=weights)
        dc.fit()
        return dc
    except Exception as e:
        print(f"  [DC fit hatası] {e}")
        return None


def poisson_match_probs(dc_model, home_team_id, away_team_id):
    if dc_model is None:
        return None
    try:
        pred = dc_model.predict(f"T{home_team_id}", f"T{away_team_id}")
        hda = pred.home_draw_away
        s = sum(hda)
        if s <= 0:
            return None
        return [p / s for p in hda]
    except Exception:
        return None


# ============================================================
# ORTAK YARDIMCILAR
# ============================================================

def _actual_outcome(home_goals, away_goals):
    if home_goals > away_goals:
        return [1, 0, 0]
    elif home_goals == away_goals:
        return [0, 1, 0]
    else:
        return [0, 0, 1]


def _brier(probs, actual):
    return sum((probs[c] - actual[c]) ** 2 for c in range(3))


def _combine(weighted_sources):
    """[(probs, weight), ...] → ağırlıklı ortalama.
    weight None olan source'lar atlanır."""
    active = [(p, w) for p, w in weighted_sources if p is not None and w > 0]
    if not active:
        return None
    total_w = sum(w for _, w in active)
    return [sum(p[c] * w for p, w in active) / total_w for c in range(3)]


# ============================================================
# BACKTEST ANA AKIŞI
# ============================================================

def load_backtest_data(db_path, elo_cache_path, last_n_seasons=3):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # son N sezonu kronolojik al
    seasons = cur.execute("""
        SELECT season, MIN(match_date) AS min_date, MAX(match_date) AS max_date, COUNT(*) AS n
        FROM matches GROUP BY season ORDER BY MIN(match_date) DESC LIMIT ?
    """, (last_n_seasons,)).fetchall()
    season_labels = [s["season"] for s in seasons]
    print(f"Backtest sezonları: {season_labels}")

    placeholders = ",".join("?" * len(season_labels))
    matches = cur.execute(f"""
        SELECT match_id, season, match_date, home_team_id, away_team_id,
               home_goals, away_goals
        FROM matches
        WHERE season IN ({placeholders})
          AND home_goals IS NOT NULL AND away_goals IS NOT NULL
        ORDER BY match_date
    """, season_labels).fetchall()

    # kapanış 1X2 oranları
    match_ids = [m["match_id"] for m in matches]
    ph = ",".join("?" * len(match_ids))
    odds_rows = cur.execute(f"""
        SELECT match_id, bookmaker, selection, price
        FROM odds
        WHERE market='1X2' AND is_closing=1 AND match_id IN ({ph})
    """, match_ids).fetchall()
    conn.close()

    by_match = defaultdict(lambda: defaultdict(dict))
    for r in odds_rows:
        by_match[r["match_id"]][r["bookmaker"]][r["selection"]] = r["price"]
    odds_by_match = {}
    for mid, bks in by_match.items():
        bk_vectors = {}
        for bk, seldict in bks.items():
            if all(sel in seldict for sel in SELECTION_ORDER):
                bk_vectors[bk] = [seldict[sel] for sel in SELECTION_ORDER]
        if bk_vectors:
            odds_by_match[mid] = bk_vectors

    elo_by_team = load_elo_cache(elo_cache_path) if elo_cache_path else {}

    # sezon başı Dixon-Coles fit — her sezon için bir kere
    print("\nDixon-Coles sezon modelleri fit ediliyor (look-ahead yok)...")
    dc_models_by_season = {}
    for s in seasons:
        season_start = s["min_date"]
        dc_models_by_season[s["season"]] = fit_dc_for_season(db_path, season_start)
        if dc_models_by_season[s["season"]] is not None:
            print(f"  {s['season']:10}  fit OK (eğitim verisi: {season_start} öncesi maçlar)")
        else:
            print(f"  {s['season']:10}  fit BAŞARISIZ/yetersiz veri")

    return matches, odds_by_match, elo_by_team, dc_models_by_season


def run_variants(matches, odds_by_match, elo_by_team, dc_models_by_season):
    """Tüm varyantları paralel hesapla. Her varyant için
    {season: {n, brier_sum, correct}, ...} döndürür."""
    variants = {
        "A_devig_only":          {"weights": {"devig": 1.0, "elo": 0.0, "poisson": 0.0}},
        "B_devig_elo_30":        {"weights": {"devig": 0.7, "elo": 0.3, "poisson": 0.0}},
        "B_devig_elo_50":        {"weights": {"devig": 0.5, "elo": 0.5, "poisson": 0.0}},
        "B_devig_elo_70":        {"weights": {"devig": 0.3, "elo": 0.7, "poisson": 0.0}},
        "C_devig_poisson_30":    {"weights": {"devig": 0.7, "elo": 0.0, "poisson": 0.3}},
        "C_devig_poisson_50":    {"weights": {"devig": 0.5, "elo": 0.0, "poisson": 0.5}},
        "C_devig_poisson_70":    {"weights": {"devig": 0.3, "elo": 0.0, "poisson": 0.7}},
        "D_devig_elo_poiss_30":  {"weights": {"devig": 0.4, "elo": 0.3, "poisson": 0.3}},
        "D_devig_elo_poiss_50":  {"weights": {"devig": 0.34, "elo": 0.33, "poisson": 0.33}},
        "D_poisson_elo_50":      {"weights": {"devig": 0.0, "elo": 0.5, "poisson": 0.5}},
    }

    # Her varyant için sayaç
    stats = {v: defaultdict(lambda: {"n": 0, "brier_sum": 0.0, "correct": 0,
                                       "skipped": 0, "min_date": "9999"})
             for v in variants}

    for m in matches:
        mid = m["match_id"]
        season = m["season"]
        if mid not in odds_by_match:
            for v in variants:
                stats[v][season]["skipped"] += 1
            continue

        # 3 sinyali hesapla
        devig_p = devig_probs_for_match(odds_by_match[mid])
        if devig_p is None:
            for v in variants:
                stats[v][season]["skipped"] += 1
            continue

        home_elo = elo_lookup(elo_by_team, m["home_team_id"], m["match_date"])
        away_elo = elo_lookup(elo_by_team, m["away_team_id"], m["match_date"])
        elo_p = elo_match_probs(home_elo, away_elo)

        dc = dc_models_by_season.get(season)
        poisson_p = poisson_match_probs(dc, m["home_team_id"], m["away_team_id"])

        actual = _actual_outcome(m["home_goals"], m["away_goals"])

        for vname, vcfg in variants.items():
            w = vcfg["weights"]
            combined = _combine([
                (devig_p, w["devig"]),
                (elo_p, w["elo"]),
                (poisson_p, w["poisson"]),
            ])
            if combined is None:
                stats[vname][season]["skipped"] += 1
                continue
            brier = _brier(combined, actual)
            pred_idx = combined.index(max(combined))
            correct = (actual[pred_idx] == 1)
            s = stats[vname][season]
            s["n"] += 1
            s["brier_sum"] += brier
            s["correct"] += int(correct)
            if m["match_date"] < s["min_date"]:
                s["min_date"] = m["match_date"]

    return stats


def print_comparison(stats, baseline_brier=0.5557):
    print("\n" + "=" * 90)
    print("  POISSON + ELO KATMAN BACKTEST KARŞILAŞTIRMA")
    print("=" * 90)
    print(f"\n{'Varyant':25} {'N':>5} {'Brier':>8} {'İsabet':>8} "
          f"{'Δ Baseline':>12} {'Karar':>12}")
    print("-" * 75)

    results = []
    for vname, season_stats in stats.items():
        total_n = sum(s["n"] for s in season_stats.values())
        if total_n == 0:
            continue
        total_brier = sum(s["brier_sum"] for s in season_stats.values())
        total_correct = sum(s["correct"] for s in season_stats.values())
        brier = total_brier / total_n
        acc = total_correct / total_n * 100
        delta = brier - baseline_brier
        decision = "EKLE" if delta < -0.005 else ("ATABİLİR" if delta < 0 else "EKLEME")
        results.append((vname, total_n, brier, acc, delta, decision))
        print(f"{vname:25} {total_n:>5} {brier:>8.4f} {acc:>7.1f}% "
              f"{delta:>+12.4f} {decision:>12}")

    print("-" * 75)
    print(f"{'Baseline (devig-only)':25} {'1028':>5} {baseline_brier:>8.4f} {'57.2':>7}% "
          f"{0.0:>+12.4f} {'—':>12}")

    print("\n--- Karar (docs/03 kuralı: Δ ≤ -0.005 değilse EKLEME) ---")
    improved = [r for r in results if r[4] < -0.005]
    if improved:
        best = min(improved, key=lambda r: r[2])
        print(f"İYİLEŞME var: {best[0]} → Brier {best[2]:.4f} (Δ {best[4]:+.4f})")
    else:
        print("İYİLEŞME YOK — Poisson/Elo katmanları EKLENMEZ (docs/03 kuralı).")
        print("Devig-only baseline (0.5557) Nostradamus'un resmi baseline'ı olarak kalır.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("db_path")
    ap.add_argument("elo_cache", help="cache/clubelo_history.csv yolu")
    ap.add_argument("--seasons", type=int, default=3)
    args = ap.parse_args()

    matches, odds_by_match, elo_by_team, dc_models = load_backtest_data(
        args.db_path, args.elo_cache, args.seasons)
    print(f"\nToplam maç: {len(matches)}  |  Kapanış 1X2 oranı olan: {len(odds_by_match)}")

    stats = run_variants(matches, odds_by_match, elo_by_team, dc_models)
    print_comparison(stats)


if __name__ == "__main__":
    main()
