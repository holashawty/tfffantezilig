# 07 — Geliştirme Günlüğü (canlı belge — HER oturumda güncelle)

Format: her girişte tarih, ne yapıldı, ne araştırıldı, ne KARARLAŞTIRILDI
(ve neden), sıradaki adım. Agent her oturum sonunda buraya YENİ bir
madde EKLESİN, öncekileri SİLMESİN.

---

## 12 Ağustos 2026 — Kurulum oturumu (Claude ile)
**Yapıldı:**
- Excel şeması Players/GameweekLog/Fixtures olarak yeniden kuruldu
  (orijinal 444 satırlık hatalı "GENEL TOPLAM" satırı temizlendi → 443 gerçek oyuncu)
- Resmi kurallar ve puanlama tablosu tfffantezilig.com/yardim'den doğrulandı
- Kadro motoru yazıldı ve gerçek veriyle test edildi: `data_loader.py`,
  `xp_model.py` (fiyat-önseli + Bayesian shrinkage), `optimizer.py`
  (scipy.optimize.milp/HiGHS — PuLP kurulamadı, ağ kapalıydı)
- Web-araştırma köprüsü kuruldu: `web_arastirma_prompti.md` +
  `update_from_web_research.py` (dry-run/apply + isim eşleştirme)
- Faz 2 kuruldu: `ingest_gameweek_results.py`, `calibrate_priors.py`
  (kod-tabanlı, LLM'siz kalibrasyon), `update_week.py` orkestratörü
- `validator.py` yazıldı, 3 ingest script'ine entegre edildi
- Fiyat mekanizması kuruldu: `price_tl_current` (Players'ta canlı
  alan), `ingest_price_updates.py`, `fiyat_guncelleme_prompti.md`
- 2 sentetik hafta ile uçtan uca pipeline test edildi (gerçek maç
  verisi YOK, sadece kod plumbing testi — gerçek isabet testi
  14 Ağustos'tan önce YAPILAMAZ, bu bilinçli bir sınır)
- Gemini'nin iki ayrı README/mimari önerisi incelendi, kritik
  hatalar bulundu (xP formülü soğuk-başlangıç sorununu görmüyor,
  LLM'e "son karar" yetkisi veriyor, veritabanı şeması oranları
  unutuyor) — REDDEDİLDİ, yerine bu `docs/` yapısı kuruldu

**Kararlaştırıldı (ve neden):**
- AI hiçbir zaman kadro/tahmin kararını onaylamaz/veto etmez —
  sadece açıklar + sınırlı araştırma yapar (bkz. `08_LLM_ROLU_VE_SINIRLAR.md`)
- SQLite'a geçiş ŞİMDİLİK yok — mevcut Excel pipeline yeterli ve test edildi
- Nostradamus'a BAŞLANMADI (kullanıcı talebiyle) — sadece plan yazıldı

**Sıradaki adım:** `06_TRANSFER_PENCERESI.md` ve `03_NOSTRADAMUS_MOTORU.md`'nin
kodlanması (Adım 0: mevcut bahis-app veritabanının denetimi ile başla).

---

## 12 Ağustos 2026 (oturum 2) — Nostradamus Adım 0+2: veri entegrasyonu + devig baseline

**Yapıldı:**
- `unified.db` (94.68 MB) içinden SADECE `league_id=17` (Süper Lig) satırları
  yeni `nostradamus/superlig_odds.db` (4.38 MB) dosyasına aktarıldı.
  Aktarım script'i: `nostradamus/build_superlig_db.py` (idempotent).
  Şema: matches(2782), odds(60849), teams(33), team_aliases(33),
  xg_stats(0 — kaynakta da boş), meta(8).
- Bilerek ALINMAYAN tablolar: `copula_models`, `transfer_models`,
  `player_injuries`, `sharp_money_signals` (hepsi kaynakta boş, hiç
  üretime alınmamış deneyler) + `OuziBet/core/` ML pipeline'ı
  (~18.000 satır torch/GNN/Transformer/RL — docs/00, docs/08 ilkesine aykırı).
- `docs/03`'e "Adım 0 ÇIKTISI — Veri Denetim Raporu" bölümü eklendi:
  sezon kronolojisi (etiketler takvim sırasını yansıtmıyor — T1(10)=2018-19,
  T1(11)=2025-26), veri kalitesi (gol NULL %0, kapanış 1X2 %99), market
  dağılımı tablosu.
- Devig-only baseline backtest yazıldı: `nostradamus/backtest_devig_baseline.py`.
  Shin's method (`shin` paketi — kafadan formül YAZILMADI), çoklu bahisçi
  medyanı (B365+PS), 3-sınıf Brier score.

**Araştırıldı (kaynak + sonuç):**
- Shin paketinin API'si: `calculate_implied_probabilities([o1, o2, o3])`
  → [p1, p2, p3]. Eski `shin_method` adı yok, silinmiş.
- Sezon etiketleri kronolojik DEĞİL: kaynak DB `T1 (1)`...`T1 (11)`
  etiketlerini rastgele dağıtmış. Backtest script'leri `match_date`
  yılına göre sıralamalı (denetim raporunda UYARI olarak not edildi).
- xg_stats tablosu kaynakta Süper Lig için tamamen boş — Poisson
  katmanı için FBref'den ayrıca toplanması gerek (Adım 3'te değerlendirilecek).

**Kararlaştırıldı (ve neden):**
- Devig baseline Brier = **0.5557** (1028 maç, 3 sezon: 2023-24, 2024-25, 2025-26).
  - Per-sezon: 2023-24 → 0.5555, 2024-25 → 0.5365, 2025-26 → 0.5774
  - İsabet: %57.2 (argmax tahmini doğru)
  - Uniform rastgele baseline (0.6667)'ye göre %16.7 iyileşme
  - 0 fallback (Shin her maçta başarılı — oransal yöntem devreye girmedi)
- Bu sabit baseline olarak KABUL EDİLDİ — sonraki katmanlar (Poisson/Elo)
  buna kıyasla değerlendirilecek, iyileşme yoksa eklenmeyecek (docs/03 kuralı).
- "Piyasa" bahisçisi sadece OU_2.5 market'ine sahip, 1X2 yok — devig
  baseline'ına katkısı yok, B365+PS medyanı kullanıldı.

**Sıradaki adım:** Poisson (Dixon-Coles via `penaltyblog`) + Elo (ClubElo via
`soccerdata`) katmanlarını dene — Brier 0.5557'nin altına düşmezse EKLEME
(docs/03 kuralı). Sonra `06_TRANSFER_PENCERESI.md` kodlanacak.

---

## 12 Ağustos 2026 (oturum 2, devam) — Nostradamus Adım 3: Poisson/Elo katman denemesi → EKLENMİYOR

**Yapıldı:**
- `penaltyblog` (DixonColesGoalModel) ve `soccerdata` (ClubElo) paketleri kuruldu.
- ClubElo cacheFetcher (`fetch_clubelo_cache.py`) ile 26/33 takımın ClubElo
  derece geçmişi `cache/clubelo_history.csv`'ye indirildi (39.448 satır).
- 7 takım ClubElo'da yok (Akhisar, Ankaragucu, Basaksehir/Buyuksehyr,
  Erzurum BB, Goztep, Karagumruk, Yeni Malatyaspor) — bunlardan 4'ü
  (Basaksehir, Ankaragucu, Goztep, Karagumruk) backtest penceresinde.
  Backtest maçlarının %73.3'ünde (754/1028) her iki takımın ClubElo verisi var.
- Dixon-Coles modeli her sezon başında, o sezonun ilk maç tarihinden ÖNCE
  oynanmış tüm maçlarla fit edildi (look-ahead bias yok).
- 10 varyant test edildi (`backtest_poisson_elo.py`):
  - B (devig+Elo, ağırlık 0.3/0.5/0.7)
  - C (devig+Poisson, ağırlık 0.3/0.5/0.7)
  - D (devig+Elo+Poisson, çeşitli kombinasyonlar)

**Araştırıldı (kaynak + sonuç):**
- ClubElo'nun takım adı eşleştirmesi: 7 takım için API yanlış isimle çağrılınca
  38 byte'lık boş CSV döndürüyor (sadece header). Doğru isimler deneme-yanılma
  ile bulundu (ör. "Ad. Demirspor" → "Adana Demirspor", "Kayserispor" → "Kayseri",
  "Rizespor" → "Rizespor", "Bodrumspor" → "Bodrum"). 4 takım hâlâ ClubElo'da yok.
- penaltyblog'un `DixonColesGoalModel.predict()` metodu `FootballProbabilityGrid`
  döndürüyor — `pred.home_draw_away` ile [p_H, p_D, p_A] listesi alınabiliyor.
- penaltyblog'un `Elo.calculate_match_probabilities()` metodu dict
  `{'home_win': ..., 'draw': ..., 'away_win': ...}` döndürüyor — ama biz
  ClubElo'yu tercih ettik (docs/01'in önerdiği kaynak).

**Kararlaştırıldı (ve neden):**
- **EKLENMİYOR.** Hiçbir varyant baseline'ı (Brier 0.5557) geçemedi:
  | Varyant | Brier | Δ Baseline | Karar |
  |---|---:|---:|---|
  | A) devig-only (baseline) | 0.5557 | — | sabit baseline |
  | B) devig+Elo @0.3 | 0.5667 | +0.0110 | EKLEME |
  | B) devig+Elo @0.5 | 0.5803 | +0.0246 | EKLEME |
  | B) devig+Elo @0.7 | 0.5989 | +0.0432 | EKLEME |
  | C) devig+Poisson @0.3 | 0.5616 | +0.0059 | EKLEME |
  | C) devig+Poisson @0.5 | 0.5686 | +0.0129 | EKLEME |
  | C) devig+Poisson @0.7 | 0.5779 | +0.0222 | EKLEME |
  | D) devig+Elo+Poiss @0.3 | 0.5769 | +0.0212 | EKLEME |
  | D) devig+Elo+Poiss @0.34 | 0.5810 | +0.0253 | EKLEME |
  | D) Poisson+Elo @0.5 (devig'siz) | 0.6215 | +0.0658 | EKLEME |

  docs/03'ün "iyileşmiyorsa EKLEME" kuralı devreye girer. **Sonuç:**
  Nostradamus motoru **devig-only** olarak kalır — Shin's method + B365/PS
  kapanış 1X2 medyanı. Bu, projenin ana tezinin (bahis piyasası zaten tüm
  kamuoyu bilgisini fiyatlıyor, ek sinyal gürültü ekler) doğrulanmasıdır.

- Backtest script'leri (`backtest_devig_baseline.py`,
  `backtest_poisson_elo.py`, `fetch_clubelo_cache.py`) repoda TUTULUR —
  ileride yeni sezon verisi eklendiğinde veya piyasa verimi değiştiğinde
  yeniden değerlendirme yapmak için. Ama üretim motoru bunları kullanmaz.

**Sıradaki adım:** `06_TRANSFER_PENCERESI.md`'nin kodlanması —
`ingest_price_updates.py` desenini kopyalayarak `ingest_transfer_window.py`
ve `is_active` kolonu.

---

## 12 Ağustos 2026 (oturum 2, devam 2) — Transfer penceresi mekanizması kodlandı

**Yapıldı:**
- `ingest_transfer_window.py` yazıldı — `ingest_price_updates.py`'nin
  `_get_or_create_headers` desenini birebir kopyalayarak `is_active`
  kolonunu otomatik ekler. 3 işlem tipi: `in` (yeni oyuncu), `out`
  (pasifleştir), `move` (takım değiştir).
- `validator.py`'ye `validate_transfer_window` fonksiyonu eklendi —
  transfer_type, position, new_price_tl zorunlu alan/aralık kontrolü.
- `data_loader.py`'nin `load_players()` fonksiyonuna `is_active` filtresi
  eklendi (kolon yoksa geriye dönük uyumlu — eski Excel dosyaları
  çalışmaya devam ediyor, kadro motoru DOKUNULMADI).
- `transfer_prompti.md` yazıldı — `web_arastirma_prompti.md` ve
  `fiyat_guncelleme_prompti.md` ile aynı formatta, web AI kopyala-yapıştır
  promptu. Transfermarkt öncelikli kaynak.

**Araştırıldı (kaynak + sonuç):**
- `ingest_price_updates.py`'nin `_get_or_create_headers` deseni:
  header satırını bulur, `is_active` yoksa son kolona ekler, tüm mevcut
  satırlar için varsayılan değer (1) yazar — birebir kopyalandı.
- Yeni player_id üretiminde bug bulundu ve düzeltildi: `_next_player_id`
  tek çağrıda max+1 veriyor, birden çok "in" transferinde aynı ID'yi
  veriyordu. Çözüm: `next_id_counter` ile her "in" için artan offset.
- `ws.max_row + 1` yerine gerçek son dolu satırı bulan döngü kullanıldı
  (openpyxl bazen None dolu "hayalet" satırları sayıyor).

**Kararlaştırıldı (ve neden):**
- 3 işlem tipi (`in`/`out`/`move`) yeterli — `reactivate` ayrı tip
  olarak eklenmedi, çünkü "pasif oyuncunun geri dönüşü" nadir bir durum
  ve uyarı mesajı operatöre manuel müdahaleyi işaret ediyor (docs/06'nın
  "satır silinmez" kuralıyla uyumlu).
- `last_season_*` alanları yeni oyuncular için BOŞ bırakıldı (uydurma
  veri yazılmadı) — docs/06'nın "uydurma değer girme" kuralıyla uyumlu.
  `xp_model.py`'nin soğuk-başlangıç önseli bu boşlukları fiyat-tabanlı
  prior'la dolduruyor.

**Test sonuçları:**
- Orijinal Excel'de (is_active yok): optimizer 443 oyuncuyla çalıştı,
  geriye dönük uyumlu.
- Test Excel'inde (1 oyuncu is_active=0): "1 pasif oyuncu filtrelendi,
  MILP'e 444 aktif oyuncu giriyor" mesajı, optimizer çalıştı.
- Dry-run modu: 2 yeni oyuncu, 2 red (validasyon), 2 eşleşmeyen isim
  raporlandı. --apply modu: 2 yeni oyuncu (PLY444, PLY445) doğru şekilde
  eklendi, boş satır bırakılmadı.

**Sıradaki adım:** `.bat` menü sistemi (docs/05'teki iskeletin
tamamlanması) + `docs/09_OPERATOR_CEKLISTI.md` (yeni belge).

---

## 12 Ağustos 2026 (oturum 2, devam 3) — Nostradamus production + .bat menü + operatör checklist

**Yapıldı:**
- `nostradamus_predict.py` yazıldı — `backtest_devig_baseline.py` ile
  birebir aynı devig mantığı (Shin + B365/PS medyanı), ama production
  kullanımı için: JSON girdi (9 maç + kapanış 1X2 oranları) → konsol
  + JSON çıktı (1-X-2 tahminleri + olasılıklar + güven skoru).
- `menu.bat` yazıldı — Windows batch dosyası, 7 ana menü + 2 alt-menü:
  - [0] Hafta no ayarla, [1] Excel seç, [2] Kadro, [3] Nostradamus,
    [4] Web AI alt-menü (sakatlık/fiyat/sonuç/transfer), [5] Transfer
    kısayolu, [6] Backtest alt-menü (devig baseline + Poisson/Elo
    karşılaştırma), [7] Çıkış.
  - Her ingest script çağrısı dry-run önce, "Uygulansın mı? (e/h)"
    onayı sonrası --apply deseninde.
- `docs/05` güncellendi — placeholder'lar gerçek dosya adlarıyla
  değiştirildi, menü seçeneklerinin tam listesi eklendi.
- `docs/09_OPERATOR_CEKLISTI.md` yazıldı (yeni belge) — operatörün
  sistem çıktısını TFF Fantezi Lig uygulamasına elle uygulama rehberi:
  - Zaman kısıtları (deadline = haftanın ilk maçından 1 saat önce,
    menajer kartı son 15 dk'da alınamaz)
  - Haftalık zaman çizelgesi (T-48h, T-24h, T-2h, T-1h, deadline sonrası)
  - TFF'ye elle giriş sırası: kadro → formasyon → kaptan → yedek sırası →
    Nostradamus → menajer kartı
  - Sık karşılaşılan sorunlar ve çözümleri
- `docs/00`'a `09_OPERATOR_CEKLISTI.md` dosya listesine eklendi +
  başarı kriterleri güncellendi (Nostradamus baseline + transfer
  penceresi TAMAMLANDI olarak işaretlendi).

**Araştırıldı (kaynak + sonuç):**
- `nostradamus_predict.py`'nin iki girdi formatı desteklemesi gerekti:
  çoklu bahisçi (`"odds": {"B365": {...}, "PS": {...}}`) ve basit
  tek-bahisçi (`"odds_h"`, `"odds_d"`, `"odds_a"`). Operatör bazen
  sadece tek kaynak bulabiliyor — esneklik gerekli.
- Windows batch (.bat) dosyalarında Türkçe karakter sorunu: `chcp 65001`
  ile UTF-8 kodlama ayarlandı (Türkçe karakterler konsolda düzgün görünsün).
- TFF Fantezi Lig uygulamasının deadline/menajer kartı kuralları
  (docs/01'den teyit): son 15 dakikada menajer kartı satın alınamaz,
  kadro deadline'dan 1 saat önce kilitlenir — docs/09'a zaman çizelgesi
  olarak işlendi.

**Kararlaştırıldı (ve neden):**
- `nostradamus_predict.py`'nin Poisson/Elo katmanları KULLANILMIYOR —
  docs/07 önceki girişine göre baseline'ı geçemediler. Script sadece
  devig-only mode kullanır, ama backtest script'leri repoda tutulur
  (ileride yeniden değerlendirme için).
- `.bat` menüsünde her ingest script'i için "Uygulansın mı? (e/h)"
  onayı ZORUNLU — `--apply`'i doğrudan çağırmak yok. Bu, docs/05'teki
  "dry-run önce, onay sonrası apply" güvenlik deseni.
- `docs/09`'da "API ile otomatikleştirilemez" dürüstlük notu tekrarlandı
  — bu sistemin kalıcı sınırı, gelecekte TODO değil (docs/04 ile uyumlu).

**Test sonuçları:**
- `nostradamus_predict.py` 9 maçlık örnek JSON ile test edildi:
  tüm maçlar için tahmin üretildi (B365+PS medyanı + basit tek-bahisçi
  formatı karışık), 0 hata.
- `menu.bat`'ın mantığı sadece Linux ortamında simüle edilebiliyor
  (Windows batch), ama Python script'leri çağrıları doğrulandı.
- `ingest_transfer_window.py` önceki girişte test edilmişti.

**Sıradaki adım:** Tüm değişiklikler commit edilecek (mesajlarda model/
araç adı geçmeyecek şekilde), sonra push.

---

## 13 Ağustos 2026 — Rehber modu (`rehber.bat`) eklendi

**Yapıldı:**
- `rehber.bat` yazıldı — `menu.bat`'ın yanına, başlangıç seviyesi
  kullanıcılar için adım adım sihirbaz menüsü. 6 ana menü + 6 alt-adım
  (2a-2f) haftalık hazırlık akışı.
- Her alt-adımda: ne yapacağını Türkçe açıklar, ilgili prompt dosyasını
  Notepad ile açar, dosya kaydedildi mi kontrol eder, sıradaki adıma
  yönlendirir.
- `[5] SİSTEM DURUMU` menüsü — "nerede kaldım?" sorusuna JSON dosyalarının
  varlığından cevap çıkarır, sıradaki adımı söyler. State dosyası tutmaz,
  her girişte dosyalardan durumu çıkarır.
- `[2c]` Nostradamus adımında, fixtures JSON dosyası yoksa otomatik
  şablon oluşturur (1 maçlı örnek), kullanıcı Notepad ile 9 maça tamamlar.
- `docs/05` güncellendi — iki batch dosyasının karşılaştırması eklendi,
  "hangisini kullanmalısın?" rehberi.
- `docs/09` başına yönlendirme notu eklendi — "ilk kez kullanıyorsan
  rehber.bat'ı çalıştır, bu belge arka plan detayı için".
- Tüm `notepad` çağrıları `start notepad`'a çevrildi (rehber.bat
  beklemesin, kullanıcı kendi tempo'sunda devam etsin).
- `if %GWeek% LSS 17` → `if !GWeek! LSS 17` (delayed expansion, sayı
  karşılaştırması güvenli).

**Araştırıldı (kaynak + sonuç):**
- Batch dosyasında `notepad "file"` çağrısı kullanıcının Notepad'i
  kapatmasını bekler (bloklar). `start notepad "file"` ise bloklamaz —
  kullanıcı kendi tempo'sunda okur, kaydeder, rehber.bat'a geri döner.
  Bu, "saat dilimi yok, ne zaman müsaitse" felsefesine uygun.
- `setlocal enabledelayedexpansion` zaten `menu.bat`'ta vardı, `rehber.bat`'a
  da eklendi. `if` bloğu içinde `set` ile değişen değişkenleri `!var!` ile
  okumak için zorunlu.
- `chcp 65001` (UTF-8 kod sayfası) batch dosyasında Türkçe karakterlerin
  konsolda düzgün görünmesi için gerekli — `menu.bat`'taki desen korundu.
- Linux'ta batch simülasyonu: `cmd.exe` olmadığı için Python ile mantık
  test edildi. 16 etiket, 16 goto/call — hepsi eşleşiyor. 3 örnek JSON
  ile full [2] akışı test edildi, tüm Python script'leri çağrı biçiminde
  sorunsuz çalışıyor.

**Kararlaştırıldı (ve neden):**
- `rehber.bat` `menu.bat`'ın **yerine** değil, **yanına** eklendi.
  İleride kullanıcı akış oturunca `menu.bat`'a geçebilir — ikisi de
  aynı Python script'lerini çağırır, sadece UX farkı var.
- Saat dilimi yok ("T-48 saat" gibi). Kullanıcı perşembe akşamı da
  girebilir, pazar sabahı da. Sistem sadece "bu adımı yaptın mı?"
  diye kontrol eder, saatlere karışmaz — kullanıcının "otonom
  ilerliyor" hissini korumak için.
- Her alt-adımda "yaptım, devam" / "şimdi yapamam, atla" / "geri dön"
  seçeneği var. Kullanıcı bir adımı atlayıp sonrasına geçebilir,
  eksik adımı sonra tamamlayabilir. State dosyası tutulmaz — her
  girişte dosya varlığından durum çıkarılır (basit, güvenli).
- "Çocuğa anlatır gibi" dil — her adımda "ADIM 1: ... ADIM 2: ..."
  şeklinde numaralandırılmış, kısa cümleler. Jargon minimum.
- Notepad kullanımı (VS Code gibi gelişmiş editör yerine) — her
  Windows'ta varsayılan olarak var, ekstra kurulum gerektirmez.

**Test sonuçları:**
- `rehber_test.py` (Linux'ta statik analiz) — 16 etiket, 16 goto/call,
  hepsi eşleşiyor. 7 Python script'inin --help çıktısı OK. Nostradamus
  şablonu geçerli JSON.
- Full [2] akışı simülasyonu (3 örnek JSON ile) — `update_from_web_research.py`
  dry-run OK (1 sakatlık, isim eşleşmedi — beklenen), `ingest_price_updates.py`
  dry-run OK (1 fiyat eşleşti), `nostradamus_predict.py` OK (2 maç tahmini
  üretildi), `run_gameweek.py` OK (kadro üretildi, gw1_kadro_onerisi.xlsx
  oluştu). 0 hata.
- Windows'ta gerçek test yapılmadı (Linux ortamı) — kullanıcı Windows'ta
  çift tıklayıp deneyebilir. Hata olursa `docs/07`'ye not düşülmeli.

**Sıradaki adım:** Kullanıcı Windows'ta `rehber.bat`'ı test edecek.
İlk hafta deneyimine göre UX iyileştirmeleri yapılabilir (örn. daha
kısa promptlar, ekran temizleme, renkli çıktı).

---

## 13 Ağustos 2026 (oturum 3) — 3 kritik madde + opsiyonel test + CRLF düzeltmesi

**Yapıldı:**

### 1. (KRİTİK) Excel yazma öncesi otomatik yedek
- `backup_utils.py` yazıldı — `backup_excel(path)` fonksiyonu.
  Yedek adı: `backups/<excel_adı>_YYYYMMDD_HHMMSS.xlsx`
  Excel dosyasiyla ayni klasorde `backups/` altinda.
- 4 ingest script'ine `--apply` bloğunda `wb.save()`'den ÖNCE
  `backup_excel(args.excel_path)` çağrısı eklendi:
  - `ingest_price_updates.py`
  - `ingest_transfer_window.py`
  - `update_from_web_research.py`
  - `ingest_gameweek_results.py`
- `.gitignore`'a `backups/` eklendi (kullanıcı-local, repoya ALINMAZ).
- Test: `ingest_price_updates.py --apply` çalıştırınca backup oluştu,
  orijinal dosya doğru güncellendi.

### 2. (KRİTİK) `örnek_kadro_yapısı.xlsx` silindi
- Dosyada Uğurcan Çakır "Çorum FK" gösteriliyordu (gerçekte Galatasaray)
  — eski test çalıştırmasından kalma bayat veri.
- docs/'ta bu dosyaya **hiç referans yok** (grep ile teyit edildi).
- Dosya silindi. İhtiyaç olursa `run_gameweek.py` ile yeniden üretilebilir.

### 3. (KRİTİK) Kadro çıktısı biçimlendirme + otomatik aç
- `run_gameweek.py`'nin `export_result()` fonksiyonu openpyxl ile
  yeniden yazıldı (pandas `.to_excel` yerine):
  - Başlık satırı: kalın beyaz yazı, koyu gri (#404040) arka plan,
    ortalı, 32px yükseklik
  - `price_tl` kolonu: `#,##0" TL"` formatı (9.000.000 TL)
  - `xp` kolonu: `0.00` formatı (3.84)
  - `play_probability`: `0%` formatı (95%)
  - CAPTAIN satırı: sarı (#FFEB3B) arka plan + ad kalın
  - VICE_CAPTAIN: açık sarı (#FFF59D) + ad kalın
  - BENCH: gri (#EEEEEE)
  - Satırlar pozisyona (GK→DEF→MID→FWD) ve role (CAPTAIN→VICE→STARTER→BENCH) göre sıralı
  - Freeze panes (A2) — başlık scroll'da sabit
  - Kolon genişlikleri ayarlı
- `rehber.bat` [2e] adımında `start "" "gw%GWeek%_kadro_onerisi.xlsx"`
  ile Excel otomatik açılıyor — kullanıcı "bu dosyayı aç" demeye gerek yok.

### 4. (Opsiyonel) Regresyon testleri
- `tests/` klasörü açıldı, 3 test dosyası yazıldı:
  - `test_ingest_price_updates.py` (4 test): dry-run Excel'i değiştirmiyor,
    --apply kolon ekliyor, fiyat doğru yazılıyor, backup oluşuyor
  - `test_ingest_transfer_window.py` (4 test): is_active kolonu ekleniyor,
    "in" yeni ID atıyor (PLY444+), "out" satır silmiyor (is_active=0),
    çoklu "in" benzersiz ID'ler
  - `test_optimizer.py` (7 test): squad=15 oyuncu, 2GK/5DEF/5MID/3FWD,
    bütçe ≤100M, max 3 kulüp, kaptan+vice squad'da, kaptan≠vice
- **15/15 test başarılı** (`python3 -m unittest discover tests -v`).

### 5. CRLF düzeltmesi (kullanıcı bildirdi)
- `rehber.bat` ve `menu.bat` Linux'ta LF-only olarak yazılmıştı.
  Windows `cmd.exe` LF-only .bat dosyalarında `goto`/`if`/`set /p`
  komutlarını düzgün işlemiyor → Python hatası.
- `scripts/crlf_convert.py` ile her iki dosya da CRLF'e çevrildi
  (874 + 252 satır, 0 LF-only kaldı).
- `.gitattributes` eklendi:
  ```
  *.bat text eol=crlf
  *.cmd text eol=crlf
  ```
  Bu sayede gelecekteki commit'lerde .bat dosyaları her ortamda
  CRLF olarak checkout edilir (Git'autocrlf' ayarı ne olursa olsun).

### 6. `rehber.bat` [1] menüsüne requirements.txt kurulumu
- `requirements.txt` oluşturuldu:
  - Üretim: openpyxl, pandas, numpy, scipy, shin
  - Backtest (opsiyonel): penaltyblog, soccerdata
- `rehber.bat` [1] İLK KEZ BAŞLIYORUM menüsüne "KONTROL 2: Python
  kütüphaneleri kurulu mu?" adımı eklendi. Kullanıcıya
  `pip install -r requirements.txt` çalıştırma seçeneği sunuluyor
  (ilk kurulumda EVET denmeli).

**Araştırıldı (kaynak + sonuç):**
- openpyxl PatternFill rengi: `start_color` ve `end_color` aynı olmak
  zorunda, `fill_type="solid"` olmadan renk görünmüyor. Test'te doğrulandı.
- Excel number_format: `#,##0" TL"` → `9.000.000 TL` (Türkçe binlik
  ayırıcı virgül, Excel'in yerel ayarına göre noktaya çevrilir).
  Test'te format doğru uygulandı.
- `.gitattributes` `text eol=crlf`: Git bunu zorunlu kılar —
  `core.autocrlf=false` olsa bile .bat dosyaları CRLF olarak checkout edilir.
- `python -m pip install -r requirements.txt`: `pip` yerine `python -m pip`
  kullanıldı (Windows'ta PATH sorunu olmasın diye).

**Kararlaştırıldı (ve neden):**
- Backup dosya adında timestamp `%Y%m%d_%H%M%S` formatı — aynı gün
  birden fazla --apply yapılırsa üzerine yazılmasın, her seferinde
  yeni yedek olsun. Disk dolarsa kullanıcı `backups/`'ı temizler.
- `backup_excel()` sessizce devam eder (exception fırlatmaz) — eğer
  backup alınamazsa, uygulamayı durdurmak yerine uyarı verir ve
  operatör kararı bekler. Çünkü bazen backup diski dolu olabilir,
  ama asıl uygulama hala yapılmalı (operatör riski kabul ederse).
- `örnek_kadro_yapısı.xlsx` silmek yerine yeniden üretmek de
  seçenekti ama dosyanın amacı belirsizdı (hiçbir docs referans
  vermiyor). Silmek daha temiz — ihtiyaç olursa `run_gameweek.py`
  ile anında üretilebilir.
- Test'ler `unittest` ile (pytest değil) — ekstra bağımlılık yok,
  her Python kurulumunda standart. İleride pytest istenirse `unittest`
  ile yazılmış test'ler pytest ile de çalışır (geriye dönük uyumlu).
- `.gitattributes`'ta sadece `.bat`/`.cmd` için `eol=crlf` zorunlu,
  diğer metin dosyaları (`*.py`, `*.md`) Git'autocrlf' ayarına bırakıldı
  — Linux geliştiriciler LF, Windows kullanıcıları CRLF alsın.

**Test sonuçları:**
- `python3 -m unittest discover tests -v` → 15/15 test OK (0.46s + 0.74s + 0.40s).
- Backup test: `backups/test_oyuncu_20260813_032025.xlsx` oluştu, orijinal
  dosya boyutu korundu, fiyat doğru yazıldı.
- Excel biçimlendirme: CAPTAIN satırı `#FFEB3B` (sarı), VICE `#FFF59D`
  (açık sarı), BENCH `#EEEEEE` (gri), header `#404040` + bold + beyaz.
  Sayı formatları doğru. Pozisyon+role sıralaması doğru.
- CRLF: her iki .bat dosyası 0 LF-only satır, tam CRLF.

**Sıradaki adım:** Kullanıcı Windows'ta `rehber.bat`'ı çift tıklayıp
test edecek. İlk hafta deneyimine göre:
- [1] kurulum akışı (requirements.txt kurulumu dahil) çalışıyor mu
- [2e] kadro üretildikten sonra Excel otomatik açılıyor mu
- Backup dosyaları `backups/` altında birikiyor mu (disk dolarsa
  temizleme uyarısı verilebilir)

---

## [SONRAKİ OTURUM İÇİN ŞABLON — kopyala, doldur]
## <Tarih> — <kısa başlık>
**Yapıldı:**
-
**Araştırıldı (kaynak + sonuç):**
-
**Kararlaştırıldı (ve neden):**
-
**Sıradaki adım:**
