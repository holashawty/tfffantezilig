@echo off
setlocal enabledelayedexpansion

REM UTF-8 Karakter seti
chcp 65001 >nul 2>&1

REM Calisma dizinini BAT dosyasinin bulundugu klasore sabitle
cd /d "%~dp0"

REM ANSI Renk Kodlari
set "ESC= "
set "C_RESET= [0m"
set "C_BOLD= [1m"
set "C_CYAN= [96m"
set "C_GREEN= [92m"
set "C_YELLOW= [93m"
set "C_BLUE= [94m"
set "C_MAGENTA= [95m"
set "C_RED= [91m"
set "C_WHITE= [97m"
set "C_GRAY= [90m"

REM Varsayilan Ayarlar
set "EXCEL=oyuncu_veritabani.xlsx"
set "GWeek=2"

:ana_menu
cls
echo %C_CYAN%==================================================================%C_RESET%
echo %C_BOLD%%C_WHITE%                  ⚡ TFF FANTEZI LIG YONETIM MERKEZI ⚡%C_RESET%
echo %C_CYAN%==================================================================%C_RESET%
echo   %C_YELLOW%● Aktif Hafta       :%C_RESET% %C_BOLD%%C_GREEN%Hafta !GWeek!%C_RESET%
echo   %C_YELLOW%● Aktif Veritabani  :%C_RESET% %C_WHITE%!EXCEL!%C_RESET%
echo %C_CYAN%==================================================================%C_RESET%
echo.
echo   %C_BOLD%%C_GREEN%[1] YENI HAFTA HAZIRLIGI (Maclar Baslamadan Once / Deadline)%C_RESET%
echo       %C_GRAY%:: 1-Tikla Express Mod veya Adim Adim: Fiyat, Sakatlik, Kadro Optimizasyonu%C_RESET%
echo.
echo   %C_BOLD%%C_BLUE%[2] GECEN HAFTANIN VERILERINI ISLE (Maclar Bittikten Sonra)%C_RESET%
echo       %C_GRAY%:: 9 Macin Skorlari, Kartlar, Puanlar, GameweekLog ^& SeasonStats Guncelleme%C_RESET%
echo.
echo   %C_BOLD%%C_MAGENTA%[3] SISTEM AYARLARI VE LIDERLIK TABLOSU%C_RESET%
echo       %C_GRAY%:: Hafta No Degistir, Excel'i Ac, Sezonluk Liderlik Tablosunu Gor%C_RESET%
echo.
echo   %C_RED%[0] Cikis%C_RESET%
echo %C_CYAN%==================================================================%C_RESET%
set /p anasecim="%C_BOLD%%C_YELLOW%Seciminiz [0-3]: %C_RESET%"

if "!anasecim!"=="1" goto yeni_hafta
if "!anasecim!"=="2" goto maclar_bitti
if "!anasecim!"=="3" goto ayarlar_menu
if "!anasecim!"=="0" goto cikis
goto ana_menu


REM ============================================================
REM [1] YENI HAFTA HAZIRLIGI (DEADLINE ONCESI)
REM ============================================================
:yeni_hafta
cls
echo %C_GREEN%==================================================================%C_RESET%
echo %C_BOLD%%C_WHITE%  [1] YENI HAFTA HAZIRLIGI - Hafta !GWeek! (Deadline Oncesi)%C_RESET%
echo %C_GREEN%==================================================================%C_RESET%
echo   %C_YELLOW%Hedef: Deadline oncesi en guncel verilerle 15 kisilik en iyi kadroyu kurmak.%C_RESET%
echo %C_GREEN%==================================================================%C_RESET%
echo.
echo   %C_BOLD%%C_CYAN%*** EN HIZLI VE OTOMATIK YONTEM:%C_RESET%
echo   %C_BOLD%%C_GREEN%[x] HIZLI MOD (1-Tikla Express Pipeline)%C_RESET%
echo       %C_GRAY%Mevcut JSON'lari algilar, Excel'i gunceller, MILP kadroyu cozer ve acar.%C_RESET%
echo.
echo   %C_BOLD%%C_WHITE%--- ADIM ADIM MANUEL REHBER ---%C_RESET%
echo   %C_WHITE%[a]%C_RESET% Sakatlik/Ceza Verisi Topla %C_GRAY%(AI Promptu ile 0dk/0xp filtreleme)%C_RESET%
echo   %C_WHITE%[b]%C_RESET% Guncel Fiyatlari Topla %C_GRAY%(tfffantezilig.com 1-tikla indirme)%C_RESET%
echo   %C_WHITE%[c]%C_RESET% Nostradamus Oranlari Topla %C_GRAY%(Oddsportal canli 1X2 oranlari)%C_RESET%
echo   %C_WHITE%[d]%C_RESET% Toplanan JSON'lari Sisteme Isle %C_GRAY%(Dry-run onayi ile)%C_RESET%
echo   %C_WHITE%[e]%C_RESET% Matematiksel Kadro Optimizasyonu %C_GRAY%(gw!GWeek!_kadro_onerisi.xlsx)%C_RESET%
echo   %C_WHITE%[f]%C_RESET% TFF Uygulamasina Kadroyu Girme Rehberi
echo.
echo   %C_YELLOW%[0] Dosya Durumu Kontrolu%C_RESET%
echo   %C_RED%[9] Ana Menuye Don%C_RESET%
echo %C_GREEN%==================================================================%C_RESET%
set /p adim="%C_BOLD%%C_YELLOW%Seciminiz: %C_RESET%"

if /i "!adim!"=="x" goto adim_2x
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
echo %C_CYAN%==================================================================%C_RESET%
echo %C_BOLD%%C_WHITE%  HAFTA !GWeek! DOSYA VE HAZIRLIK DURUMU%C_RESET%
echo %C_CYAN%==================================================================%C_RESET%
echo.
if exist "web_research_gw!GWeek!.json" (
  echo   [a] Sakatlik/Ceza JSON : %C_GREEN%[HAZIR]%C_RESET% (web_research_gw!GWeek!.json)
) else (
  echo   [a] Sakatlik/Ceza JSON : %C_RED%[EKSIK]%C_RESET%
)
if exist "fiyat_gw!GWeek!.json" (
  echo   [b] Fiyat Verisi JSON  : %C_GREEN%[HAZIR]%C_RESET% (fiyat_gw!GWeek!.json)
) else (
  echo   [b] Fiyat Verisi JSON  : %C_RED%[EKSIK]%C_RESET%
)
if exist "nostradamus_fixtures_gw!GWeek!.json" (
  echo   [c] Oranlar JSON       : %C_GREEN%[HAZIR]%C_RESET% (nostradamus_fixtures_gw!GWeek!.json)
) else (
  echo   [c] Oranlar JSON       : %C_RED%[EKSIK]%C_RESET%
)
if exist "gw!GWeek!_kadro_onerisi.xlsx" (
  echo   [e] Kadro Onerisi      : %C_GREEN%[URETILDI]%C_RESET% (gw!GWeek!_kadro_onerisi.xlsx)
) else (
  echo   [e] Kadro Onerisi      : %C_YELLOW%[HENUZ URETILMEDI]%C_RESET%
)
echo.
echo %C_CYAN%==================================================================%C_RESET%
pause
goto yeni_hafta

:adim_2x
cls
echo %C_GREEN%==================================================================%C_RESET%
echo %C_BOLD%%C_WHITE%  [1x] HIZLI MOD (EXPRESS PIPELINE) - Hafta !GWeek!%C_RESET%
echo %C_GREEN%==================================================================%C_RESET%
echo.
echo %C_YELLOW%Mevcut JSON dosyalari isleniyor ve kadro olusturuluyor...%C_RESET%
echo.
python quick_pipeline.py --excel "%EXCEL%" --gameweek !GWeek! --apply
echo.
pause
goto yeni_hafta

:adim_2a
cls
echo %C_GREEN%==================================================================%C_RESET%
echo %C_BOLD%%C_WHITE%  [1a] SAKATLIK VE CEZA VERISI TOPLA (Hafta !GWeek!)%C_RESET%
echo %C_GREEN%==================================================================%C_RESET%
echo.
echo %C_YELLOW%1. 462 oyuncu ve 18 kulup kadrosuyla prompt hazirlaniyor...%C_RESET%
python generate_injury_prompt.py --gameweek !GWeek! --excel "%EXCEL%"
echo.
echo %C_GREEN%2. web_arastirma_prompti.md aciliyor. Metni AI'a yapistirin.%C_RESET%
start notepad "web_arastirma_prompti.md"
echo.
echo 3. AI'dan gelen JSON yanitini su isimle bu klasore kaydedin:
echo    %C_BOLD%%C_CYAN%web_research_gw!GWeek!.json%C_RESET%
echo.
pause
goto yeni_hafta

:adim_2b
cls
echo %C_GREEN%==================================================================%C_RESET%
echo %C_BOLD%%C_WHITE%  [1b] GUNCEL FIYAT VERISINI TOPLA (Hafta !GWeek!)%C_RESET%
echo %C_GREEN%==================================================================%C_RESET%
echo.
echo   %C_BOLD%%C_GREEN%[1] TARAYICI KONSOLU ILE 1-TIKLA INDIR (tff_fantezi_export.js)%C_RESET%
echo   %C_WHITE%[2] AI Promptu ile Topla (fiyat_guncelleme_prompti.md)%C_RESET%
echo   %C_RED%[0] Geri Don%C_RESET%
echo.
set /p fsecim="%C_BOLD%%C_YELLOW%Secim [0-2]: %C_RESET%"

if "!fsecim!"=="1" (
  start notepad "tff_fantezi_export.js"
  echo %C_GREEN%tff_fantezi_export.js acildi.%C_RESET%
  echo tfffantezilig.com sitesinde F12 Console'a yapistirip "Fiyatlari Indir"e basin.
  pause
  goto yeni_hafta
)
if "!fsecim!"=="2" (
  start notepad "fiyat_guncelleme_prompti.md"
  pause
  goto yeni_hafta
)
goto yeni_hafta

:adim_2c
cls
echo %C_GREEN%==================================================================%C_RESET%
echo %C_BOLD%%C_WHITE%  [1c] NOSTRADAMUS ORANLARI TOPLA (Hafta !GWeek!)%C_RESET%
echo %C_GREEN%==================================================================%C_RESET%
echo.
echo   %C_BOLD%%C_GREEN%[1] TARAYICI KONSOLU ILE INDIR (oddsportal_export.js)%C_RESET%
echo   %C_WHITE%[2] WEB AI ORAN TOPLAMA PROMPTU (nostradamus_oran_prompti.md)%C_RESET%
echo   %C_YELLOW%[3] Dosyayi Notepad ile Duzenle (nostradamus_fixtures_gw!GWeek!.json)%C_RESET%
echo   %C_RED%[0] Geri Don%C_RESET%
echo.
set /p osecim="%C_BOLD%%C_YELLOW%Secim [0-3]: %C_RESET%"

if "!osecim!"=="1" (
  start notepad "oddsportal_export.js"
  pause
  goto yeni_hafta
)
if "!osecim!"=="2" (
  start notepad "nostradamus_oran_prompti.md"
  pause
  goto yeni_hafta
)
if "!osecim!"=="3" (
  start notepad "nostradamus_fixtures_gw!GWeek!.json"
  pause
  goto yeni_hafta
)
goto yeni_hafta

:adim_2d
cls
echo %C_GREEN%==================================================================%C_RESET%
echo %C_BOLD%%C_WHITE%  [1d] SISTEME YUKLE (JSON Dosyalarini Excel'e Isle)%C_RESET%
echo %C_GREEN%==================================================================%C_RESET%
echo.
if exist "web_research_gw!GWeek!.json" (
  python update_from_web_research.py "%EXCEL%" "web_research_gw!GWeek!.json" --apply
)
if exist "fiyat_gw!GWeek!.json" (
  python ingest_price_updates.py "%EXCEL%" "fiyat_gw!GWeek!.json" --apply
)
if exist "nostradamus_fixtures_gw!GWeek!.json" (
  python nostradamus_predict.py "nostradamus_fixtures_gw!GWeek!.json"
)
echo.
pause
goto yeni_hafta

:adim_2e
cls
echo %C_GREEN%==================================================================%C_RESET%
echo %C_BOLD%%C_WHITE%  [1e] KADRO OPTIMIZASYONU - Hafta !GWeek!%C_RESET%
echo %C_GREEN%==================================================================%C_RESET%
echo.
python run_gameweek.py "%EXCEL%" --gameweek !GWeek!
echo.
if exist "gw!GWeek!_kadro_onerisi.xlsx" (
  start "" "gw!GWeek!_kadro_onerisi.xlsx"
)
echo.
pause
goto yeni_hafta

:adim_2f
cls
echo %C_GREEN%==================================================================%C_RESET%
echo %C_BOLD%%C_WHITE%  [1f] TFF'YE ELLE GIRIS REHBERI%C_RESET%
echo %C_GREEN%==================================================================%C_RESET%
echo.
echo   1. https://tfffantezilig.com/kadro-secimi adresine gidin.
echo   2. gw!GWeek!_kadro_onerisi.xlsx dosyasindaki 15 oyuncuyu secin.
echo   3. KAPTAN (2x) ve YEDEK KAPTAN secimlerini Excel'e gore ayarlayin.
echo   4. Yedek oyuncularin siralama onceligini Excel'deki sirayla dizin.
echo   5. Nostradamus tahminlerini nostradamus_predict_gw!GWeek!.json dosyasindan girin.
echo.
pause
goto yeni_hafta


REM ============================================================
REM [2] GECEN HAFTANIN VERILERINI ISLE (MACLAR SONRASI)
REM ============================================================
:maclar_bitti
cls
echo %C_BLUE%==================================================================%C_RESET%
echo %C_BOLD%%C_WHITE%  [2] GECEN HAFTANIN VERILERINI ISLE (Hafta Sonuclari)%C_RESET%
echo %C_BLUE%==================================================================%C_RESET%
echo.
echo   %C_BOLD%%C_GREEN%[1] Mac Sonuclarini ve Puanlari Sisteme Isle (match_sonuclari_gw!GWeek!.json)%C_RESET%
echo       %C_GRAY%GameweekLog, Fixtures skorlari ve SeasonStats liderlik tablosunu gunceller.%C_RESET%
echo.
echo   %C_CYAN%[2] Fiksturden 9 Maci 1-Tikla Cek (tff_fantezi_export.js)%C_RESET%
echo   %C_WHITE%[3] Sezonluk Liderlik Tablosunu Ekranda Gor (SeasonStats)%C_RESET%
echo   %C_RED%[9] Ana Menuye Don%C_RESET%
echo %C_BLUE%==================================================================%C_RESET%
set /p msecim="%C_BOLD%%C_YELLOW%Seciminiz [1-3, 9]: %C_RESET%"

if "!msecim!"=="1" goto isle_sonuclar
if "!msecim!"=="2" (
  start notepad "tff_fantezi_export.js"
  echo %C_GREEN%tff_fantezi_export.js acildi.%C_RESET%
  echo tfffantezilig.com sitesinde F12 Console'a yapistirip "9 Macin Resmi Istatistiklerini Indir"e basin.
  pause
  goto maclar_bitti
)
if "!msecim!"=="3" goto goruntule_liderlik
if "!msecim!"=="9" goto ana_menu
goto maclar_bitti

:isle_sonuclar
cls
echo %C_BLUE%==================================================================%C_RESET%
echo %C_BOLD%%C_WHITE%  MAC SONUCLARI VE OYUNCU PUANLARI ISLENIYOR...%C_RESET%
echo %C_BLUE%==================================================================%C_RESET%
echo.
if exist "match_sonuclari_gw!GWeek!.json" (
  python ingest_gameweek_results.py "%EXCEL%" "match_sonuclari_gw!GWeek!.json" --apply
) else (
  echo %C_RED%[HATA] match_sonuclari_gw!GWeek!.json bulunamadi!%C_RESET%
)
echo.
pause
goto maclar_bitti

:goruntule_liderlik
cls
echo %C_CYAN%==================================================================%C_RESET%
echo %C_BOLD%%C_WHITE%  TOP 15 SEZONLUK LIDERLIK TABLOSU (SeasonStats)%C_RESET%
echo %C_CYAN%==================================================================%C_RESET%
echo.
python -c "
import openpyxl, pandas as pd
wb = openpyxl.load_workbook('oyuncu_veritabani.xlsx', data_only=True)
if 'SeasonStats' in wb.sheetnames:
    ws = wb['SeasonStats']
    data = list(ws.iter_rows(values_only=True))[3:]
    df = pd.DataFrame(data[1:], columns=data[0])
    print(df.head(15)[['name', 'team', 'position_code', 'total_minutes', 'total_points', 'points_per_90', 'total_goals', 'total_assists', 'form_score']].to_string())
else:
    print('SeasonStats sayfasi bulunamadi.')
"
echo.
echo %C_CYAN%==================================================================%C_RESET%
pause
goto maclar_bitti


REM ============================================================
REM [3] SISTEM AYARLARI VE LIDERLIK TABLOSU
REM ============================================================
:ayarlar_menu
cls
echo %C_MAGENTA%==================================================================%C_RESET%
echo %C_BOLD%%C_WHITE%  [3] SISTEM AYARLARI VE ARACLAR%C_RESET%
echo %C_MAGENTA%==================================================================%C_RESET%
echo.
echo   [1] Aktif Hafta Numarasini Degistir %C_GRAY%(Su an: !GWeek!)%C_RESET%
echo   [2] Ana Excel Veritabanini Ac %C_GRAY%(oyuncu_veritabani.xlsx)%C_RESET%
echo   [3] Sezonluk Liderlik Tablosunu Gor %C_GRAY%(SeasonStats)%C_RESET%
echo   [4] En Son Uretilen Kadro Onerisini Ac %C_GRAY%(gw!GWeek!_kadro_onerisi.xlsx)%C_RESET%
echo   [5] Gecmis Yedekleri Gor %C_GRAY%(backups/ klasoru)%C_RESET%
echo   [9] Ana Menuye Don
echo %C_MAGENTA%==================================================================%C_RESET%
set /p asecim="%C_BOLD%%C_YELLOW%Secim [1-5, 9]: %C_RESET%"

if "!asecim!"=="1" (
  set /p GWeek="Yeni Hafta Numarasi [1-38]: "
  goto ayarlar_menu
)
if "!asecim!"=="2" (
  start "" "%EXCEL%"
  goto ayarlar_menu
)
if "!asecim!"=="3" (
  goto goruntule_liderlik
)
if "!asecim!"=="4" (
  if exist "gw!GWeek!_kadro_onerisi.xlsx" start "" "gw!GWeek!_kadro_onerisi.xlsx"
  goto ayarlar_menu
)
if "!asecim!"=="5" (
  explorer backups
  goto ayarlar_menu
)
if "!asecim!"=="9" goto ana_menu
goto ayarlar_menu

:cikis
cls
echo %C_GREEN%TFF Fantezi Lig Yonetim Merkezi kapatildi.%C_RESET%
exit /b 0
