# Hafta-Sonu Maç Sonuçları ve Oyuncu Puanları Rehberi

Bu aşama, maç haftası tamamlandıktan sonra gerçek performans verilerini (`GameweekLog`) sisteme işlemek için kullanılır.

> [!IMPORTANT]
> **462 Oyuncunun Profiline Tek Tek Tıklamanıza Kesinlikle Gerek Yoktur!**
> Aşağıdaki pratik yöntemlerden birini kullanarak tüm haftanın verilerini saniyeler veya dakikalar içinde toplayabilirsiniz.

---

## 🚀 YÖNTEM 1: Tarayıcıdan 1-Tıkla İndirme (En Hızlı & Sıfır Zahmet - ~1 Saniye)

1. Tarayıcınızda [tfffantezilig.com](https://tfffantezilig.com) sitesini açın.
2. Klavyeden `F12` tuşuna basın (veya sağ tık -> *İncele*), açılan pencerede **Console (Konsol)** sekmesine gelin.
3. Proje klasöründeki `tff_fantezi_export.js` dosyasının içeriğini kopyalayıp konsola yapıştırın ve `Enter`'a basın.
4. Ekranın sağ üst köşesinde beliren panelden **"⚽ Maç Sonuçlarını İndir"** butonuna tıklayın.
5. İndirilen `match_sonuclari_gwX.json` dosyasını proje klasörüne kopyalayın.

---

## 📸 YÖNTEM 2: Fikstür / Maç Özeti Ekranı (Toplu Ekran Görüntüsü - ~2 Dakika)

Haftada 462 oyuncu yerine sadece **9 maç** oynanır.
1. TFF Fantezi Lig uygulamasında **"Fikstür / Sonuçlar"** sekmesine gidin.
2. Oynanan 9 maçın detayına tıklayarak sahaya çıkan oyuncuların ve puanların ekran görüntüsünü alın.
3. Gemini'ye aşağıdaki prompt ile birlikte görselleri yükleyin:

```text
Bu ekran görüntülerindeki TFF Fantezi Lig maç sonuçlarını ve oyuncu puanlarını aşağıdaki JSON şemasına dönüştür. SADECE geçerli bir JSON döndür, açıklama ekleme:

{
  "gameweek": [HAFTA NO],
  "results": [
    {
      "player_name": "Oyuncu Adı",
      "team": "Takım Adı",
      "minutes": 90,
      "goals": 0,
      "assists": 0,
      "yellow_cards": 0,
      "red_cards": 0,
      "fantasy_points": 6.0
    }
  ]
}
```
4. AI'ın ürettiği çıktıyı `match_sonuclari_gwX.json` olarak kaydedin.

---

## 🌐 YÖNTEM 3: Web Araştırması (Harici İstatistikler)

Eğer TFF platformuna erişilemiyorsa, Gemini/ChatGPT'ye şu promptu verin:

```text
Türkiye Trendyol Süper Lig [HAFTA NO]. hafta maçlarının sonuçlarını, oynayan oyuncuları, dakika, gol, asist ve kart istatistiklerini araştır. Sonuçları aşağıdaki JSON şemasına dönüştür:

{
  "gameweek": [HAFTA NO],
  "results": [
    {
      "player_name": "...",
      "team": "...",
      "minutes": 90,
      "goals": 0,
      "assists": 0,
      "yellow_cards": 0,
      "red_cards": 0,
      "fantasy_points": null
    }
  ]
}
```

---

## Sisteme Yükleme

Dosyayı oluşturduktan sonra `rehber.bat` menüsünden **[3] MAÇLAR BİTTİ** -> **[1] Sonuçları Tek Tıkla Sisteme İşle** seçeneğini seçin.
