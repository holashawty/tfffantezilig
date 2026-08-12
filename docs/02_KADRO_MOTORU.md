# 02 — Kadro Motoru (ZATEN YAZILDI VE TEST EDİLDİ — ÜZERİNE İNŞA ET)

Bu bölüm için sıfırdan kod yazmaya BAŞLAMA. Aşağıdaki dosyalar repo
kökünde zaten var, çalışıyor, gerçek veriyle test edildi:

| Dosya | Ne yapar |
|---|---|
| `data_loader.py` | Excel şemasını okur, resmi kural sabitleri burada |
| `xp_model.py` | xP hesabı: fiyat-tabanlı soğuk-başlangıç önseli + Bayesian shrinkage |
| `optimizer.py` | MİLP kadro çözücü (`scipy.optimize.milp`, HiGHS solver) |
| `calibrate_priors.py` | PRIOR_CONFIG'i gerçek veriyle KOD-TABANLI (LLM değil) yeniden tahmin eder |
| `validator.py` | Her veri girişini kabul etmeden önce doğrular |
| `run_gameweek.py` | Ana çalıştırma script'i |
| `update_week.py` | Haftalık tüm adımları zincirleyen orkestratör |

## xP formülü (özet — detay `xp_model.py` içinde, kod yorum satırları
zaten açıklıyor)
```
xP = [appearance + goal_pts + assist_pts + clean_sheet_pts
      + save_pts + conceded_penalty + card_penalty] × play_probability
```
Soğuk başlangıç: `xp_prior` (fiyat yüzdelik dilimine dayalı).
Gerçek veri birikince: `xp_blended = w(n)*gerçek_ortalama + (1-w(n))*xp_prior`,
`w(n) = n/(n+K)`, K=4. Bu zaten kodda var, DOKUNMA — sadece
`PRIOR_CONFIG` katsayıları `calibrate_priors.py` ile zamanla
otomatik iyileşiyor.

## Neden LLM'e "en iyi kadroyu seç" dedirtilmiyor
443 oyuncu arasından kesin kısıtlı (bütçe/mevki/kulüp) bir optimizasyon
problemi — bu MİLP'in çözdüğü klasik bir problem, matematiksel garantili
tek doğru cevabı var. LLM'e sordurmak hem yavaş hem kısıtları
garanti etmez. Bu ilkeye SADIK KAL.

## Senin (agent) yapman gereken tek şey burada
1. `06_TRANSFER_PENCERESI.md`'deki oyuncu ekleme/çıkarma mekanizmasını kur.
2. Sezon ilerledikçe `calibrate_priors.py`'nin gerçekten doğru
   çalıştığını (aşırı uydurma / overfitting yapmadığını) haftalık
   kontrol et — `--min-players` ve `--min-games` eşiklerini gerekirse
   ayarla, ama KENDİ BAŞINA yeni bir kalibrasyon yöntemi icat etme.
3. Kaptan seçim mantığını (`optimizer.py` içindeki `captain_score`,
   xP + tavan ağırlığı) gerçek veri birikince gözden geçir — CEILING_WEIGHT
   sabiti kod başında, ayarlanabilir.
