# 01 — Oyun Kuralları ve ELO (DOĞRULANMIŞ, RESMİ)

Bu sohbette tfffantezilig.com/yardim'den doğrudan çekilip doğrulanmıştır.
Agent bu sayıları TEKRAR ARAŞTIRMASIN, sadece sezon ortasında değişip
değişmediğini periyodik kontrol etsin.

## Kadro kısıtları
- Bütçe: 100.000.000 TL
- Kadro: 15 oyuncu — 2 Kaleci, 5 Defans, 5 Orta Saha, 3 Forvet
- İlk 11: min 1 Kaleci, min 3 Defans, min 1 Forvet, toplam 11
- Kulüp sınırı: aynı takımdan en fazla 3 oyuncu
- Kaptan: puanı 2x. Kaptan süre almazsa yardımcı kaptana geçer.
- Yedek sıralaması: kaleci hariç 1-2-3 sıra, otomatik değişiklik
  formasyon kuralını bozmayacaksa devreye girer.
- Transfer: sınırsız (bkz. `06_TRANSFER_PENCERESI.md`)

## Resmi puanlama tablosu
| Olay | Puan |
|---|---|
| Oynama (<60dk) | 1 |
| Oynama (60dk+) | 2 |
| Gol — Kaleci | 10 |
| Gol — Defans | 6 |
| Gol — Orta Saha | 5 |
| Gol — Forvet | 4 |
| Asist (hepsi) | 3 |
| Gol yememe (60dk+ şart) — Kaleci/Defans | 4 |
| Gol yememe (60dk+ şart) — Orta Saha | 1 |
| Gol yememe — Forvet | yok |
| Kurtarış (Kaleci) | her 3'te 1 |
| Penaltı kurtarma | 5 |
| Penaltı kaçırma | -2 |
| Yenilen her 2 gol (Kaleci/Defans) | -1 |
| Sarı kart | -1 |
| Kırmızı kart | -3 |
| Kendi kalesine gol | -2 |
| Maç bonusu (haftanın en iyi 3'ü) | +3 / +2 / +1 |

## Nostradamus puanlaması
- 9 maçın TAMAMI için tahmin yapılırsa: +1
- Doğru tahmin edilen HER maç için: +1 daha
- Sadece 1-X-2 (maç sonucu), kesin skor DEĞİL — bu yüzden Dixon-Coles
  zorunlu değil, sadece isteğe bağlı çapraz kontrol (bkz. 03).
- Güven skoru oyuna girmiyor — sadece bizim iç kalibrasyonumuz için.

## ELO — "sabit kalacak" talimatının uygulaması
Proje sahibi ELO'nun basit/sabit kalmasını istiyor — bunu şöyle uygula:
**Kendi ELO algoritmanı yazma.** `soccerdata` kütüphanesi ClubElo
verisini tek satırda çeker (clubelo.com kaynaklı, hazır ve güncel).
Bunu takım gücü sinyali olarak Nostradamus modeline opsiyonel bir
girdi yap — ama asıl karar yine devig edilmiş bahis oranlarından
gelsin (bkz. `03_NOSTRADAMUS_MOTORU.md`, oranlar zaten piyasa bilgisini
fiyatlıyor, ELO ona ek bir çapraz kontrol).
