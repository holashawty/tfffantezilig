@echo off
chcp 65001 >nul
REM ============================================================
REM TFF Fantezi Lig Sistemi - Operator Menusu
REM docs/05_CALISMA_PRENSIBI_VE_SISTEM_MIMARISI.md'nin uygulamasi
REM ============================================================
REM Kullanim: Windows uzerinde cift tikla veya komut satirinda calistir.
REM Python'un PATH'te oldugunu varsayar (python --version calismali).

setlocal enabledelayedexpansion

REM Varsayilan dosya yollari
set "EXCEL=oyuncu_veritabani.xlsx"
set "GWeek=1"

:baslangic
cls
echo ==================================================================
echo   TFF FANTEZi LIG SiSTEMi
echo ==================================================================
echo   Aktif Excel : %EXCEL%
echo   Aktif Hafta : %GWeek%
echo ------------------------------------------------------------------
echo   [0] Hafta numarasini ayarla
echo   [1] Excel dosyasi sec (farkli bir dosya)
echo   [2] Kadro optimizasyonu (MILP + kaptan + yedek sirasi)
echo   [3] Nostradamus tahminleri (9 mac)
echo   [4] Web AI ciktilarini sisteme yukle
echo   [5] Transfer penceresi (oyuncu ekle/cikar/tasimak)
echo   [6] Backtest calistir (Nostradamus baseline kontrolu)
echo   [7] Cikis
echo ==================================================================
set /p secim="Secim [0-7]: "

if "%secim%"=="0" goto set_hafta
if "%secim%"=="1" goto set_excel
if "%secim%"=="2" goto kadro
if "%secim%"=="3" goto nostradamus
if "%secim%"=="4" goto webai_menu
if "%secim%"=="5" goto transfer
if "%secim%"=="6" goto backtest
if "%secim%"=="7" goto son
goto baslangic

:set_hafta
set /p GWeek="Hafta numarasi (1-38): "
if "!GWeek!"=="" set "GWeek=1"
echo Hafta !GWeek! olarak ayarlandi.
pause
goto baslangic

:set_excel
set /p EXCEL="Excel dosyasi yolu (ornek: oyuncu_veritabani.xlsx): "
if "!EXCEL!"=="" set "EXCEL=oyuncu_veritabani.xlsx"
echo Excel !EXCEL! olarak ayarlandi.
pause
goto baslangic

:kadro
echo.
echo [2] Kadro optimizasyonu calistiriliyor (Hafta %GWeek%)...
echo ------------------------------------------------------------------
python run_gameweek.py "%EXCEL%" --gameweek %GWeek%
echo.
pause
goto baslangic

:nostradamus
echo.
echo [3] Nostradamus tahminleri
echo ------------------------------------------------------------------
echo Bu adim icin once 9 macin oranlarini iceren bir JSON dosyasi
echo hazirlamalisin (bkz. docs/09_OPERATOR_CEKLISTI.md adim 5).
echo Ornek dosya: nostradamus_fixtures_gw%GWeek%.json
echo.
set /p NOS_JSON="JSON dosyasi yolu (bos birakirsa varsayilan): "
if "!NOS_JSON!"=="" set "NOS_JSON=nostradamus_fixtures_gw%GWeek%.json"
if not exist "!NOS_JSON!" (
  echo [HATA] Dosya bulunamadi: !NOS_JSON!
  echo Once JSON dosyasini olustur (nostradamus_predict.py icin sablon).
  pause
  goto baslangic
)
python nostradamus_predict.py "!NOS_JSON!"
echo.
pause
goto baslangic

:webai_menu
cls
echo ==================================================================
echo   WEB AI CIKTILARINI YUKLE - Alt Menu
echo ==================================================================
echo   [1] Sakatlik/ceza guncellemesi (web_arastirma_prompti.md)
echo   [2] Fiyat guncellemesi (fiyat_guncelleme_prompti.md)
echo   [3] Mac sonuclari (match_sonuclari_prompti.md)
echo   [4] Geri (ana menu)
echo ==================================================================
set /p ai_secim="Secim [1-4]: "

if "%ai_secim%"=="1" goto ai_sakatlik
if "%ai_secim%"=="2" goto ai_fiyat
if "%ai_secim%"=="3" goto ai_sonuc
if "%ai_secim%"=="4" goto baslangic
goto webai_menu

:ai_sakatlik
set /p SAKAT_JSON="Sakatlik/ceza JSON dosyasi: "
if "!SAKAT_JSON!"=="" (
  echo Bos birakilamaz.
  pause
  goto webai_menu
)
if not exist "!SAKAT_JSON!" (
  echo [HATA] Dosya bulunamadi: !SAKAT_JSON!
  pause
  goto webai_menu
)
echo.
echo --- DRY-RUN (once kontrol et) ---
python update_from_web_research.py "%EXCEL%" "!SAKAT_JSON!"
echo.
set /p onay="Uygulansin mi? (e/h): "
if /i "!onay!"=="e" (
  python update_from_web_research.py "%EXCEL%" "!SAKAT_JSON!" --apply
)
pause
goto baslangic

:ai_fiyat
set /p FIYAT_JSON="Fiyat JSON dosyasi: "
if "!FIYAT_JSON!"=="" (
  echo Bos birakilamaz.
  pause
  goto webai_menu
)
if not exist "!FIYAT_JSON!" (
  echo [HATA] Dosya bulunamadi: !FIYAT_JSON!
  pause
  goto webai_menu
)
echo.
echo --- DRY-RUN (once kontrol et) ---
python ingest_price_updates.py "%EXCEL%" "!FIYAT_JSON!"
echo.
set /p onay="Uygulansin mi? (e/h): "
if /i "!onay!"=="e" (
  python ingest_price_updates.py "%EXCEL%" "!FIYAT_JSON!" --apply
)
pause
goto baslangic

:ai_sonuc
set /p SONUC_JSON="Mac sonuclari JSON dosyasi: "
if "!SONUC_JSON!"=="" (
  echo Bos birakilamaz.
  pause
  goto webai_menu
)
if not exist "!SONUC_JSON!" (
  echo [HATA] Dosya bulunamadi: !SONUC_JSON!
  pause
  goto webai_menu
)
echo.
echo --- DRY-RUN (once kontrol et) ---
python ingest_gameweek_results.py "%EXCEL%" "!SONUC_JSON!"
echo.
set /p onay="Uygulansin mi? (e/h): "
if /i "!onay!"=="e" (
  python ingest_gameweek_results.py "%EXCEL%" "!SONUC_JSON!" --apply
)
pause
goto baslangic

:transfer
echo.
echo [5] Transfer penceresi (sadece 17. haftadan sonra)
echo ------------------------------------------------------------------
echo Transfer promptu icin bkz. transfer_prompti.md
echo.
set /p TR_JSON="Transfer JSON dosyasi: "
if "!TR_JSON!"=="" (
  echo Bos birakilamaz.
  pause
  goto baslangic
)
if not exist "!TR_JSON!" (
  echo [HATA] Dosya bulunamadi: !TR_JSON!
  pause
  goto baslangic
)
echo.
echo --- DRY-RUN (once kontrol et) ---
python ingest_transfer_window.py "%EXCEL%" "!TR_JSON!"
echo.
set /p onay="Uygulansin mi? (e/h): "
if /i "!onay!"=="e" (
  python ingest_transfer_window.py "%EXCEL%" "!TR_JSON!" --apply
)
pause
goto baslangic

:backtest
cls
echo ==================================================================
echo   BACKTEST - Nostradamus Baseline Kontrolu
echo ==================================================================
echo   [1] Devig-only baseline (Brier score)
echo   [2] Poisson+Elo katman denemesi (karsilastirma)
echo   [3] Geri (ana menu)
echo ==================================================================
set /p bt_secim="Secim [1-3]: "

if "%bt_secim%"=="1" goto bt_devig
if "%bt_secim%"=="2" goto bt_poisson
if "%bt_secim%"=="3" goto baslangic
goto backtest

:bt_devig
if not exist "nostradamus\superlig_odds.db" (
  echo [HATA] nostradamus\superlig_odds.db bulunamadi.
  echo Once: python nostradamus\build_superlig_db.py ^<unified.db yolu^> nostradamus\superlig_odds.db
  pause
  goto backtest
)
set /p BT_SEZON="Kac sezon backtest? (varsayilan 3): "
if "!BT_SEZON!"=="" set "BT_SEZON=3"
python nostradamus\backtest_devig_baseline.py nostradamus\superlig_odds.db --seasons !BT_SEZON!
pause
goto backtest

:bt_poisson
if not exist "nostradamus\superlig_odds.db" (
  echo [HATA] nostradamus\superlig_odds.db bulunamadi.
  pause
  goto backtest
)
if not exist "nostradamus\cache\clubelo_history.csv" (
  echo [HATA] nostradamus\cache\clubelo_history.csv bulunamadi.
  echo Once: python nostradamus\fetch_clubelo_cache.py nostradamus\superlig_odds.db nostradamus\cache\clubelo_history.csv
  pause
  goto backtest
)
python nostradamus\backtest_poisson_elo.py nostradamus\superlig_odds.db nostradamus\cache\clubelo_history.csv --seasons 3
pause
goto backtest

:son
echo Cikiliyor.
endlocal
exit /b 0
