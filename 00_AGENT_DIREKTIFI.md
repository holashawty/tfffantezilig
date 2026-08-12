# TFF Fantezi Lig Otonom Sistemi — Agent Direktifi

Bu belge sana (Agent) doğrudan hitap eder. Talimattır, öneri değildir.
Repoyu (`holashawty/tfffantezilig`) incele, `tff_fantasy/` klasöründeki
mevcut kodu (data_loader.py, xp_model.py, optimizer.py, validator.py,
calibrate_priors.py, ingest_*.py, update_week.py, *.md promptlar) BAŞTAN
YAZMA — üzerine inşa et. Bu kod gerçek veriyle test edildi, çalışıyor.

---

## 1. Vizyon ve Deney Sorusu

Bu bir deney projesi. Soru: veri + matematik + sınırlı yorumlama gücü,
1 sezon boyunca insan sezgisinden daha iyi kadro kurup maç tahmin
edebilir mi? Cevap 1 sezon sürecek, sabırsızlanıp kısayol arama.

**Felsefe (tartışmaya kapalı):** Oyunu matematik ve veri oynar, AI
oynamaz. AI'nin rolü aşağıda 2. maddede KESİN olarak tanımlanmıştır —
bunun dışına çıkma.

## 2. AI'nin rolü — kesin sınır

AI (Gemini free tier veya web AI chat) SADECE şunları yapar:
1. **Nitel web araştırması**: sakatlık/ceza/fiyat/maç sonucu verisini
   JSON'a çevirir (mevcut `web_arastirma_prompti.md`,
   `match_sonuclari_prompti.md`, `fiyat_guncelleme_prompti.md`
   desenini kullan — bunlar zaten var, kopyalama).
2. **Açıklama üretimi**: MILP+xP motorunun ürettiği kadroyu/Nostradamus
   tahminini insan-okunur bir gerekçeye çevirir ("bu 15 kişi seçildi
   çünkü X, kaptan Y çünkü Z"). Operatör bunu okuyup uygulamaya
   kendisi girer.
3. **Anomali işaretleme**: kaynak veride bariz bir tutarsızlık varsa
   (örn. cezalı bir oyuncu optimizasyona dahil olmuş) bunu operatöre
   BİLDİRİR. Hiçbir zaman kendisi düzeltmez, hiçbir zaman matematiğin
   kararını değiştirmez, veto etmez, "onaylamaz."

AI'ye "son karar mercisi", "onay katmanı" gibi yetkiler VERME. Bu,
projenin bütün amacını (tarafsız matematiksel karar) baltalar.

## 3. Kadro Motoru — mevcut, çalışıyor, geliştir

`xp_model.py` + `optimizer.py` zaten şunu yapıyor, DOKUNMA:
- xP = fiyat-tabanlı soğuk-başlangıç önseli + Bayesian shrinkage
  (`w(n) = n/(n+K)`, gerçek veri arttıkça devreye girer)
- MILP (scipy/HiGHS): 100M TL, 15 oyuncu (2K-5D-5O-3F), takım başı
  max 3, ilk 11 kısıtları — resmi kurallardan doğrulandı
- `calibrate_priors.py`: PRIOR_CONFIG katsayılarını gerçek
  GameweekLog verisiyle KOD ile (regresyon) yeniden tahmin eder —
  bunu LLM'e YAPTIRMA, istatistik işi.

**Senin görevin burada:** eksik olan **transfer penceresi** mekanizması.
17. haftadan sonra yeni transferler girer/çıkar. Yapılacak:
- `Players` sheet'ine `is_active` (bool) kolonu ekle. Oyuncu SİLİNMEZ
  (GameweekLog geçmiş referansları kırılır), pasife alınır.
- Yeni oyuncu eklerken `player_id` sırası bozulmasın, yeni ID'ler
  sondan devam etsin (PLY444, PLY445...).
- Bu işlem de diğerleri gibi dry-run/`--apply` + `validator.py`
  desenini kullanmalı — mevcut `ingest_price_updates.py`'nin kolon
  ekleme mantığına bak, aynı deseni tekrar et.

## 4. Nostradamus Motoru — matematik mimarisi

**ÖNCE DOĞRULA:** TFF'nin Nostradamus'u tam olarak ne istiyor —
sadece 1-X-2 mi, yoksa kesin skor da mı? Play Store açıklaması
"skor veya sonuç tahmini" diyor, oyun içi rehber sadece "maç sonucu"
diyordu — bu iki kaynak çelişiyor, gerçek oyun ekranından TEYİT ET.
Bu, Dixon-Coles'un zorunlu mu opsiyonel mi olduğunu belirler.

### 4.1 Öncelik — mevcut veritabanını denetle
Kullanıcının zaten 5 sezonluk oran+skor verisi olan bir bahis/tahmin
uygulaması var. **İlk iş bu DB'yi denetlemek**, football-data.co.uk
gibi kaynaklar SADECE boşluk doldurmak için (eksik sezon/lig/oran
sütunu). Sıfırdan DB kurma.

### 4.2 Üç bağımsız sinyal, ensemble
```
Sinyal 1: Piyasa (oran-implied olasılık)
  - Varsayılan: p_i = π_i / Σπ_j  (π_i = 1/oran_i) — basit, güvenli
  - Daha iyi: Shin's method — kafadan formül YAZMA, PyPI `shin`
    paketini kullan (test edilmiş, doğru)
  - Birden fazla bahisçi varsa medyan al, kapanış oranını tercih et

Sinyal 2: Dixon-Coles/Poisson (varsa, skor tahmini gerekiyorsa)
  - Kafadan MLE türetme, `penaltyblog` gibi hazır paket kullan
  - Takım hücum/savunma gücü, ev sahibi avantajı parametreleri

Sinyal 3: Elo (kullanıcının istediği, sabit/kalıcı sistem)
  - Standart futbol Elo güncelleme kuralı: her maç sonrası
    kazanan/kaybeden puanları, beklenen sonuca göre ölçeklenerek
    güncellenir (K-faktörü ayarlanabilir sabit)
  - Elo'dan maç sonucu olasılığına çevirme: standart lojistik
    dönüşüm (ör. 1/(1+10^(-Elo_farkı/400)))

Nihai karar: üç sinyalin ağırlıklı ortalaması veya çoğunluk oyu.
argmax(p_1, p_X, p_2) — Kelly kriteri, portföy teorisi, kontrarian
oynama EKLEME, buranın puanlaması buna ihtiyaç duymuyor (her doğru
tahmin = sabit puan, bahis değil).
```

### 4.3 Kalibrasyon — kod, LLM değil
Rolling Brier score / log-loss takibi + periyodik isotonic/Platt
regression (kod ile). LLM'in maç-sonrası öz-eleştiri metni bir
insan-okunur günlük olarak saklanır ama OTOMATİK kural haline
GETİRİLMEZ — n=1'den kural çıkarmak istatistiksel olarak çürük.

### 4.4 Test — bu gerçekten şimdi yapılabilir
Kadro motorunun aksine (gerçek sezon beklemek zorunda), Nostradamus
geçmiş sezonlarla **şimdi backtest edilebilir**. Piyasa-devig-only
modelin Brier score'unu geçmiş 2-3 sezonda ölç, bunu baseline yap.
Poisson/Elo eklenince skor İYİLEŞMİYORSA o katmanı ekleme.

## 5. Veri Kaynağı Doğrulama Görevleri

Tek sayfada, iki ayrı liste tut (`04_VERI_KAYNAKLARI.md`):
- **Puan/maaş kaynağı listesi**: tfffantezilig.com öncelik, resmi
  fiyatlar sadece oyunun kendi arayüzünde (dinamik ekonomi, dışarıda
  yayınlanmaz) — bkz. `fiyat_guncelleme_prompti.md`.
- **Sakatlık/kart kaynağı listesi**: tff.org'un Cezalar sayfası
  cezalar için güvenilir (TFF'nin kendi idari kararı). Sakatlık
  MERKEZİ DEĞİL — kulüp açıklamaları/spor basınından derlenir, tek
  kaynak yokmuş gibi davranma.
- Her kaynağı ekleme/değiştirme öncesi gerçekten erişilebilir mi,
  güncel sezon (2026-2027) verisi var mı TEST ET, varsayma.

## 6. `docs/` Klasörü — bu belgeyi böl

Bu belgeyi aşağıdaki dosyalara böl, her birine ilgili bölümü taşı,
madde 3 ve 4'teki teknik detayı SEYRELTME:

| Dosya | Kaynak bölüm |
|---|---|
| `01_VIZYON.md` | Bölüm 1 |
| `02_OYUN_KURALLARI.md` | Bu sohbette doğrulanan resmi kurallar (100M, 15 oyuncu, 2-5-5-3, kaptan 2x, resmi puanlama tablosu) |
| `03_KADRO_MOTORU.md` | Bölüm 3 + `xp_model.py`/`optimizer.py` referansı |
| `04_NOSTRADAMUS_MOTORU.md` | Bölüm 4 |
| `05_VERI_KAYNAKLARI.md` | Bölüm 5 |
| `06_CALISMA_PRENSIBI.md` | `update_week.py` akışı, dry-run/apply deseni, `.bat` menü |
| `07_AI_ROLU_VE_SINIRLARI.md` | Bölüm 2 |
| `08_GELISTIRME_GUNLUGU.md` | Her değişiklikte tek satır: tarih, ne yapıldı, ne test edildi. Toplu yaz, tek tek değil. |

## 7. İlk 5 Adım (sırayla)
```
1. Mevcut bahis/tahmin DB'sini denetle (şema+kapsam+kalite raporu)
2. Nostradamus'un skor mu sonuç mu istediğini oyundan teyit et
3. Devig-only baseline'ı geçmiş sezonlarla backtest et (Brier score)
4. is_active/transfer penceresi mekanizmasını mevcut validator
   desenine uyumlu şekilde ekle
5. Bu belgeyi docs/ altında 8 dosyaya böl, 08'i her adımda güncelle
```
