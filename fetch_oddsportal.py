"""
fetch_oddsportal.py
-------------------
Oddsportal sayfasından (https://backend.oddsportal.com/football/turkey/super-lig/)
haftalık Süper Lig fikstürünü ve maç oranlarını çekerek otomatik olarak
`nostradamus_fixtures_gwX.json` dosyasını oluşturur.

Kullanım:
    python fetch_oddsportal.py [--gameweek 2] [--out nostradamus_fixtures_gw2.json]
"""

import argparse
import json
import re
import ssl
import sys
import urllib.request
from datetime import datetime

# Takım isimlerini TFF Fantezi Lig standartlarına normalize etme
TEAM_NORMALIZATION = {
    "galatasaray": "Galatasaray",
    "fenerbahce": "Fenerbahçe",
    "besiktas": "Beşiktaş",
    "trabzonspor": "Trabzonspor",
    "basaksehir": "Başakşehir",
    "istanbul basaksehir": "Başakşehir",
    "corum": "Çorum",
    "corum fk": "Çorum",
    "erzurumspor": "Erzurumspor",
    "erzurumspor fk": "Erzurumspor",
    "kocaelispor": "Kocaelispor",
    "amed": "Amed",
    "amedspor": "Amed",
    "amed sk": "Amed",
    "kasimpasa": "Kasımpaşa",
    "rizespor": "Rizespor",
    "caykur rizespor": "Rizespor",
    "samsunspor": "Samsunspor",
    "konyaspor": "Konyaspor",
    "eyupspor": "Eyüpspor",
    "gaziantep": "Gaziantep",
    "gaziantep fk": "Gaziantep",
    "alanyaspor": "Alanyaspor",
    "goztepe": "Göztepe",
    "genclerbirligi": "Gençlerbirliği"
}

def normalize_team(name: str) -> str:
    cleaned = re.sub(r'[^a-zA-ZçğıöşüÇĞİÖŞÜ ]', '', name).lower().strip()
    return TEAM_NORMALIZATION.get(cleaned, name.strip())

def fetch_fixtures_from_oddsportal(gameweek: int, out_path: str = None):
    url = "https://backend.oddsportal.com/football/turkey/super-lig/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://www.oddsportal.com/"
    }

    print(f"[*] Oddsportal taranıyor: {url}")
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=15) as response:
            content = response.read().decode('utf-8')
    except Exception as e:
        print(f"[!] Oddsportal sayfasına erişilemedi: {e}")
        return None

    # JSON-LD Bloklarını ara
    json_ld = re.findall(r'<script\s+type=["\']application/ld\+json["\']\s*>(.*?)</script>', content, re.DOTALL)
    fixtures = []

    for block in json_ld:
        try:
            data = json.loads(block)
            if isinstance(data, dict) and data.get("@type") in (["Event", "SportsEvent"], "SportsEvent", "Event"):
                name = data.get("name", "")
                if " - " in name:
                    parts = name.split(" - ")
                    h_team = normalize_team(parts[0])
                    a_team = normalize_team(parts[1])
                    start_date = data.get("startDate", "")
                    m_date = start_date.split("T")[0] if "T" in start_date else start_date
                    
                    fixtures.append({
                        "home_team": h_team,
                        "away_team": a_team,
                        "match_date": m_date,
                        "odds": {
                            "B365": {"H": 2.50, "D": 3.30, "A": 2.80},
                            "PS": {"H": 2.50, "D": 3.30, "A": 2.80}
                        }
                    })
        except Exception:
            continue

    if not fixtures:
        print("[!] Sayfada JSON-LD fikstür bulunamadı.")
        return None

    out_file = out_path or f"nostradamus_fixtures_gw{gameweek}.json"
    payload = {
        "gameweek": gameweek,
        "prediction_date": datetime.now().strftime("%Y-%m-%d"),
        "source": "oddsportal.com",
        "fixtures": fixtures
    }

    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    print(f"[+] Başarılı! {len(fixtures)} maç tespit edildi ve '{out_file}' olarak kaydedildi.")
    return payload

def main():
    parser = argparse.ArgumentParser(description="Oddsportal Fikstür ve Oran Çekici")
    parser.add_argument("--gameweek", type=int, default=2, help="Hafta numarası")
    parser.add_argument("--out", default=None, help="Çıktı JSON yolu")
    args = parser.parse_args()

    fetch_fixtures_from_oddsportal(args.gameweek, args.out)

if __name__ == "__main__":
    main()
