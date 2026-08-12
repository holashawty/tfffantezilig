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

---

## Uygulama durumu (12 Ağustos 2026 — yazıldı)

Kod tamamlandı:
- `ingest_transfer_window.py` — `ingest_price_updates.py`'nin
  `_get_or_create_headers` desenini kopyalayarak `is_active` kolonunu
  otomatik ekler (ilk çalıştırmada, tüm mevcut oyuncular `is_active=1`).
- `validator.py`'ye `validate_transfer_window` fonksiyonu eklendi
  (transfer_type, position, new_price_tl doğrulaması).
- `data_loader.py`'nin `load_players()` fonksiyonu `is_active` kolonu
  varsa pasif oyuncuları filtreler (kolon yoksa geriye dönük uyumlu —
  tüm oyuncular aktif kabul edilir).
- `transfer_prompti.md` — web AI için kopyala-yapıştır prompt.

İşlem tipleri:
- `"in"`  → yeni satır, yeni `player_id` (`PLY444`, `PLY445`... devam eder)
- `"out"` → `is_active=0` (satır SİLİNMEZ)
- `"move"` → `team` alanı güncellenir

Test edildi (geçici Excel kopyası ile):
- Yeni oyuncu ekleme (PLY444, PLY445 sıralı ID'lerle)
- Pasifleştirme (is_active 1→0)
- Takım değişikliği (move)
- Validasyon reddi (aralık dışı fiyat, boş isim, geçersiz pozisyon)
- `data_loader.py`'nin pasif oyuncuyu MILP'ten filtrelemesi

Kullanım:
```
python ingest_transfer_window.py oyuncu_veritabani_guncel.xlsx transfer_pencere_YYYYMMDD.json
# dry-run raporu uygunsa:
python ingest_transfer_window.py oyuncu_veritabani_guncel.xlsx transfer_pencere_YYYYMMDD.json --apply
```
