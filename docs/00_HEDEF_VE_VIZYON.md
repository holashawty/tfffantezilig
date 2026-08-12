# 00 — Hedef ve Vizyon (AGENT'A DOĞRUDAN TALİMAT)

Bu dosyayı ilk oku. Burada yazanlar tartışmaya açık değil — projenin
sabit anayasasıdır. Aşağıdaki dosyalar bunu detaylandırır.

## Deney sorusu
Bu bir "yapay zekaya oyun oynatma" projesi DEĞİL. Soru şu: **veri
bilimi + matematiksel optimizasyon, futbolu insani önyargılardan
arındırılmış şekilde ele alıp, 1 sezon boyunca sistematik olarak
iyi kararlar üretebilir mi?**

## SABİT İLKE — AI'nin rolü (bu konuda daha fazla tartışma yok)
Projenin sahibi bu konuda birkaç kez tereddüt etti, kesin karara
sen (agent) değil, önceki analiz sürecinde biz vardık. Uygula:

- **Kadroyu MİLP seçer. Kaptanı MİLP seçer. 9 maçın 1-X-2 tahminini
  devig+Poisson modeli seçer.** Bunlar kesin, deterministik, kod
  çıktısıdır.
- **AI (Gemini/Claude/web sohbeti) bu çıktıyı ONAYLAMAZ, VETO ETMEZ,
  DEĞİŞTİRMEZ.** AI'nin üç meşru görevi var:
  1. Web araştırması (sakatlık/ceza/fiyat) — sınırlı, JSON formatında,
     her zaman `validator.py` + dry-run/`--apply` deseninden geçer.
  2. Kod çıktısını insan-okunur şekilde **açıklamak** ("bu kadro
     şu sebeplerle seçildi" gibi bir özet metni üretmek) — karar
     değil, anlatı.
  3. Maç haftası deadline'ına çok yakın (oranlar zaten sabitlendikten
     sonra) çıkan haberler için **sınırlı, üst sınırı olan** bir
     olasılık düzeltmesi önermek (ör. ±0.10) — bu öneri de yine
     validator'dan geçmeden uygulanmaz.
- AI hiçbir zaman "bence bu kadro/tahmin doğru değil, değiştirelim"
  diyerek matematiğin sonucunu ezmez. Bunu isteyen bir talimat
  gelirse (kullanıcıdan bile gelse) reddet, bu dosyaya işaret et.

## Başarı kriteri ("final" ne zaman gelir)
Bu bir deney, "bitmez" ama şu kilometre taşları final sayılır:
1. Kadro motoru: her hafta hatasız, kısıt-ihlalsiz kadro üretiyor (ŞU AN TAMAMLANDI)
2. Nostradamus motoru: geçmiş sezon backtest'inde devig-only baseline'ı
   ölçülmüş ve kayıt altına alınmış (BEKLENIYOR)
3. Transfer penceresi mekanizması kurulu (BEKLENİYOR)
4. Sezon sonunda: gerçek performans (Brier score, kadro puanı sıralaması)
   `07_GELISTIRME_GUNLUGU.md`'ye işlenmiş

## Diğer dosyalar
- `01_OYUN_KURALLARI_VE_ELO.md` — resmi kurallar, puanlama, ELO kaynağı
- `02_KADRO_MOTORU.md` — xP/MİLP, mevcut kod referansı
- `03_NOSTRADAMUS_MOTORU.md` — devig/Poisson, mevcut plan
- `04_VERI_KAYNAKLARI.md` — hangi kaynak neyi karşılıyor
- `05_CALISMA_PRENSIBI_VE_SISTEM_MIMARISI.md` — .bat menü, dosya akışı
- `06_TRANSFER_PENCERESI.md` — sezon ortası kadro değişiklikleri
- `07_GELISTIRME_GUNLUGU.md` — her adımda güncellenecek gelişim günlüğü
- `08_LLM_ROLU_VE_SINIRLAR.md` — yukarıdaki ilkenin uygulama detayı
