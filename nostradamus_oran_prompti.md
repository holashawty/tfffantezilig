# Nostradamus 9 Maç Bahis Oranları Toplama Promptu

Bu prompt, web araması yapabilen herhangi bir yapay zekaya (Gemini, ChatGPT, Claude) verilerek 9 maçın kapanış/güncel 1X2 oranlarını toplamak için kullanılır.

---

## 📋 KOPYALA-YAPISTIR PROMPT:

```text
GÖREV: Türkiye Trendyol Süper Lig 2026-2027 Sezonu [HAFTA NO]. Hafta maçlarının 1X2 bahis oranlarını (Bet365 / Pinnacle veya genel piyasa ortalaması) bul.

AŞAĞIDAKİ 9 MAÇ İÇİN 1-X-2 (Ev Sahibi - Beraberlik - Deplasman) ORANLARINI TOPLA:
[Buraya haftanın 9 maçını yazın, örneğin:
1. Erzurumspor - Galatasaray
2. Çorum - Kasımpaşa
3. Rizespor - Samsunspor
4. Fenerbahçe - Konyaspor
5. Trabzonspor - Başakşehir
6. Eyüpspor - Gaziantep
7. Alanyaspor - Beşiktaş
8. Göztepe - Gençlerbirliği
9. Kocaelispor - Amed]

SADECE aşağıdaki JSON şemasında, JSON DIŞINDA HİÇBİR AÇIKLAMA EKLEMEDEN cevap ver:

{
  "gameweek": [HAFTA NO],
  "prediction_date": "[YYYY-MM-DD]",
  "fixtures": [
    {
      "home_team": "Ev Sahibi",
      "away_team": "Deplasman",
      "match_date": "YYYY-MM-DD",
      "odds": {
        "B365": {"H": 1.50, "D": 4.00, "A": 6.50}
      }
    }
  ]
}
```

---

## 💾 Dosyayı Kaydetme

Çıkan JSON'u `nostradamus_fixtures_gw[HAFTA].json` olarak kaydedin.
Ardından `rehber.bat` -> `[1] Yeni Hafta Hazırlığı` -> `[x] Hızlı Mod` veya `[d] Sisteme Yükle` ile tahminleri otomatik üretin.
