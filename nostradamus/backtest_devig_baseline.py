"""
backtest_devig_baseline.py
--------------------------
docs/03 Adım 2: Devig-only baseline backtest.

Mimari (docs/03'teki karar):
  1. Her maç için kapanış 1X2 oranlarını topla (B365 + PS, ikisi de varsa)
  2. Devig uygula:
       - Birincil: Shin's method (`shin` paketi — kafadan formül YAZILMAZ)
       - Fallback: oransal yöntem p_i = (1/odds_i) / Σ(1/odds_j)
  3. Birden fazla bahisçi varsa olasılıkların MEDYANını al (docs/03 kuralı)
  4. Argmax → tahmin (her maç için en yüksek olasılıklı sonuç)
  5. Brier score: 3-sınıf çoklu-sınıf Brier (düşük = iyi, 0 = mükemmel,
     uniform rastgele = 0.667)

Kullanım:
    python backtest_devig_baseline.py <superlig_odds.db> [--seasons N]
    --seasons: son N sezonu al (kronolojik, varsayılan 3)

Örnek:
    python backtest_devig_baseline.py superlig_odds.db --seasons 3
"""

import argparse
import sqlite3
import sys
from collections import defaultdict
from statistics import median

from shin import calculate_implied_probabilities


SELECTION_ORDER = ["H", "D", "A"]  # 1-X-2 sırası


def _proportional_devig(odds_3):
    """Güvenli fallback: p_i = (1/odds_i) / Σ(1/odds_j). docs/03'ün
    'basit, her zaman doğru' yöntemi. Shin sayısal olarak başarısız
    olursa (negatif odds, 0 odds, vs.) devreye girer."""
    invs = [1.0 / o for o in odds_3]
    s = sum(invs)
    return [v / s for v in invs]


def _shin_devig(odds_3):
    """Birincil yöntem: Shin's method. `shin` paketi test edilmiş,
    favori-uzun-oran yanlılığını düzeltir. Hata olursa fallback'e düş."""
    try:
        probs = calculate_implied_probabilities(odds_3)
        # Shin paketi bazen [0,1] dışına taşan küçük sayısal hatalar
        # verebilir; kırp ve yeniden normalize et.
        probs = [max(0.0, min(1.0, p)) for p in probs]
        s = sum(probs)
        if s <= 0:
            return _proportional_devig(odds_3)
        return [p / s for p in probs]
    except Exception:
        return _proportional_devig(odds_3)


def _devig_one(odds_3):
    """Tek bir bahisçinin 3 oranına devig uygula. odds_3 = [H, D, A]."""
    if any(o is None or o <= 1.0 for o in odds_3):
        return None  # geçersiz oran — bu bahisçi atlanır
    return _shin_devig(odds_3)


def _aggregate_bookmaker_probs(prob_vectors):
    """docs/03 kuralı: birden fazla bahisçi varsa MEDYAN al.
    prob_vectors: [[p_H, p_D, p_A], ...] her bahisçi için bir liste."""
    if not prob_vectors:
        return None
    by_class = [[v[c] for v in prob_vectors] for c in range(3)]
    med = [median(col) for col in by_class]
    s = sum(med)
    if s <= 0:
        return None
    return [p / s for p in med]


def load_backtest_matches(db_path, last_n_seasons=3):
    """Son N sezonu match_date yılına göre kronolojik sırayla al.
    docs/03'ün UYARI notuna uy: sezon etiketleri kronolojik DEĞİL,
    match_date'e göre sırala."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # her sezonu MIN(match_date)'in yılıyla etiketle, sonra kronolojik sırala
    seasons = cur.execute("""
        SELECT season, MIN(match_date) AS min_date, MAX(match_date) AS max_date,
               COUNT(*) AS n
        FROM matches
        GROUP BY season
        ORDER BY MIN(match_date) DESC
        LIMIT ?
    """, (last_n_seasons,)).fetchall()

    if not seasons:
        sys.exit("[HATA] Hiç sezon bulunamadı.")

    season_labels = [s["season"] for s in seasons]
    print(f"\nBacktest sezonları (kronolojik sırayla, son {last_n_seasons}):")
    for s in reversed(seasons):
        print(f"  {s['season']:10}  {s['min_date']} → {s['max_date']}  ({s['n']} maç)")

    placeholders = ",".join("?" * len(season_labels))
    matches = cur.execute(f"""
        SELECT m.match_id, m.season, m.match_date, m.home_goals, m.away_goals,
               m.home_team_id, m.away_team_id
        FROM matches m
        WHERE m.season IN ({placeholders})
          AND m.home_goals IS NOT NULL AND m.away_goals IS NOT NULL
        ORDER BY m.match_date
    """, season_labels).fetchall()

    conn.close()
    return matches


def load_closing_1x2_odds(db_path, match_ids):
    """Her maç için kapanış 1X2 oranlarını {match_id: {bookmaker: [H,D,A]}}
    olarak döndür."""
    if not match_ids:
        return {}
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    placeholders = ",".join("?" * len(match_ids))
    rows = cur.execute(f"""
        SELECT match_id, bookmaker, selection, price
        FROM odds
        WHERE market='1X2' AND is_closing=1 AND match_id IN ({placeholders})
        ORDER BY match_id, bookmaker, selection
    """, match_ids).fetchall()
    conn.close()

    # match_id -> bookmaker -> {selection: price}
    by_match = defaultdict(lambda: defaultdict(dict))
    for r in rows:
        by_match[r["match_id"]][r["bookmaker"]][r["selection"]] = r["price"]

    # her (match, bookmaker) için [H, D, A] listesi üret — 3'lü eksikse atla
    result = {}
    for mid, bks in by_match.items():
        bk_vectors = {}
        for bk, seldict in bks.items():
            if all(sel in seldict for sel in SELECTION_ORDER):
                bk_vectors[bk] = [seldict[sel] for sel in SELECTION_ORDER]
        if bk_vectors:
            result[mid] = bk_vectors
    return result


def _actual_outcome(home_goals, away_goals):
    """[1, 0, 0] = home win, [0, 1, 0] = draw, [0, 0, 1] = away win."""
    if home_goals > away_goals:
        return [1, 0, 0]
    elif home_goals == away_goals:
        return [0, 1, 0]
    else:
        return [0, 0, 1]


def run_backtest(db_path, last_n_seasons):
    matches = load_backtest_matches(db_path, last_n_seasons)
    match_ids = [m["match_id"] for m in matches]
    odds_by_match = load_closing_1x2_odds(db_path, match_ids)

    print(f"\nToplam maç: {len(matches)}  |  Kapanış 1X2 oranı olan: {len(odds_by_match)}")

    # Per-season accumulators
    season_stats = defaultdict(lambda: {
        "n": 0, "brier_sum": 0.0,
        "correct": 0, "skipped_no_odds": 0,
        "fallback_used": 0, "min_date": "9999",
    })
    overall = {"n": 0, "brier_sum": 0.0, "correct": 0,
               "skipped_no_odds": 0, "fallback_used": 0}

    # Per-match detail (first 20 for inspection)
    details = []

    for m in matches:
        mid = m["match_id"]
        season = m["season"]
        if mid not in odds_by_match:
            season_stats[season]["skipped_no_odds"] += 1
            overall["skipped_no_odds"] += 1
            continue

        bk_vectors = odds_by_match[mid]
        per_bookmaker_probs = []
        fallback_this_match = False
        for bk, odds_3 in bk_vectors.items():
            # Shin'i dene, hata olursa fallback (oransal) devreye girer
            try:
                p = _shin_devig(odds_3)
            except Exception:
                p = _proportional_devig(odds_3)
                fallback_this_match = True
            per_bookmaker_probs.append(p)

        if not per_bookmaker_probs:
            season_stats[season]["skipped_no_odds"] += 1
            overall["skipped_no_odds"] += 1
            continue

        # Çoklu bahisçi varsa medyan al (docs/03)
        final_probs = _aggregate_bookmaker_probs(per_bookmaker_probs)
        if final_probs is None:
            season_stats[season]["skipped_no_odds"] += 1
            overall["skipped_no_odds"] += 1
            continue

        actual = _actual_outcome(m["home_goals"], m["away_goals"])
        brier = sum((final_probs[c] - actual[c]) ** 2 for c in range(3))
        pred_idx = final_probs.index(max(final_probs))
        correct = (actual[pred_idx] == 1)

        season_stats[season]["n"] += 1
        season_stats[season]["brier_sum"] += brier
        season_stats[season]["correct"] += int(correct)
        if m["match_date"] < season_stats[season]["min_date"]:
            season_stats[season]["min_date"] = m["match_date"]
        if fallback_this_match:
            season_stats[season]["fallback_used"] += 1

        overall["n"] += 1
        overall["brier_sum"] += brier
        overall["correct"] += int(correct)
        if fallback_this_match:
            overall["fallback_used"] += 1

        if len(details) < 20:
            sel_labels = ["1", "X", "2"]
            details.append({
                "match_id": mid, "season": season,
                "date": m["match_date"],
                "score": f"{m['home_goals']}-{m['away_goals']}",
                "probs": " ".join(f"{sel_labels[c]}={final_probs[c]:.3f}" for c in range(3)),
                "pred": sel_labels[pred_idx],
                "actual": sel_labels[actual.index(1)],
                "correct": correct,
                "brier": brier,
                "n_bookmakers": len(per_bookmaker_probs),
            })

    return season_stats, overall, details


def print_report(season_stats, overall, details):
    print("\n" + "=" * 72)
    print("  DEVIG-ONLY BASELINE BACKTEST")
    print("=" * 72)
    print(f"\n{'Sezon':12} {'Maç':>6} {'Brier':>8} {'İsabet':>8} {'Fallback':>10}")
    print("-" * 50)
    for season in sorted(season_stats.keys(),
                          key=lambda s: season_stats[s]["min_date"]):
        s = season_stats[season]
        if s["n"] == 0:
            continue
        brier = s["brier_sum"] / s["n"]
        acc = s["correct"] / s["n"] * 100
        print(f"{season:12} {s['n']:>6} {brier:>8.4f} {acc:>7.1f}% {s['fallback_used']:>10}")
    print("-" * 50)
    if overall["n"] > 0:
        brier = overall["brier_sum"] / overall["n"]
        acc = overall["correct"] / overall["n"] * 100
        print(f"{'TOPLAM':12} {overall['n']:>6} {brier:>8.4f} {acc:>7.1f}% "
              f"{overall['fallback_used']:>10}")
        print(f"\n  Atlanan (oransız maç): {overall['skipped_no_odds']}")
        print(f"  Uniform rastgele baseline Brier: 0.6667")
        print(f"  Bu baseline'ın rastgeleye göre iyileşmesi: "
              f"{(0.6667 - brier) / 0.6667 * 100:.1f}%")

    print("\n--- İlk 20 maç detayı ---")
    print(f"{'Sezon':10} {'Tarih':12} {'Skor':6} {'Olasılıklar (1/X/2)':28} "
          f"{'Tah':4} {'Ger':4} {'Doğ':4} {'Brier':>7}")
    for d in details:
        print(f"{d['season']:10} {d['date']:12} {d['score']:6} {d['probs']:28} "
              f"{d['pred']:4} {d['actual']:4} {'E' if d['correct'] else 'H':4} "
              f"{d['brier']:>7.4f}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("db_path", help="superlig_odds.db yolu")
    ap.add_argument("--seasons", type=int, default=3,
                    help="Son N sezonu al (kronolojik, varsayılan 3)")
    args = ap.parse_args()

    season_stats, overall, details = run_backtest(args.db_path, args.seasons)
    print_report(season_stats, overall, details)


if __name__ == "__main__":
    main()
