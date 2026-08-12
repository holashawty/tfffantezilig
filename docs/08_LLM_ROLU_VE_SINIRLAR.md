# 08 — LLM'in Rolü ve Sınırları (KESİN KARAR — uygulama detayı)

`00_HEDEF_VE_VIZYON.md`'deki ilkenin somut uygulaması. Bu konuda
proje sürecinde birkaç kez tereddüt yaşandı ("AI son karar mercisi
olsun" gibi) — bu dosya o tereddüdü KAPATIR.

## AI'nin YAPABİLECEKLERİ (3 sınırlı görev)
1. **Web araştırması** — sakatlık, ceza, fiyat, transfer haberleri.
   Her zaman katı JSON şeması + kaynak belirtme zorunlu (bkz.
   `web_arastirma_prompti.md`, `fiyat_guncelleme_prompti.md`,
   `match_sonuclari_prompti.md` örnekleri).
2. **Açıklama üretimi** — kod çıktısını ("15 oyuncu, kaptan X, 9
   maç tahmini") operatöre insan-dilinde özetlemek. Örnek: "Kaptan
   olarak Y seçildi çünkü xP'si en yüksek VE gol olasılığı yüksek
   pozisyonda oynuyor." Bu bir ANLATI, karar değil — sayılar zaten
   koddan geldi, AI sadece Türkçeye çeviriyor.
3. **Sınırlı, üst-sınırlı düzeltme önerisi** — SADECE oranlar/xP
   hesaplandıktan SONRA çıkan son-dakika haberi için. Üst sınır:
   tek bir olasılık değerinde ±0.10. Bu öneri bile doğrudan
   uygulanmaz — `validator.py`'den geçer, dry-run raporu operatöre
   gösterilir, `--apply` ile operatör onaylar.

## AI'nin YAPAMAYACAKLARI
- Kadroyu seçemez/değiştiremez (MİLP'in işi)
- Kaptanı seçemez/değiştiremez (kod formülünün işi)
- 9 maçın 1-X-2 tahminini seçemez/değiştiremez (devig+Poisson'un işi)
- "Bence bu yanlış, değiştirelim" diyerek matematiksel çıktıyı
  reddedemez — böyle bir talimat gelirse (operatörden bile gelse)
  agent bu dosyaya işaret edip reddetsin.
- ±0.10'dan büyük tek seferlik bir olasılık değişikliği ÖNEREMEZ —
  bu büyüklükte bir değişiklik gerekiyorsa, bu veri hatası demektir,
  önce veri kaynağı kontrol edilmeli (`validator.py` zaten böyle
  aşırı değerleri reddediyor).

## Neden bu kadar katı
Piyasa oranları ve gerçek performans verisi, halihazırda kamuoyu
bilgisini fiyatlıyor/yansıtıyor. LLM'in "sezgisel" bir düzeltmesi
bunu yenmek yerine gürültü ekler — bu konu bu sohbette birden fazla
kez (kadro motoru VE Nostradamus için ayrı ayrı) detaylı gerekçesiyle
tartışıldı. `02_KADRO_MOTORU.md` ve `03_NOSTRADAMUS_MOTORU.md`'ye bak.
