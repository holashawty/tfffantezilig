# 07 — Geliştirme Günlüğü (canlı belge — HER oturumda güncelle)

Format: her girişte tarih, ne yapıldı, ne araştırıldı, ne KARARLAŞTIRILDI
(ve neden), sıradaki adım. Agent her oturum sonunda buraya YENİ bir
madde EKLESİN, öncekileri SİLMESİN.

---

## 12 Ağustos 2026 — Kurulum oturumu (Claude ile)
**Yapıldı:**
- Excel şeması Players/GameweekLog/Fixtures olarak yeniden kuruldu
  (orijinal 444 satırlık hatalı "GENEL TOPLAM" satırı temizlendi → 443 gerçek oyuncu)
- Resmi kurallar ve puanlama tablosu tfffantezilig.com/yardim'den doğrulandı
- Kadro motoru yazıldı ve gerçek veriyle test edildi: `data_loader.py`,
  `xp_model.py` (fiyat-önseli + Bayesian shrinkage), `optimizer.py`
  (scipy.optimize.milp/HiGHS — PuLP kurulamadı, ağ kapalıydı)
- Web-araştırma köprüsü kuruldu: `web_arastirma_prompti.md` +
  `update_from_web_research.py` (dry-run/apply + isim eşleştirme)
- Faz 2 kuruldu: `ingest_gameweek_results.py`, `calibrate_priors.py`
  (kod-tabanlı, LLM'siz kalibrasyon), `update_week.py` orkestratörü
- `validator.py` yazıldı, 3 ingest script'ine entegre edildi
- Fiyat mekanizması kuruldu: `price_tl_current` (Players'ta canlı
  alan), `ingest_price_updates.py`, `fiyat_guncelleme_prompti.md`
- 2 sentetik hafta ile uçtan uca pipeline test edildi (gerçek maç
  verisi YOK, sadece kod plumbing testi — gerçek isabet testi
  14 Ağustos'tan önce YAPILAMAZ, bu bilinçli bir sınır)
- Gemini'nin iki ayrı README/mimari önerisi incelendi, kritik
  hatalar bulundu (xP formülü soğuk-başlangıç sorununu görmüyor,
  LLM'e "son karar" yetkisi veriyor, veritabanı şeması oranları
  unutuyor) — REDDEDİLDİ, yerine bu `docs/` yapısı kuruldu

**Kararlaştırıldı (ve neden):**
- AI hiçbir zaman kadro/tahmin kararını onaylamaz/veto etmez —
  sadece açıklar + sınırlı araştırma yapar (bkz. `08_LLM_ROLU_VE_SINIRLAR.md`)
- SQLite'a geçiş ŞİMDİLİK yok — mevcut Excel pipeline yeterli ve test edildi
- Nostradamus'a BAŞLANMADI (kullanıcı talebiyle) — sadece plan yazıldı

**Sıradaki adım:** `06_TRANSFER_PENCERESI.md` ve `03_NOSTRADAMUS_MOTORU.md`'nin
kodlanması (Adım 0: mevcut bahis-app veritabanının denetimi ile başla).

---

## [SONRAKİ OTURUM İÇİN ŞABLON — kopyala, doldur]
## <Tarih> — <kısa başlık>
**Yapıldı:**
-
**Araştırıldı (kaynak + sonuç):**
-
**Kararlaştırıldı (ve neden):**
-
**Sıradaki adım:**
