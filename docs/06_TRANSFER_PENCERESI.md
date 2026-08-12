# 06 — Transfer Penceresi (YENİ İHTİYAÇ — henüz kod yok)

Sezonun ikinci yarısında (17. haftadan sonra) kulüpler oyuncu
alıp satacak. `Players` sayfası bunu yansıtmalı.

## KESİN KURAL: satır silme YASAK
`GameweekLog` geçmiş satırları `player_id`'ye referans veriyor.
Bir oyuncuyu `Players`'tan silersen geçmiş veri kırılır ve
`calibrate_priors.py` çöker. Bunun yerine:

## Yöntem: `is_active` bayrağı
1. `Players` sayfasına `is_active` kolonu ekle (varsayılan: 1) —
   `ingest_price_updates.py`'nin `price_tl_current` kolonunu otomatik
   ekleme mantığını AYNEN kopyala (bkz. o dosyadaki `_get_or_create_headers`).
2. Takımdan ayrılan oyuncu: `is_active = 0` — optimizer'ın kullandığı
   `load_players()` bu satırları filtrelesin (MİLP'e hiç girmesin).
3. Yeni transfer olan oyuncu: yeni satır, yeni `player_id`
   (`PLY444` gibi devam eden numaralandırma), `is_active = 1`,
   `last_season_*` alanları YİNE BOŞ BIRAK (uydurma), fiyatı
   `price_tl_current`'a gerçek transfer bedeliyle gir.

## Veri kaynağı
Transfer haberleri için `web_arastirma_prompti.md`'deki JSON şemasına
benzer bir üçüncü prompt yaz (`transfer_prompti.md`) — aynı
kaynak önceliği kuralları (04'teki liste) geçerli.

## Script
`ingest_transfer_window.py` — `ingest_price_updates.py`'nin
yapısını (dry-run/apply, validator, fuzzy match) BİREBİR takip
etsin. Yeni bir desen icat etme.
