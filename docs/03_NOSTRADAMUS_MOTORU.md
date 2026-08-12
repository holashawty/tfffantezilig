# 03 — Nostradamus Tahmin Motoru (YAPILACAK — henüz kod yok)

## Adım 0 — ZORUNLU, ATLAMA
Proje sahibinin **zaten 5 sezonluk oran+skor verisi olan bir bahis/
tahmin uygulaması var.** Bunu ilk iş olarak denetle (şema, veri
kalitesi, kapsam, hangi ligler/sezonlar). football-data.co.uk / Kaggle
gibi kaynaklar SADECE bu mevcut veritabanındaki BOŞLUKLARI doldurmak
için kullanılır — sıfırdan yeni bir DB kurup mevcut projeyi çöpe atma.

## Mimari
```
[Bahis oranları (çoklu bahisçi varsa medyan)]
        → devig (marj temizleme)  → p_market(1,X,2)
[Geçmiş gol verisi + opsiyonel ClubElo]
        → Poisson/Dixon-Coles     → p_model(1,X,2)   [İKİNCİL, opsiyonel]
[LLM web araştırması — SADECE oranlar sabitlendikten SONRAKİ haberler]
        → sınırlı (±0.10 max) düzeltme, validator'dan geçer
→ nihai p(1,X,2) → argmax → tahmin
```

## Devig (oran arındırma)
- **Varsayılan/güvenli:** oransal yöntem — `p_i = (1/oran_i) / Σ(1/oran_j)`.
  Basit, her zaman doğru, hemen kodla.
- **Daha iyi (favori-uzun-oran yanlılığı düzeltir):** Shin's method.
  **Formülü ezberden yazma** — Python `shin` paketini kullan (pip
  install shin) ya da kaynağını (Shin 1992/93) doğrulayarak kodla.
  Kafadan türetilen formül risklidir.
- Birden fazla bahisçi kolonu varsa (football-data.co.uk'de B365, PS,
  WH gibi) ortalama/medyanını al, tek kaynağa güvenme.
- Mümkünse KAPANIŞ oranını kullan (maça yakın), açılıştan daha
  bilgi-verimlidir.

## Poisson/Dixon-Coles (opsiyonel, zorunlu değil)
Nostradamus sadece 1-X-2 istiyor, kesin skor değil (bkz. 01) — bu
katman sadece piyasa tahminini çapraz kontrol etmek için var.
Kendi MLE türetmene gerek yok — `penaltyblog` gibi hazır, test
edilmiş bir Dixon-Coles implementasyonu kullan.

## Karar kuralı — BASİT TUTULMALI
Puanlama her doğru tahmine sabit +1 verdiği için (Kelly kriteri,
bankroll optimizasyonu YOK, çünkü gerçek para bahsi değil) optimum
strateji trivial: **her maç için en yüksek olasılıklı sonucu seç
(argmax).** Kontrarian oynama, portföy teorisi EKLEME — gereksiz.

## Kalibrasyon — kod-tabanlı, LLM'in "tek maçtan kural çıkarması" YASAK
- Rolling Brier score / log-loss'u KOD ile takip et (haftalık).
- Periyodik (15-20 maçta bir) isotonic regression / Platt scaling ile
  olasılıkları yeniden kalibre et — `calibrate_priors.py`'deki
  felsefeyle birebir aynı: istatistik kod yapar, LLM yapmaz.
- LLM'in maç-sonrası öz-eleştiri metnini bir GÜNLÜK olarak sakla
  (insan okusun) ama OTOMATİK KURAL haline getirip sisteme enjekte
  ETME — n=1'den kural çıkarmak overfitting'dir.

## Test stratejisi — burası kadro motorundan farklı, GERÇEKTEN test edilebilir
Geçmiş sezonların sonucu zaten biliniyor. İlk iş:
1. Devig-only modelin son 2-3 sezon üzerindeki Brier score'unu ölç.
2. Bunu baseline olarak sabitle.
3. Poisson/ELO/LLM katmanları eklendikçe bu skor iyileşiyor mu kontrol
   et — iyileşmiyorsa o katmanı EKLEME, gereksiz karmaşıklık.

---

## Adım 0 ÇIKTISI — Veri Denetim Raporu (12 Ağustos 2026)

### Kaynak
- **Kaynak dosya:** `unified.db` (OuziBet masaüstü uygulamasından, 94.68 MB)
- **Hedef dosya:** `nostradamus/superlig_odds.db` (4.38 MB — %95.4 küçülme)
- **Aktarım script'i:** `nostradamus/build_superlig_db.py` (idempotent, tekrar üretilebilir)
- **Filtre:** `league_id = 17` (Süper Lig / Turkey / tier 1)

### Aktarılan tablolar (sadece league_id=17 satırları)
| Tablo | Satır sayısı | Not |
|---|---:|---|
| `matches` | 2.782 | 8 sezon, 2018-08-10 → 2026-05-17 |
| `odds` | 60.849 | 3 bahisçi × 3 market × açılış/kapanış |
| `teams` | 33 | sadece Süper Lig'de oynamış takımlar |
| `team_aliases` | 33 | her takım için 1 alias (football-data kaynaklı) |
| `xg_stats` | 0 | **kaynakta Süper Lig için boş** — beklenen, ileride FBref doldurabilir |
| `meta` | 8 | build meta verisi (tarih, kaynak, not) |

### Bilerek ALINMAYAN tablolar (docs/00 ve docs/08 ilkesi)
- `copula_models`, `transfer_models`, `player_injuries`,
  `sharp_money_signals` — **hepsi kaynakta boş**, yani hiç üretime
  alınmamış deneylerdi. Getirilmedi.
- `OuziBet/core/` ML pipeline'ı (~18.000 satır torch/GNN/Transformer/RL)
  referans bile alınmadı — proje felsefesiyle (basit, kod=matematik
  karar verir) çelişiyor.

### Sezon kronolojisi (kaynak DB'nin sezon etiketleri kronolojik DEĞİL)
| Kaynak etiket | Gerçek sezon | Maç sayısı | Tarih aralığı |
|---|---|---:|---|
| T1 (10) | 2018-19 | 306 | 2018-08-10 → 2019-05-26 |
| T1 (9)  | 2019-20 | 306 | 2019-08-16 → 2020-07-26 (Covid uzaması) |
| T1 (5)  | 2020-21 | 420 | 2020-09-11 → 2021-05-15 |
| T1 (4)  | 2021-22 | 380 | 2021-08-13 → 2022-05-22 |
| T1 (3)  | 2022-23 | 342 | 2022-08-05 → 2023-06-07 |
| T1 (2)  | 2023-24 | 380 | 2023-08-11 → 2024-05-26 |
| T1 (1)  | 2024-25 | 342 | 2024-08-09 → 2025-06-01 |
| T1 (11) | 2025-26 | 306 | 2025-08-08 → 2026-05-17 |

**UYARI:** Backtest script'leri sezon etiketine değil `match_date`
yılına göre sıralamalı — etiketler takvim sırasını yansıtmıyor.

### Veri kalitesi
- **Gol NULL oranı:** 0/2782 = %0.00 (mükemmel)
- **1X2 oranı olan maç oranı:** 2753/2782 = %99.0
- **Kapanış 1X2 oranı olan maç oranı:** 2753/2782 = %99.0
  (docs/03'ün "kapanışı tercih et" kuralı için yeterli kapsam)
- **Eksik 3'lü (H/D/A'dan biri yok):** 0 maç (her 1X2 satırı tam)
- **Bahisçi başına kapanış 1X2 maç sayısı:** PS 2581, B365 2447
  (ikisi birden varsa medyan al — docs/03 kuralı)

### Backtest havuzu (son 3 sezon, kronolojik olarak)
- **2023-24 (T1 (2)):** 380 maç, 380 kapanış 1X2 (%100)
- **2024-25 (T1 (1)):** 342 maç, 342 kapanış 1X2 (%100)
- **2025-26 (T1 (11)):** 306 maç, 306 kapanış 1X2 (%100)
- **Toplam:** 1.028 maç, hepsi tam kapanış oranına ve sonuca sahip

### Market dağılımı (Süper Lig alt kümesi)
| Bahisçi | Market | Açılış | Kapanış | Toplam |
|---|---|---:|---:|---:|
| B365 | 1X2 | 8.229 | 7.341 | 15.570 |
| B365 | AH | 4.830 | 4.888 | 9.718 |
| PS | 1X2 | 7.716 | 7.743 | 15.459 |
| PS | AH | 4.540 | 4.550 | 9.090 |
| Piyasa | OU_2.5 | 1.224 | 9.788 | 11.012 |
| **Toplam** | | **26.539** | **34.310** | **60.849** |

**Not:** "Piyasa" bahisçisinin sadece OU_2.5 (Alt/Üst 2.5 gol) marketi
var — 1X2 yok. Bu yüzden devig baseline backtest'i B365 + PS ortalaması
üzerinden yürüyecek (docs/03'ün "çoklu bahisçi varsa medyan al" kuralı).

