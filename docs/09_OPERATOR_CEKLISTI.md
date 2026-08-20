# 09 — Operatör Günlük Checklist'i

> **Önce şunu oku:** Eğer projeyi ilk kez kullanıyorsan veya akışı
> bilmiyorsan, **`rehber.bat`** dosyasını çalıştır (Windows'ta çift tıkla).
> Bu belge rehber.bat'ın arka planındaki detayları içerir — rehber.bat
> seni adım adım yönlendirirken, bu belge "neden öyle?" sorusunun
> cevabını verir. Akış oturduktan sonra bu belgeye bakmaya gerek
> kalmayabilir.

Bu belge, sistemin ürettiği çıktıyı (15 oyuncu + kaptan/yedek kaptan +
9 maç tahmini) gerçek TFF Fantezi Lig uygulamasına/sitesine **elle**
nasıl gireceğini adım adım anlatır. Sistem otomatik olarak TFF'ye
bağlanıp kadro gönderemez — bu adım Manuel olarak operatöre aittir
(docs/04'ün "fiyat ve sakatlık verisi API ile otomatikleştirilemez"
dürüstlük notuyla aynı felsefe).

## Zaman kısıtları (oyunun kendi kuralları — docs/01)

- **Deadline:** haftanın ilk maçından **1 saat önce** kadro kilitlenir.
  Bu saatten sonra kadro/transfer/kaptan DEĞİŞTİRİLEMEZ.
- **Menajer kartı:** son 15 dakikada **satın alınamaz**. Eğer menajer
  kartı kullanılacaksa, deadline'dan en az 15 dakika önce alınmalı.
- **Nostradamus tahminleri:** haftanın ilk maçından önce gönderilmeli.
  İlk maç başlayınca o hafta için Nostradamus kilitlenir.
- Bu kısıtlar oyunun kendi kurallarıdır (docs/01), sistem tarafından
  atlanamaz. Operatör saatleri kontrol etmeli.

## Önerilen zaman çizelgesi (haftalık)

TFF Süper Lig maçları genelde Cuma-Pazartesi arası oynanır. Aşağıdaki
çizelge örnek bir Cuma-Perşembe haftası için; maç takvimine göre
kaydırılmalı.

### T-48 saat (Perşembe sabahı)
1. **Web araştırması yap:** `web_arastirma_prompti.md`'yi bir web AI'ya
   (Gemini, ChatGPT veya web araması yapabilen bir AI) yapıştır. Çıkan JSON'u
   `web_research_gwN.json` olarak kaydet.
2. **Dry-run:** `menu.bat` → [4] → [4a] → dosya yolu gir → raporu oku.
   - İsim eşleşmeyenler listesini kontrol et — yanlış JSON girişi varsa düzelt.
   - Reddedilenler (validator hatası) varsa düzelt.
3. **Onayla:** "Uygulansın mı? (e/h)" sorusuna `e` yaz.
4. **Fiyat güncellemesi:** TFF uygulamasında "Transferler" ekranından
   ekran görüntüsü al → `fiyat_guncelleme_prompti.md`'deki gibi JSON'a
   çevir → `menu.bat` → [4] → [4b] ile yükle.

### T-24 saat (Cuma sabahı)
5. **Nostradamus oranlarını topla:** 9 maçın kapanış 1X2 oranlarını
   bir bahis oranları sitesinden (ör. oddsportal.com, flashscore.com)
   al. Her maç için B365 ve PS kapanış oranlarını not et.
6. **Nostradamus JSON'ını hazırla:** Aşağıdaki formata göre
   `nostradamus_fixtures_gwN.json` dosyasını doldur:
   ```json
   {
     "gameweek": 5,
     "prediction_date": "2026-09-15",
     "fixtures": [
       {
         "home_team": "Galatasaray",
         "away_team": "Fenerbahce",
         "match_date": "2026-09-20",
         "odds": {
           "B365": {"H": 1.85, "D": 3.6, "A": 4.2},
           "PS":  {"H": 1.88, "D": 3.55, "A": 4.25}
         }
       }
     ]
   }
   ```
   Not: sadece tek bahisçi varsa `"odds_h"`, `"odds_d"`, `"odds_a"`
   alanlarını da kullanabilirsin (script ikisini de destekler).
7. **Nostradamus tahminini üret:** `menu.bat` → [3] → JSON yolu gir.
   Çıktıyı `nostradamus_predict_gwN.json` olarak kaydet.

### T-2 saat (Pazar öğleden sonra, maçların çoğu pazartesi akşamıysa)
8. **Son-dakika haber kontrolü:** Son 24 saatte sakatlık/ceza değişikliği
   var mı? Varsa tekrar `web_arastirma_prompti.md` çalıştır, güncel JSON
   üret, `menu.bat` → [4] → [4a] ile yükle.
9. **Kadro optimizasyonunu çalıştır:** `menu.bat` → [0] (hafta no) → [2].
   Çıktı: `gwN_kadro_onerisi.xlsx` ve konsolda kadro listesi.

### T-1 saat (deadline'dan 1 saat önce, son pencere)
10. **TFF Fantezi Lig uygulamasını aç.** Aşağıdaki sırayla gir:

### TFF Uygulamasına Elle Giriş Sırası (önemli)

**Adım 1 — Kadro:**
- 15 oyuncuyu seç (2 GK, 5 DEF, 5 MID, 3 FWD).
- Sistemdeki `gwN_kadro_onerisi.xlsx` dosyasındaki "STARTER" ve "BENCH"
  etiketlerine bak.
- Önce mevcut kadrodan ÇIKARILACAK oyuncuları çıkart, sonra EKLENECEK
  oyuncuları ekle. Bütçe limitini (100M TL) aşmamaya dikkat et.

**Adım 2 — Formasyon:**
- İlk 11'i yerle (1 GK, min 3 DEF, min 1 FWD, toplam 11).
- `gwN_kadro_onerisi.xlsx`'teki "STARTER" etiketli oyuncular ilk 11'de
  olmalı. Bench oyuncuları yedek.

**Adım 3 — Kaptan:**
- `gwN_kadro_onerisi.xlsx`'te `role=CAPTAIN` olan oyuncuyu kaptan yap.
- `role=VICE_CAPTAIN` olan oyuncuyu yedek kaptan yap.
- Kaptanın puanı 2x sayılır — kaptan süre almazsa yedek kaptanın puanı
  2x sayılır (docs/01).

**Adım 4 — Yedek sıralaması:**
- Bench oyuncularını öncelik sırasına göre diz.
- Sistem otomatik değişiklik yaparken formasyon kuralını bozmayacaksa
  devreye girer (ör. kaleci çıkar → yedek kaleci girer).
- `gwN_kadro_onerisi.xlsx`'teki sıraya uy: bench_gk önce, sonra
  bench_outfield[0], [1], [2].

**Adım 5 — Nostradamus:**
- Uygulamada "Nostradamus" sekmesine git.
- 9 maçın her biri için 1/X/2 seç.
- `nostradamus_predict_gwN.json`'daki `prediction` alanını kullan
  (1 = ev sahibi, X = beraberlik, 2 = deplasman).
- Tüm 9 maçı doldurduktan sonra "Gönder" — tam 9 maç girilince +1 puan.

**Adım 6 — Menajer kartı (opsiyonel):**
- Eğer bu hafta menajer kartı kullanılacaksa, **deadline'dan en az
  15 dakika önce** satın al.
- Son 15 dakikada satın alınamaz (oyun kuralı, docs/01).
- Menajer kartı, deadline sonrası bir oyuncunun performansını 2x yapar
  (kaptanınki yerine).

### Deadline sonrası (maçlar oynandıktan sonra)
11. **Maç sonuçlarını işle:** Maçlar oynandıktan sonra gerçekçi
    performans verilerini topla. `match_sonuclari_prompti.md`'yi
    kullanarak JSON üret → `menu.bat` → [4] → [4c] ile yükle.
    - Bu, `calibrate_priors.py`'nin çalışması için gerekli — bir sonraki
      haftanın xP hesabının doğruluğu buna bağlı.
12. **Geliştirme günlüğüne işle:** `docs/07_GELISTIRME_GUNLUGU.md`'ye
    kısa not ekle — tahmin doğruluğu, kadro puanı, gözlemler.

## Önemli uyarılar

### Yapılmaması gerekenler
- **Kadro/transfer/kaptan değişikliklerini AI'ye yaptırma.** Sistem
  sadece öneri üretir — uygulama operatöre aittir (docs/00 ilkesi).
- **±0.10'dan büyük manuel düzeltme yapma.** Eğer sistem çıktısında
  bariz hata varsa (ör. sakat oyuncu kadroda), kaynak veriyi düzeltip
  sistemi yeniden çalıştır — çıktıyı elle değiştirme.
- **`--apply`'i dry-run'siz çalıştırma.** Her ingest script'i önce
  dry-run gösterir, onay sonrası uygular. `menu.bat` bu deseni zorunlu
  kılar ama komut satırından doğrudan çağırırsan dikkat et.
- **Excel'i elle düzenleme.** `Players` sheet'ine manuel satır ekleme
  veya silme — `ingest_transfer_window.py` veya `ingest_price_updates.py`
  kullan. Manuel düzenleme `player_id` sırasını bozabilir.

### Sık karşılaşılan sorunlar
- **"İsim eşleşmeyen" hatası:** Web AI çıktısındaki oyuncu adı, Excel'deki
  adla birebir uyuşmuyor. `source_note` alanından kontrol et, JSON'da adı
  düzelt, tekrar dry-run çalıştır.
- **"play_probability aralık dışı" hatası:** JSON'da 0.0-1.0 dışında
  değer var. Validator reddeder — kaynağı kontrol et.
- **"geçersiz pozisyon" hatası:** Transfer JSON'unda position alanı
  4 geçerli değerden biri değil: `"GK - Kaleci"`, `"DEF - Defans"`,
  `"MID - Orta Saha"`, `"FWD - Forvet"`. Tam yazım önemli.
- **Nostradamus JSON'da "geçerli oran yok" uyarısı:** Oranlardan biri
  1.0'dan küçük veya eşit (geçersiz). Kaynağı kontrol et.

### Backtest ile kalibrasyon kontrolü
Her 5-10 haftada bir, `menu.bat` → [6] → [6a] ile devig baseline
backtest çalıştır. Brier score ~0.55 civarında kalmalı. Eğer belirgin
bozulma varsa (ör. 0.60+), bu ya:
- Oran kalitesinin düştüğünü (kapanış oranları düzgün alınmıyor)
- Veya piyasa veriminin değiştiğini gösterebilir.

`docs/07_GELISTIRME_GUNLUGU.md`'ye backtest sonucunu not et.
