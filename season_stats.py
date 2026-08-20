"""
season_stats.py
---------------
GameweekLog ve Players sayfalarini birlestirerek sezonluk tum
metrikleri hesaplar:
  - Toplam Mac, Ilk 11 Baslama Orani, Toplam Dakika, Mac Basi Dakika
  - Toplam Puan, Mac Basi Puan (PPM), 90 Dk Basi Puan (P90)
  - Toplam Gol, Asist, Sari Kart, Kirmizi Kart, Kurtaris
  - Agirlikli Form Skoru (zaman-agirlikli exponential decay)
"""

import pandas as pd
import numpy as np


def compute_comprehensive_season_stats(players: pd.DataFrame, log: pd.DataFrame) -> pd.DataFrame:
    """462 oyuncunun sezon boyunca biriken tum metriklerini hesaplar.
    Hic log kaydi olmayan oyuncular icin 0 degerleriyle guvenli sekilde doldurur.
    """
    df_players = players[["player_id", "name", "team", "position_code", "price_tl", "play_probability"]].copy()

    if log.empty:
        # Sezon basi (0 mac oynandi)
        df_players["total_games"] = 0
        df_players["starts"] = 0
        df_players["total_minutes"] = 0
        df_players["avg_minutes"] = 0.0
        df_players["total_points"] = 0
        df_players["avg_points"] = 0.0
        df_players["points_per_90"] = 0.0
        df_players["total_goals"] = 0
        df_players["total_assists"] = 0
        df_players["total_yellow"] = 0
        df_players["total_red"] = 0
        df_players["total_saves"] = 0
        df_players["form_score"] = 0.0
        return df_players

    # Log tablosundaki her oyuncu icin ozet
    log_clean = log.copy()
    for col in ["minutes", "goals", "assists", "yellow_cards", "red_cards", "fantasy_points"]:
        if col in log_clean.columns:
            log_clean[col] = pd.to_numeric(log_clean[col], errors="coerce").fillna(0)

    # 1. Temel toplamlar
    stats = []
    max_gw = int(log_clean["gameweek"].max()) if "gameweek" in log_clean.columns and not log_clean["gameweek"].empty else 1

    for p_id, p_group in log_clean.groupby("player_id"):
        n_weeks = len(p_group)
        mins = p_group["minutes"].sum()
        starts = (p_group["minutes"] >= 60).sum()
        played_games = (p_group["minutes"] > 0).sum()
        pts = p_group["fantasy_points"].sum()
        goals = p_group["goals"].sum()
        assists = p_group["assists"].sum()
        yellows = p_group["yellow_cards"].sum()
        reds = p_group["red_cards"].sum()
        saves = p_group.get("saves", pd.Series(0, index=p_group.index)).sum() if "saves" in p_group.columns else 0

        avg_mins = mins / n_weeks if n_weeks > 0 else 0.0
        avg_pts = pts / n_weeks if n_weeks > 0 else 0.0
        p90 = (pts / (mins / 90.0)) if mins >= 45 else avg_pts

        # Zaman-agirlikli form (Son haftalara daha yuksek agirlik: lambda = 0.75)
        if "gameweek" in p_group.columns and len(p_group) > 1:
            decay_weights = 0.75 ** (max_gw - p_group["gameweek"].values)
            form = np.average(p_group["fantasy_points"].values, weights=decay_weights)
        else:
            form = avg_pts

        stats.append({
            "player_id": p_id,
            "total_games": played_games,
            "starts": starts,
            "total_minutes": int(mins),
            "avg_minutes": round(float(avg_mins), 1),
            "total_points": int(pts),
            "avg_points": round(float(avg_pts), 2),
            "points_per_90": round(float(p90), 2),
            "total_goals": int(goals),
            "total_assists": int(assists),
            "total_yellow": int(yellows),
            "total_red": int(reds),
            "total_saves": int(saves),
            "form_score": round(float(form), 2),
        })

    stats_df = pd.DataFrame(stats)
    out = df_players.merge(stats_df, on="player_id", how="left")

    num_cols = [
        "total_games", "starts", "total_minutes", "avg_minutes",
        "total_points", "avg_points", "points_per_90", "total_goals",
        "total_assists", "total_yellow", "total_red", "total_saves", "form_score"
    ]
    for c in num_cols:
        out[c] = out[c].fillna(0)

    return out
