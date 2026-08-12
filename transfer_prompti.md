# Transfer Penceresi Prompti (docs/06'nın uygulaması)

Sezon ortası transfer penceresi (genelde 17. hafta civarı, TFF takvimine
göre değişir) açıldığında, Süper Lig'e gelen/giden/transfer olan
oyuncuları güncellemek için bu promptu kullan. Mevcut `ingest_transfer_window.py`
script'i, bu promptun çıktısını `Players` sheet'ine işler.

## KULLANIM ZAMANI

- Sezon ortası transfer penceresi açıldığında (genelde Ocak başı)
- Pencere kapandıktan sonra bir kez daha (geç transferler için)
- Sezon başında yeni oyuncu listesi yayımlandığında (yeni sezon öncesi)

Bu prompt her hafta çalıştırılmaz — sadece transfer hareketliliği
olan dönemlerde. Normal haftalarda `web_arastirma_prompti.md` yeterli.

## KAYNAK ÖNCELİĞİ (docs/04'teki listeyle uyumlu)

1. **Transfermarkt** (`transfermarkt.com`) — birincil kaynak. Transfer
   tarihi, eski/yeni kulüp, transfer bedeli burada en düzenli.
2. **tff.org** — sadece resmi kulüp kayıtları için (kesinleşmiş transferler).
3. **fotmob.com** — oyuncu bazlı transfer geçmişi için iyi üçüncü-parti kaynak.
4. Spor basını (beIN Sports, Fanatik, Sporx) — teyit için.

**UYARI:** Söylenti ve resmi açıklama arasını ayır. "Transferi yakın"
diyen haberleri ALMA — sadece resmileşmiş (kulüp tarafından açıklanmış
veya Transfermarkt'ta kayıt altına alınmış) transferleri listele.

------------------------------------------------------------------
KOPYALA-YAPIŞTIR PROMPT (aşağısı, "-----" arası):
------------------------------------------------------------------

Türkiye Trendyol Süper Lig transfer penceresi için [TARİH ARALIĞI,
örn: "1-31 Ocak 2026"] döneminde resmileşen transferleri ara.
SADECE Transfermarkt, kulüp resmi açıklamaları ve tff.org'ta
kayıtlı transferleri dahil et — söylentileri DEĞİL.

Aşağıdaki JSON formatında, JSON DIŞINDA HİÇBİR METİN OLMADAN cevap ver.
Her transfer için doğru `transfer_type`'ı seç:
  - "in":  oyuncu Süper Lig dışından bir Süper Lig takımına geldi
  - "out": oyuncu Süper Lig'den ayrıldı (başka lige gitti veya serbest kaldı)
  - "move": oyuncu Süper Lig içinde bir takımdan diğerine geçti

{
  "transfer_date": "<YYYY-MM-DD>",
  "transfers": [
    {
      "player_name": "<oyuncunun tam adı, mevcut veritabanındaki yazımıyla uyumlu>",
      "transfer_type": "in | out | move",
      "team": "<yeni takım — 'in' ve 'move' için zorunlu, 'out' için boş bırakılabilir>",
      "position": "GK - Kaleci | DEF - Defans | MID - Orta Saha | FWD - Forvet",
      "new_price_tl": <sadece 'in' için, opsiyonel — verilmezse 2.000.000 varsayılan>,
      "source_note": "<kısa kaynak notu, örn 'transfermarkt.com - 5M EUR'>"
    }
  ]
}

Kurallar:
- "in" için `team` ve `position` ZORUNLU. `new_price_tl` opsiyonel
  (verilmezse sistem 2.000.000 TL varsayılan atar).
- "out" için mevcut oyuncunun adını veritabanındaki yazımıyla eşleştir.
- "move" için `team` = yeni takım (eski takım sistemde zaten var).
- Emin olmadığın transferi YAZMA — uydurma bilgi verme.
- `new_price_tl` 1.000.000 ile 25.000.000 arasında olmalı (validator
  reddeder).

------------------------------------------------------------------

## ÇALIŞTIRMA

Çıktıyı `transfer_pencere_YYYYMMDD.json` olarak kaydet, sonra:

    # Önce dry-run ile kontrol et:
    python ingest_transfer_window.py oyuncu_veritabani_guncel.xlsx transfer_pencere_YYYYMMDD.json

    # Rapor uygunsa --apply ile uygula:
    python ingest_transfer_window.py oyuncu_veritabani_guncel.xlsx transfer_pencere_YYYYMMDD.json --apply

## İLK ÇALIŞTIRMADA

Script ilk çalıştığında Players sheet'ine `is_active` kolonu otomatik
eklenir (tüm mevcut oyuncular `is_active=1` olarak ayarlanır). Bu
bir-kerelik işlemdir — sonraki çalıştırmalarda kolon zaten var, atlanır.

## ÖNEMLİ KURAL (docs/06)

**Satır SİLİNMEZ.** "out" tipindeki transferler `is_active=0` olarak
işaretlenir ama satır Excel'de kalır — çünkü `GameweekLog` geçmiş
kayıtları `player_id`'ye referans veriyor, satır silinirse geçmiş veri
kırılır ve `calibrate_priors.py` çöker.
