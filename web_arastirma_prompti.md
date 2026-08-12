# Haftalik Web-Arastirma Prompti (Faz 1.5)

API erisimi olmadigi icin bu adim MANUEL: asagidaki promptu her hafta
deadline'dan birkac saat once, web aramasi yapabilen bir AI'ya (Gemini,
Grok, Claude web, ChatGPT) YAPISTIR. Cikan JSON'u oldugu gibi
`web_research_gwN.json` olarak kaydet (N = o haftanin numarasi).
Sonra `update_from_web_research.py` scripti bunu Excel'e isler.

## KAYNAK ONCELIGI (onemli)

Once tfffantezilig.com ve tff.org'un resmi sayfalarina (Oyuncular,
Cezalar, Futbolcular, Statlar) bak — ozellikle CEZA (sari/kirmizi
kart birikimi) bilgisi TFF'nin kendi idari karari oldugu icin buradan
guvenilir sekilde alinabilir. Genel web aramasi sadece bu resmi
kaynaklar yetersiz kaldiginda ikinci siraya dusmeli.

DIKKAT — SAKATLIK VERISI ICIN ISTISNA: Sakatlik bilgisi tff.org'da
merkezi/guvenilir sekilde YOK. Kulup basin acamalarindan ucuncu parti
kaynaklarca (beIN Sports, fotmob, spor basini) derleniyor. Bunu tek
ve kesin dogru kaynaktan geliyormus gibi sunma; source_note alaninda
hangi kaynaktan geldigini mutlaka belirt.

## VERI KALITESI KONTROLU (henuz otomatik degil — TODO)

Su an update_from_web_research.py sadece isim eslesmesini kontrol
ediyor (bkz. NAME_MATCH_THRESHOLD). Asagidaki gibi bir "kontrolcu"
katmani HENUZ YAZILMADI, ekleyen agent su sartlari dogrulamali:
  - Beklenen oyuncu sayisinin kayda deger bir kismi eksik mi?
  - Zorunlu alanlar (player_name, team, play_probability) bos mu?
  - play_probability 0.0-1.0 araliginda mi?
  - Dry-run/--apply guvenlik deseni bozulmadan calisiyor mu?
Bu kontrol gecmeden hicbir guncelleme sessizce uygulanmamali.

------------------------------------------------------------------
KOPYALA-YAPISTIR PROMPT (asagisi, "-----" arasi):
------------------------------------------------------------------

Turkiye Trendyol Super Lig icin [HAFTA NUMARASINI YAZ]. hafta oncesi
sakatlik, cezali durum ve muhtemel 11 durumunu arastir. Guncel haberleri
(Transfermarkt, kulup aciklamalari, spor basini) tara.

SADECE asagidaki JSON formatinda, JSON DISINDA HICBIR METIN OLMADAN
cevap ver. Emin olmadigin oyuncuyu YAZMA (uydurma bilgi verme, sadece
gercekten haber bulabildigin oyunculari listele):

{
  "gameweek": <hafta_no>,
  "research_date": "<YYYY-MM-DD>",
  "updates": [
    {
      "player_name": "<oyuncunun tam adi>",
      "team": "<takimi>",
      "status": "injured | suspended | doubtful | confirmed_starter | confirmed_out | rotation_risk",
      "play_probability": <0.0 ile 1.0 arasi sayi>,
      "source_note": "<kisa aciklama, hangi haberden>"
    }
  ]
}

status -> play_probability rehberi:
  confirmed_out / injured / suspended -> 0.0
  doubtful / rotation_risk            -> 0.3 - 0.6 arasi, ciddiyete gore
  confirmed_starter                   -> 1.0

------------------------------------------------------------------

NOT: Web AI'nin uydurmasini engellemenin garantisi yok. Bu yuzden
update_from_web_research.py, her guncellemeyi ISLEMEDEN ONCE ekrana
yazdirir ve eslesmeyen/belirsiz isimleri ayrica raporlar — kor kor
uygulamaz. Haftada bir gozden gecir.
