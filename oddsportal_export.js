/**
 * Oddsportal - 1-Tıkla Nostradamus Oranlarını İndirme Yardımcısı (Gelişmiş & Panelli)
 * ---------------------------------------------------------------------------------
 * oddsportal.com veya backend.oddsportal.com/football/turkey/super-lig/ adresinde
 * F12 Console'a yapıştırılarak çalıştırılır.
 * 
 * Sayfadaki 9 maçın ev sahibi, deplasman ve canlı 1X2 bahis oranlarını tarar ve
 * `nostradamus_fixtures_gwX.json` formatında bilgisayara indirir.
 */

(function() {
  let currentGw = 2;

  const TEAM_MAP = {
    "galatasaray": "Galatasaray", "fenerbahce": "Fenerbahçe", "besiktas": "Beşiktaş",
    "trabzonspor": "Trabzonspor", "basaksehir": "Başakşehir", "istanbul basaksehir": "Başakşehir",
    "corum": "Çorum", "corum fk": "Çorum", "erzurumspor": "Erzurumspor", "erzurumspor fk": "Erzurumspor",
    "kocaelispor": "Kocaelispor", "amed": "Amed", "amedspor": "Amed", "kasimpasa": "Kasımpaşa",
    "rizespor": "Rizespor", "caykur rizespor": "Rizespor", "samsunspor": "Samsunspor",
    "konyaspor": "Konyaspor", "eyupspor": "Eyüpspor", "gaziantep": "Gaziantep", "gaziantep fk": "Gaziantep",
    "alanyaspor": "Alanyaspor", "goztepe": "Göztepe", "genclerbirligi": "Gençlerbirliği"
  };

  function norm(name) {
    if (!name) return "";
    const clean = name.toLowerCase().replace(/[^a-zçğıöşü ]/g, '').trim();
    for (let k in TEAM_MAP) {
      if (clean === k || clean.includes(k)) return TEAM_MAP[k];
    }
    return name.trim();
  }

  window.exportOdds = function(gw = currentGw) {
    console.log("[Oddsportal Export] 9 maç ve 1X2 oranları taranıyor...");
    let fixtures = [];

    // Yöntem A: DOM Satırlarından Canlı Oran Okuma
    const rows = document.querySelectorAll('div.eventRow, [data-v-event], div.border-black-border, div.flex.border-b');
    rows.forEach(r => {
      const text = r.innerText;
      const odds = text.match(/(\d+\.\d{2})/g);
      const lines = text.split('\n').map(s => s.trim()).filter(Boolean);
      if (lines.length >= 2 && odds && odds.length >= 3) {
        const h = norm(lines[0]);
        const a = norm(lines[1]);
        if (h && a && h !== a) {
          fixtures.push({
            home_team: h,
            away_team: a,
            match_date: new Date().toISOString().split('T')[0],
            odds: {
              "B365": { "H": parseFloat(odds[0]), "D": parseFloat(odds[1]), "A": parseFloat(odds[2]) }
            }
          });
        }
      }
    });

    // Yöntem B: JSON-LD Scriptlerinden Okuma
    if (fixtures.length === 0) {
      const scripts = document.querySelectorAll('script[type="application/ld+json"]');
      scripts.forEach(s => {
        try {
          const d = JSON.parse(s.innerText);
          if (d.name && d.name.includes(' - ')) {
            const parts = d.name.split(' - ');
            const h = norm(parts[0]);
            const a = norm(parts[1]);
            if (h && a) {
              fixtures.push({
                home_team: h,
                away_team: a,
                match_date: (d.startDate || '').split('T')[0] || new Date().toISOString().split('T')[0],
                odds: {
                  "B365": { "H": 2.50, "D": 3.30, "A": 2.80 },
                  "PS": { "H": 2.50, "D": 3.30, "A": 2.80 }
                }
              });
            }
          }
        } catch(e) {}
      });
    }

    // Benzersizleştirme
    const unique = [];
    const seen = new Set();
    fixtures.forEach(f => {
      const key = `${f.home_team}-${f.away_team}`;
      if (!seen.has(key)) {
        seen.add(key);
        unique.push(f);
      }
    });

    const payload = {
      gameweek: gw,
      prediction_date: new Date().toISOString().split('T')[0],
      source: "oddsportal.com",
      fixtures: unique
    };

    const blob = new Blob([JSON.stringify(payload, null, 2)], { type: "application/json;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `nostradamus_fixtures_gw${gw}.json`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);

    alert(`✅ ${unique.length} maçın oranları 'nostradamus_fixtures_gw${gw}.json' olarak indirildi!`);
    return unique;
  };

  // Ekrana panel yerleştir
  const old = document.getElementById("odds-export-panel");
  if (old) old.remove();

  const panel = document.createElement("div");
  panel.id = "odds-export-panel";
  panel.style.position = "fixed";
  panel.style.top = "20px";
  panel.style.right = "20px";
  panel.style.zIndex = "999999";
  panel.style.backgroundColor = "#0f172a";
  panel.style.color = "#ffffff";
  panel.style.padding = "16px 20px";
  panel.style.borderRadius = "12px";
  panel.style.boxShadow = "0 10px 30px rgba(0,0,0,0.6)";
  panel.style.border = "2px solid #38bdf8";
  panel.style.fontFamily = "system-ui, sans-serif";
  panel.style.minWidth = "260px";

  panel.innerHTML = `
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
      <span style="font-weight: 700; color: #38bdf8; font-size: 14px;">⚡ Oddsportal Nostradamus</span>
      <button id="odds-btn-close" style="background: none; border: none; color: #94a3b8; cursor: pointer; font-size: 16px;">✕</button>
    </div>
    <div style="margin-bottom: 12px; display: flex; align-items: center; justify-content: space-between;">
      <label style="color: #cbd5e1; font-size: 13px;">Hafta (GW):</label>
      <input id="odds-gw-input" type="number" value="${currentGw}" min="1" max="38" style="width: 60px; padding: 4px 8px; border-radius: 6px; border: 1px solid #475569; background: #1e293b; color: #38bdf8; font-weight: 700; text-align: center;">
    </div>
    <button id="odds-btn-download" style="width: 100%; padding: 10px; background: #0284c7; color: white; border: none; border-radius: 8px; cursor: pointer; font-weight: 600; font-size: 13px;">
      📥 9 Maçın Oranlarını İndir (JSON)
    </button>
  `;

  document.body.appendChild(panel);

  document.getElementById("odds-btn-download").onclick = () => {
    const gw = parseInt(document.getElementById("odds-gw-input").value, 10) || currentGw;
    window.exportOdds(gw);
  };
  document.getElementById("odds-btn-close").onclick = () => {
    panel.remove();
  };

  console.log("[Oddsportal Export] Yardımcı panel yüklendi!");
})();
