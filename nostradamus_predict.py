"""
nostradamus_predict.py
----------------------
TFF Fantezi Lig Nostradamus tahmin motoru — 9 maç için 1-X-2 tahmini üretir.

Mimari (docs/03, baseline olarak SABİTLENDİ — bkz. docs/07 12 Ağustos 2026):
  1. Her maç için kapanış 1X2 oranlarını topla (B365 + PS, ikisi de varsa)
  2. Devig: Shin's method (`shin` paketi — kafadan formül YAZILMADI)
       Fallback: oransal p_i = (1/odds_i) / Σ(1/odds_j)
  3. Çoklu bahisçi varsa olasılıkların MEDYANı (docs/03 kuralı)
  4. Argmax → tahmin (en yüksek olasılıklı sonuç)
  5. Çıktı: konsol + JSON dosyası

Poisson/Elo katmanları test edildi ama baseline'ı iyileştirmediği için
EKLENMEDİ (docs/07'ye bak).

GİRDİ FORMATI (JSON):
{
  "gameweek": 5,
  "prediction_date": "2026-09-15",
  "fixtures": [
    {
      "home_team": "Galatasaray",
      "away_team": "Fenerbahce",
      "match_date": "2026-09-20",
      "odds": {                          # opsiyonel: çoklu bahisçi
        "B365": {"H": 1.25, "D": 6.5, "A": 9.5},
        "PS":  {"H": 1.27, "D": 6.51, "A": 9.79}
      },
      "odds_h": 1.25,                    # VEYA basit tek-bahisçi formatı
      "odds_d": 6.5,
      "odds_a": 9.5
    }
  ]
}

Kullanım:
    python nostradamus_predict.py <fixtures.json> [--out cikti.json]

Örnek:
    python nostradamus_predict.py nostradamus_fixtures_gw5.json
"""

import argparse
import json
import os
import sys
from datetime import datetime
from statistics import median

from shin import calculate_implied_probabilities


SELECTION_ORDER = ["H", "D", "A"]  # 1-X-2 sırası
SELECTION_LABEL = {"H": "1", "D": "X", "A": "2"}  # TFF Nostradamus etiketleri


# ============================================================
# DEVIG (backtest_devig_baseline.py ile birebir aynı)
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


def devig_fixture(fixture):
    """Bir fixture'in odds alanından [p_H, p_D, p_A] üretür.
    İki format destekler:
      1. 'odds' alt-objesi: {"B365": {"H":..,"D":..,"A":..}, "PS": {...}}
      2. Basit: 'odds_h', 'odds_d', 'odds_a' alanları
    Çoklu bahisçi varsa medyan alır (docs/03)."""
    if "odds" in fixture and isinstance(fixture["odds"], dict):
        # çoklu bahisçi formatı
        per_bk = []
        for bk, sel in fixture["odds"].items():
            if not isinstance(sel, dict):
                continue
            if all(s in sel for s in SELECTION_ORDER):
                odds_3 = [float(sel[s]) for s in SELECTION_ORDER]
                if all(o > 1.0 for o in odds_3):
                    per_bk.append(_shin_devig(odds_3))
        return _aggregate_bookmaker_probs(per_bk), len(per_bk)
    elif all(k in fixture for k in ("odds_h", "odds_d", "odds_a")):
        odds_3 = [float(fixture["odds_h"]), float(fixture["odds_d"]), float(fixture["odds_a"])]
        if all(o > 1.0 for o in odds_3):
            return _shin_devig(odds_3), 1
    return None, 0


# ============================================================
# ANA AKIŞ
# ============================================================

def predict(fixtures_data):
    """JSON verisinden tahmin üretir. (predictions_list, stats) döndürür."""
    fixtures = fixtures_data.get("fixtures", [])
    if not fixtures:
        sys.exit("[HATA] JSON'da 'fixtures' alanı boş veya yok.")

    predictions = []
    n_devig_ok = 0
    n_failed = 0

    for i, fx in enumerate(fixtures, 1):
        probs, n_bk = devig_fixture(fx)
        if probs is None:
            print(f"  [UYARI] Maç {i} ({fx.get('home_team','?')} vs "
                  f"{fx.get('away_team','?')}): geçerli oran yok, atlandı.")
            n_failed += 1
            continue

        pred_idx = probs.index(max(probs))
        pred_label = SELECTION_LABEL[SELECTION_ORDER[pred_idx]]

        predictions.append({
            "match_no": i,
            "home_team": fx.get("home_team", "?"),
            "away_team": fx.get("away_team", "?"),
            "match_date": fx.get("match_date", ""),
            "probabilities": {
                "1": round(probs[0], 4),
                "X": round(probs[1], 4),
                "2": round(probs[2], 4),
            },
            "prediction": pred_label,
            "confidence": round(max(probs), 4),
            "n_bookmakers": n_bk,
        })
        n_devig_ok += 1

    return predictions, {"n_total": len(fixtures), "n_ok": n_devig_ok, "n_failed": n_failed}


def print_predictions(predictions, stats, gameweek):
    print(f"\n{'='*65}")
    print(f"  NOSTRADAMUS TAHMINLERI — HAFTA {gameweek}")
    print(f"{'='*65}")
    print(f"  Toplam maç: {stats['n_total']}  |  Tahmin üretilen: {stats['n_ok']}  |  Atlanan: {stats['n_failed']}")
    print()

    print(f"  {'#':>3}  {'Maç':36} {'1':>7} {'X':>7} {'2':>7}  {'Tah':>4}  {'Güven':>7}  {'Taktik Not'}")
    print("  " + "-" * 88)
    for p in predictions:
        match = f"{p['home_team']} vs {p['away_team']}"[:36]
        p1, px, p2 = p['probabilities']['1'], p['probabilities']['X'], p['probabilities']['2']
        
        # Taktiksel ipucu analizi
        note = ""
        if abs(p1 - p2) < 0.08 and px >= 0.27:
            note = "⚡ Dengeli Maç (X düşünülebilir)"
        elif p['confidence'] >= 0.65:
            note = "★ Banko / Güçlü Favori"

        print(f"  {p['match_no']:>3}  {match:36} "
              f"{p1:>7.1%} {px:>7.1%} "
              f"{p2:>7.1%}  {p['prediction']:>4}  "
              f"{p['confidence']:>7.1%}  {note}")

    print()
    print("  Nostradamus kuralları (docs/01):")
    print("    - 9 maçın TAMAMI için tahmin yapılırsa: +1 puan")
    print("    - Doğru tahmin edilen HER maç için: +1 puan daha")
    print("    - Maksimum puan: 10 (1 + 9 doğru)")
    print()
    print("  Tahminler devig-only modele dayanır (Shin's method + B365/PS medyanı).")
    print("  docs/07 12 Ağustos 2026 tarihli girişine göre baseline Brier = 0.5557")
    print("  (son 3 sezon, 1028 maç) — Poisson/Elo katmanları eklenmedi.")


def save_output(predictions, stats, gameweek, fixtures_data, out_path):
    out = {
        "gameweek": gameweek,
        "prediction_date": fixtures_data.get("prediction_date",
                                              datetime.now().strftime("%Y-%m-%d")),
        "model": "devig-only (shin + B365/PS median)",
        "baseline_brier": 0.5557,
        "stats": stats,
        "predictions": predictions,
    }
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(f"\n  Çıktı yazıldı: {out_path}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("fixtures_json", help="Maç+oran JSON dosyası")
    ap.add_argument("--out", default=None,
                    help="Çıktı JSON yolu (varsayılan: nostradamus_predict_gwN.json)")
    args = ap.parse_args()

    if not os.path.exists(args.fixtures_json):
        sys.exit(f"[HATA] Fixtures JSON bulunamadı: {args.fixtures_json}")

    with open(args.fixtures_json, "r", encoding="utf-8") as f:
        fixtures_data = json.load(f)

    gameweek = fixtures_data.get("gameweek", "?")
    predictions, stats = predict(fixtures_data)
    print_predictions(predictions, stats, gameweek)

    out_path = args.out or f"nostradamus_predict_gw{gameweek}.json"
    save_output(predictions, stats, gameweek, fixtures_data, out_path)


if __name__ == "__main__":
    main()
