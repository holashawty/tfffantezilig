# Hafta-Sonu Mac Sonuclari Prompti (Faz 2)

Bu, web_arastirma_prompti.md'den FARKLI bir adim: o hafta BASLAMADAN
once (sakatlik/ceza), bu ise o hafta BITTIKTEN sonra (gercek
performans) kullanilir.

## KAYNAK ONCELIGI (onemli)

Puan, sari/kirmizi kart ve varsa fiyat verisi icin ONCE
tfffantezilig.com (oyunun kendi resmi kaynagi) ve tff.org'un resmi
Futbolcular/Statlar sayfalarina bak. Genel web aramasi (sofascore,
goal.com vb.) sadece resmi kaynak eksik/erisilemezse kullanilmali.

## VERI KALITESI KONTROLU (henuz otomatik degil — TODO)

ingest_gameweek_results.py su an sadece isim eslesmesini kontrol
ediyor. Eklenmesi gereken "kontrolcu" katmani:
  - Beklenen mac sayisina gore oyuncu sayisi makul mu (asiri eksik
    veri yok mu)?
  - minutes/goals/assists gibi alanlar mantikli araliklarda mi
    (ornegin goller negatif olamaz, dakika 0-90+uzatma disinda olamaz)?
  - fantasy_points TFF'nin kendi kaynagindan mi (A yontemi) yoksa
    tahmini mi (B yontemi) — hangisi oldugu isaretlenmeli.
Bu kontrol gecmeden hicbir sonuc GameweekLog'a sessizce eklenmemeli.

## FIYAT GUNCELLEMESI — HENUZ EKSIK (TODO)

price_tl alani JSON semasinda ve GameweekLog'da var, ama fiyatlarin
haftalik nasil degistigini arastiracak ayri bir prompt/mekanizma
HENUZ YAZILMADI. Fiyatlar tfffantezilig.com'un kendi arayuzunde
gorunuyorsa, oraya ozel bir arastirma adimi eklenmeli.

## Tercih edilen yontem (A): TFF uygulamasindan dogrudan transkript

TFF Fantezi Lig'de "Puanim" ekranindaki haftalik oyuncu puanlarinin
ekran goruntusunu al. Belge/gorsel yukleyebilen bir AI'ya (Gemini) su
sekilde ver:

------------------------------------------------------------------
Bu ekran goruntusundeki TFF Fantezi Lig oyuncu haftalik puanlarini
asagidaki JSON semasina donustur. SADECE JSON don, baska metin ekleme.
Gorseldeki her satiri birebir aktar, sayilari uydurma:

{
  "gameweek": [HAFTA NO],
  "results": [
    {
      "player_name": "...", "team": "...",
      "minutes": 0, "goals": 0, "assists": 0,
      "yellow_cards": 0, "red_cards": 0,
      "fantasy_points": 0.0
    }
  ]
}
------------------------------------------------------------------

Bu en guvenilir kaynak: fantasy_points TFF'nin KENDI hesapladigi
gercek deger, bizim tahminimize gerek yok.

## Tamamlayici yontem (B): web arastirmasiyla mac istatistikleri

Eger (A) elde degilse veya PRIOR_CONFIG kalibrasyonu icin daha fazla
oyuncunun ham istatistiklerine (dakika/gol/asist) ihtiyac varsa, web
aramasi yapabilen bir AI'ya:

------------------------------------------------------------------
Trendyol Super Lig [HAFTA NO]. hafta maclarinin sonuclarini ve oyuncu
istatistiklerini (sofascore, goal.com, resmi kulup siteleri) arastir.
SADECE gercekten bulabildigin oyuncular icin, asagidaki JSON semasina
gore cevap ver (fantasy_points alanini biliyorsan doldur, bilmiyorsan
null birak, UYDURMA):

{
  "gameweek": [HAFTA NO],
  "results": [
    {"player_name": "...", "team": "...", "minutes": 0, "goals": 0,
     "assists": 0, "yellow_cards": 0, "red_cards": 0,
     "fantasy_points": null}
  ]
}
------------------------------------------------------------------

Cikan JSON'u `sonuclar_gwN.json` olarak kaydet, sonra:

    python ingest_gameweek_results.py oyuncu_veritabani_guncel.xlsx sonuclar_gwN.json
    (rapor iyiyse) --apply ile tekrar calistir
