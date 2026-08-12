"""
data_loader.py
---------------
Super_Lig_Oyuncu_ve_Maas_Listesi_Optimizasyon_3.xlsx dosyasindaki
Players / GameweekLog / Fixtures sheet'lerini temiz DataFrame'lere
cevirir.

Dosyanin ilk 3 satiri baslik/aciklama satirlaridir (Gemini'nin
formatiyla uyumlu calismak icin header=3 kullanilir).
"""

import pandas as pd

POSITION_MAP = {
    "GK - Kaleci": "GK",
    "DEF - Defans": "DEF",
    "MID - Orta Saha": "MID",
    "FWD - Forvet": "FWD",
}

SQUAD_REQUIREMENTS = {"GK": 2, "DEF": 5, "MID": 5, "FWD": 3}
STARTING_MIN = {"GK": 1, "DEF": 3, "FWD": 1}  # resmi kural: ilk 11'de min bu kadar
BUDGET_TL = 100_000_000
MAX_PER_CLUB = 3
SQUAD_SIZE = 15
STARTING_SIZE = 11

# Resmi puanlama tablosu (tfffantezilig.com/yardim, dogrulandi)
GOAL_POINTS = {"GK": 10, "DEF": 6, "MID": 5, "FWD": 4}
ASSIST_POINTS = 3
CLEAN_SHEET_POINTS = {"GK": 4, "DEF": 4, "MID": 1, "FWD": 0}
SAVE_POINTS_PER_3 = 1
PENALTY_SAVE_POINTS = 5
PENALTY_MISS_POINTS = -2
CONCEDED_PENALTY_PER_2 = -1  # sadece GK/DEF
YELLOW_CARD_POINTS = -1
RED_CARD_POINTS = -3
OWN_GOAL_POINTS = -2
APPEARANCE_POINTS_UNDER_60 = 1
APPEARANCE_POINTS_60_PLUS = 2


def load_players(path: str) -> pd.DataFrame:
    df = pd.read_excel(path, sheet_name="Players", header=3)
    df = df.rename(columns={"price_tl_gw1": "price_tl_base"})
    df["position_code"] = df["position"].map(POSITION_MAP)
    if df["position_code"].isnull().any():
        bad = df[df["position_code"].isnull()]["position"].unique()
        raise ValueError(f"Taninmayan pozisyon degeri(leri): {bad}")
    # Canli fiyat: Players sheet'inde price_tl_current kolonu varsa
    # (ingest_price_updates.py ile guncellenir) o kullanilir; yoksa
    # baslangic fiyatina (price_tl_base) dusulur. Fiyatlar transfer
    # piyasasina gore degistigi icin GameweekLog'daki gecmis fiyat
    # DEGIL, bu canli deger optimizer'a girer.
    if "price_tl_current" in df.columns:
        df["price_tl"] = df["price_tl_current"].fillna(df["price_tl_base"])
    else:
        df["price_tl"] = df["price_tl_base"]
    df["play_probability"] = df["play_probability"].fillna(1.0).clip(0.0, 1.0)
    return df


def load_gameweek_log(path: str) -> pd.DataFrame:
    df = pd.read_excel(path, sheet_name="GameweekLog", header=3)
    # Bos sablon da olsa dogru kolonlarla donsun
    expected_cols = [
        "player_id", "gameweek", "minutes", "goals", "assists",
        "yellow_cards", "red_cards", "fantasy_points", "price_tl",
    ]
    for c in expected_cols:
        if c not in df.columns:
            df[c] = pd.Series(dtype="float64")
    return df.dropna(subset=["player_id"])


def load_fixtures(path: str) -> pd.DataFrame:
    df = pd.read_excel(path, sheet_name="Fixtures", header=3)
    return df.dropna(how="all")


def apply_latest_prices(players: pd.DataFrame, log: pd.DataFrame) -> pd.DataFrame:
    """ARTIK BIRINCIL FIYAT KAYNAGI DEGIL — bkz. load_players()'daki
    price_tl_current. Bu fonksiyon sadece denetim/capraz-kontrol icin
    tutuluyor: GameweekLog'a o hafta islenen tarihsel fiyatla,
    Players.price_tl_current arasinda buyuk fark varsa fark edilsin
    diye. Optimizer artik bunu cagirmiyor."""
    if log.empty or log["price_tl"].isnull().all():
        return players
    latest = (
        log.dropna(subset=["price_tl"])
        .sort_values("gameweek")
        .groupby("player_id")["price_tl"]
        .last()
    )
    players = players.copy()
    players["price_tl_gameweeklog_latest"] = players["player_id"].map(latest)
    return players
