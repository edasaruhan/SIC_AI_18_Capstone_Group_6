// Builds showcase/NudgeWell_Sunum_TR.pptx, the Turkish deck for the 1 December 2026 final showcase.
// 7 main slides (5:00) + a hidden video fallback + backup. Every number is read from the
// aggregate result files below; nothing here touches the dataset.
//
// Requires pptxgenjs (npm i -g pptxgenjs). From the repository root:
//   NODE_PATH="$(npm root -g)" node deliverables/06_deployment/build/build_showcase_tr.js
// If showcase/NudgeWell_Demo_Yedek.mp4 exists, it is embedded on the hidden slide 5.

const fs = require("node:fs");
const path = require("node:path");
const pptxgen = require("pptxgenjs");

const root = path.resolve(__dirname, "..");
const read = (p) => JSON.parse(fs.readFileSync(p, "utf8"));
const hw6 = read(path.join(root, "build/results/hw6_local_evidence.json"));
const replay = read(path.join(root, "build/results/hw6_policy_replay.json"));
const checks = read(path.join(root, "build/results/showcase_headline_checks.json"));
const hw5 = read(path.join(root, "../05_model_refinement_test_submission/build/results",
  "hw5-v1-step5-20261117_evaluation.json"));
const VIDEO = path.join(root, "showcase", "NudgeWell_Demo_Yedek.mp4");
// Set to the send date (e.g. "28 Kasım 2026") once the licence email has actually been sent.
const PERMISSION_SENT = null;

// Turkish number format: 1.234,5
const tr = (x, d = 0) => Number(x).toLocaleString("tr-TR", { minimumFractionDigits: d, maximumFractionDigits: d });
const pct = (x, d = 0) => "%" + tr(x, d);

const INK = "15302A", PALE = "F5F3EC", OLIVE = "557366", LINE = "CAD2C6",
  RUST = "922F36", MINT = "D3E8D7", WHITE = "FFFFFF", AMBER = "B7791F";
const FONT = "Arial";
const X = 0.75, W = 11.83;

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE";
pres.title = "NudgeWell final sunumu";
pres.author = "Grup 6, Samsung Innovation Campus";
pres.theme = { headFontFace: FONT, bodyFontFace: FONT };

pres.defineSlideMaster({
  title: "DARK", background: { color: INK },
  objects: [{ placeholder: { options: { name: "title", type: "title", x: X, y: 0.55, w: W, h: 0.9,
    fontFace: FONT, fontSize: 36, bold: true, color: WHITE, margin: 0, valign: "middle", align: "left" }, text: "" } }],
});
pres.defineSlideMaster({
  title: "CONTENT", background: { color: PALE },
  objects: [{ placeholder: { options: { name: "title", type: "title", x: X, y: 0.55, w: W, h: 0.9,
    fontFace: FONT, fontSize: 34, bold: true, color: INK, margin: 0, valign: "middle", align: "left" }, text: "" } }],
  slideNumber: { x: 12.2, y: 6.95, w: 0.4, h: 0.3, fontFace: FONT, fontSize: 11, color: OLIVE, align: "right" },
});

function txt(slide, value, x, y, w, h, o = {}) {
  slide.addText(value, { x, y, w, h, isTextBox: true, margin: 0, fontFace: FONT, fontSize: 16,
    color: INK, valign: "top", ...o });
}
function card(slide, x, y, w, h, fill = WHITE) {
  slide.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h, rectRadius: 0.08,
    fill: { color: fill }, line: { color: LINE, width: 0.75 } });
}
function badge(slide, label, x, y, d = 0.55, fill = INK, color = WHITE) {
  slide.addShape(pres.shapes.OVAL, { x, y, w: d, h: d, fill: { color: fill }, line: { color: fill, width: 0 } });
  txt(slide, label, x, y, d, d, { fontSize: 18, bold: true, color, align: "center", valign: "middle" });
}
function footer(slide, value, color = OLIVE) {
  txt(slide, value, X, 6.9, 11.2, 0.35, { fontSize: 11, color, valign: "middle" });
}
function content(title, notes, section) {
  const s = pres.addSlide({ masterName: "CONTENT", sectionTitle: section });
  s.addText(title, { placeholder: "title" });
  s.addNotes(notes);
  return s;
}

const MAIN = "Sunum (5 dakika)";
const daily = checks.daily_all, noTop = checks.daily_without_most_extreme_person;
const stop = checks.stop_leaning;

// ------------------------------------------------------------------ Main talk
pres.addSection({ title: MAIN });

{ // 1. Title and hook
  const s = pres.addSlide({ masterName: "DARK", sectionTitle: MAIN });
  txt(s, "NudgeWell", X, 1.6, W, 1.2, { fontSize: 66, bold: true, color: WHITE, valign: "middle" });
  txt(s, "Hâlâ telefonda olmak istiyor musun?", X, 2.8, W, 0.75, { fontSize: 32, color: MINT, valign: "middle" });
  txt(s, "Samsung Innovation Campus Yapay Zekâ · Grup 6 · Yeşilay ile dijital bağımlılık bitirme projesi", X, 5.0, W, 0.45,
    { fontSize: 18, bold: true, color: WHITE, valign: "middle" });
  txt(s, "Yusuf Ersel Kara · Bahadır Maral · Çağla Eryılmaz · Fatih Mehmet Menteşe · Damla Nur Öcal", X, 5.5, W, 0.4,
    { fontSize: 15, color: MINT, valign: "middle" });
  s.addNotes("[0:00–0:20] Merhaba, biz Grup 6. Saat 23:10. Deniz, uydurma bir kullanıcımız, Instagram'ı " +
    "\"bir dakikalığına\" açtı; yirmi beş dakika oldu. Bırakmak istiyor ama devam ediyor. " +
    "NudgeWell, telefonun hiç sormadığı soruyu soruyor: hâlâ burada olmak istiyor musun?");
}

{ // 2. Problem
  const s = content("Sorun dakika değil, kontrol kaybı",
    "[0:20–1:00] Bugünkü dijital denge araçları zamana dayanıyor: uygulama zamanlayıcıları, günlük limitler. " +
    "Bu iki yerde başarısız oluyor. Amaçlı kullanımı, yol tarifini ya da bir grup sohbetini, yine de kesiyor. " +
    "Asıl önemli anda ise sessiz kalıyor: bırakmaya karar vermişsin ama limitin altında kaydırmaya devam ediyorsun. " +
    "Bu an sanıldığından sık. AwareMind çalışmasında insanlar \"bırakmalıyım\" dediğinde, anların yaklaşık yarısında " +
    "beş dakikadan fazla devam ettiler: " + pct(stop.over5_pct, 0) + ". \"Devam\" dediklerinde de " +
    pct(checks.continue_leaning_over5_pct, 0) + ". Yani \"bırakmalıyım\" demek tek başına pek bir şey değiştirmiyor. " +
    "Kaynak: Zheng & Choe 2026; 5.627 tekil check-in üzerinde kendi analizimiz (yinelenen satırlar çıkarıldı).",
    MAIN);
  const rows = [
    ["Amaçlı kullanımı böler", "Yol tarifi ya da grup sohbeti yine de kesilir."],
    ["Asıl anda sessiz kalır", "Bırakmaya karar vermişsin ama limitin altında kaydırmaya devam ediyorsun."],
  ];
  rows.forEach(([h, d], i) => {
    const y = 1.85 + i * 1.75;
    card(s, X, y, 6.9, 1.5);
    badge(s, "!", X + 0.3, y + 0.47, 0.55, RUST);
    txt(s, h, X + 1.15, y + 0.28, 5.5, 0.45, { fontSize: 22, bold: true, valign: "middle" });
    txt(s, d, X + 1.15, y + 0.75, 5.5, 0.6, { fontSize: 16 });
  });
  txt(s, "Dakikalar zararı iyi anlatmaz. Kontrol kaybı daha iyi bir işarettir.", X, 5.55, 6.9, 0.8,
    { fontSize: 16, italic: true, color: OLIVE });
  card(s, 8.15, 1.85, 4.43, 4.45, WHITE);
  txt(s, pct(stop.over5_pct, 0), 8.5, 2.1, 3.8, 1.3, { fontSize: 72, bold: true, color: RUST, valign: "middle" });
  txt(s, "\"Bırakmalıyım\" denen anların ardından 5 dakikadan fazla kullanım sürdü (" + tr(stop.n) + " anın " +
    tr(stop.over5) + "'i)", 8.5, 3.45, 3.8, 1.3, { fontSize: 17 });
  txt(s, "\"Devam\" denen anlarda: " + pct(checks.continue_leaning_over5_pct, 0), 8.5, 4.85, 3.8, 0.45,
    { fontSize: 16, bold: true, color: OLIVE });
  txt(s, "AwareMind, 37 yetişkin, kendi analizimiz", 8.5, 5.6, 3.8, 0.4, { fontSize: 12, color: OLIVE });
  footer(s, "Kaynak: Zheng & Choe 2026 (AwareMind) · 5.627 tekil check-in · build/results/showcase_headline_checks.json");
}

{ // 3. Objective and innovative solution
  const s = content("Yalnızca niyet ile davranış ayrıştığında sor",
    "[1:00–1:40] Amacımız iki parçalı. Birincisi bir soru: telefon, kişinin bırakmak isteyip devam ettiği anı sezebilir mi, " +
    "sezebiliyorsa neye bakarak? İkincisi bir tasarım: seyrek soran ve kararı kişiye bırakan bir dürtme. " +
    "Yenilik üç kuralda. Bir: tetikleyici ekran süresi değil, istenmeyen kullanım. İki: seyrek, tasarım gereği; " +
    "günde en fazla üç soru, aralarında en az otuz dakika. Üç: kontrol kullanıcıda; yerelde çalışır, tek dokunuşla kapanır, " +
    "öneriyi kişinin kendisi seçer.",
    MAIN);
  card(s, X, 1.75, W, 1.35, MINT);
  txt(s, "AMAÇ", X + 0.35, 1.9, 2.0, 0.3, { fontSize: 13, bold: true, color: OLIVE });
  txt(s, "Telefonun, kişinin bırakmak isteyip devam ettiği anı sezip sezemeyeceğini bulmak ve seyrek soran, kararı kişiye bırakan bir dürtme tasarlamak.",
    X + 0.35, 2.2, W - 0.7, 0.8, { fontSize: 20, bold: true });
  const items = [
    ["1", "Boşluğu hedefler", "Tetikleyici ekran süresi değil, istenmeyen kullanım."],
    ["2", "Seyrek sorar", "Günde en fazla 3 soru, aralarında en az 30 dakika."],
    ["3", "Kontrol kullanıcıda", "Yerelde çalışır. Tek dokunuşla kapanır. Öneriyi kişi seçer."],
  ];
  const cw = 3.73, gap = 0.32;
  items.forEach(([n, h, d], i) => {
    const x = X + i * (cw + gap);
    card(s, x, 3.35, cw, 2.95);
    badge(s, n, x + 0.3, 3.65);
    txt(s, h, x + 0.3, 4.45, cw - 0.6, 0.5, { fontSize: 22, bold: true });
    txt(s, d, x + 0.3, 5.05, cw - 0.6, 1.0, { fontSize: 16 });
  });
  footer(s, "HW1 fikir önerisi · HW3 kavram notu, hedefler O1–O6 ve gönderim politikası §4.5");
}

{ // 4. Live demo cue
  const s = content("Canlı: Deniz'in bir günü",
    "[1:40–2:55] Şimdi tarayıcıya geçiyorum. [Alt+Tab, Boşluk ile oynat.] Bu, uydurma bir hafta içi günü. " +
    "Her check-in, dağıtılan modelimizle aynı yerel API'ye gidiyor; buradaki model ise elle ayarlanmış temsili bir model, " +
    "çünkü veriyle eğitilmiş modeli izin gelmeden paylaşmıyoruz. Sabah ve öğlen NudgeWell sessiz; zamanlayıcı ise " +
    "15 dakikayı geçen her oturumda bölerdi. 20:30'da ilk soru geliyor. 20:50'de yine aday ama otuz dakika dolmadığı için " +
    "sormuyor. 23:10'da Deniz'in son soru hakkı: [kartta \"Hayır, bırakıyorum\"a dokun] kendi listesinden bir öneri. " +
    "23:55'te yine aday, ama günlük üç soru dolduğu için sessiz. Günün sonunda: zamanlayıcı altı kez bölerdi, " +
    "NudgeWell üç kez sordu. Bu bir gösterim, kanıt değil; kanıt birazdan. " +
    "[Demo 10 saniyede açılmazsa: bir sonraki gizli slayttaki videoya geç.]",
    MAIN);
  txt(s, "Tarayıcı: 127.0.0.1:8767  ·  Boşluk: oynat  ·  1 / 2: kart yanıtı", X, 1.7, W, 0.45, { fontSize: 18, color: OLIVE });
  const items = [
    ["Sessiz kalır", "Risk eşiğin altında. Zamanlayıcı ise dakikaya bakıp yine de bölebilir.", OLIVE],
    ["Sorar", "Risk eşiğin üstünde ve sınırlar uygun. Tek dokunuşla kapanır.", RUST],
    ["Bekletir", "30 dakikalık ara ya da günlük 3 soru dolmuşsa aday olsa bile sormaz.", AMBER],
  ];
  const cw = 3.73, gap = 0.32;
  items.forEach(([h, d, c], i) => {
    const x = X + i * (cw + gap);
    card(s, x, 2.45, cw, 2.9);
    s.addShape(pres.shapes.OVAL, { x: x + 0.3, y: 2.8, w: 0.45, h: 0.45, fill: { color: c }, line: { color: c, width: 0 } });
    txt(s, h, x + 0.3, 3.45, cw - 0.6, 0.5, { fontSize: 24, bold: true, color: c });
    txt(s, d, x + 0.3, 4.05, cw - 0.6, 1.1, { fontSize: 16 });
  });
  txt(s, "Puanlar canlı yerel API'den gelir. Model temsilidir ve elle ayarlanmıştır; uygulama adı modele gönderilmez.",
    X, 5.7, W, 0.5, { fontSize: 16, bold: true, color: INK });
  footer(s, "Temsili model showcase-illustrative-v2 · gönderim kuralları build/replay_policy.py · demo: showcase/demo_web/");
}

{ // 4b. Hidden fallback video
  const s = content("Yedek: kayıtlı demo",
    "Yalnızca canlı demo açılmazsa göster. \"Canlı demo açılmadı; aynı akışın kaydı bu.\" deyip videoyu oynat.",
    MAIN);
  s.hidden = true;
  if (fs.existsSync(VIDEO)) {
    s.addMedia({ type: "video", path: VIDEO, x: 1.4, y: 1.55, w: 10.53, h: 5.2 });
  } else {
    card(s, X, 1.8, W, 4.6, WHITE);
    txt(s, "Video henüz eklenmedi.\nKayıt: showcase/NudgeWell_Demo_Yedek.mp4, sonra bu dosyayı yeniden oluştur.",
      X + 0.4, 3.3, W - 0.8, 1.4, { fontSize: 20, color: RUST, align: "center", valign: "middle" });
  }
}

{ // 5. Method
  const lat = hw6.serving, exp = hw6.export;
  const s = content("Hiç görmediği kişilerde test edildi",
    "[2:55–3:30] Yöntem kısaca. AwareMind verisi: 37 yetişkinden 5.627 tekil check-in; her birinde kişi bırakmak isteyip " +
    "istemediğini söylüyor ve ardından ne yaptığını görüyoruz. Model yalnızca o an bilinenleri görüyor: saat, haftanın günü " +
    "ve oturumun ne kadar sürdüğü. Kalibre edilmiş bir lojistik regresyon bunu olasılığa çeviriyor; rastgele orman ve basit " +
    "bir kuralla karşılaştırdık. Hep, modelin hiç görmediği kişilerde test ettik. Sonra modeli ONNX'e aktarıp yerel bir " +
    "API ile sunduk: " + tr(exp.held_out_rows) + " test anında araştırma koduyla sıfır fark, yanıt yaklaşık " +
    tr(lat.latency_p50_ms, 0) + " milisaniye.",
    MAIN);
  const steps = [
    ["Veri", "5.627 check-in, 37 yetişkin (AwareMind)"],
    ["Sinyaller", "Saat, haftanın günü, oturum süresi"],
    ["Model", "Kalibre lojistik regresyon; rastgele orman ve basit kuralla karşılaştırıldı"],
    ["Karar", "Eşik + günde 3 soru + 30 dk ara"],
  ];
  const bw = 2.6, bg = 0.48;
  steps.forEach(([h, d], i) => {
    const x = X + i * (bw + bg);
    card(s, x, 1.85, bw, 2.35, i === 3 ? MINT : WHITE);
    txt(s, h, x + 0.25, 2.05, bw - 0.5, 0.45, { fontSize: 20, bold: true, color: i === 3 ? INK : OLIVE });
    txt(s, d, x + 0.25, 2.55, bw - 0.5, 1.5, { fontSize: 16 });
    if (i < 3) s.addShape(pres.shapes.LINE, { x: x + bw + 0.07, y: 3.02, w: bg - 0.14, h: 0,
      line: { color: INK, width: 2 } });
  });
  card(s, X, 4.6, W, 1.65, WHITE);
  txt(s, "Dağıtım", X + 0.35, 4.8, 2.5, 0.45, { fontSize: 20, bold: true, color: OLIVE });
  const stats = [
    ["ONNX + yerel API", "internet gerekmez"],
    ["0 fark", tr(exp.held_out_rows) + " test anında araştırma koduyla"],
    ["~" + tr(lat.latency_p50_ms, 0) + " ms", "ortanca yanıt süresi"],
  ];
  stats.forEach(([v, d], i) => {
    const x = X + 0.35 + i * 3.9;
    txt(s, v, x, 5.25, 3.6, 0.5, { fontSize: 24, bold: true });
    txt(s, d, x, 5.75, 3.6, 0.4, { fontSize: 14, color: OLIVE });
  });
  footer(s, "HW5 katılımcı-dışı değerlendirme · HW6 ONNX dışa aktarımı ve yerel sunum · build/results/hw6_local_evidence.json");
}

{ // 6. Result
  const s = content("Sonuç: boşluk kişiye özgü",
    "[3:30–4:20] Bulduğumuz en net sonuç şu: boşluk kişiye özgü. Aynı " + tr(daily.rows) + " check-in üzerinde, " +
    "işaretlenen anların ne kadarı gerçekten boşluk anıydı diye baktık. Şans düzeyi " + pct(daily.prevalence_pct, 0) + ". " +
    "Başkalarından öğrenilen saat ve oturum sinyalleri " + pct(daily.global.precision_pct, 0) + ". Basit kural " +
    pct(daily.fixed_rule.precision_pct, 0) + ". Kişinin en az bir haftalık kendi geçmişi eklenince " +
    pct(daily.offset.precision_pct, 0) + ": yaklaşık iki kat. En uç katılımcıyı çıkarınca da " +
    pct(noTop.offset.precision_pct, 0) + "'ya karşı " + pct(noTop.global.precision_pct, 0) + ", yine yaklaşık iki kat. " +
    "Olumsuz sonucu da açıkça söylüyoruz: yepyeni kullanıcılarda modelimiz iyileşmedi ve aynı günlük sınırla basit kural " +
    "daha çok anı yakaladı, " + replay.methods.fixed_three_signal_rule.positive_labels_reached + "'e karşı " +
    replay.methods.refined_fixed_cutoffs.positive_labels_reached + ". Bunlar geçmişe dönük; kimseye dürtme gönderilmedi. " +
    "Not: kuralın bu satırlardaki değeri 27 Kasım'da eklenen betimsel bir kontroldür. " +
    "Soru gelirse: model yine başkalarından öğrenildi ve kişiler hâlâ ayrı tutuldu; buradaki fark, kişinin kendi " +
    "önceki günlerinden gelen kişisel düzeyin eklenmesi.",
    MAIN);
  const bars = [
    ["Şans (taban oran)", daily.prevalence_pct, LINE, INK],
    ["Yalnızca saat sinyalleri (başkalarından)", daily.global.precision_pct, OLIVE, WHITE],
    ["Basit kural*", daily.fixed_rule.precision_pct, AMBER, WHITE],
    ["Kişinin kendi geçmişi (en az 1 hafta)", daily.offset.precision_pct, RUST, WHITE],
  ];
  txt(s, "İşaretlenen anların gerçekten boşluk anı olma oranı · aynı " + tr(daily.rows) + " check-in",
    X, 1.65, 7.6, 0.4, { fontSize: 15, color: OLIVE });
  const bx = X + 3.4, bmax = 4.1, scale = bmax / 40;
  bars.forEach(([label, v, fill, ink], i) => {
    const y = 2.2 + i * 0.95;
    txt(s, label, X, y, 3.25, 0.7, { fontSize: 15, bold: i === 3, valign: "middle" });
    s.addShape(pres.shapes.RECTANGLE, { x: bx, y: y + 0.08, w: v * scale, h: 0.55, fill: { color: fill }, line: { color: fill, width: 0 } });
    txt(s, pct(v, 1), bx + v * scale + 0.12, y, 1.1, 0.7, { fontSize: 18, bold: true, valign: "middle", color: i === 3 ? RUST : INK });
  });
  card(s, 9.0, 1.65, 3.58, 4.1, WHITE);
  txt(s, "≈2 kat", 9.3, 1.85, 3.0, 0.9, { fontSize: 48, bold: true, color: RUST, valign: "middle" });
  txt(s, "Kişinin kendi geçmişiyle işaretlemeler, saat sinyallerine göre yaklaşık iki kat isabetli.", 9.3, 2.85, 3.0, 1.2, { fontSize: 15 });
  txt(s, "En uç katılımcı çıkarılınca: " + pct(noTop.offset.precision_pct, 0) + " / " + pct(noTop.global.precision_pct, 0) +
    ", yine ≈2 kat.", 9.3, 4.15, 3.0, 0.8, { fontSize: 14, color: OLIVE });
  txt(s, "Geçmiş, daha çok kimin ve hangi günün riskli olduğunu söyler.", 9.3, 4.95, 3.0, 0.7, { fontSize: 13, color: OLIVE, italic: true });
  card(s, X, 6.0, W, 0.75, MINT);
  txt(s, "Yeni kullanıcılarda modelimiz iyileşmedi; aynı günlük sınırla basit kural daha çok anı yakaladı (" +
    replay.methods.fixed_three_signal_rule.positive_labels_reached + " / " + replay.methods.refined_fixed_cutoffs.positive_labels_reached + ").",
    X + 0.3, 6.0, W - 0.6, 0.75, { fontSize: 16, bold: true, valign: "middle" });
  footer(s, "Geçmişe dönük, kimseye dürtme gönderilmedi · 7 günlük ısınmadan sonraki check-in'ler · *kural: 27 Kasım betimsel kontrolü, dondurulmuş HW5 protokolü dışında");
}

{ // 7. Impact
  const s = pres.addSlide({ masterName: "DARK", sectionTitle: MAIN });
  s.addText("Bu ne değiştiriyor?", { placeholder: "title" });
  s.addNotes("[4:20–5:00] Peki etkisi ne? Yeşilay için: destek, ekran süresine değil kişinin kendi niyetine dayanmalı. " +
    "Somut öneri: yeni kullanıcıda basit kuralla başla, bir hafta sonra kişinin kendi yanıtlarıyla kişiselleştir. " +
    "Teslim ettiklerimiz: çevrimdışı çalışan, sınırları test edilmiş açık bir dürtme motoru; araştırma koduyla doğrulanmış " +
    "bir dağıtım; ve yazılı bir pilot protokolü. Sıradaki adımlar: veri izni, cihaz doğrulaması ve Türkiye'de yetişkinlerle " +
    "bir pilot. Davranışı değiştirdiğini henüz iddia etmiyoruz; bunu ölçmek için gerekeni kurduk. Teşekkürler.");
  const cols = [
    ["Yeşilay için", ["Destek, ekran süresine değil kişinin kendi niyetine dayanmalı",
      "Yeni kullanıcıda basit kuralla başla; bir hafta sonra kişinin kendi yanıtlarıyla kişiselleştir"]],
    ["Teslim ettiklerimiz", ["Çevrimdışı çalışan açık dürtme motoru; sınırları test edildi",
      "Araştırma koduyla doğrulanmış dağıtım (0 fark)", "Yazılı pilot protokolü"]],
    ["Sıradaki adımlar", ["Veri izni", "Telefonda cihaz doğrulaması",
      "Türkiye'de yetişkin pilotu: öneri ile sessiz kalmayı karşılaştırmak"]],
  ];
  cols.forEach(([h, list], i) => {
    const x = X + i * 4.0;
    txt(s, h, x, 1.8, 3.7, 0.5, { fontSize: 22, bold: true, color: MINT });
    s.addText(list.map((t, j) => ({ text: t, options: { bullet: true, breakLine: j < list.length - 1 } })),
      { x, y: 2.45, w: 3.7, h: 2.8, isTextBox: true, margin: 0, fontFace: FONT, fontSize: 17, color: WHITE,
        valign: "top", paraSpaceAfter: 10 });
  });
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: X, y: 5.45, w: W, h: 0.95, rectRadius: 0.08,
    fill: { color: MINT }, line: { color: MINT, width: 0 } });
  txt(s, "Davranışı değiştirdiğini henüz iddia etmiyoruz; bunu ölçmek için gerekeni kurduk.", X + 0.35, 5.45, W - 0.7, 0.95,
    { fontSize: 20, bold: true, valign: "middle" });
}

// ------------------------------------------------------------------ Backup
const BACK = "Yedek slaytlar (sorular için)";
pres.addSection({ title: BACK });

function table(s, rows, x, y, colW, size = 16) {
  s.addTable(rows.map((r, i) => r.map((c) => ({ text: String(c), options: {
    bold: i === 0 ? false : false, fontSize: i === 0 ? 13 : size, color: i === 0 ? OLIVE : INK, fontFace: FONT,
    border: [{ type: "none" }, { type: "none" }, { pt: 0.75, color: LINE }, { type: "none" }] } }))),
  { x, y, w: colW.reduce((a, b) => a + b, 0), colW, rowH: 0.48, margin: 0.05 });
}

{ // B1. HW5 results
  const n = hw5.new_user, b = hw5.secondary_prespecified_contrast;
  const s = content("Yedek · HW5 değerlendirmesi ne buldu?",
    "AP sıralamayı, Brier olasılık hatasını özetler. AP için eşleştirilmiş güven aralığı sıfırı kesiyor: net kazanç yok. " +
    "Brier kazancı kişisel taban orana göre ve küçük. Kaynak: 05_*/build/evaluation_review.md.", BACK);
  txt(s, "Yeni kullanıcılar (37 kişi, 5.627 check-in)", X, 1.7, 5.6, 0.4, { fontSize: 18, bold: true });
  table(s, [["Yöntem", "Dengeli AP ↑"],
    ["Sabit temel seçici", tr(n.fixed_baseline_selector.participant_balanced_AP, 4)],
    ["İyileştirilmiş seçici", tr(n.refined_selector.participant_balanced_AP, 4)],
    ["Fark (%95 aralık)", "−0,0169 (−0,0652; +0,0222)"]], X, 2.2, [3.0, 2.6]);
  txt(s, "Günlük kişiselleştirme (aynı 3.772 check-in)", X + 6.1, 1.7, 5.7, 0.4, { fontSize: 18, bold: true });
  table(s, [["Yöntem", "İsabet", "Yakalama", "Uyarı payı"],
    ["Saat sinyalleri", pct(daily.global.precision_pct, 1), pct(daily.global.recall_pct, 1), pct(daily.global.alert_share_pct, 1)],
    ["Kişisel taban oran", pct(daily.personal_rate.precision_pct, 1), pct(daily.personal_rate.recall_pct, 1), pct(daily.personal_rate.alert_share_pct, 1)],
    ["Günlük kişisel ofset", pct(daily.offset.precision_pct, 1), pct(daily.offset.recall_pct, 1), pct(daily.offset.alert_share_pct, 1)],
    ["Basit kural*", pct(daily.fixed_rule.precision_pct, 1), pct(daily.fixed_rule.recall_pct, 1), pct(daily.fixed_rule.alert_share_pct, 1)]],
    X + 6.1, 2.2, [2.3, 1.1, 1.2, 1.15], 15);
  txt(s, "Ofsetin kişisel taban orana göre Brier kazancı: " + tr(b.point_difference, 5) + " (" + tr(b.interval[0], 5) + "; " +
    tr(b.interval[1], 5) + "). Küçük ama aralık sıfırı kesmiyor.", X, 5.1, W, 0.8, { fontSize: 16 });
  footer(s, "Geçmişe dönük değerlendirme · *kural satırı: 27 Kasım betimsel kontrolü · build/results/showcase_headline_checks.json");
}

{ // B2. Policy replay
  const f = replay.methods.refined_fixed_cutoffs, r = replay.methods.fixed_three_signal_rule;
  const s = content("Yedek · Aynı sınırlarla geçmişe dönük gönderim",
    "Model kuraldan daha az soru gönderir ama daha az boşluk anına ulaşır. Kuralı geçtiğimizi iddia etmiyoruz. " +
    "Kaynak: build/results/hw6_policy_replay.json.", BACK);
  txt(s, "Günde en fazla 3 soru · en az 30 dk ara · " + tr(f.observed_participant_days) + " katılımcı-gün", X, 1.7, W, 0.45, { fontSize: 18, color: OLIVE });
  table(s, [["", "Model (HW5)", "Basit kural"],
    ["Aday işaret", tr(f.candidate_flags), tr(r.candidate_flags)],
    ["Gönderilen soru", tr(f.delivered_prompts), tr(r.delivered_prompts)],
    ["Ulaşılan boşluk anı", tr(f.positive_labels_reached), tr(r.positive_labels_reached)],
    ["30 dk arası nedeniyle bekletilen", tr(f.cooldown_suppressions), tr(r.cooldown_suppressions)],
    ["Günlük sınır nedeniyle bekletilen", tr(f.daily_cap_suppressions), tr(r.daily_cap_suppressions)]],
    X, 2.3, [4.6, 2.6, 2.6], 18);
  footer(s, "Simüle gönderimler, örneklenmiş geçmiş check-in'ler · kimse gerçekten dürtülmedi");
}

{ // B3. Deployment verification
  const lat = hw6.serving, exp = hw6.export;
  const s = content("Yedek · Dağıtım doğrulaması",
    "Dışa aktarılan ONNX modeli, aynı test satırlarında Python araştırma koduyla karşılaştırıldı. Süreler Windows loopback, " +
    "30 ısınma + 200 ölçümlü sentetik istek. Kaynak: build/results/hw6_local_evidence.json.", BACK);
  const items = [
    [tr(exp.held_out_rows) + " test anı, " + exp.held_out_participants + " kişi", "Karar farkı: " + exp.disagreeing_alert_flags],
    [tr(lat.latency_p50_ms, 2) + " ms ortanca", tr(lat.latency_p95_ms, 2) + " ms p95"],
    ["POST /v1/predict · GET /health · GET /metrics", "X-API-Key, yalnızca 127.0.0.1"],
  ];
  items.forEach(([h, d], i) => {
    const y = 1.85 + i * 1.5;
    card(s, X, y, W, 1.3);
    txt(s, h, X + 0.35, y + 0.2, W - 0.7, 0.5, { fontSize: 24, bold: true });
    txt(s, d, X + 0.35, y + 0.75, W - 0.7, 0.4, { fontSize: 16, color: OLIVE });
  });
  footer(s, "HW6 · ilk dış katman (fold 0) · " + exp.model_version);
}

{ // B4. Why synthetic
  const s = content("Yedek · Demo neden temsili bir model kullanıyor?",
    "Soru gelirse: Veri setinin lisansı yok; yazarlar yazılı izin verene kadar veriyle eğitilmiş hiçbir modeli yayımlamıyor " +
    "ya da canlı göstermiyoruz. Demo aynı API'yi kullanıyor; gerçek dışa aktarım ayrıca doğrulandı.", BACK);
  const rows = [
    ["Gerçek", "Yerel API, gönderim kuralları (günde 3, 30 dk), ONNX dışa aktarımı ve 0 fark doğrulaması"],
    ["Temsili", "Demo modelinin ağırlıkları elle ayarlandı; yalnızca yayımlanmış yönü izler (gece ve uzun oturum daha riskli)"],
    ["Bekleyen", "AwareMind yazarlarından yazılı izin. OSF sayfasında lisans yok; " +
      (PERMISSION_SENT ? "izin talebi gönderildi: " + PERMISSION_SENT : "izin talebi hazırlandı, henüz gönderilmedi")],
  ];
  rows.forEach(([h, d], i) => {
    const y = 1.85 + i * 1.5;
    card(s, X, y, W, 1.3);
    txt(s, h, X + 0.35, y + 0.2, 2.6, 0.9, { fontSize: 24, bold: true, valign: "middle", color: i === 1 ? AMBER : i === 2 ? RUST : OLIVE });
    txt(s, d, X + 3.0, y + 0.2, W - 3.4, 0.9, { fontSize: 17, valign: "middle" });
  });
  footer(s, "Veri ve model kuralları: data/README.md · showcase/demo_web/fixture_v2.py");
}

{ // B5. Data and transfer
  const s = content("Yedek · Veri ve Türkiye'ye aktarım",
    "Soru: Yeşilay için neden ABD verisi? Bulabildiğimiz, o anda bırakmak isteyip istemediğini ve ardından ne yaptığını " +
    "kaydeden tek açık veri seti bu. Katılımcılar azaltmak isteyen yetişkinler; ama Amerikalı ve Android kullanıcıları. " +
    "Aktarım kanıtlanmadı; pilotun ilk sorusu bu.", BACK);
  const items = [
    ["Kim?", "37 ABD'li yetişkin, 18–64 yaş (ort. 42), Android, günde en az 3 saat, kullanımı azaltmak isteyen"],
    ["Neden bu veri?", "O andaki niyeti ve sonraki davranışı birlikte kaydeden, bulabildiğimiz tek açık veri seti"],
    ["Sınır", "Ülke, yaş ve platform farkı. Türkiye'deki gençlere doğrudan genellenemez"],
    ["Sıradaki adım", "Türkiye'de onaylı bir yetişkin pilotunda önce sessiz modda ölçüm"],
  ];
  items.forEach(([h, d], i) => {
    const y = 1.8 + i * 1.18;
    card(s, X, y, W, 1.02);
    txt(s, h, X + 0.35, y + 0.15, 2.8, 0.7, { fontSize: 20, bold: true, valign: "middle" });
    txt(s, d, X + 3.2, y + 0.15, W - 3.6, 0.7, { fontSize: 16, valign: "middle" });
  });
  footer(s, "Zheng & Choe 2026 · data/README.md");
}

{ // B6. Why logistic regression
  const s = content("Yedek · Neden basit bir model?",
    "Yeni kullanıcı testinde karmaşıklık kişileri ezberledi. Rastgele orman eğitim kişilerinde 0,32–0,42, yeni kişilerde 0,17 " +
    "dengeli AP aldı. Bu yüzden kalibre basit model dürüst seçim. Dizi modelleri (TCN/GRU) kişi başına daha çok veri ister; " +
    "erteledik ve bunu HW5'te yazdık.", BACK);
  table(s, [["Model", "Eğitim kişileri (dengeli AP)", "Yeni kişiler (dengeli AP)"],
    ["Rastgele orman", "0,32–0,42", tr(hw5.new_user.fixed_RF.participant_balanced_AP, 3)],
    ["Lojistik regresyon", "0,18–0,22", tr(hw5.new_user.fixed_LR.participant_balanced_AP, 3)]],
    X, 2.0, [3.6, 4.0, 4.0], 20);
  txt(s, "Daha karmaşık model, eğitimde gördüğü kişileri ezberledi; yeni kişilerde avantajı kalmadı. HW3'teki TCN/GRU ertelendi (HW5 README).",
    X, 4.0, W, 0.9, { fontSize: 17 });
  footer(s, "05_*/build/results/hw5-v1-step5-20261117_metrics.csv · eğitim aralıkları beş dış katmandan");
}

{ // B7. Eşik
  const s = content("Yedek · Telefonda: Eşik prototipi",
    "Eşik, Ağustos 2026 hackathon'unda yaptığımız Android prototipi. Sabit bir günlük eşik kullanıyor ve NudgeWell'e bağlı değil. " +
    "Sıradaki adım, sabit eşiğin yerine modeli koymak ve fiziksel telefonda doğrulamak.", BACK);
  const steps = [
    ["1", "An algılanır", "Telefon, kullanıcının belirlediği limitin dolduğunu fark eder."],
    ["2", "Öneri sunulur", "Kişinin kendi seçtiği kısa bir etkinlik."],
    ["3", "Karar kullanıcıda", "Tek dokunuşla kapanır. Suçlama yok, kilitleme yok."],
  ];
  const cw = 3.73, gap = 0.32;
  steps.forEach(([n, h, d], i) => {
    const x = X + i * (cw + gap);
    card(s, x, 1.95, cw, 3.0);
    badge(s, n, x + 0.3, 2.3);
    txt(s, h, x + 0.3, 3.1, cw - 0.6, 0.5, { fontSize: 22, bold: true });
    txt(s, d, x + 0.3, 3.7, cw - 0.6, 1.0, { fontSize: 16 });
  });
  txt(s, "Sabit eşik bugün; model entegrasyonu ve telefonda doğrulama sıradaki adım.", X, 5.4, W, 0.5, { fontSize: 18, bold: true, color: OLIVE });
  footer(s, "Eşik: Ağustos 2026 hackathon prototipi · NudgeWell masaüstü modelinden ayrı");
}

{ // B8. Ethics
  const s = content("Yedek · Etik ve güvenlik",
    "Tanı koymuyoruz, terapi yerine geçmiyoruz. Destekleyici dil kullanıyoruz ve gerçek yardıma yönlendiriyoruz.", BACK);
  const items = [
    ["Tanı yok", "Bağımlılık teşhisi koymaz; yalnızca kişinin kendi hedefine göre seyrek bir soru sorar."],
    ["Destekleyici dil", "Suçlamayan, kısa, tek dokunuşla kapanan bir kart."],
    ["Gerçek yardım", "Gerektiğinde YEDAM ve 115 hattına yönlendirme."],
    ["Gizlilik", "Yerelde çalışır; check-in'ler cihazdan çıkmaz; izleme yalnızca toplu sayılar."],
  ];
  items.forEach(([h, d], i) => {
    const y = 1.8 + i * 1.18;
    card(s, X, y, W, 1.02);
    txt(s, h, X + 0.35, y + 0.15, 2.8, 0.7, { fontSize: 20, bold: true, valign: "middle" });
    txt(s, d, X + 3.2, y + 0.15, W - 3.6, 0.7, { fontSize: 16, valign: "middle" });
  });
  footer(s, "Tasarım ilkeleri · HW3 kavram notu, etik bölümü");
}

const out = path.join(root, "showcase", "NudgeWell_Sunum_TR.pptx");
pres.writeFile({ fileName: out }).then((f) => console.log(f));
