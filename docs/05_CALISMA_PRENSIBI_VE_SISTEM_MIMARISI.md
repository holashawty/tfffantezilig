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
`menu.bat` dosyası repo kökünde yazıldı. Tüm ingest script'lerini
dry-run önce, onay sonrası `--apply` deseninde çağırır. Operatör
sadece hafta numarasını ve JSON dosya yollarını girer.

Menü seçenekleri:
- **[0]** Hafta numarası ayarla (tüm script'lerde `%GWeek%` olarak kullanılır)
- **[1]** Excel dosyası seç (varsayılan: `oyuncu_veritabani.xlsx`)
- **[2]** Kadro optimizasyonu → `python run_gameweek.py <excel> --gameweek <N>`
- **[3]** Nostradamus tahminleri → `python nostradamus_predict.py <fixtures.json>`
  (operator önce 9 maçın oranlarını JSON'a manuel girer, bkz. `docs/09`)
- **[4]** Web AI çıktıları alt-menüsü:
  - `[4a]` Sakatlık/ceza → `update_from_web_research.py`
  - `[4b]` Fiyat → `ingest_price_updates.py`
  - `[4c]` Maç sonuçları → `ingest_gameweek_results.py`
  - `[4d]` Transfer penceresi → `ingest_transfer_window.py`
  Her biri önce dry-run, sonra "Uygulansın mı? (e/h)" onayı.
- **[5]** Transfer penceresi (aynı [4d], kısayol)
- **[6]** Backtest alt-menüsü (Nostradamus baseline kontrolü):
  - `[6a]` Devig-only baseline Brier score
  - `[6b]` Poisson+Elo karşılaştırma (docs/03 kuralı gereği EKLENMEZ,
    ama tekrar değerlendirme için tutulur)
- **[7]** Çıkış

İskeletin eski halindeki placeholder'lar (`nostradamus_predict.py` ve
`ingest_transfer_window.py`) artık gerçek dosya adlarıdır — her ikisi de
yazıldı ve test edildi.

## Bir "hafta güncelle" döngüsünün tam akışı
`update_week.py` zaten bunu yapıyor (5 adım: sonuç işleme →
kalibrasyon → fiyat → sakatlık/ceza → optimizasyon). `.bat` menüsü
bunun üstüne kullanıcı-dostu bir kabuk. Mantığı `update_week.py`'den
KOPYALAMA, `.bat`'tan onu ÇAĞIR.
