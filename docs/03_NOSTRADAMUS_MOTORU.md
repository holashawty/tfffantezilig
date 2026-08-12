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
