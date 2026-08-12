"""
build_superlig_db.py
--------------------
Kaynak: OuziBet projesinden gelen unified.db (~99MB, 20 tablo, 11 lig).
Hedef:  nostradamus/superlig_odds.db — SADECE Süper Lig (league_id=17)
        satırlarını içeren küçük, temiz, tek-amaçlı SQLite dosyası.

İlke (docs/00, docs/03):
    - Kaynak dosya BİREBİR KOPYALANMAZ — sadece ilgili satırlar taşınır.
    - Ağır ML pipeline (GNN/Bayesian NN/TFT/RL/copula/multi-agent LLM)
      ve boş tabloları (copula_models, transfer_models, player_injuries,
      sharp_money_signals) bu projeye HİÇ ALINMAZ — docs/00 ve docs/08
      "basit, kod=matematik karar verir" ilkesiyle çelişiyor.
    - Bu script TEKRAR ÜRETİLEBİLİR (idempotent): hedef dosya varsa
      silinip yeniden yazılır, üzerine ek yapmaz.

Kullanım:
    python build_superlig_db.py <unified_db_yolu> <hedef_db_yolu>

Örnek:
    python build_superlig_db.py ../unified.db superlig_odds.db
"""

import argparse
import os
import sqlite3
import sys
from datetime import datetime


LEAGUE_ID = 17  # Süper Lig


def _log(msg: str):
    print(f"  {msg}")


def build(src_path: str, dst_path: str):
    if not os.path.exists(src_path):
        sys.exit(f"[HATA] Kaynak DB bulunamadı: {src_path}")

    if os.path.exists(dst_path):
        os.remove(dst_path)
        _log(f"Mevcut hedef dosya silindi (üzerine yazılacak): {dst_path}")

    src = sqlite3.connect(src_path)
    src.row_factory = sqlite3.Row
    dst = sqlite3.connect(dst_path)

    _create_schema(dst)
    _copy_teams(src, dst)
    _copy_team_aliases(src, dst)
    _copy_matches(src, dst)
    _copy_odds(src, dst)
    _copy_xg_stats(src, dst)  # kaynakta 0 satır — boş tablo oluştur
    _write_meta(dst, src_path)
    _create_indices(dst)

    dst.commit()
    dst.close()
    src.close()

    size_mb = os.path.getsize(dst_path) / 1_048_576
    print(f"\n[TAMAM] {dst_path}  ({size_mb:.2f} MB)")


def _create_schema(dst):
    _log("Şema oluşturuluyor...")
    dst.executescript("""
        CREATE TABLE teams (
            team_id        INTEGER PRIMARY KEY,
            canonical_name TEXT NOT NULL
        );

        CREATE TABLE team_aliases (
            alias     TEXT NOT NULL,
            source    TEXT,
            team_id   INTEGER NOT NULL,
            FOREIGN KEY(team_id) REFERENCES teams(team_id)
        );

        CREATE TABLE matches (
            match_id      INTEGER PRIMARY KEY,
            season        TEXT,
            match_date    TEXT,
            home_team_id  INTEGER NOT NULL,
            away_team_id  INTEGER NOT NULL,
            home_goals    INTEGER,
            away_goals    INTEGER,
            source        TEXT,
            FOREIGN KEY(home_team_id) REFERENCES teams(team_id),
            FOREIGN KEY(away_team_id) REFERENCES teams(team_id)
        );

        CREATE TABLE odds (
            match_id    INTEGER NOT NULL,
            bookmaker   TEXT NOT NULL,
            market      TEXT NOT NULL,
            selection   TEXT NOT NULL,
            price       REAL NOT NULL,
            is_closing  INTEGER NOT NULL,
            FOREIGN KEY(match_id) REFERENCES matches(match_id)
        );

        CREATE TABLE xg_stats (
            match_id    INTEGER NOT NULL,
            team_id     INTEGER NOT NULL,
            xg_for      REAL,
            xg_against  REAL,
            source      TEXT,
            FOREIGN KEY(match_id) REFERENCES matches(match_id),
            FOREIGN KEY(team_id) REFERENCES teams(team_id)
        );

        CREATE TABLE meta (
            key   TEXT PRIMARY KEY,
            value TEXT
        );
    """)


def _copy_teams(src, dst):
    # sadece league_id=17 maçlarında görünen takımları al
    rows = src.execute("""
        SELECT DISTINCT t.team_id, t.canonical_name
        FROM teams t
        WHERE t.team_id IN (
                SELECT home_team_id FROM matches WHERE league_id=?
              UNION
                SELECT away_team_id FROM matches WHERE league_id=?
              )
        ORDER BY t.canonical_name
    """, (LEAGUE_ID, LEAGUE_ID)).fetchall()
    dst.executemany(
        "INSERT INTO teams(team_id, canonical_name) VALUES (?, ?)",
        [(r["team_id"], r["canonical_name"]) for r in rows]
    )
    _log(f"teams: {len(rows)} takım")


def _copy_team_aliases(src, dst):
    # Hedef db'deki teams tablosundaki team_id'leri al (kaynaktaki
    # teams tablosu 85K takım içeriyor, bizim 33 takımımıza filtrele).
    dst_team_ids = [r[0] for r in dst.execute("SELECT team_id FROM teams").fetchall()]
    if not dst_team_ids:
        _log("team_aliases: ATLANDI (hedef teams tablosu boş)")
        return
    placeholders = ",".join("?" * len(dst_team_ids))
    rows = src.execute(
        f"""SELECT alias, source, team_id
            FROM team_aliases
            WHERE team_id IN ({placeholders})
            ORDER BY team_id, alias""",
        dst_team_ids
    ).fetchall()
    dst.executemany(
        "INSERT INTO team_aliases(alias, source, team_id) VALUES (?, ?, ?)",
        [(r["alias"], r["source"], r["team_id"]) for r in rows]
    )
    _log(f"team_aliases: {len(rows)} alias")


def _copy_matches(src, dst):
    rows = src.execute("""
        SELECT match_id, season, match_date, home_team_id, away_team_id,
               home_goals, away_goals, source
        FROM matches
        WHERE league_id=?
        ORDER BY match_date
    """, (LEAGUE_ID,)).fetchall()
    dst.executemany(
        """INSERT INTO matches
           (match_id, season, match_date, home_team_id, away_team_id,
            home_goals, away_goals, source)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        [(r["match_id"], r["season"], r["match_date"], r["home_team_id"],
          r["away_team_id"], r["home_goals"], r["away_goals"], r["source"])
         for r in rows]
    )
    _log(f"matches: {len(rows)} maç (league_id={LEAGUE_ID})")

    # sezon bazında özet
    season_counts = src.execute("""
        SELECT season, COUNT(*) AS n
        FROM matches WHERE league_id=?
        GROUP BY season ORDER BY season
    """, (LEAGUE_ID,)).fetchall()
    for sc in season_counts:
        _log(f"    sezon '{sc['season']}': {sc['n']} maç")


def _copy_odds(src, dst):
    rows = src.execute("""
        SELECT o.match_id, o.bookmaker, o.market, o.selection,
               o.price, o.is_closing
        FROM odds o
        WHERE o.match_id IN (
            SELECT match_id FROM matches WHERE league_id=?
        )
        ORDER BY o.match_id, o.market, o.bookmaker, o.is_closing
    """, (LEAGUE_ID,)).fetchall()
    dst.executemany(
        """INSERT INTO odds
           (match_id, bookmaker, market, selection, price, is_closing)
           VALUES (?, ?, ?, ?, ?, ?)""",
        [(r["match_id"], r["bookmaker"], r["market"], r["selection"],
          r["price"], r["is_closing"]) for r in rows]
    )
    _log(f"odds: {len(rows)} satır (Süper Lig maçları için)")

    # bahisçi/market dağılımı
    dist = src.execute("""
        SELECT o.bookmaker, o.market, o.is_closing, COUNT(*) AS n
        FROM odds o JOIN matches m ON o.match_id=m.match_id
        WHERE m.league_id=?
        GROUP BY o.bookmaker, o.market, o.is_closing
        ORDER BY o.bookmaker, o.market, o.is_closing
    """, (LEAGUE_ID,)).fetchall()
    for d in dist:
        _log(f"    {d['bookmaker']:6} {d['market']:8} is_closing={d['is_closing']}: {d['n']}")


def _copy_xg_stats(src, dst):
    # Kaynakta league_id=17 için 0 satır — yine de tabloyu boş olarak
    # oluştur, ileride football-data.co.uk/FBref doldurursa bu şema
    # hazır olsun. Audit raporunda bu durum açıkça not edilir.
    rows = src.execute("""
        SELECT x.match_id, x.team_id, x.xg_for, x.xg_against, x.source
        FROM xg_stats x JOIN matches m ON x.match_id=m.match_id
        WHERE m.league_id=?
    """, (LEAGUE_ID,)).fetchall()
    if rows:
        dst.executemany(
            """INSERT INTO xg_stats
               (match_id, team_id, xg_for, xg_against, source)
               VALUES (?, ?, ?, ?, ?)""",
            [(r["match_id"], r["team_id"], r["xg_for"], r["xg_against"], r["source"])
             for r in rows]
        )
    _log(f"xg_stats: {len(rows)} satır (kaynakta Süper Lig için boş — beklenen)")


def _write_meta(dst, src_path):
    meta = {
        "build_date": datetime.now().isoformat(timespec="seconds"),
        "source_db": os.path.basename(src_path),
        "source_db_size_mb": f"{os.path.getsize(src_path)/1_048_576:.2f}",
        "league_id": str(LEAGUE_ID),
        "league_name": "Süper Lig",
        "country": "Turkey",
        "schema_version": "1",
        "note": "Sadece league_id=17 satırları içerir. OuziBet ağır ML "
                "pipeline'ı ve boş tabloları bilerek ALINMADI (docs/00, "
                "docs/08 ilkesi).",
    }
    dst.executemany(
        "INSERT INTO meta(key, value) VALUES (?, ?)",
        list(meta.items())
    )


def _create_indices(dst):
    dst.executescript("""
        CREATE INDEX idx_matches_date    ON matches(match_date);
        CREATE INDEX idx_matches_season  ON matches(season);
        CREATE INDEX idx_odds_match      ON odds(match_id);
        CREATE INDEX idx_odds_market     ON odds(market, is_closing);
        CREATE INDEX idx_odds_bookmaker  ON odds(bookmaker);
        CREATE INDEX idx_aliases_team    ON team_aliases(team_id);
    """)
    _log("Indeksler oluşturuldu")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("src_db", help="Kaynak unified.db yolu")
    ap.add_argument("dst_db", help="Hedef superlig_odds.db yolu")
    args = ap.parse_args()
    build(args.src_db, args.dst_db)
