"""
tests/test_optimizer.py
-----------------------
optimizer.py icin temel regresyon testi.

Test eder:
  1. optimize_squad 15 oyuncu dondurur (2 GK, 5 DEF, 5 MID, 3 FWD)
  2. Bütçe kısıtına (100M TL) uyulur
  3. Kulüp sınırına (ayni takimdan max 3) uyulur
  4. Kaptan ve yedek kaptain squad icinde olmasi

Calistirma:
    python tests/test_optimizer.py
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from data_loader import load_players, load_gameweek_log, BUDGET_TL, SQUAD_SIZE, SQUAD_REQUIREMENTS, MAX_PER_CLUB
from xp_model import compute_xp
from optimizer import optimize_squad


REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOURCE_EXCEL = os.path.join(REPO_ROOT, "oyuncu_veritabani.xlsx")


class TestOptimizer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.players = load_players(SOURCE_EXCEL)
        cls.log = load_gameweek_log(SOURCE_EXCEL)
        cls.players = compute_xp(cls.players, cls.log)
        cls.result = optimize_squad(cls.players)

    def test_1_squad_size_is_15(self):
        """Squad tam 15 oyuncu icermeli."""
        self.assertEqual(len(self.result.squad), SQUAD_SIZE,
                         f"Squad {SQUAD_SIZE} olmali, {len(self.result.squad)} var")

    def test_2_position_distribution(self):
        """Pozisyon dagilimi 2GK/5DEF/5MID/3FWD olmali."""
        pos_counts = self.result.squad["position_code"].value_counts().to_dict()
        for pos, expected in SQUAD_REQUIREMENTS.items():
            actual = pos_counts.get(pos, 0)
            self.assertEqual(actual, expected,
                             f"Pozisyon {pos}: {expected} olmali, {actual} var")

    def test_3_budget_constraint(self):
        """Toplam maliyet 100M TL'yi asmamali."""
        total = self.result.squad["price_tl"].sum()
        self.assertLessEqual(total, BUDGET_TL,
                             f"Toplam maliyet {BUDGET_TL} TL'yi asti: {total}")

    def test_4_max_per_club(self):
        """Ayni takimdan max 3 oyuncu olmali."""
        club_counts = self.result.squad["team"].value_counts()
        max_count = club_counts.max()
        self.assertLessEqual(max_count, MAX_PER_CLUB,
                             f"Tek takimdan {max_count} oyuncu var (max {MAX_PER_CLUB})")

    def test_5_captain_in_squad(self):
        """Kaptan squad icinde olmali."""
        captain_id = self.result.captain["player_id"]
        squad_ids = set(self.result.squad["player_id"])
        self.assertIn(captain_id, squad_ids,
                      "Kaptan squad icinde degil")

    def test_6_vice_captain_in_squad(self):
        """Yedek kaptan squad icinde olmali."""
        vice_id = self.result.vice_captain["player_id"]
        squad_ids = set(self.result.squad["player_id"])
        self.assertIn(vice_id, squad_ids,
                      "Yedek kaptan squad icinde degil")

    def test_7_captain_and_vice_different(self):
        """Kaptan ve yedek kaptan ayni oyuncu olmamali."""
        captain_id = self.result.captain["player_id"]
        vice_id = self.result.vice_captain["player_id"]
        self.assertNotEqual(captain_id, vice_id,
                            "Kaptan ve yedek kaptan ayni oyuncu")


if __name__ == "__main__":
    unittest.main(verbosity=2)
