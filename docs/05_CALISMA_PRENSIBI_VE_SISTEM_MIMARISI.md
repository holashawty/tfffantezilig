# 05 — Çalışma Prensibi ve Sistem Mimarisi

## Veri katmanı
Excel (`oyuncu_veritabani_guncel.xlsx`, 3 sheet: `Players`,
`GameweekLog`, `Fixtures`). SQLite'a geçiş şu an GEREKSİZ — mevcut
pipeline çalışıyor ve test edildi. Eğer ileride ölçek sorunu
çıkarsa (443 oyuncu için çıkmayacak), SQLite'a geçiş ayrı bir
görev olarak ele alınır, ŞİMDİ DEĞİL.

## Güvenlik deseni — HER veri girişi script'i bunu izler
1. JSON oku
2. `validator.py` ile doğrula (zorunlu alan / mantıklı aralık kontrolü)
3. İsim eşleştir (fuzzy match, `difflib`)
4. Rapor bas (dry-run) — HİÇBİR ŞEY YAZILMAZ
5. Kullanıcı/operatör onaylarsa `--apply` ile gerçek yazma

Bu desen zaten `update_from_web_research.py`, `ingest_gameweek_results.py`,
`ingest_price_updates.py` içinde var. Yeni bir ingest script'i
yazarsan (ör. transfer penceresi için) AYNI DESENİ kopyala.

## `.bat` Menü Sistemi (Windows, operatör için)

Repo kökünde **iki** batch dosyası var. İhtiyacına göre birini seç:

### `rehber.bat` — Başlangıç seviyesi (önerilen)
"sihirbaz" gibi — seni adım adım elinden tutar. Hangi sırada ne
yapacağını bilmiyorsan bunu kullan. Saat dilimi yok, "ne zaman
müsaitse gir" felsefesi.

6 ana menü:
- **[1] İLK KEZ BAŞLIYORUM** — sezon başı tek seferlik kurulum
  (Python/Excel/prompt dosyalarını kontrol eder, hafta numarasını sorar)
- **[2] YENİ HAFTA HAZIRLIĞI** — deadline'dan önce yapılacaklar
  6 alt-adım: a) sakatlık topla → b) fiyat topla → c) oran topla →
  d) sisteme yükle → e) kadro üret → f) TFF'ye elle gir
  Her alt-adımda: ne yapacağını söyler, ilgili prompt dosyasını
  Notepad ile açar, dosyayı kaydedip kaydetmediğini kontrol eder.
  İstediğin adımda çıkıp sonra devam edebilirsin.
- **[3] MAÇLAR BİTTİ** — maç sonrası gerçek sonuçları gir
  (calibrate_priors.py için gerekli)
- **[4] TRANSFER PENCERESİ** — sadece 17. hafta sonrası
- **[5] SİSTEM DURUMU** — "nerede kaldım?" sorusuna cevap verir,
  hangi JSON dosyalarının hazır olduğunu gösterir, sıradaki adımı söyler
- **[6] BACKTEST** — aylık sağlık kontrolü (Brier score)

### `menu.bat` — İleri kullanıcılar
"Araç kutusu" gibi — her script'i ayrı seçenek olarak çağırır.
Hangi sırada kullanacağını biliyorsan bunu kullan. `rehber.bat`'ın
yaptığı yönlendirmeyi içermez, sadece Python script'lerini çalıştırır.

7 ana menü + 2 alt-menü (Web AI çıktıları + Backtest). Her ingest
script'i dry-run önce, "Uygulansın mı? (e/h)" onayı sonrası --apply.

### Hangisini kullanmalısın?
- **İlk hafta veya emin değilsen**: `rehber.bat`
- **Birkaç hafta sonra akış oturduğunda**: `menu.bat` (daha hızlı)
- İkisi de aynı Python script'lerini çağırır, sadece UX farkı var

İskeletin eski halindeki placeholder'lar (`nostradamus_predict.py` ve
`ingest_transfer_window.py`) artık gerçek dosya adlarıdır — her ikisi de
yazıldı ve test edildi.

## Bir "hafta güncelle" döngüsünün tam akışı
`update_week.py` zaten bunu yapıyor (5 adım: sonuç işleme →
kalibrasyon → fiyat → sakatlık/ceza → optimizasyon). `.bat` menüsü
bunun üstüne kullanıcı-dostu bir kabuk. Mantığı `update_week.py`'den
KOPYALAMA, `.bat`'tan onu ÇAĞIR.
