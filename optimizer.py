"""
optimizer.py
------------
Kesin (deterministik) kadro secimi: MILP (Mixed Integer Linear
Programming), scipy.optimize.milp (HiGHS solver) ile.

Neden LLM/prompt degil: bu problem "443 oyuncu icinden butce,
mevki ve kulup kisitlarini KESIN saglayan xP-maksimize eden 15
kisiyi bul" seklinde klasik bir tam sayili optimizasyon problemi.
MILP saniyeler icinde matematiksel garantili en iyi cozumu bulur;
bir LLM'e tabloyu okutup sectirmek ne kisitlari garanti eder ne de
tekrarlanabilir sonuc verir.

Karar degiskenleri:
  x_i in {0,1}  -> oyuncu i, 15 kisilik kadroda mi?
  s_i in {0,1}  -> oyuncu i, ilk 11'de mi?

Kisitlar (resmi kurallar, tfffantezilig.com/yardim):
  - s_i <= x_i                          (ilk 11, kadronun alt kumesi)
  - sum(x) == 15                        (kadro boyutu)
  - sum(s) == 11                        (ilk 11 boyutu)
  - sum(price_i * x_i) <= 100.000.000   (butce)
  - pozisyon bazli kadro sayilari: 2 GK, 5 DEF, 5 MID, 3 FWD
  - ilk 11 icinde: GK == 1, DEF >= 3, FWD >= 1
  - takim basi kadroda en fazla 3 oyuncu
"""

from dataclasses import dataclass, field
import numpy as np
import pandas as pd
from scipy.optimize import milp, LinearConstraint, Bounds

from data_loader import (
    SQUAD_REQUIREMENTS, STARTING_MIN, BUDGET_TL, MAX_PER_CLUB,
    SQUAD_SIZE, STARTING_SIZE, GOAL_POINTS,
)

CAPTAIN_CEILING_WEIGHT = 0.5  # kaptan secerken tavan(gol olasiligi) agirligi


@dataclass
class SquadResult:
    squad: pd.DataFrame          # 15 oyuncu
    starters: pd.DataFrame       # 11 oyuncu (xp'ye gore siralanmis degil, mevkiye gore)
    bench_gk: pd.Series
    bench_outfield: pd.DataFrame  # 3 oyuncu, oynama onceligine gore siralanmis (1,2,3)
    captain: pd.Series
    vice_captain: pd.Series
    total_budget_used: float
    total_starting_xp: float


def _build_and_solve(players: pd.DataFrame) -> pd.DataFrame:
    n = len(players)
    pos = players["position_code"].values
    price = players["price_tl"].values.astype(float)
    xp = players["xp"].values.astype(float)
    teams = players["team"].values

    # Degisken vektoru: [x_0..x_{n-1}, s_0..s_{n-1}]
    n_vars = 2 * n
    c = np.zeros(n_vars)
    c[n:] = -xp  # minimize(-xp) == maximize(xp), sadece starter'lar puan getirir

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

    # butce
    A = np.zeros((1, n_vars)); A[0, :n] = price
    constraints.append(LinearConstraint(A, 0, BUDGET_TL))

    # pozisyon bazli kadro sayilari
    for p, count in SQUAD_REQUIREMENTS.items():
        A = np.zeros((1, n_vars))
        idx = np.where(pos == p)[0]
        A[0, idx] = 1
        constraints.append(LinearConstraint(A, count, count))

    # ilk 11 pozisyon kurallari
    idx_gk = np.where(pos == "GK")[0]
    A = np.zeros((1, n_vars)); A[0, n + idx_gk] = 1
    constraints.append(LinearConstraint(A, 1, 1))  # tam 1 kaleci sahada

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

    x = res.x[:n] > 0.5
    s = res.x[n:] > 0.5

    out = players.copy()
    out["in_squad"] = x
    out["is_starter"] = s
    return out


def optimize_squad(players: pd.DataFrame) -> SquadResult:
    if players["xp"].isnull().any():
        raise ValueError("xp kolonu bos olan oyuncu(lar) var — once compute_xp calistir.")

    solved = _build_and_solve(players)
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

    # Kaptan: xP + tavan(gol olasiligi * gol puani) agirlikli skor
    starters = starters.copy()
    starters["captain_score"] = starters["xp"] + CAPTAIN_CEILING_WEIGHT * (
        starters["goal_prob_component"] * starters["position_code"].map(GOAL_POINTS)
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
        total_budget_used=squad["price_tl"].sum(),
        total_starting_xp=starters["xp"].sum(),
    )
