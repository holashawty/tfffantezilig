"""
optimizer.py
------------
Kesin (deterministik) kadro secimi: MILP (Mixed Integer Linear Programming),
scipy.optimize.milp (HiGHS solver) ile.

Yedek Kadro Deger Agirligi (Bench Weighting):
  Obj = sum(s_i * xp_i) + BENCH_WEIGHT * sum((x_i - s_i) * xp_i)
Bu sayede bakiye butce (orn: 10M TL) bos 0-xp oyunculara harcanmaz;
sahaya cikip puan alma potansiyeli en yuksek canli yedekler alinir.
"""

from dataclasses import dataclass
import numpy as np
import pandas as pd
from scipy.optimize import milp, LinearConstraint, Bounds

from data_loader import (
    SQUAD_REQUIREMENTS, STARTING_MIN, BUDGET_TL, MAX_PER_CLUB,
    SQUAD_SIZE, STARTING_SIZE, GOAL_POINTS,
)

CAPTAIN_CEILING_WEIGHT = 0.5
BENCH_XP_WEIGHT = 0.15  # Yedeklerin toplam kadro degerine katkisi (butceyi verimli kullanir)


@dataclass
class SquadResult:
    squad: pd.DataFrame
    starters: pd.DataFrame
    bench_gk: pd.Series
    bench_outfield: pd.DataFrame
    captain: pd.Series
    vice_captain: pd.Series
    total_budget_used: float
    total_starting_xp: float
    formation: str


def _build_and_solve(players: pd.DataFrame, bench_weight: float = BENCH_XP_WEIGHT) -> pd.DataFrame:
    n = len(players)
    pos = players["position_code"].values
    price = players["price_tl"].values.astype(float)
    xp = players["xp"].values.astype(float)
    teams = players["team"].values

    n_vars = 2 * n
    c = np.zeros(n_vars)
    c[:n] = -bench_weight * xp            # 15 kisilik kadrodaki tum oyuncularin degeri
    c[n:] = -(1.0 - bench_weight) * xp   # Ilk 11 oyuncusu tam 1.0 agirlik kazanir

    integrality = np.ones(n_vars)
    bounds = Bounds(lb=np.zeros(n_vars), ub=np.ones(n_vars))
    constraints = []

    # s_i <= x_i  ->  s_i - x_i <= 0
    A = np.zeros((n, n_vars))
    for i in range(n):
        A[i, i] = -1
        A[i, n + i] = 1
    constraints.append(LinearConstraint(A, -np.inf, 0))

    # sum(x) == 15
    A = np.zeros((1, n_vars)); A[0, :n] = 1
    constraints.append(LinearConstraint(A, SQUAD_SIZE, SQUAD_SIZE))

    # sum(s) == 11
    A = np.zeros((1, n_vars)); A[0, n:] = 1
    constraints.append(LinearConstraint(A, STARTING_SIZE, STARTING_SIZE))

    # butce <= 100M
    A = np.zeros((1, n_vars)); A[0, :n] = price
    constraints.append(LinearConstraint(A, 0, BUDGET_TL))

    # pozisyon bazli kadro: 2 GK, 5 DEF, 5 MID, 3 FWD
    for p_code, count in SQUAD_REQUIREMENTS.items():
        A = np.zeros((1, n_vars))
        idx = np.where(pos == p_code)[0]
        A[0, idx] = 1
        constraints.append(LinearConstraint(A, count, count))

    # ilk 11 kurali: GK == 1, DEF >= 3, FWD >= 1
    idx_gk = np.where(pos == "GK")[0]
    A = np.zeros((1, n_vars)); A[0, n + idx_gk] = 1
    constraints.append(LinearConstraint(A, 1, 1))

    idx_def = np.where(pos == "DEF")[0]
    A = np.zeros((1, n_vars)); A[0, n + idx_def] = 1
    constraints.append(LinearConstraint(A, STARTING_MIN["DEF"], 5))

    idx_fwd = np.where(pos == "FWD")[0]
    A = np.zeros((1, n_vars)); A[0, n + idx_fwd] = 1
    constraints.append(LinearConstraint(A, STARTING_MIN["FWD"], 3))

    # takim basi max 3
    for team in np.unique(teams):
        A = np.zeros((1, n_vars))
        idx = np.where(teams == team)[0]
        A[0, idx] = 1
        constraints.append(LinearConstraint(A, 0, MAX_PER_CLUB))

    res = milp(c, constraints=constraints, integrality=integrality, bounds=bounds)
    if not res.success:
        raise RuntimeError(f"MILP cozulemedi: {res.message}")

    out = players.copy()
    out["in_squad"] = res.x[:n] > 0.5
    out["is_starter"] = res.x[n:] > 0.5
    return out


def optimize_squad(players: pd.DataFrame, bench_weight: float = BENCH_XP_WEIGHT) -> SquadResult:
    if players["xp"].isnull().any():
        raise ValueError("xp kolonu bos olan oyuncu(lar) var — once compute_xp calistir.")

    solved = _build_and_solve(players, bench_weight=bench_weight)
    squad = solved[solved["in_squad"]].copy()
    starters = squad[squad["is_starter"]].copy()
    bench = squad[~squad["is_starter"]].copy()

    bench_gk_rows = bench[bench["position_code"] == "GK"]
    bench_gk = bench_gk_rows.iloc[0] if len(bench_gk_rows) else None
    bench_outfield = (
        bench[bench["position_code"] != "GK"]
        .sort_values("xp", ascending=False)
        .reset_index(drop=True)
    )

    # Taktik dizilis tespiti (Orn: 3-5-2, 4-3-3, 3-4-3)
    n_def = (starters["position_code"] == "DEF").sum()
    n_mid = (starters["position_code"] == "MID").sum()
    n_fwd = (starters["position_code"] == "FWD").sum()
    formation = f"{n_def}-{n_mid}-{n_fwd}"

    # Kaptan: xP + tavan skoru
    starters = starters.copy()
    goal_component = starters["goal_prob_component"] if "goal_prob_component" in starters.columns else 0.0
    starters["captain_score"] = starters["xp"] + CAPTAIN_CEILING_WEIGHT * (
        goal_component * starters["position_code"].map(GOAL_POINTS)
    )
    starters_sorted = starters.sort_values("captain_score", ascending=False)
    captain = starters_sorted.iloc[0]
    vice_captain = starters_sorted.iloc[1]

    return SquadResult(
        squad=squad,
        starters=starters,
        bench_gk=bench_gk,
        bench_outfield=bench_outfield,
        captain=captain,
        vice_captain=vice_captain,
        total_budget_used=float(squad["price_tl"].sum()),
        total_starting_xp=float(starters["xp"].sum()),
        formation=formation
    )
