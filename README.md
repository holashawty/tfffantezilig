# TFF Fantezi Lig — Otonom Kadro & Nostradamus Sistemi

**Agent/LLM: önce `docs/00_HEDEF_VE_VIZYON.md` dosyasını oku, sonra
sırayla `docs/01`...`docs/08`.** Bu proje sıfırdan başlamıyor —
kadro motoru (xP + MİLP) yazılmış ve gerçek veriyle test edilmiş
durumda. Sıfırdan yazmaya başlamadan önce mutlaka `docs/` klasörünü
oku, aksi halde zaten çözülmüş sorunları (soğuk başlangıç problemi,
kısıt ihlalleri, veri doğrulama) tekrar çözmeye çalışırsın.

## Klasör yapısı
```
docs/                          -> BURADAN BAŞLA (00-08 sırayla)
data_loader.py                 -> Excel okuma/şema
xp_model.py                    -> xP hesaplama (fiyat-önseli + shrinkage)
optimizer.py                   -> MİLP kadro çözücü
calibrate_priors.py            -> kod-tabanlı katsayı kalibrasyonu
validator.py                   -> tüm veri girişleri için ortak doğrulayıcı
run_gameweek.py                -> tek haftalık kadro çalıştırma
update_week.py                 -> tüm haftalık akışı zincirleyen orkestratör
update_from_web_research.py    -> sakatlık/ceza -> play_probability
ingest_gameweek_results.py     -> maç sonrası gerçek performans
ingest_price_updates.py        -> haftalık fiyat güncelleme
*_prompti.md                   -> web AI'ya kopyala-yapıştır promptları
oyuncu_veritabani_guncel.xlsx  -> güncel veri (Players/GameweekLog/Fixtures)
gw1_kadro_onerisi.xlsx         -> ilk hafta için üretilmiş örnek çıktı
```

## Henüz yazılmamış (docs/'ta spesifikasyonu var)
- Nostradamus tahmin motoru (`docs/03`)
- Transfer penceresi mekanizması (`docs/06`)
- `.bat` menü sistemi (`docs/05`)

## Değiştirilemez ilkeler (kısa özet, detay `docs/00` ve `docs/08`)
1. Matematik/kod karar verir, LLM asla onaylamaz/veto etmez.
2. Her veri girişi: doğrula → dry-run göster → `--apply` ile yaz.
3. İstatistiksel kalibrasyon kod ile yapılır, LLM'e "tahmin ettir" denmez.
