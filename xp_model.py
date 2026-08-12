"""
xp_model.py
-----------
Her oyuncu icin haftalik Beklenen Puan (xP) hesabi.

YONTEM:
1. SOGUK BASLANGIC ONSELI (price-based prior)
   Oyunun hic fantezi-puan gecmisi yok (yeni oyun). Bu yuzden ilk
   haftalarda tek guvenilir sinyal FIYAT: TFF'nin oyuncuya bictigi
   fiyat, oyuncunun mevkisindeki goreli kalitesini yansitir (transfer
   degeri, form, takimdaki rolu gibi bircok faktoru ozetler).
   price_percentile (pozisyon ici) -> beklenen gol/asist/gol yememe
   olasiligi/oynama suresi olasiligina cevrilir.

   BU KATSAYILAR TAHMINIDIR (calibrated degil). Kod icinde tek yerde
   (PRIOR_CONFIG) toplanmistir; gercek veri birikince (bkz. adim 2)
   kalibre edilebilir/regresyonla yeniden kestirilebilir.

2. BAYESIAN SHRINKAGE (gercek veri arttikca)
   GameweekLog'da bir oyuncunun n haftalik gercek performansi
   birikince:
       xP_final = w(n) * gercek_ortalama + (1 - w(n)) * price_prior
       w(n) = n / (n + K)      (K = stabilizasyon sabiti, varsayilan 4)
   n=0 -> tamamen price_prior (GW1 durumu budur)
   n buyudukce gercek performans agirligi artar (kucuk orneklem
   regresyonu / James-Stein tipi shrinkage, sabermetrics'te standart).

3. play_probability CARPANI
   Web-arastirma katmaninin urettigi (sakatlik/ceza) play_probability
   ile xP dogrudan carpilir.
"""

from dataclasses import dataclass
import copy
import json
import os
import numpy as np
import pandas as pd

from data_loader import (
    GOAL_POINTS, ASSIST_POINTS, CLEAN_SHEET_POINTS, SAVE_POINTS_PER_3,
    CONCEDED_PENALTY_PER_2, YELLOW_CARD_POINTS, RED_CARD_POINTS,
    APPEARANCE_POINTS_UNDER_60, APPEARANCE_POINTS_60_PLUS,
)

SHRINKAGE_K = 4  # kac hafta gercek veri sonra prior'un agirligi ~%50'ye iner

# --- Soguk-baslangic onsel konfigurasyonu (mevki bazli, TAHMINI) ---
# Her deger: (baz, price_percentile ile kazanilan max ek)
PRIOR_CONFIG = {
    "GK": {
        "start_prob": (0.35, 0.55),
        "goals_per_match": (0.0, 0.0),
        "assists_per_match": (0.0, 0.01),
        "clean_sheet_prob": (0.15, 0.35),
        "saves_per_match": (3.0, 0.0),
        "conceded_per_match": (1.9, -1.1),   # yuksek kalite -> daha az gol yer
        "yellow_prob": (0.03, 0.0),
        "red_prob": (0.005, 0.0),
    },
    "DEF": {
        "start_prob": (0.35, 0.55),
        "goals_per_match": (0.02, 0.05),
        "assists_per_match": (0.02, 0.06),
        "clean_sheet_prob": (0.15, 0.35),
        "saves_per_match": (0.0, 0.0),
        "conceded_per_match": (1.9, -1.1),
        "yellow_prob": (0.14, 0.0),
        "red_prob": (0.01, 0.0),
    },
    "MID": {
        "start_prob": (0.30, 0.60),
        "goals_per_match": (0.05, 0.20),
        "assists_per_match": (0.05, 0.18),
        "clean_sheet_prob": (0.15, 0.35),   # sadece 1 puanlik katki
        "saves_per_match": (0.0, 0.0),
        "conceded_per_match": (0.0, 0.0),   # MID icin yenilen gol cezasi yok
        "yellow_prob": (0.13, 0.0),
        "red_prob": (0.008, 0.0),
    },
    "FWD": {
        "start_prob": (0.30, 0.60),
        "goals_per_match": (0.15, 0.40),
        "assists_per_match": (0.05, 0.12),
        "clean_sheet_prob": (0.0, 0.0),     # forvete gol yememe puani yok
        "saves_per_match": (0.0, 0.0),
        "conceded_per_match": (0.0, 0.0),
        "yellow_prob": (0.10, 0.0),
        "red_prob": (0.008, 0.0),
    },
}

SUB_APPEARANCE_PROB = 0.08  # 60dk alti oyuncu olarak sahaya cikma ihtimali (baz)

CALIBRATED_CONFIG_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "prior_config_calibrated.json"
)


def get_active_prior_config(path: str = CALIBRATED_CONFIG_PATH) -> dict:
    """PRIOR_CONFIG'in varsayilanlarini doner; ayni klasorde
    prior_config_calibrated.json varsa (calibrate_priors.py --apply
    ile uretilir), sadece icinde bulunan (pos, stat) ciftlerini
    varsayilanin UZERINE yazar. Boylece kod hic degismeden, gercek
    veriyle kalibre edilen katsayilar otomatik devreye girer.
    """
    cfg = copy.deepcopy(PRIOR_CONFIG)
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            override = json.load(f)
        for pos, stats in override.items():
            for stat, val in stats.items():
                if pos in cfg and stat in cfg[pos]:
                    cfg[pos][stat] = tuple(val)
    return cfg


def _price_percentile(players: pd.DataFrame) -> pd.Series:
    return players.groupby("position_code")["price_tl"].rank(pct=True)


def _prior_value(cfg: dict, cfg_key: str, pos: str, pct: float) -> float:
    base, spread = cfg[pos][cfg_key]
    return base + spread * pct


def compute_price_prior_xp(players: pd.DataFrame, prior_config: dict = None) -> pd.DataFrame:
    """Sadece fiyat/mevki bazli soguk-baslangic xP (n=0 durumu).

    prior_config verilmezse get_active_prior_config() ile otomatik
    yuklenir (kalibre edilmis dosya varsa onu, yoksa varsayilani kullanir).
    """
    cfg = prior_config if prior_config is not None else get_active_prior_config()
    df = players.copy()
    df["price_pct"] = _price_percentile(df)

    rows = []
    for _, r in df.iterrows():
        pos = r["position_code"]
        pct = r["price_pct"]

        start_p = _prior_value(cfg, "start_prob", pos, pct)
        sub_p = SUB_APPEARANCE_PROB * (1 - start_p)
        play_p = start_p + sub_p  # herhangi bir sekilde oynama ihtimali

        goals = _prior_value(cfg, "goals_per_match", pos, pct)
        assists = _prior_value(cfg, "assists_per_match", pos, pct)
        cs_prob = _prior_value(cfg, "clean_sheet_prob", pos, pct)
        saves = _prior_value(cfg, "saves_per_match", pos, pct)
        conceded = max(_prior_value(cfg, "conceded_per_match", pos, pct), 0.0)
        yellow_p = _prior_value(cfg, "yellow_prob", pos, pct)
        red_p = _prior_value(cfg, "red_prob", pos, pct)

        appearance_pts = (
            start_p * APPEARANCE_POINTS_60_PLUS
            + sub_p * APPEARANCE_POINTS_UNDER_60
        )
        goal_pts = start_p * goals * GOAL_POINTS[pos]
        assist_pts = play_p * assists * ASSIST_POINTS
        cs_pts = start_p * cs_prob * CLEAN_SHEET_POINTS[pos]
        save_pts = start_p * (saves / 3.0) * SAVE_POINTS_PER_3
        conceded_pts = (
            start_p * (conceded / 2.0) * CONCEDED_PENALTY_PER_2
            if pos in ("GK", "DEF") else 0.0
        )
        card_pts = play_p * (yellow_p * YELLOW_CARD_POINTS + red_p * RED_CARD_POINTS)

        raw_xp = (
            appearance_pts + goal_pts + assist_pts + cs_pts
            + save_pts + conceded_pts + card_pts
        )

        rows.append({
            "player_id": r["player_id"],
            "start_prob": start_p,
            "xp_prior": raw_xp,
            "goal_prob_component": goals,  # kaptan tavan skoru icin saklanir
        })

    prior_df = pd.DataFrame(rows)
    return df.merge(prior_df, on="player_id", how="left")


def compute_observed_stats(log: pd.DataFrame) -> pd.DataFrame:
    """GameweekLog'dan oyuncu basina n (oynanan hafta) ve gercek
    ortalama fantasy_points cikarir. Bos log icin bos DataFrame doner."""
    if log.empty:
        return pd.DataFrame(columns=["player_id", "n_games", "avg_points"])
    g = log.groupby("player_id")["fantasy_points"]
    out = g.agg(n_games="count", avg_points="mean").reset_index()
    return out


def compute_xp(players: pd.DataFrame, log: pd.DataFrame, prior_config: dict = None) -> pd.DataFrame:
    """Tam xP hesabi: price_prior + shrinkage + play_probability."""
    df = compute_price_prior_xp(players, prior_config=prior_config)
    observed = compute_observed_stats(log)
    df = df.merge(observed, on="player_id", how="left")
    df["n_games"] = df["n_games"].fillna(0)
    df["avg_points"] = df["avg_points"].fillna(df["xp_prior"])

    w = df["n_games"] / (df["n_games"] + SHRINKAGE_K)
    df["xp_blended"] = w * df["avg_points"] + (1 - w) * df["xp_prior"]

    df["xp"] = df["xp_blended"] * df["play_probability"]
    df["xp"] = df["xp"].clip(lower=0)
    return df
