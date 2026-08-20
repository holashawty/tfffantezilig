"""
validator.py
------------
Web-arastirma/sonuc/fiyat guncellemelerinin Excel'e islenmeden once
gectigi ortak "kontrolcu" katmani. Hicbir ingest script'i bu kontrolden
gecmeyen bir kaydi SESSIZCE uygulamaz.

Iki tur kontrol:
  1. KAYIT-DUZEYINDE (hard): zorunlu alan eksikse veya deger mantik
     disi bir aralikta ise (ornegin play_probability 1.4) o kayit
     REDDEDILIR — eslesmeyen isim gibi ayri listelenir, uygulanmaz.
  2. BATCH-DUZEYINDE (soft/uyari): toplam kapsam beklenenden cok
     dusukse (ornegin 443 oyuncudan sadece 12'si icin veri geldi)
     UYARI basilir ama --apply engellenmez — bu bazen normal olabilir
     (ornegin sadece sakatlari raporlayan bir hafta), karar kullaniciya
     birakilir.
"""

from dataclasses import dataclass, field


@dataclass
class ValidationResult:
    valid_records: list = field(default_factory=list)
    rejected_records: list = field(default_factory=list)  # (record, reason)
    warnings: list = field(default_factory=list)

    def print_report(self, label: str):
        print(f"\n--- VERI KALITE RAPORU: {label} ---")
        print(f"Gecerli kayit: {len(self.valid_records)}  |  "
              f"Reddedilen: {len(self.rejected_records)}  |  "
              f"Uyari: {len(self.warnings)}")
        if self.rejected_records:
            print("REDDEDILENLER (uygulanmayacak):")
            for rec, reason in self.rejected_records:
                name = rec.get("player_name", "?")
                print(f"  - {name}: {reason}")
        for w in self.warnings:
            print(f"  [UYARI] {w}")


def _require_fields(record: dict, fields: list) -> str | None:
    for f in fields:
        if record.get(f) in (None, ""):
            return f"zorunlu alan eksik: '{f}'"
    return None


def _check_range(record: dict, field_name: str, lo: float, hi: float) -> str | None:
    val = record.get(field_name)
    if val is None:
        return None
    try:
        val = float(val)
    except (TypeError, ValueError):
        return f"'{field_name}' sayi degil: {val!r}"
    if not (lo <= val <= hi):
        return f"'{field_name}'={val} beklenen aralik disinda [{lo}, {hi}]"
    return None


def validate_injury_updates(updates: list, total_player_count: int) -> ValidationResult:
    res = ValidationResult()
    for rec in updates:
        err = _require_fields(rec, ["player_name", "play_probability"])
        if not err:
            err = _check_range(rec, "play_probability", 0.0, 1.0)
        if err:
            res.rejected_records.append((rec, err))
        else:
            res.valid_records.append(rec)

    if total_player_count > 0:
        coverage = len(res.valid_records) / total_player_count
        if coverage > 0.5:
            res.warnings.append(
                f"Guncelleme sayisi ({len(res.valid_records)}) toplam kadronun "
                f"%{coverage*100:.0f}'i — bu genelde sadece birkac oyuncuyu "
                f"kapsayan bir sakatlik/ceza raporu icin cok yuksek, kaynagi "
                f"kontrol et (belki gereksiz/uydurma satirlar var)."
            )
    return res


def validate_match_results(results: list) -> ValidationResult:
    res = ValidationResult()
    for rec in results:
        err = _require_fields(rec, ["player_name"])
        if not err:
            err = _check_range(rec, "minutes", 0, 120)
        if not err:
            err = _check_range(rec, "goals", 0, 10)
        if not err:
            err = _check_range(rec, "assists", 0, 10)
        if not err and rec.get("fantasy_points") is not None:
            err = _check_range(rec, "fantasy_points", -20, 50)
        if err:
            res.rejected_records.append((rec, err))
        else:
            res.valid_records.append(rec)
    return res


def validate_price_updates(prices: list, min_price=1_000_000, max_price=25_000_000) -> ValidationResult:
    res = ValidationResult()
    for rec in prices:
        err = _require_fields(rec, ["player_name", "price_tl"])
        if not err:
            # Otomatik birim donusumu: Eger fiyat 100'den kucukse (orn 4.5, 10.0), Milyon TL kabul edip tam TL'ye cevir
            try:
                val = float(rec["price_tl"])
                if 1.0 <= val <= 100.0:
                    rec["price_tl"] = int(round(val * 1_000_000))
                else:
                    rec["price_tl"] = int(round(val))
            except (ValueError, TypeError):
                pass
            err = _check_range(rec, "price_tl", min_price, max_price)
        if err:
            res.rejected_records.append((rec, err))
        else:
            res.valid_records.append(rec)
    return res


# Transfer penceresi için izin verilen değerler (data_loader.py ile uyumlu)
VALID_TRANSFER_TYPES = {"in", "out", "move"}
VALID_POSITIONS = {
    "GK - Kaleci", "DEF - Defans", "MID - Orta Saha", "FWD - Forvet",
}


def validate_transfer_window(transfers: list, total_player_count: int = 0) -> ValidationResult:
    """Transfer penceresi kayıtlarını doğrular.

    Beklenen JSON şeması (transfer_prompti.md ile üretilir):
        {
          "transfer_date": "YYYY-MM-DD",
          "transfers": [
            {
              "player_name": "...",          # zorunlu
              "transfer_type": "in|out|move", # zorunlu
              "team": "...",                  # 'in' ve 'move' için zorunlu
              "position": "GK - Kaleci",      # 'in' için zorunlu
              "new_price_tl": 5000000,        # 'in' için opsiyonel (verilmezse fiyat=2M)
              "source_note": "..."            # opsiyonel ama önerilen
            }
          ]
        }

    transfer_type anlamları:
      - "in":  yeni oyuncu Süper Lig'e geliyor (yeni player_id atanır)
      - "out": oyuncu Süper Lig'den ayrılıyor (is_active=0, satır SİLİNMEZ)
      - "move": oyuncu Süper Lig içinde takım değiştiriyor (team alanı güncellenir)
    """
    res = ValidationResult()
    for rec in transfers:
        err = _require_fields(rec, ["player_name", "transfer_type"])
        if not err:
            tt = rec.get("transfer_type")
            if tt not in VALID_TRANSFER_TYPES:
                err = f"transfer_type='{tt}' geçersiz (olmalı: {sorted(VALID_TRANSFER_TYPES)})"
            elif tt == "in":
                # yeni oyuncu — team ve position zorunlu
                err = _require_fields(rec, ["team", "position"])
                if not err and rec.get("position") not in VALID_POSITIONS:
                    err = f"position='{rec.get('position')}' geçersiz (olalı: {sorted(VALID_POSITIONS)})"
                if not err and rec.get("new_price_tl") is not None:
                    err = _check_range(rec, "new_price_tl", 1_000_000, 25_000_000)
            elif tt == "move":
                # takım değiştirme — team zorunlu (yeni takım)
                err = _require_fields(rec, ["team"])
        if err:
            res.rejected_records.append((rec, err))
        else:
            res.valid_records.append(rec)

    if total_player_count > 0:
        # transfer penceresi genelde az kayıt içerir — beklenen aralık 1-50
        if len(res.valid_records) > 100:
            res.warnings.append(
                f"Transfer kaydı sayısı ({len(res.valid_records)}) yüksek — "
                f"tek bir pencere için 100'den fazla transfer beklenmez, "
                f"JSON'u kontrol et."
            )
    return res
