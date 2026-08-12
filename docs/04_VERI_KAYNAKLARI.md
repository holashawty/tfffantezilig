# 04 — Veri Kaynakları (3 liste, proje sahibinin istediği format)

Bu liste bu sohbette araştırılıp doğrulanmıştır. Agent periyodik
olarak (ör. ayda bir) linklerin hâlâ geçerli olduğunu kontrol etsin,
ama sıfırdan yeniden araştırmasın.

## Liste 1 — Puan / Maaş (fiyat) kaynakları
- **tfffantezilig.com** (oyunun kendi arayüzü) — TEK güvenilir fiyat
  kaynağı. Fiyatlar TFF'nin kapalı iç ekonomisi, başka hiçbir yerde
  yayınlanmıyor. Otomatikleştirilemez — bkz. `fiyat_guncelleme_prompti.md`
  (uygulama ekranı transkripsiyonu).
- **tfffantezilig.com/yardim** — resmi puanlama tablosu (bkz. 01).
- Oyun içi "Puanım" ekranı — haftalık gerçek fantasy_points için EN
  GÜVENİLİR kaynak (TFF'nin kendi hesabı, bizim tahminimiz değil).

## Liste 2 — Sakatlık / Sarı-Kırmızı kart kaynakları
- **tff.org** — "Cezalar" sayfası: idari ceza (kart birikimi
  sonucu men) için GÜVENİLİR, çünkü TFF'nin kendi kararı.
- **tff.org — Futbolcular/Statlar** — sezonluk kart istatistikleri.
- **SAKATLIK İÇİN ÖNEMLİ UYARI:** tff.org'da merkezi/güvenilir bir
  sakatlık veritabanı YOK. Bu bilgi kulüp basın açıklamalarından
  üçüncü parti kaynaklarca (fotmob.com, beIN Sports, spor basını)
  derleniyor. Tek kesin kaynak yokmuş gibi davranma, her güncellemede
  `source_note` alanına kaynağı yaz.
- **fotmob.com** — yapılandırılmış, oyuncu bazlı, maç-maç istatistik
  ve sakatlık durumu için iyi bir üçüncü-parti toplayıcı.

## Liste 3 — Diğer önemli kaynaklar
- **football-data.co.uk** — Türkiye Süper Lig dahil 25+ lig, ücretsiz
  CSV, maç sonucu + çoklu bahisçi oranı (1X2). Nostradamus'un ana
  girdisi (bkz. 03), ama önce mevcut bahis-app veritabanının
  boşluklarını doldurmak için kullan, sıfırdan DB kurma.
- **`soccerdata` (Python paketi)** — FBref, ClubElo, Transfermarkt
  verisini tek satırda çeker. ELO için bunu kullan (bkz. 01), kendi
  ELO algoritmanı yazma.
- **Kaggle** — "Turkish Super League Results" türü hazır setler,
  football-data.co.uk yetersiz kalırsa ikincil kaynak.
- **`shin` (pip paketi)** — devig için Shin's method hazır implementasyonu.
- **`penaltyblog` (pip paketi)** — Dixon-Coles hazır implementasyonu.

## Dürüstlük notu (agent bunu bilerek ilerlesin)
Fiyat ve sakatlık verisi API ile OTOMATİKLEŞTİRİLEMEZ — proje
sahibinin ücretli API'si yok, bu adımlar kalıcı olarak yarı-manuel
kalacak (bkz. `05_CALISMA_PRENSIBI_VE_SISTEM_MIMARISI.md`). Bunu
"gelecekte otomatikleştirilecek TODO" gibi sunma, bu sistemin kalıcı
bir sınırı.
