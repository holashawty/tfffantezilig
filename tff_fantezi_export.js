/**
 * TFF Fantezi Lig - Kusursuz Fikstür & 9 Maç İstatistik Çekici (v8.0)
 * -------------------------------------------------------------------
 * - Tüm UI gürültülerini (BÜTÇE, FORVETLER, Fikstür başlıkları vb.) tamamen filtreler.
 * - Fikstürdeki 9 maçın (1. maç Galatasaray - Çorum dahil) çekmecelerini sırayla açar.
 * - "OYUNCU İSTATİSTİKLERİ" -> "Tümü" sekmesinden sahaya çıkan tüm futbolcuların
 *   resmi maç verilerini (Puan, Süre, Gol, Asist, Kartlar, Bonus, Kurtarış) çeker.
 * - Çekmeceyi kapatıp sıradaki maça geçer.
 * - Temiz `match_sonuclari_gwX.json` üretir.
 */

(function() {
  function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  function downloadJson(filename, data) {
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    console.log(`[TFF Fikstür Export] ${filename} başarıyla indirildi!`);
  }

  function triggerFullClick(el) {
    if (!el) return;
    const opts = { bubbles: true, cancelable: true, view: window };
    ['pointerdown', 'mousedown', 'pointerup', 'mouseup', 'click'].forEach(evt => {
      try { el.dispatchEvent(new MouseEvent(evt, opts)); } catch (e) {}
    });
    if (typeof el.click === 'function') el.click();
  }

  function parseCellVal(val) {
    if (!val || val === '-' || val === '—' || val === '') return 0;
    const clean = String(val).replace(',', '.').trim();
    const num = parseFloat(clean);
    return isNaN(num) ? 0 : num;
  }

  // Geçersiz/Gürültü başlıkları filtreleme
  const INVALID_NAMES = new Set([
    "BÜTÇE", "OYUNCULAR", "FİYAT", "KALECİLER", "DEFANSLAR", "ORTA SAHALAR", "FORVETLER",
    "POZİSYON", "TAKIM", "İSTATİSTİK", "OTOMATİK SEÇİM", "SIFIRLA", "TRANSFER ET",
    "FİKSTÜR", "MAÇ HAFTASI", "MAÇ DETAYLARI", "OYUNCU İSTATİSTİKLERİ"
  ]);

  function isValidPlayerName(name) {
    if (!name || typeof name !== 'string') return false;
    const clean = name.trim();
    if (clean.length < 2) return false;
    if (clean.startsWith('₺') || clean.startsWith('TL')) return false;
    if (clean.includes('Maç Haftası') || clean.includes('Fikstür Çekici') || clean.includes('Maça Kalan')) return false;
    if (INVALID_NAMES.has(clean.toUpperCase())) return false;
    return true;
  }

  // 1. FİYAT ÇEKİCİ
  window.exportPrices = function(gw = 2) {
    const seen = new Set();
    const players = [];
    const allDivs = document.querySelectorAll('div, li, tr');
    allDivs.forEach(el => {
      const text = el.innerText || "";
      const priceMatch = text.match(/₺?\s*(\d+[.,]\d+|\d+)\s*m/i);
      if (priceMatch) {
        const lines = text.split('\n').map(s => s.trim()).filter(Boolean);
        if (lines.length >= 2) {
          const name = lines[0];
          const team = lines[1];
          if (isValidPlayerName(name) && team && !seen.has(name)) {
            seen.add(name);
            players.push({
              player_name: name,
              team: team,
              price_tl: parseFloat(priceMatch[1].replace(',', '.'))
            });
          }
        }
      }
    });

    const payload = { gameweek: gw, prices: players };
    downloadJson(`fiyat_gw${gw}.json`, payload);
    alert(`✅ ${players.length} oyuncunun güncel fiyatı 'fiyat_gw${gw}.json' olarak kaydedildi!`);
  };

  // 2. FİKSTÜR 9 MAÇ ÇEKMECE TARAYICI
  window.scrapeFixtureResults = async function(targetGw = 1) {
    const logEl = document.getElementById("tff-crawler-log");
    const progressEl = document.getElementById("tff-crawler-progress");

    function updateLog(msg, pct = 0) {
      if (logEl) logEl.innerText = msg;
      if (progressEl) {
        progressEl.style.width = `${pct}%`;
        progressEl.innerText = `${Math.round(pct)}%`;
      }
      console.log(`[TFF Fikstür v8] ${msg}`);
    }

    updateLog("Fikstür maçları tespit ediliyor...", 5);

    // Fikstür bölümüne kaydır
    const headings = Array.from(document.querySelectorAll('h1, h2, h3, h4, div'));
    const fHeader = headings.find(el => (el.innerText || "").trim() === "Fikstür" || (el.innerText || "").includes("Maç Haftası 1"));
    if (fHeader) {
      fHeader.scrollIntoView({ behavior: 'smooth', block: 'start' });
      await sleep(300);
    }

    // Skor içeren tüm maç satırlarını bul (9 maç)
    // Skor formatı: "\d+ - \d+" (Örn: "2 - 2", "1 - 1", "0 - 1", "2 - 1", "2 - 0", "3 - 0", "1 - 0", "3 - 3")
    const allDivs = Array.from(document.querySelectorAll('div, li, section'));
    const matchRowCandidates = allDivs.filter(el => {
      const t = el.innerText || "";
      const hasScore = /\b\d+\s*-\s*\d+\b/.test(t);
      const isHeader = t.includes("Maç Haftası") || t.includes("Fikstür") || t.includes("Programı");
      const isTab = t.includes("MAÇ DETAYLARI");
      const isPanel = el.closest('#tff-helper-panel');
      const isParent = el.children.length > 8; // Çok büyük kapsayıcıları ele
      return hasScore && !isHeader && !isTab && !isPanel && !isParent && el.offsetHeight >= 35 && el.offsetHeight <= 110;
    });

    // Benzersiz 9 maç satırını çıkar
    const uniqueMatchRows = [];
    const seenMatchSignatures = new Set();

    matchRowCandidates.forEach(el => {
      const t = el.innerText.trim();
      const scoreMatch = t.match(/\b\d+\s*-\s*\d+\b/);
      if (scoreMatch) {
        const sig = t.split('\n').filter(Boolean).slice(0, 3).join(' ');
        if (!seenMatchSignatures.has(sig)) {
          seenMatchSignatures.add(sig);
          uniqueMatchRows.push(el);
        }
      }
    });

    console.log(`Tespit edilen ${uniqueMatchRows.length} maç satırı:`, Array.from(seenMatchSignatures));
    if (uniqueMatchRows.length === 0) {
      alert("⚠️ Fikstür maç satırları tespit edilemedi. Lütfen sayfayı Fikstür maçları görünecek şekilde kaydırıp tekrar deneyin.");
      return;
    }

    const activePlayersMap = new Map();

    for (let mIdx = 0; mIdx < uniqueMatchRows.length; mIdx++) {
      const matchRow = uniqueMatchRows[mIdx];
      const matchTitle = matchRow.innerText.split('\n').filter(Boolean).slice(0, 3).join(' ');
      updateLog(`[${mIdx + 1}/${uniqueMatchRows.length}] ${matchTitle} açılıyor...`, (mIdx / uniqueMatchRows.length) * 90 + 5);

      matchRow.scrollIntoView({ behavior: 'instant', block: 'center' });
      await sleep(150);

      // Sağdaki ok butonunu (chevron) bul
      let chevronBtn = matchRow.querySelector('button, svg, [role="button"]');
      if (!chevronBtn) {
        const allSvgs = matchRow.querySelectorAll('svg');
        if (allSvgs.length > 0) chevronBtn = allSvgs[allSvgs.length - 1];
      }

      // Çekmeceyi aç
      if (chevronBtn) triggerFullClick(chevronBtn);
      else triggerFullClick(matchRow);
      await sleep(400); // Çekmece açılma animasyonu

      // "OYUNCU İSTATİSTİKLERİ" sekmesini bul ve tıkla
      const tabButtons = Array.from(document.querySelectorAll('button, div[role="tab"], span')).filter(b => {
        const text = (b.innerText || "").toUpperCase().trim();
        return text.includes("OYUNCU İSTATİSTİK") || text.includes("OYUNCU ISTATISTIK");
      });

      if (tabButtons.length > 0) {
        const statsTab = tabButtons[tabButtons.length - 1];
        triggerFullClick(statsTab);
        await sleep(250);
      }

      // "Tümü" butonunu tıkla (her iki takımın oyuncuları gelsin)
      const allFilterBtns = Array.from(document.querySelectorAll('button')).filter(b => (b.innerText || "").trim() === "Tümü");
      if (allFilterBtns.length > 0) {
        triggerFullClick(allFilterBtns[allFilterBtns.length - 1]);
        await sleep(150);
      }

      // Tablodaki oyuncu satırlarını oku
      const tables = document.querySelectorAll('table');
      if (tables.length > 0) {
        const activeTable = tables[tables.length - 1];
        const rows = activeTable.querySelectorAll('tbody tr, tr');
        let countInMatch = 0;

        rows.forEach(r => {
          const cells = Array.from(r.querySelectorAll('td')).map(td => td.innerText.trim());
          if (cells.length >= 3) {
            const playerLines = cells[0].split('\n').map(s => s.trim()).filter(Boolean);
            const pName = playerLines[0] || "";
            const pMeta = playerLines[1] || "";
            let pTeam = "";
            let pPos = "";
            if (pMeta.includes('-')) {
              const parts = pMeta.split('-');
              pTeam = parts[0].trim();
              pPos = parts[1].trim();
            } else if (pMeta.includes('·')) {
              const parts = pMeta.split('·');
              pTeam = parts[0].trim();
              pPos = parts[1].trim();
            } else {
              pTeam = pMeta;
            }

            if (isValidPlayerName(pName)) {
              countInMatch++;
              activePlayersMap.set(pName, {
                player_name: pName,
                team: pTeam,
                position: pPos,
                fantasy_points: parseCellVal(cells[1]),  // Puan
                starting_11: parseCellVal(cells[2]),     // İ11
                minutes: parseCellVal(cells[3]),         // OS (Oynanan Süre)
                goals: parseCellVal(cells[4]),           // Gol
                assists: parseCellVal(cells[5]),         // Asist
                bonus: parseCellVal(cells[6]),           // Bonus
                goals_conceded: parseCellVal(cells[7]),  // YG (Yenilen Gol)
                own_goals: parseCellVal(cells[8]),       // KKG
                penalties_saved: parseCellVal(cells[9]), // PKu
                penalties_missed: parseCellVal(cells[10]),// PKa
                yellow_cards: cells.length > 11 ? parseCellVal(cells[11]) : 0, // SK
                red_cards: cells.length > 12 ? parseCellVal(cells[12]) : 0,    // KK
                saves: cells.length > 13 ? parseCellVal(cells[13]) : 0         // Kurt
              });
            }
          }
        });
        console.log(`Maç ${mIdx + 1} (${matchTitle}): ${countInMatch} oyuncu başarıyla okundu.`);
      }

      // Çekmeceyi geri kapat
      if (chevronBtn) triggerFullClick(chevronBtn);
      else triggerFullClick(matchRow);
      await sleep(150);
    }

    const cleanResultsList = Array.from(activePlayersMap.values());
    console.log(`Fikstürden toplam ${cleanResultsList.length} oyuncu başarıyla toplandı!`);
    updateLog(`✅ 9 Maç tamamlandı! ${cleanResultsList.length} oyuncu hazırlandı.`, 100);

    const payload = {
      gameweek: targetGw,
      results: cleanResultsList
    };

    downloadJson(`match_sonuclari_gw${targetGw}.json`, payload);
    alert(`🎉 TEBRİKLER!\n\n9 maçın tamamı (Galatasaray - Çorum dahil) tarandı ve sahaya çıkan ${cleanResultsList.length} futbolcunun tüm resmi istatistikleri (Puan, Süre, Gol, Asist, Sarı/Kırmızı Kart, Bonus, Kurtarış) 'match_sonuclari_gw${targetGw}.json' olarak indirildi!`);
  };

  // UI Paneli
  const old = document.getElementById("tff-helper-panel");
  if (old) old.remove();

  const panel = document.createElement("div");
  panel.id = "tff-helper-panel";
  panel.style.position = "fixed";
  panel.style.top = "20px";
  panel.style.right = "20px";
  panel.style.zIndex = "9999999";
  panel.style.backgroundColor = "#0f172a";
  panel.style.color = "#ffffff";
  panel.style.padding = "18px 22px";
  panel.style.borderRadius = "14px";
  panel.style.boxShadow = "0 12px 40px rgba(0,0,0,0.85)";
  panel.style.border = "2px solid #38bdf8";
  panel.style.fontFamily = "system-ui, -apple-system, sans-serif";
  panel.style.fontSize = "13px";
  panel.style.minWidth = "320px";

  panel.innerHTML = `
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; border-bottom: 1px solid #334155; padding-bottom: 8px;">
      <span style="font-weight: 800; color: #38bdf8; font-size: 14px;">⚡ TFF Fantezi Fikstür Çekici v8</span>
      <button id="tff-btn-close" style="background: none; border: none; color: #94a3b8; cursor: pointer; font-size: 16px; font-weight: bold;">✕</button>
    </div>
    <div style="margin-bottom: 12px; display: flex; align-items: center; justify-content: space-between;">
      <label style="color: #cbd5e1; font-weight: 600;">Hafta (GW):</label>
      <input id="tff-gw-input" type="number" value="1" min="1" max="38" style="width: 55px; padding: 5px 8px; border-radius: 6px; border: 1px solid #475569; background: #1e293b; color: #38bdf8; font-weight: 700; text-align: center;">
    </div>
    <button id="tff-btn-fikstur" style="display: block; width: 100%; margin-bottom: 9px; padding: 12px 14px; background: #16a34a; color: white; border: none; border-radius: 8px; cursor: pointer; font-weight: 700; font-size: 13px; box-shadow: 0 4px 14px rgba(22, 163, 74, 0.45);">
      ⚽ 9 Maçın Resmi İstatistiklerini İndir
    </button>
    <button id="tff-btn-prices" style="display: block; width: 100%; margin-bottom: 8px; padding: 8px 12px; background: #0284c7; color: white; border: none; border-radius: 8px; cursor: pointer; font-weight: 600; font-size: 12px;">
      📥 462 Oyuncunun Fiyatlarını İndir (fiyat_gwX.json)
    </button>
    <div style="background: #1e293b; border-radius: 6px; height: 16px; width: 100%; margin-top: 8px; overflow: hidden;">
      <div id="tff-crawler-progress" style="background: #38bdf8; height: 100%; width: 0%; font-size: 10px; color: #0f172a; font-weight: bold; text-align: center; line-height: 16px;">0%</div>
    </div>
    <div id="tff-crawler-log" style="font-size: 11px; color: #94a3b8; margin-top: 6px; text-align: center; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">Hazır</div>
  `;

  document.body.appendChild(panel);

  document.getElementById("tff-btn-fikstur").onclick = () => {
    const gw = parseInt(document.getElementById("tff-gw-input").value, 10) || 1;
    window.scrapeFixtureResults(gw);
  };
  document.getElementById("tff-btn-prices").onclick = () => {
    const gw = parseInt(document.getElementById("tff-gw-input").value, 10) || 2;
    window.exportPrices(gw);
  };
  document.getElementById("tff-btn-close").onclick = () => {
    panel.remove();
  };

  console.log("[TFF Fantezi Export] Fikstür Çekici Paneli v8 Yüklendi!");
})();
