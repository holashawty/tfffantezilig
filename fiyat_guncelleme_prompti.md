# Haftalık Fiyat Güncelleme Rehberi

Fiyatlar TFF Fantezi Lig'in kendi iç piyasa dinamiklerine göre değişir. Bu veriyi toplamak için iki kolay yöntem bulunmaktadır:

---

## 🚀 YÖNTEM 1: Tarayıcıdan 1-Tıkla İndirme (En Hızlı - ~1 Saniye)

1. Tarayıcınızda [tfffantezilig.com](https://tfffantezilig.com) adresine girin.
2. `F12` tuşuna basarak (veya Sağ Tık -> *İncele*) **Console** sekmesine gelin.
3. Projedeki `tff_fantezi_export.js` kodunu konsola yapıştırıp `Enter`'a basın.
4. Sağ üstteki panelden **"📥 Fiyatları İndir"** butonuna tıklayın.
5. İndirilen `fiyat_gwX.json` dosyasını proje klasörüne kaydedin.

---

## 📸 YÖNTEM 2: Uygulama Ekranı Transkripsiyonu (Görsel + AI)

1. TFF Fantezi Lig uygulamasında "Transferler" veya "Piyasa" ekranının ekran görüntüsünü alın.
2. Gemini'ye aşağıdaki prompt ile birlikte görseli yükleyin:

```text
Bu ekran görüntüsündeki TFF Fantezi Lig oyuncu fiyatlarını aşağıdaki JSON şemasına dönüştür. SADECE geçerli bir JSON döndür, açıklama ekleme:

{
  "gameweek": [HAFTA NO],
  "prices": [
    {
      "player_name": "Oyuncu Adı",
      "team": "Takım Adı",
      "price_tl": 5.5
    }
  ]
}
```
3. Çıkan JSON'u `fiyat_gwX.json` olarak kaydedin.

---

## Sisteme Yükleme

Dosyayı oluşturduktan sonra `rehber.bat` menüsünden **[2] YENİ HAFTA HAZIRLIĞI** -> **[x] HIZLI MOD (Express Pipeline)** ile tek tıkla uygulayabilirsiniz.
