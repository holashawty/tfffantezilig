# ⚡ TFF Fantezi Lig — Matematiksel Kadro Optimizasyonu & Tahmin Sistemi

<div align="center">

![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)
![SciPy](https://img.shields.io/badge/SciPy-HiGHS%20MILP-8CAAE6?style=for-the-badge&logo=scipy&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)
![Super Lig](https://img.shields.io/badge/Trendyol%20Süper%20Lig-2026--2027-red?style=for-the-badge)

**Trendyol Süper Lig TFF Fantezi Lig oyunu için Tam Sayılı Doğrusal Programlama (MILP), Bayesian Çıkarım, Fikstür Zorluk Katsayıları (FDR) ve Nostradamus Maç Tahmin Motoru.**

[Özellikler](#-temel-özellikler) • [Mimari & Matematik](#-matematiksel-ve-istatistiksel-mimari) • [Kurulum](#-kurulum) • [Kullanım Rehberi](#-kullanım-rehberi) • [Veritabanı Yapısı](#-veritabanı-mimarisi)

</div>

---

## 🌟 Temel Özellikler

- 🎯 **Deterministik Kadro Optimizasyonu (MILP)**:
  `scipy.optimize.milp` (HiGHS solver) ile 462 futbolcu arasından 100.000.000 TL bütçe, kulüp kotası (takım başı maks 3) ve mevki kurallarını matematiksel kesinlikle sağlayan **global optimum 15 kişilik kadroyu milisaniyeler içinde çözer**.
- 📈 **Bayesian Shrinkage & xP Modeli**:
  Fiyat tabanlı önsel değerleri (prior) gerçek maç performanslarıyla harmanlar ($w = \frac{n}{n + 4}$). Sezon ilerledikçe şansa bağlı tek maçlık patlamaları filtreler ve istikrarlı oyuncuları öne çıkarır.
- ⏱️ **Sürekli İyileşen Süre Güvenilirliği (Minutes-Learning)**:
  $w_T = \frac{T}{T + 3}$ formülü ile oyuncuların toplam sahada kaldığı dakikaları hafızasında tutar. 10 haftada 30 dakika alan yedekleri kademeli olarak eler, 90 dakika oynayan garanti isimleri seçer.
- 🛡️ **Akıllı Yedek Kadro Değerlemesi (Bench Value Weighting)**:
  Amaç fonksiyonuna eklenen $\text{BENCH\_XP\_WEIGHT} = 0.15$ ağırlığı ile arta kalan bütçeyi 0 xP'li oyunculara bırakmaz; sahaya çıktığında puan getirme potansiyeli en yüksek aktif ve canlı yedekleri kadroya katar.
- ⚔️ **Fikstür ve Rakip Zorluk Çarpanı (FDR / Match Odds Multiplier)**:
  Nostradamus canlı 1X2 iddaa oranlarından her takım için **Hücum Çarpanı ($M_{\text{att}}$)** ve **Savunma/Clean Sheet Çarpanı ($M_{\text{cs}}$)** hesaplayarak oyuncuların puan beklentisini haftalık fikstür zorluğuna göre ölçekler.
- 🔮 **Nostradamus Maç Tahmin Motoru**:
  Süper Lig'in 9 maçının olasılıklarını devig (Shin + B365/Pinnacle medyanı) ile hesaplar; banko, dengeli ve sürpriz maç analizleri ile haftalık en olası skor tercihlerini sunar.
- 🚀 **1-Tıkla Yönetim & Rehber Sihirbazı (`rehber.bat`)**:
  F12 tarayıcı yardımcı scriptleri (`tff_fantezi_export.js`, `oddsportal_export.js`) ve Express Pipeline ile veri toplama, sakatlık işleme, fiyat güncelleme ve Excel çıktısını uçtan uca otomatikleştirir.

---

## 🧠 Matematiksel ve İstatistiki Mimari

### 1. Mixed Integer Linear Programming (MILP) Kadro Optimizasyonu

Kadro seçimi deterministik bir tam sayılı optimizasyon problemidir:

$$\max_{x, s} \sum_{i=1}^{n} s_i \cdot xP_i + \beta \sum_{i=1}^{n} (x_i - s_i) \cdot xP_i$$

**Kısıtlar (Resmi TFF Fantezi Lig Kuralları):**
- $s_i \le x_i, \quad \forall i \in \{1, \dots, n\}$ *(İlk 11 oyuncusu, 15 kişilik kadronun alt kümesidir)*
- $\sum_{i=1}^{n} x_i = 15, \quad \sum_{i=1}^{n} s_i = 11$
- $\sum_{i=1}^{n} \text{Fiyat}_i \cdot x_i \le 100.000.000 \text{ TL}$
- **Kadro Mevki Dağılımı:** $x_{\text{GK}} = 2, \quad x_{\text{DEF}} = 5, \quad x_{\text{MID}} = 5, \quad x_{\text{FWD}} = 3$
- **İlk 11 Mevki Kuralları:** $s_{\text{GK}} = 1, \quad 3 \le s_{\text{DEF}} \le 5, \quad 1 \le s_{\text{FWD}} \le 3$
- **Kulüp Kotası:** $\sum_{i \in \text{Kulüp}_k} x_i \le 3, \quad \forall k$

---

### 2. Bayesian Shrinkage & Zaman Ağırlıklı Form Skoru

Oyuncunun beklenen puanı ($xP_{\text{blended}}$), sezonluk maç sayısı ($n$) ve zaman ağırlıklı hareketli ortalama ($\lambda = 0.75$) ile güncellenir:

$$w_n = \frac{n}{n + 4}$$

$$xP_{\text{blended}} = w_n \cdot \text{FormSkoru}_i + (1 - w_n) \cdot xP_{\text{Önsel}}$$

---

### 3. Fikstür ve Rakip Zorluk Çarpanı (FDR)

Canlı maç olasılıkları ($P_{\text{win}}, P_{\text{draw}}, P_{\text{opp}}$) üzerinden her takıma haftalık dinamik katsayılar atanır:

- **Hücum Çarpanı ($M_{\text{att}}$):** $M_{\text{att}} = \text{clip}(0.60 + 0.90 \cdot P_{\text{win}} + 0.15 \cdot P_{\text{draw}}, 0.65, 1.45)$
- **Savunma/Clean Sheet Çarpanı ($M_{\text{cs}}$):** $M_{\text{cs}} = \text{clip}(1.0 + 1.1 \cdot (P_{\text{win}} - P_{\text{opp}}), 0.25, 1.80)$

---

## 📂 Proje Dizin Yapısı

```text
├── oyuncu_veritabani.xlsx        # 462 oyuncunun tam veritabanı (Players, GameweekLog, Fixtures, SeasonStats)
├── rehber.bat                    # Türkçe interaktif yönetim ve çalıştırma sihirbazı
├── quick_pipeline.py             # 1-Tıkla uçtan uca otomasyon motoru
├── run_gameweek.py               # MILP çözücü & haftalık Excel kadro raporu üretici
├── xp_model.py                   # Bayesian xP, FDR çarpanları ve süre güvenilirliği motoru
├── optimizer.py                  # SciPy HiGHS MILP kadro çözücüsü
├── season_stats.py               # Sezonluk kümülatif istatistikler ve liderlik tablosu
├── ingest_gameweek_results.py    # Maç sonuçları ve puanları Excel'e işleme motoru
├── ingest_price_updates.py       # Dinamik piyasa değeri güncelleyici
├── update_from_web_research.py   # Sakatlık/ceza/kadro dışı filtreleme motoru
├── nostradamus_predict.py        # 9 Süper Lig maçının Nostradamus oran tahmin motoru
├── tff_fantezi_export.js         # tfffantezilig.com için F12 Console tek tıkla veri çekici
├── oddsportal_export.js          # Canlı iddaa oranlarını tek tıkla indiren tarayıcı scripti
├── docs/                         # Resmi kurallar, matematiksel metodoloji ve karar kayıtları
└── backups/                      # Her güncelleme öncesi alınan otomatik Excel yedekleri
```

---

## 🛠️ Kurulum

Python 3.10 veya daha üstü bir sürüm gereklidir.

```bash
# 1. Repoyu klonlayın
git clone https://github.com/holashawty/tfffantezilig.git
cd tfffantezilig

# 2. Gerekli kütüphaneleri yükleyin
pip install -r requirements.txt
```

---

## 🚀 Kullanım Rehberi

Tüm işlemler **`rehber.bat`** üzerinden Türkçe ve adım adım yönetilebilir:

```cmd
rehber.bat
```

### 1. Maç Öncesi Hazırlık (Deadline Öncesi Kadro Kurulumu)
1. `rehber.bat` açıp **`[1] YENİ HAFTA HAZIRLIĞI`** menüsüne girin.
2. **`[x] HIZLI MOD`** seçin (veya adım adım sakatlık, fiyat ve oranları güncelleyin).
3. Sistem MILP optimizasyonunu çalıştırarak en ideal 15 kişilik kadroyu, kaptanı (2x) ve yedek sıralamasını hesaplar ve **`gwX_kadro_onerisi.xlsx`** dosyasını ekranda açar.

### 2. Maç Sonrası Sonuç Girişi
1. `tff_fantezi_export.js` kodunu `tfffantezilig.com` konsoluna yapıştırıp `match_sonuclari_gwX.json` dosyasını indirin.
2. `rehber.bat` -> **`[2] GEÇEN HAFTANIN VERİLERİNİ İŞLE`** seçin.
3. Sistem tüm oyuncuların dakika, gol, asist, kart, kurtarış ve puanlarını `GameweekLog`, `Fixtures` ve `SeasonStats` sayfalarına tek tıkla işler.

---

## 📊 Veritabanı Mimarisi (`oyuncu_veritabani.xlsx`)

| Sayfa Adı | Açıklama |
| :--- | :--- |
| **`Players`** | 462 futbolcunun ID, mevki, kulüp, güncel fiyat, oynama olasılığı ve sakatlık notları |
| **`GameweekLog`** | Her haftanın gerçekleşen resmi dakika, gol, asist, kart ve fantezi puanı kayıtları |
| **`Fixtures`** | 38 haftanın 9'ar maçlık fikstürü, resmi skorları ve maç başlama saatleri |
| **`SeasonStats`** | Toplam maç, ilk 11 sayısı, toplam süre, puan, P90 verimliliği ve canlı liderlik tablosu |

---

## 📄 Lisans

Bu proje **MIT Lisansı** altında lisanslanmıştır.
Detaylar için `LICENSE` dosyasına bakabilirsiniz.
