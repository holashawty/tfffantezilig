# Haftalik Fiyat Guncelleme Prompti (eksik olan 2. parca)

Fiyatlar TFF Fantezi Lig'in KENDI IC EKONOMISI (transfer yogunluguna
gore degisiyor) — bu yuzden tfffantezilig.com disinda baska hicbir
kaynakta (tff.org dahil) guvenilir sekilde bulunmaz. Web aramasi
BURADA ISE YARAMAZ, cunku bu veri disariya yayinlanan bir istatistik
degil, oyunun kendi arayuzunde gorunen bir deger.

## Tercih edilen yontem: Uygulama ekrani transkripsiyonu

TFF Fantezi Lig uygulamasinda "Transferler" / "Piyasa" ekranindaki
guncel fiyatlarin ekran goruntusunu al (ideal olarak degisen
oyunculari gosteren bir ekran, ya da tum kadronun/ilgi duydugun
oyuncularin fiyat listesi). Belge/gorsel okuyabilen bir AI'ya
(Gemini) ver:

------------------------------------------------------------------
Bu ekran goruntusundeki TFF Fantezi Lig oyuncu fiyatlarini asagidaki
JSON semasina donustur. SADECE JSON don. Gorseldeki her oyuncuyu
birebir aktar, sayilari uydurma, gorunmeyen oyuncuyu ekleme:

{
  "gameweek": [HAFTA NO],
  "prices": [
    {"player_name": "...", "team": "...", "price_tl": 0}
  ]
}
------------------------------------------------------------------

Cikan JSON'u `fiyat_gwN.json` olarak kaydet, sonra:

    python ingest_price_updates.py oyuncu_veritabani_guncel.xlsx fiyat_gwN.json
    (rapor iyiyse) --apply ile tekrar calistir

## Onemli sinirlama (durustce belirtilmeli)

Bu adim, diger ikisinden (sakatlik, mac sonuclari) farkli olarak web
aramasiyla OTOMATIKLESTIRILEMEZ — veri kaynagi tek, kapali bir
uygulama arayuzu. Yani sen (veya ekrani goren biri) her hafta bu
ekran goruntusunu almadan bu adim calismaz. Kadronda olmayan/
ilgilenmedigin oyuncularin fiyatini takip etmemek pratik bir sinirdir
— sadece transfer dusundugun oyunculari guncellemen yeterlidir,
tum 443 oyuncuyu her hafta cekmek zorunda degilsin.
