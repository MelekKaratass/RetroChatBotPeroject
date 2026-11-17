const log = document.getElementById("log");
const form = document.getElementById("chat-form");
const input = document.getElementById("message");
const sendButton = document.getElementById("send");
const clearButton = document.getElementById("clear");
const statusLine = document.getElementById("status");
const counter = document.getElementById("counter");
const modernizeButton = document.getElementById("modernize");

const eras = {
  "1995": {
    bot: "RETRO-BOT",
    you: "SEN",
    title: "RETRO-BOT ~ Kişisel Ana Sayfam ~ 1995",
    eyebrow: "1995",
    heading: "RETRO-BOT'un Ana Sayfası",
    aboutTitle: "Ben Kimim?",
    about: "Adım RETRO-BOT. 486 işlemcili bilgisayarım, 28.8 modemim ve bir yığın disketim var. Sene 1995. Bana bir şey sor; Pentium'dan IRC'ye, yeni çıkan Windows 95'ten en sevdiğim kasetlere kadar anlatırım. Gelecekten gelen tuhaf kelimeleri pek anlamam.",
    chatTitle: "Ziyaretçi Defteri / Sohbet",
    label: "Mesajın:",
    placeholder: "Buraya yaz...",
    send: "Gönder",
    clear: "Defteri Temizle",
    ready: "Hat hazır · 28.8 kbps",
    busy: "Modem çeviriyor...",
    failed: "Hat koptu",
    greeting: "Selam! Modemin bağlandı mı? Bir şey sormak ister misin?",
    cleared: "Defteri sildim. Yeni bir yapraktan başlayalım.",
    footer: "Bu sayfa eğitim amaçlıdır · RETRO-BOT Webring · En iyi 256 renkte görünür · Lütfen bant genişliğimi çalma",
    modernize: "Modernleştir",
  },
  "2030": {
    bot: "LUMEN",
    you: "SEN",
    title: "Lumen · 2030",
    eyebrow: "2030",
    heading: "Lumen",
    aboutTitle: "Bugün",
    about: "Sene 2030. Şehir daha sakin, ekranlar daha az bağırıyor. Ben Lumen. Geçmişi hatırlarım ama bugünü 2030 sanırım.",
    chatTitle: "Sohbet",
    label: "Mesaj",
    placeholder: "Bir şey sor...",
    send: "Gönder",
    clear: "Sohbeti kapat",
    ready: "Bağlantı sakin",
    busy: "Düşünüyor",
    failed: "Bağlantı kesildi",
    greeting: "Merhaba. 2030'dayız. Sormak istediğin bir şey varsa buradayım.",
    cleared: "Sohbeti kapattım. Yeniden başlayabiliriz.",
    footer: "Eğitim amaçlı bir arayüz · 2030",
    modernize: "1995'e dön",
  },
};

const history = [];
let era = "1995";
let busy = false;

function addMessage(role, author, text) {
  const paragraph = document.createElement("p");
  paragraph.className = role === "user" ? "msg user" : "msg bot";

  const name = document.createElement("b");
  name.textContent = author;
  const body = document.createElement("span");
  body.textContent = text;
  paragraph.append(name, body);

  log.appendChild(paragraph);
  log.scrollTop = log.scrollHeight;
}

function setBusy(isBusy, text) {
  busy = isBusy;
  sendButton.disabled = isBusy;
  input.disabled = isBusy;
  modernizeButton.disabled = isBusy;
  statusLine.textContent = text;
}

function resetLog() {
  history.length = 0;
  log.innerHTML = "";
  addMessage("bot", eras[era].bot, eras[era].greeting);
}

function applyEra(nextEra) {
  era = nextEra;
  const copy = eras[era];
  document.body.classList.toggle("era-2030", era === "2030");
  document.title = copy.title;
  document.getElementById("eyebrow").textContent = copy.eyebrow;
  document.getElementById("page-title").textContent = copy.heading;
  document.getElementById("about-title").textContent = copy.aboutTitle;
  document.getElementById("about-text").textContent = copy.about;
  document.getElementById("chat-title").textContent = copy.chatTitle;
  document.getElementById("message-label").textContent = copy.label;
  input.placeholder = copy.placeholder;
  sendButton.textContent = copy.send;
  clearButton.textContent = copy.clear;
  statusLine.textContent = copy.ready;
  document.getElementById("footer").textContent = copy.footer;
  modernizeButton.textContent = copy.modernize;
  resetLog();
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const message = input.value.trim();
  if (!message || busy) {
    return;
  }

  const copy = eras[era];
  addMessage("user", copy.you, message);
  input.value = "";
  setBusy(true, copy.busy);

  try {
    const response = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message, history, era }),
    });
    const data = await response.json();
    if (!response.ok) {
      const detail = data.detail || "Bilinmeyen hata.";
      addMessage("bot", "SİSTEM", String(detail));
      setBusy(false, copy.failed);
      return;
    }

    history.push({ role: "user", text: message });
    history.push({ role: "model", text: data.reply });
    if (history.length > 12) {
      history.splice(0, history.length - 12);
    }
    addMessage("bot", copy.bot, data.reply);
    setBusy(false, copy.ready);
  } catch (error) {
    addMessage("bot", "SİSTEM", "Bağlantı koptu. Sunucu çalışıyor mu?");
    setBusy(false, copy.failed);
  }
});

clearButton.addEventListener("click", () => {
  if (busy) {
    return;
  }
  history.length = 0;
  log.innerHTML = "";
  addMessage("bot", eras[era].bot, eras[era].cleared);
});

modernizeButton.addEventListener("click", () => {
  if (busy) {
    return;
  }
  applyEra(era === "1995" ? "2030" : "1995");
});

fetch("/api/counter")
  .then((response) => response.json())
  .then((data) => {
    counter.textContent = String(data.visitors).padStart(6, "0");
  })
  .catch(() => {
    counter.textContent = "------";
  });
