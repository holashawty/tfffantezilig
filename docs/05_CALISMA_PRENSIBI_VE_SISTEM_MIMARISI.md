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

## `.bat` Menü Sistemi (Windows, operatör için — YAZILACAK)
```bat
@echo off
:menu
cls
echo === TFF Fantezi Lig Sistemi ===
echo [1] Yeni fikstur/hafta verisi ekle
echo [2] Kadro optimizasyonunu calistir (kadro + kaptan)
echo [3] Nostradamus tahminlerini calistir (9 mac)
echo [4] Web AI arastirma ciktisini sisteme yukle (sakatlik/fiyat/sonuc)
echo [5] Transfer penceresi (oyuncu ekle/cikar) - sadece 17. hafta sonrasi
echo [6] Cikis
set /p secim="Secim: "

if "%secim%"=="1" ( python run_gameweek.py oyuncu_veritabani_guncel.xlsx --gameweek %hafta% & goto menu )
if "%secim%"=="2" ( python run_gameweek.py oyuncu_veritabani_guncel.xlsx --gameweek %hafta% & goto menu )
if "%secim%"=="3" ( python nostradamus_predict.py & goto menu )
if "%secim%"=="4" ( goto webai_submenu )
if "%secim%"=="5" ( python ingest_transfer_window.py oyuncu_veritabani_guncel.xlsx & goto menu )
if "%secim%"=="6" ( exit )
goto menu
```
Agent, `nostradamus_predict.py` ve `ingest_transfer_window.py`'yi
yazınca bu iskeleti tamamlasın; placeholder script isimlerini
GERÇEK dosya adlarıyla değiştirsin.

## Bir "hafta güncelle" döngüsünün tam akışı
`update_week.py` zaten bunu yapıyor (5 adım: sonuç işleme →
kalibrasyon → fiyat → sakatlık/ceza → optimizasyon). `.bat` menüsü
bunun üstüne kullanıcı-dostu bir kabuk. Mantığı `update_week.py`'den
KOPYALAMA, `.bat`'tan onu ÇAĞIR.
