@echo off
chcp 65001 >nul
REM ============================================================
REM TFF Fantezi Lig - REHBER MODU
REM ------------------------------------------------------------
REM Bu dosya "menu.bat"'in yaninda yer alir. Farki:
REM   menu.bat  = arac kutusu (ileri kullanici, ne yapacagini biliyor)
REM   rehber.bat = sihirbaz (adim adim elinden tutar, sirayi sasirtmaz)
REM
REM Kullanici ne zaman musaitse girer. Saat dilimi yok. Her giriste
REM dosyalardan durumu cikarir, "nerede kaldin?" sorusuna cevap verir.
REM ============================================================

setlocal enabledelayedexpansion

REM Varsayilan dosya yollari
set "EXCEL=oyuncu_veritabani.xlsx"
set "GWeek=1"

:ana_menu
cls
echo ==================================================================
echo   TFF FANTEZI LIG - REHBER MODU
echo ==================================================================
echo   Bu program seni adim adim yonlendirecek. Ne yapacagini bilmesen
echo   bile, sirayla ilerlersen her sey tamam olur.
echo.
echo   Aktif Excel : %EXCEL%
echo   Aktif Hafta : %GWeek%
echo ------------------------------------------------------------------
echo.
echo   [1] ILK KEZ BASLIYORUM  (sezon basi, tek seferlik kurulum)
echo   [2] YENI HAFTA HAZIRLIGI (deadline'dan once yapilacaklar)
echo   [3] MAQLAR BITTI - SONUQLARI GIR (hafta sonrasi)
echo   [4] TRANSFER PENCERESI  (sadece sezon ortasi, 17. hafta sonrasi)
echo   [5] SISTEM DURUMU - nerede kaldim, ne yapmaliyim?
echo   [6] BACKTEST - sistem dogru calisiyor mu? (aylik kontrol)
echo   [0] CIKIS
echo ==================================================================
set /p secim="Secim [0-6]: "

if "%secim%"=="1" goto ilk_kurulum
if "%secim%"=="2" goto yeni_hafta
if "%secim%"=="3" goto maclar_bitti
if "%secim%"=="4" goto transfer_penceresi
if "%secim%"=="5" goto sistem_durumu
if "%secim%"=="6" goto backtest
if "%secim%"=="0" goto cikis
goto ana_menu

REM ============================================================
REM [1] ILK KEZ BASLIYORUM
REM ============================================================
:ilk_kurulum
cls
echo ==================================================================
echo   [1] ILK KEZ BASLIYORUM - Sezon Basi Kurulumu
echo ==================================================================
echo.
echo Bu adim sezonun BASINDA bir kere yapilir. Amaci:
echo   - Python kurulu mu kontrol etmek
echo   - Excel dosyasi yerinde mi kontrol etmek
echo   - Prompt dosyalari hazir mi kontrol etmek
echo   - Hangi haftadan basladigini kaydetmek
echo.
echo --- KONTROL 1: Python kurulu mu? ---
python --version 2>nul
if errorlevel 1 (
  echo.
  echo [HATA] Python bulunamadi!
  echo   Python'u https://python.org indir ve kur.
  echo   Kurarken "Add Python to PATH" kutusunu ISARETLE.
  echo   Kurduktan sonra bu menuye geri don.
  echo.
  pause
  goto ana_menu
)
echo   Python: OK
echo.
echo --- KONTROL 2: Python kutuphaneleri kurulu mu? ---
echo   Gerekli kutuphaneler: openpyxl, pandas, scipy, shin
echo   (Backtest icin: penaltyblog, soccerdata — opsiyonel)
echo.
echo   Kurmak istiyor musun? (Ilk kurulumda EVET demen lazim)
set /p install_deps="pip install -r requirements.txt calistirilsin mi? (e/h): "
if /i "!install_deps!"=="e" (
  echo.
  echo   Kurulum basliyor...
  echo.
  python -m pip install -r requirements.txt
  if errorlevel 1 (
    echo.
    echo [UYARI] Kurulumda hata olustu. Yukaridaki mesaji oku.
    echo   Tek tek denemek icin: pip install openpyxl pandas scipy shin
    echo.
    pause
  ) else (
    echo.
    echo [TAMAM] Kutuphaneler kuruldu.
  )
) else (
  echo   Atlandi. Daha sonra "pip install -r requirements.txt" ile kurabilirsin.
)
echo.
echo --- KONTROL 3: Excel dosyasi yerinde mi? ---
if not exist "%EXCEL%" (
  echo [HATA] Excel dosyasi bulunamadi: %EXCEL%
  echo   Bu dosya repo ile birlikte gelmeli. Klasorunde oldugundan emin ol.
  echo.
  pause
  goto ana_menu
)
echo   Excel: OK (%EXCEL%)
echo.
echo --- KONTROL 4: Prompt dosyalari hazir mi? ---
set "prompts=web_arastirma_prompti.md fiyat_guncelleme_prompti.md match_sonuclari_prompti.md transfer_prompti.md"
set "all_ok=1"
for %%p in (%prompts%) do (
  if exist "%%p" (
    echo   %%p : OK
  ) else (
    echo   %%p : EKSIK!
    set "all_ok=0"
  )
)
if "!all_ok!"=="0" (
  echo.
  echo [HATA] Baz prompt dosyalari eksik. Repoyu yeniden indir.
  pause
  goto ana_menu
)
echo.
echo --- KONTROL 5: Hangi haftadan basliyorsun? ---
set /p GWeek="Kacinci haftaya hazirlaniyorsun? (1-38, varsayilan 1): "
if "!GWeek!"=="" set "GWeek=1"
echo   Hafta !GWeek! olarak ayarlandi.
echo.
echo ==================================================================
echo   KURULUM TAMAM!
echo ==================================================================
echo   Simdi [2] YENI HAFTA HAZIRLIGI'na gec.
echo   Orada sistem seni adim adim yonlendirecek:
echo     2a. Sakatlik/ceza verisi topla
echo     2b. Fiyat verisi topla
echo     2c. Nostradamus oranlari topla
echo     2d. Sisteme yukle
echo     2e. Kadro optimizasyonu
echo     2f. TFF'ye elle gir
echo.
pause
goto ana_menu

REM ============================================================
REM [2] YENI HAFTA HAZIRLIGI
REM ============================================================
:yeni_hafta
cls
echo ==================================================================
echo   [2] YENI HAFTA HAZIRLIGI - Hafta %GWeek%
echo ==================================================================
echo.
echo Bu adim haftanin ilk macindan ONCE yapilmali (deadline = ilk mac
echo saatinden 1 saat once). Sistem 6 alt-adimda seni yonlendirecek.
echo.
echo Hangi adimdasin? (Emin degilsen 0 sec, sistem soyler)
echo.
echo   [a] Sakatlik/ceza verisi topla
echo   [b] Fiyat verisi topla
echo   [c] Nostradamus oranlari topla
echo   [d] Sisteme yukle (3 JSON'i isle)
echo   [e] Kadro optimizasyonu
echo   [f] TFF'ye elle gir
echo   [0] Hangi adimda kaldigimi soyle
echo   [9] Ana menuye don
echo.
set /p adim="Secim: "

if /i "!adim!"=="a" goto adim_2a
if /i "!adim!"=="b" goto adim_2b
if /i "!adim!"=="c" goto adim_2c
if /i "!adim!"=="d" goto adim_2d
if /i "!adim!"=="e" goto adim_2e
if /i "!adim!"=="f" goto adim_2f
if "!adim!"=="0" goto adim_durumu
if "!adim!"=="9" goto ana_menu
goto yeni_hafta

:adim_durumu
cls
echo ==================================================================
echo   ADIM DURUMU - Hafta %GWeek%
echo ==================================================================
echo.
echo Mevcut JSON dosyalarin:
echo.
if exist "web_research_gw!GWeek!.json" (
  echo   [a] Sakatlik : HAZIR (web_research_gw!GWeek!.json)
) else (
  echo   [a] Sakatlik : EKSIK - henuz olusturulmadi
)
if exist "fiyat_gw!GWeek!.json" (
  echo   [b] Fiyat    : HAZIR (fiyat_gw!GWeek!.json)
) else (
  echo   [b] Fiyat    : EKSIK - henuz olusturulmadi
)
if exist "nostradamus_fixtures_gw!GWeek!.json" (
  echo   [c] Oranlar  : HAZIR (nostradamus_fixtures_gw!GWeek!.json)
) else (
  echo   [c] Oranlar  : EKSIK - henuz olusturulmadi
)
if exist "gw!GWeek!_kadro_onerisi.xlsx" (
  echo   [e] Kadro    : HAZIR (gw!GWeek!_kadro_onerisi.xlsx)
) else (
  echo   [e] Kadro    : HENUZ uretilmedi
)
echo.
echo --- Oneri ---
set "onerilen=a"
if exist "web_research_gw!GWeek!.json" set "onerilen=b"
if exist "web_research_gw!GWeek!.json" if exist "fiyat_gw!GWeek!.json" set "onerilen=c"
if exist "web_research_gw!GWeek!.json" if exist "fiyat_gw!GWeek!.json" if exist "nostradamus_fixtures_gw!GWeek!.json" set "onerilen=d"
if exist "gw!GWeek!_kadro_onerisi.xlsx" set "onerilen=f"
echo   Bundan sonra [!onerilen!] adimina gecmelisin.
echo.
pause
goto yeni_hafta

REM ============================================================
REM [2a] SAKATLIK/CEZA VERISI
REM ============================================================
:adim_2a
cls
echo ==================================================================
echo   ADIM 2a - SAKATLIK/CEZA VERISI TOPLA
echo ==================================================================
echo.
echo Bu adimda bu hafta oynamayacak/sakat/cezali oyunculari tespit
echo edecegiz. Kaynak: tff.org (cezalar) + fotmob + spor basini (sakatlik).
echo.
echo ADIM 1: web_arastirma_prompti.md dosyasini aciyorum...
echo   (Notepad ile acilacak. Icindeki promptu kopyala.)
echo.
pause
start notepad "web_arastirma_prompti.md"
echo.
echo ADIM 2: Promptu bir web AI'ya yapistir (Gemini, ChatGPT, Claude web).
echo   AI'a soyle de:
echo     "Turkiye Trendyol Super Lig icin hafta %GWeek% oncesi
echo      sakatlik, cezali durum ve muhtemel 11 durumunu arastir."
echo.
echo ADIM 3: AI sana JSON formatinda cevap verecek. Su dosya adıyla
echo   kaydet (ayni klasore, rehber.bat'in yanina):
echo.
echo   web_research_gw%GWeek%.json
echo.
echo ADIM 4: Kaydettin mi?
set /p kaydetti="Dosyayi kaydettin mi? (e/h): "
if /i not "!kaydetti!"=="e" (
  echo.
  echo Tamam, bu adimi simdilik atladin. Istedigin zaman [2] ^> [a]'ya
  echo geri donup tamamlayabilirsin.
  pause
  goto yeni_hafta
)
if not exist "web_research_gw!GWeek!.json" (
  echo.
  echo [HATA] Dosya bulunamadi: web_research_gw!GWeek!.json
  echo   Dosyayi dogru klasore kaydettiginden emin ol.
  echo   Klasor: %CD%
  pause
  goto yeni_hafta
)
echo.
echo [TAMAM] web_research_gw!GWeek!.json hazir.
echo   Siradaki adim: [b] Fiyat verisi topla
echo.
pause
goto adim_2b

REM ============================================================
REM [2b] FIYAT VERISI
REM ============================================================
:adim_2b
cls
echo ==================================================================
echo   ADIM 2b - FIYAT VERISI TOPLA
echo ==================================================================
echo.
echo TFF Fantezi Lig'de oyuncu fiyatlari oyunun KENDI ic ekonomisi -
echo baska hicbir yerde yayinlanmiyor. Bu yuzden TFF uygulamasindan
echo ekran goruntusu alip AI'a cevirecegiz.
echo.
echo ADIM 1: TFF Fantezi Lig uygulamasini ac (telefonda veya web).
echo   - Web: https://tfffantezilig.com/kadro-secimi
echo   - "Transferler" veya "Piyasa" ekranina git.
echo   - Kadrosundaki oyuncularin guncel fiyat listesini bul.
echo.
echo ADIM 2: Ekran goruntusu al. (Tum kadroyu goremiyorsan birden
echo   fazla ekran goruntusu alabilirsin.)
echo.
echo ADIM 3: fiyat_guncelleme_prompti.md dosyasini aciyorum...
echo   (Notepad ile acilacak. Icindeki promptu kopyala.)
echo.
pause
start notepad "fiyat_guncelleme_prompti.md"
echo.
echo ADIM 4: Bir AI'a git (Gemini - ekran goruntusu okuyabiliyor).
echo   - Promptu yapistir
echo   - Ekran goruntusu/lerini yukle
echo   - AI sana JSON formatinda fiyat listesi verecek
echo.
echo ADIM 5: JSON'i su dosya adıyla kaydet:
echo   fiyat_gw%GWeek%.json
echo.
echo ADIM 6: Kaydettin mi?
set /p kaydetti="Dosyayi kaydettin mi? (e/h): "
if /i not "!kaydetti!"=="e" (
  echo.
  echo Tamam, fiyat guncellemesini atladin. Daha sonra tamamlayabilirsin.
  echo   Not: Fiyat guncellenmezse sistem gecmis haftanin fiyatiyla
  echo   kadro kurmaya calisir. Cok farkliysa kadro baskalasabilir.
  pause
  goto yeni_hafta
)
if not exist "fiyat_gw!GWeek!.json" (
  echo.
  echo [HATA] Dosya bulunamadi: fiyat_gw!GWeek!.json
  echo   Klasor: %CD%
  pause
  goto yeni_hafta
)
echo.
echo [TAMAM] fiyat_gw!GWeek!.json hazir.
echo   Siradaki adim: [c] Nostradamus oranlari topla
echo.
pause
goto adim_2c

REM ============================================================
REM [2c] NOSTRADAMUS ORANLARI
REM ============================================================
:adim_2c
cls
echo ==================================================================
echo   ADIM 2c - NOSTRADAMUS ORANLARI TOPLA
echo ==================================================================
echo.
echo Nostradamus = TFF Fantezi Lig'in 9 mac tahmin oyunu. Her hafta
echo 9 mac icin 1/X/2 tahmini yaparsin. Sistem bahis oranlarindan
echo en olasi sonucu hesapliyor.
echo.
echo ADIM 1: Bu haftanin 9 macini bul.
echo   - TFF Fantezi Lig uygulamasinda "Nostradamus" sekmesi
echo   - VEYA tfffantezilig.com fikstur sayfasi
echo.
echo ADIM 2: Her mac icin 1X2 kapanis oranlarini topla.
echo   Kaynak: oddsportal.com veya flashscore.com
echo   - B365 (Bet365) ve PS (Pinnacle) kapanis oranlarini al
echo   - Sadece tek kaynak bulabiliyorsan da olur (B365 yeterli)
echo.
echo ADIM 3: nostradamus_fixtures_gw%GWeek%.json dosyasini hazirla.
if exist "nostradamus_fixtures_gw!GWeek!.json" (
  echo   (Dosya zaten var, notepad'te aciyorum - uzerine yazabilirsin)
) else (
  echo   (Yeni dosya olusturuyorum, icine ornek sablon koyuyorum)
  call :sablon_olustur "nostradamus_fixtures_gw!GWeek!.json"
)
echo.
pause
start notepad "nostradamus_fixtures_gw!GWeek!.json"
echo.
echo ADIM 4: Dosyayi kaydettin mi?
set /p kaydetti="Dosyayi kaydettin mi? (e/h): "
if /i not "!kaydetti!"=="e" (
  echo.
  echo Tamam, Nostradamus adimini atladin.
  echo   UYARI: Nostradamus tahmin olmadan o hafta +10 puan firsati kacar.
  pause
  goto yeni_hafta
)
echo.
echo [TAMAM] nostradamus_fixtures_gw!GWeek!.json hazir.
echo   Siradaki adim: [d] Sisteme yukle
echo.
pause
goto adim_2d

REM ============================================================
REM [2d] SISTEME YUKLE
REM ============================================================
:adim_2d
cls
echo ==================================================================
echo   ADIM 2d - SISTEME YUKLE (3 JSON'i isle)
echo ==================================================================
echo.
echo Bu adimda hazirladigin 3 JSON dosyasini sisteme isleyecegiz.
echo Her biri once DRY-RUN (kontrol), sonra onay ile UYGULA.
echo.

REM --- 2d.1 Sakatlik ---
echo --- 2d.1 SAKATLIK YUKLEME ---
if not exist "web_research_gw!GWeek!.json" (
  echo   [ATLANDI] web_research_gw!GWeek!.json bulunamadi.
  echo   [2] ^> [a] adimina geri donup olustur.
) else (
  echo   Dry-run calistiriliyor...
  echo.
  python update_from_web_research.py "%EXCEL%" "web_research_gw!GWeek!.json"
  echo.
  echo   Yukaridaki raporu oku. Isim eslesmeyenler veya reddedilenler
  echo   varsa once JSON'i duzeltip tekrar dry-run yap.
  echo.
  set /p onay="Uygula? (e/h): "
  if /i "!onay!"=="e" (
    python update_from_web_research.py "%EXCEL%" "web_research_gw!GWeek!.json" --apply
    echo   [TAMAM] Sakatlik verisi islendi.
  ) else (
    echo   [ATLANDI] Sakatlik uygulanmadi.
  )
)
echo.
pause

REM --- 2d.2 Fiyat ---
cls
echo ==================================================================
echo   ADIM 2d - SISTEME YUKLE (devam)
echo ==================================================================
echo.
echo --- 2d.2 FIYAT YUKLEME ---
if not exist "fiyat_gw!GWeek!.json" (
  echo   [ATLANDI] fiyat_gw!GWeek!.json bulunamadi.
  echo   [2] ^> [b] adimina geri donup olustur.
) else (
  echo   Dry-run calistiriliyor...
  echo.
  python ingest_price_updates.py "%EXCEL%" "fiyat_gw!GWeek!.json"
  echo.
  set /p onay="Uygula? (e/h): "
  if /i "!onay!"=="e" (
    python ingest_price_updates.py "%EXCEL%" "fiyat_gw!GWeek!.json" --apply
    echo   [TAMAM] Fiyat verisi islendi.
  ) else (
    echo   [ATLANDI] Fiyat uygulanmadi.
  )
)
echo.
pause

REM --- 2d.3 Nostradamus tahmin ---
cls
echo ==================================================================
echo   ADIM 2d - SISTEME YUKLE (devam)
echo ==================================================================
echo.
echo --- 2d.3 NOSTRADAMUS TAHMINI URET ---
if not exist "nostradamus_fixtures_gw!GWeek!.json" (
  echo   [ATLANDI] nostradamus_fixtures_gw!GWeek!.json bulunamadi.
  echo   [2] ^> [c] adimina geri donup olustur.
) else (
  echo   Tahmin uretiliyor...
  echo.
  python nostradamus_predict.py "nostradamus_fixtures_gw!GWeek!.json"
  echo.
  echo   [TAMAM] Tahminler nostradamus_predict_gw!GWeek!.json olarak kaydedildi.
  echo   Bu dosyayi [2f] adiminda TFF'ye elle girerken kullanacaksin.
)
echo.
pause
goto adim_2e

REM ============================================================
REM [2e] KADRO OPTIMIZASYONU
REM ============================================================
:adim_2e
cls
echo ==================================================================
echo   ADIM 2e - KADRO OPTIMIZASYONU
echo ==================================================================
echo.
echo Simdi sistem verileri kullanarak en iyi 15 oyuncuyu secer.
echo Cikti: gw%GWeek%_kadro_onerisi.xlsx
echo.
echo   - 2 Kaleci, 5 Defans, 5 Orta Saha, 3 Forvet
echo   - Toplam 100M TL budget
echo   - Ayni takimdan max 3 oyuncu
echo   - Kaptan ve yedek kaptan otomatik secilir
echo   - Yedek sirasi otomatik belirlenir
echo.
pause
echo Calistiriliyor...
echo.
python run_gameweek.py "%EXCEL%" --gameweek %GWeek%
echo.
if exist "gw!GWeek!_kadro_onerisi.xlsx" (
  echo [TAMAM] Kadro onerisi hazir: gw!GWeek!_kadro_onerisi.xlsx
  echo   Dosyayi otomatik aciyorum...
  start "" "gw!GWeek!_kadro_onerisi.xlsx"
  echo.
  echo   Excel acildi. Sari satir = KAPTAN, acik sari = YEDEK KAPTAN,
  echo   gri satir = BENCH. Satirlar pozisyona gore sirali (GK ^> DEF ^> MID ^> FWD).
  echo.
  echo Siradaki adim: [f] TFF'ye elle gir
) else (
  echo [HATA] Kadro dosyasi olusturulamadi. Yukaridaki hata mesajini oku.
)
echo.
pause
goto adim_2f

REM ============================================================
REM [2f] TFF'YE ELLE GIR
REM ============================================================
:adim_2f
cls
echo ==================================================================
echo   ADIM 2f - TFF'YE ELLE GIR
echo ==================================================================
echo.
echo Sistem kadroyu hazirladi, ama TFF'ye SEN gireceksin. Otomatik
echo gonderim yok (oyun API vermiyor).
echo.
echo Bu adimi sirayla yap:
echo.
echo   1. TFF Fantezi Lig uygulamasini ac
echo      Web: https://tfffantezilig.com/kadro-secimi
echo.
echo   2. KADRO SECIMI - 15 oyuncu sec:
echo      - gw%GWeek%_kadro_onerisi.xlsx dosyasini ac
echo      - "STARTER" ve "BENCH" etiketlerine bak
echo      - Once mevcut kadrodan CIKACAK oyunculari cikar
echo      - Sonra EKLENECEK oyunculari ekle
echo      - 100M TL budget'i asma
echo.
echo   3. ILK 11 - formasyonu yerlestir:
echo      - "STARTER" etiketli 11 oyuncu ilk 11'de olmali
echo      - Min 1 Kaleci, min 3 Defans, min 1 Forvet
echo.
echo   4. KAPTAN:
echo      - role=CAPTAN olan oyuncuyu kaptan yap (puan 2x)
echo      - role=VICE_CAPTAIN olan oyuncuyu yedek kaptan yap
echo.
echo   5. YEDEK SIRASI:
echo      - Bench oyuncularini oncelik sirasina gore diz
echo      - Excel'deki siraya uy (bench_gk once, sonra 1-2-3)
echo.
echo   6. NOSTRADAMUS:
echo      - "Nostradamus" sekmesine git
echo      - 9 mac icin nostradamus_predict_gw%GWeek%.json'daki
echo        "prediction" alanini kullan (1/X/2)
echo      - 9 macin TAMAMINI doldur (+1 puan)
echo.
echo   7. MENAJER KARTI (opsiyonel):
echo      - Deadline'dan en az 15 dk ONCE satin al
echo      - Son 15 dk'da alinamiyor (oyun kurali)
echo.
echo --- ONEMLI ZAMAN KISITI ---
echo   Deadline = haftanin ilk macindan 1 saat once.
echo   Bu saatten sonra kadro/transfer/kaptan DEGISTIRILEMEZ.
echo   Saatini kontrol et, erken gir.
echo.
echo ==================================================================
echo   Tum adimlari uyguladin mi?
echo ==================================================================
set /p bitti="TFF'ye kadroyu girdin mi? (e/h): "
if /i "!bitti!"=="e" (
  echo.
  echo [BASARILI] Hafta %GWeek% hazirligi tamam!
  echo   Maclar oynandiktan sonra [3] MAQLAR BITTI adimina gel.
  echo   Orada gerçek sonuçları sisteme yükleyecegiz.
  echo.
  set /a nextWeek=GWeek+1
  echo   Not: Bir sonraki hafta hazirligina baslamak istersen
  echo   ana menude GWeek'i !nextWeek! olarak guncelle.
)
echo.
pause
goto ana_menu

REM ============================================================
REM [3] MAQLAR BITTI - SONUQLARI GIR
REM ============================================================
:maclar_bitti
cls
echo ==================================================================
echo   [3] MAQLAR BITTI - SONUQLARI GIR (Hafta %GWeek%)
echo ==================================================================
echo.
echo Bu adim haftanin maclari bitince yapilir. Gercek performans
echo verisini (dakika, gol, asist, kart, puan) sisteme yukleriz.
echo Bu veri BIR SONRAKI haftanin kadro optimizasyonunu iyilestirir.
echo.

REM --- 3a: Sonuç JSON'u oluştur ---
echo --- 3a: MAC SONUQLARINI JSON'A CEVIR ---
echo.
echo ADIM 1: TFF Fantezi Lig uygulamasinda "Puanim" ekranina git.
echo   - Bu ekran haftanin tum oyuncularinin gercek puanini gosterir
echo   - Ekran goruntusu al
echo.
echo ADIM 2: match_sonuclari_prompti.md dosyasini aciyorum...
pause
start notepad "match_sonuclari_prompti.md"
echo.
echo ADIM 3: Gemini (goruntu okuyabilen AI) git.
echo   - Promptu yapistir
echo   - Ekran goruntusunu yukle
echo   - AI sana JSON verecek
echo.
echo ADIM 4: JSON'i su dosya adıyla kaydet:
echo   match_sonuclari_gw%GWeek%.json
echo.
echo ADIM 5: Kaydettin mi?
set /p kaydetti="Dosyayi kaydettin mi? (e/h): "
if /i not "!kaydetti!"=="e" (
  echo.
  echo Tamam, bu adimi atladin. Maclar bittiginde tekrar gel.
  pause
  goto ana_menu
)
if not exist "match_sonuclari_gw!GWeek!.json" (
  echo [HATA] match_sonuclari_gw!GWeek!.json bulunamadi.
  pause
  goto ana_menu
)
echo.
echo [TAMAM] match_sonuclari_gw!GWeek!.json hazir.
echo.

REM --- 3b: Sisteme yükle ---
echo --- 3b: SONUQLARI SISTEME YUKLE ---
echo.
echo Dry-run calistiriliyor...
echo.
python ingest_gameweek_results.py "%EXCEL%" "match_sonuclari_gw!GWeek!.json"
echo.
echo Raporu oku. Isim eslesmeyenler varsa once JSON'i duzelt.
echo.
set /p onay="Uygula? (e/h): "
if /i "!onay!"=="e" (
  python ingest_gameweek_results.py "%EXCEL%" "match_sonuclari_gw!GWeek!.json" --apply
  echo.
  echo [TAMAM] Hafta %GWeek% sonuclari sisteme islendi.
  echo.
  echo Bu veri bir sonraki haftanin kadro optimizasyonu icin kullanilacak.
  echo   - xp_model.py gercek performans ile prior kalibrasyonu yapar
  echo   - Birikme adimindan sonra (5-6 hafta) kadro onerileri daha iyi
  echo.
  set /a nextWeek=GWeek+1
  echo BIR SONRAKI HAFTA: GWeek'i !nextWeek! olarak guncelle ve
  echo [2] YENI HAFTA HAZIRLIGI'na basla.
) else (
  echo [ATLANDI] Sonuclar uygulanmadi.
)
echo.
pause
goto ana_menu

REM ============================================================
REM [4] TRANSFER PENCERESI
REM ============================================================
:transfer_penceresi
cls
echo ==================================================================
echo   [4] TRANSFER PENCERESI (Sezon Ortasi)
echo ==================================================================
echo.
echo BU ADIM SADECE 17. HAFTADAN SONRA KULLANILIR.
echo Sezon ortasi transfer penceresi (genelde Ocak basi) acildiginda
echo yeni gelen/giden/transfer olan oyunculari sisteme isle.
echo.
if !GWeek! LSS 17 (
  echo [UYARI] Su anki hafta %GWeek%. Transfer penceresi 17. haftadan
  echo   once kullanilmaz. Eger emin degilsen [5] SISTEM DURUMU'na bak.
  echo.
  set /p yine_de="Yine de devam et? (e/h): "
  if /i not "!yine_de!"=="e" goto ana_menu
)
echo.
echo ADIM 1: transfer_prompti.md dosyasini aciyorum...
pause
start notepad "transfer_prompti.md"
echo.
echo ADIM 2: Bir web AI'ya git (Gemini, ChatGPT).
echo   - Promptu yapistir
echo   - "Transfermarkt'tan son transferleri ara" de
echo   - AI sana JSON formatinda transfer listesi verecek
echo.
echo ADIM 3: JSON'i su dosya adıyla kaydet:
echo   transfer_pencere_YYYYMMDD.json  (YYYYMMDD = bugunun tarihi)
echo.
echo ADIM 4: Kaydettin mi?
set /p kaydetti="Dosyayi kaydettin mi? (e/h): "
if /i not "!kaydetti!"=="e" (
  pause
  goto ana_menu
)
echo.
echo --- Transfer dosyasini sec ---
echo Olusturdugun JSON dosyasinin adini tam yaz:
set /p tr_json="Dosya adi (ornek: transfer_pencere_20260115.json): "
if "!tr_json!"=="" (
  echo [HATA] Bos birakilamaz.
  pause
  goto ana_menu
)
if not exist "!tr_json!" (
  echo [HATA] Dosya bulunamadi: !tr_json!
  echo   Klasor: %CD%
  pause
  goto ana_menu
)
echo.
echo Dry-run calistiriliyor...
echo.
python ingest_transfer_window.py "%EXCEL%" "!tr_json!"
echo.
echo Raporu oku:
echo   - "in" : yeni oyuncu (yeni player_id atanir)
echo   - "out": pasiflestirilir (satir silinmez, is_active=0)
echo   - "move": takimi guncellenir
echo.
set /p onay="Uygula? (e/h): "
if /i "!onay!"=="e" (
  python ingest_transfer_window.py "%EXCEL%" "!tr_json!" --apply
  echo.
  echo [TAMAM] Transferler islendi.
  echo   Yeni oyuncular bir sonraki kadro optimizasyonunda secilebilir.
) else (
  echo [ATLANDI] Transferler uygulanmadi.
)
echo.
pause
goto ana_menu

REM ============================================================
REM [5] SISTEM DURUMU
REM ============================================================
:sistem_durumu
cls
echo ==================================================================
echo   [5] SISTEM DURUMU
echo ==================================================================
echo.
echo --- MEVCUT DOSYALAR ---
echo Excel: %EXCEL% 
if exist "%EXCEL%" (
  echo   [OK] Bulundu
) else (
  echo   [EKSIK] Bulunamadi!
)
echo.
echo --- GW %GWeek% ICIN HAZIRLIK ---
if exist "web_research_gw!GWeek!.json" (
  echo   [a] Sakatlik       : HAZIR
) else (
  echo   [a] Sakatlik       : EKSIK
)
if exist "fiyat_gw!GWeek!.json" (
  echo   [b] Fiyat          : HAZIR
) else (
  echo   [b] Fiyat          : EKSIK
)
if exist "nostradamus_fixtures_gw!GWeek!.json" (
  echo   [c] Oranlar        : HAZIR
) else (
  echo   [c] Oranlar        : EKSIK
)
if exist "nostradamus_predict_gw!GWeek!.json" (
  echo   Nostradamus tahmin : HAZIR
) else (
  echo   Nostradamus tahmin : HENUZ uretilmedi
)
if exist "gw!GWeek!_kadro_onerisi.xlsx" (
  echo   [e] Kadro          : HAZIR
) else (
  echo   [e] Kadro          : HENUZ uretilmedi
)
if exist "match_sonuclari_gw!GWeek!.json" (
  echo   [3] Sonuclar       : HAZIR
) else (
  echo   [3] Sonuclar       : HENUZ girilmedi
)
echo.
echo --- TAVSIYE ---
echo.
echo Su an %GWeek%. haftasinin hazirligindasin.
echo.
if not exist "match_sonuclari_gw!GWeek!.json" if exist "gw!GWeek!_kadro_onerisi.xlsx" (
  echo Maclar henuz oynanmadi veya sonuclar girilmedi.
  echo   - Maclar bitince [3]'e gel.
  echo   - Yeni haftaya gecmek istersen: GWeek'i bir artir.
)
if not exist "gw!GWeek!_kadro_onerisi.xlsx" (
  echo Kadro henuz uretilmedi.
  echo   [2] YENI HAFTA HAZIRLIGI'na girip adimlari takip et.
)
echo.
pause
goto ana_menu

REM ============================================================
REM [6] BACKTEST
REM ============================================================
:backtest
cls
echo ==================================================================
echo   [6] BACKTEST - Sistem Saglik Kontrolu
echo ==================================================================
echo.
echo Bu adim sistemimin gecmis sezonlarda ne kadar iyi tahmin
echo yaptigini olcer. Ayda bir calistirmak yeterli.
echo.
echo Bakmasi gerekenler:
echo   - Brier skoru 0.55 civarindaysa: SISTEM SAGLIKLI
echo   - Brier 0.60 uzerindense: Bir seyler degismis, not al
echo   - Rastgele tahmin = 0.6667 (kötü)
echo.
pause
if not exist "nostradamus\superlig_odds.db" (
  echo [HATA] nostradamus\superlig_odds.db bulunamadi.
  echo   Once su komutu calistir:
  echo   python nostradamus\build_superlig_db.py ^<unified.db yolu^> nostradamus\superlig_odds.db
  pause
  goto ana_menu
)
echo Calistiriliyor...
echo.
python nostradamus\backtest_devig_baseline.py nostradamus\superlig_odds.db --seasons 3
echo.
echo Yukaridaki ciktiyi oku. Brier skoru "TOPLAM" satirinda.
echo Sonucu docs\07_GELISTIRME_GUNLUGU.md'ye not et (her seferinde).
echo.
pause
goto ana_menu

REM ============================================================
REM CIKIS
REM ============================================================
:cikis
echo.
echo Rehber modu kapatiliyor.
echo   Unutma: Maclar bitince [3]'e gel.
echo           Yeni haftaya gecince GWeek'i artir.
echo.
endlocal
exit /b 0

REM ============================================================
REM ALT YORDAM: Nostradamus sablonu olustur
REM ============================================================
:sablon_olustur
REM Parametre %1 = dosya adi
(
echo {
echo   "gameweek": %GWeek%,
echo   "prediction_date": "2026-MM-DD",
echo   "fixtures": [
echo     {
echo       "home_team": "Ev Sahibi Takim",
echo       "away_team": "Deplasman Takim",
echo       "match_date": "2026-MM-DD",
echo       "odds": {
echo         "B365": {"H": 1.85, "D": 3.6, "A": 4.2},
echo         "PS":  {"H": 1.88, "D": 3.55, "A": 4.25}
echo       }
echo     }
echo   ]
echo }
) > "%~1"
echo   Sablon olusturuldu: %~1
echo   9 maci fixtures dizisine ekle (yukaridaki ornegi kopyala).
goto :eof
