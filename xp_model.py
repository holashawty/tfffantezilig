"""
xp_model.py
-----------
Her oyuncu icin haftalik Beklenen Puan (xP) hesabi:
1. SOGUK BASLANGIC ONSELI (price-based prior)
2. SURE VE BASLAMA GUVENILIRLIGI (Continuous Bayesian Minutes Learning: w_T = T / (T + 3))
3. GERCEK SEZONLUK VERI & BAYESIAN SHRINKAGE (Zaman agirlikli form ile)
4. FIKSTUR VE RAKIP ZORLUGU CARPANI (FDR / Nostradamus Canli Mac Oranlari)
5. SAKATLIK/CEZA CARPANI (play_probability)
"""

from dataclasses import dataclass
import copy
import json
import os
import unicodedata
import numpy as np
import pandas as pd

from data_loader import (
    GOAL_POINTS, ASSIST_POINTS, CLEAN_SHEET_POINTS, SAVE_POINTS_PER_3,
    CONCEDED_PENALTY_PER_2, YELLOW_CARD_POINTS, RED_CARD_POINTS,
    APPEARANCE_POINTS_UNDER_60, APPEARANCE_POINTS_60_PLUS,
)
from season_stats import compute_comprehensive_season_stats

SHRINKAGE_K = 4  # kac hafta gercek veri sonra prior'un agirligi ~%50'ye iner

PRIOR_CONFIG = {
    "GK": {
        "start_prob": (0.35, 0.55),
        "goals_per_match": (0.0, 0.0),
        "assists_per_match": (0.0, 0.01),
        "clean_sheet_prob": (0.15, 0.35),
        "saves_per_match": (3.0, 0.0),
        "conceded_per_match": (1.9, -1.1),
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
        "clean_sheet_prob": (0.15, 0.35),
        "saves_per_match": (0.0, 0.0),
        "conceded_per_match": (0.0, 0.0),
        "yellow_prob": (0.13, 0.0),
        "red_prob": (0.008, 0.0),
    },
    "FWD": {
        "start_prob": (0.30, 0.60),
        "goals_per_match": (0.15, 0.40),
        "assists_per_match": (0.05, 0.12),
        "clean_sheet_prob": (0.0, 0.0),
        "saves_per_match": (0.0, 0.0),
        "conceded_per_match": (0.0, 0.0),
        "yellow_prob": (0.10, 0.0),
        "red_prob": (0.008, 0.0),
    },
}

SUB_APPEARANCE_PROB = 0.08

CALIBRATED_CONFIG_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "prior_config_calibrated.json"
)


def _norm(text: str) -> str:
    if not text:
        return ""
    t = text.lower().replace("ı", "i").replace("ğ", "g").replace("ü", "u").replace("ş", "s").replace("ö", "o").replace("ç", "c")
    nfd = unicodedata.normalize('NFD', t)
    return "".join(c for c in nfd if unicodedata.category(c) != 'Mn').strip()


def get_active_prior_config(path: str = CALIBRATED_CONFIG_PATH) -> dict:
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


def compute_fixture_multipliers(predict_or_fixtures_path: str, all_teams: list) -> dict:
    """Nostradamus veya Fikstur oranlarindan her takim icin hucum ve savunma carpanlarini hesaplar."""
    if not predict_or_fixtures_path or not os.path.exists(predict_or_fixtures_path):
        return {t: {"att": 1.0, "cs": 1.0, "conceded": 1.0, "opp": "N/A", "is_home": True, "p_win": 0.38} for t in all_teams}

    with open(predict_or_fixtures_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    matches = data.get("predictions", [])
    if not matches:
        matches = data.get("fixtures", [])

    team_mults = {}

    for m in matches:
        home = m.get("home_team", "")
        away = m.get("away_team", "")
        probs = m.get("probabilities", {})

        if probs:
            p_home = probs.get("1", 0.38)
            p_draw = probs.get("X", 0.28)
            p_away = probs.get("2", 0.34)
        else:
            odds = m.get("odds", {}).get("B365", {})
            h_odd = odds.get("H", 2.5)
            d_odd = odds.get("D", 3.2)
            a_odd = odds.get("A", 2.8)
            raw_sum = (1.0 / h_odd) + (1.0 / d_odd) + (1.0 / a_odd)
            p_home = (1.0 / h_odd) / raw_sum
            p_draw = (1.0 / d_odd) / raw_sum
            p_away = (1.0 / a_odd) / raw_sum

        att_home = float(np.clip(0.60 + 0.90 * p_home + 0.15 * p_draw, 0.65, 1.45))
        att_away = float(np.clip(0.60 + 0.90 * p_away + 0.15 * p_draw, 0.65, 1.45))

        diff_home = p_home - p_away
        cs_home = float(np.clip(1.0 + 1.1 * diff_home, 0.25, 1.80))
        conceded_home = float(np.clip(1.0 - 0.7 * diff_home, 0.50, 1.70))

        diff_away = p_away - p_home
        cs_away = float(np.clip(1.0 + 1.1 * diff_away, 0.25, 1.80))
        conceded_away = float(np.clip(1.0 - 0.7 * diff_away, 0.50, 1.70))

        team_mults[home] = {"att": att_home, "cs": cs_home, "conceded": conceded_home, "opp": away, "is_home": True, "p_win": p_home}
        team_mults[away] = {"att": att_away, "cs": cs_away, "conceded": conceded_away, "opp": home, "is_home": False, "p_win": p_away}

    res = {}
    for db_t in all_teams:
        norm_db = _norm(db_t)
        found = False
        for fix_t, m_dict in team_mults.items():
            norm_fix = _norm(fix_t)
            if norm_fix in norm_db or norm_db in norm_fix:
                res[db_t] = m_dict
                found = True
                break
        if not found:
            res[db_t] = {"att": 1.0, "cs": 1.0, "conceded": 1.0, "opp": "Fikstur Disi", "is_home": True, "p_win": 0.38}
    return res


def compute_xp(players: pd.DataFrame, log: pd.DataFrame, fixtures_path: str = None, prior_config: dict = None) -> pd.DataFrame:
    """Sureklilik ogrenmeli (Continuous Minutes-Learning) ve Fikstur Agirlikli Gelismis xP Modeli"""
    cfg = prior_config if prior_config is not None else get_active_prior_config()
    df = players.copy()
    df["price_pct"] = _price_percentile(df)

    all_teams = df["team"].unique().tolist()
    fdr = compute_fixture_multipliers(fixtures_path, all_teams)

    season_stats = compute_comprehensive_season_stats(players, log)
    season_map = season_stats.set_index("player_id").to_dict("index")

    # Toplam tamamlanan hafta sayisi
    completed_gws = log["gameweek"].nunique() if not log.empty and "gameweek" in log.columns else 0

    rows = []
    for _, r in df.iterrows():
        p_id = r["player_id"]
        pos = r["position_code"]
        pct = r["price_pct"]
        team = r["team"]
        team_fdr = fdr.get(team, {"att": 1.0, "cs": 1.0, "conceded": 1.0, "opp": "N/A", "is_home": True})

        m_att = team_fdr["att"]
        m_cs = team_fdr["cs"]
        m_conceded = team_fdr["conceded"]

        prior_start_p = _prior_value(cfg, "start_prob", pos, pct)

        p_stat = season_map.get(p_id, {})
        n_games = p_stat.get("total_games", 0)
        total_mins = p_stat.get("total_minutes", 0)
        form_score = p_stat.get("form_score", 0.0)

        # Sure ve Baslama Guvenilirligi (Continuous Minutes Learning)
        # Hafta ilerledikce (T=1, 2, 5, 10...) oynamayan oyuncunun ilk 11 baslama ihtimali gercek dakikaya yaklasir.
        if completed_gws > 0:
            w_mins = completed_gws / (completed_gws + 3.0)  # T=1 -> 0.25, T=3 -> 0.50, T=10 -> 0.77
            empirical_start_ratio = min(total_mins / (90.0 * completed_gws), 1.0)
            start_p = (1.0 - w_mins) * prior_start_p + w_mins * empirical_start_ratio
        else:
            start_p = prior_start_p

        sub_p = SUB_APPEARANCE_PROB * (1.0 - start_p)
        play_p = start_p + sub_p

        goals = _prior_value(cfg, "goals_per_match", pos, pct) * m_att
        assists = _prior_value(cfg, "assists_per_match", pos, pct) * m_att
        cs_prob = min(_prior_value(cfg, "clean_sheet_prob", pos, pct) * m_cs, 0.85)
        saves = _prior_value(cfg, "saves_per_match", pos, pct)
        conceded = max(_prior_value(cfg, "conceded_per_match", pos, pct) * m_conceded, 0.0)
        yellow_p = _prior_value(cfg, "yellow_prob", pos, pct)
        red_p = _prior_value(cfg, "red_prob", pos, pct)

        appearance_pts = start_p * APPEARANCE_POINTS_60_PLUS + sub_p * APPEARANCE_POINTS_UNDER_60
        goal_pts = start_p * goals * GOAL_POINTS[pos]
        assist_pts = play_p * assists * ASSIST_POINTS
        cs_pts = start_p * cs_prob * CLEAN_SHEET_POINTS[pos]
        save_pts = start_p * (saves / 3.0) * SAVE_POINTS_PER_3
        conceded_pts = start_p * (conceded / 2.0) * CONCEDED_PENALTY_PER_2 if pos in ("GK", "DEF") else 0.0
        card_pts = play_p * (yellow_p * YELLOW_CARD_POINTS + red_p * RED_CARD_POINTS)

        raw_xp = appearance_pts + goal_pts + assist_pts + cs_pts + save_pts + conceded_pts + card_pts

        # Bayesian Shrinkage (Gercek Form ile Birlestirme)
        w_form = n_games / (n_games + SHRINKAGE_K) if n_games > 0 else 0.0
        adjusted_form = form_score * (m_att if pos in ("MID", "FWD") else m_cs)
        xp_blended = w_form * adjusted_form + (1.0 - w_form) * raw_xp

        final_xp = max(0.0, float(xp_blended * r["play_probability"]))

        rows.append({
            "player_id": p_id,
            "start_prob": start_p,
            "xp_prior": raw_xp,
            "xp": final_xp,
            "goal_prob_component": goals,
            "fdr_opp": team_fdr.get("opp", ""),
            "fdr_att": m_att,
            "fdr_cs": m_cs
        })

    out_df = pd.DataFrame(rows)
    return df.merge(out_df, on="player_id", how="left")
