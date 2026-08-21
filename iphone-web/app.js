const MESSAGES = [
  "Mirror, mirror on the wall, {name} is the smartest of them all.",
  "You make every challenge feel like an adventure.",
  "You are the most beautiful bunny in the whole Enchanted Forest.",
  "Keep moving forward. You are doing an incredible job.",
  "To infinity and beyond. That is how far I love you.",
  "You are the hero of our story.",
  "You are the real magic in the Magic Kingdom.",
  "Your smile is the only enchantment I will ever need.",
  "You make the impossible look like a simple Tuesday afternoon.",
  "Your brilliance is the real heart of this house.",
  "You are the reason I believe in miracles every day.",
  "In the grand adventure of life, you are the only partner I want.",
  "You are the wise owl in a forest full of bunnies.",
  "Your love is the truest adventure I have ever known.",
  "You are the heart and soul of this entire operation."
];

const BUNNY_IMAGES = [
  "../bunny1.png",
  "../assets/bunny2.png",
  "../assets/bunny3.png",
  "../assets/bunny4.png",
  "../assets/bunny5.png"
];

const THEME_MAP = {
  sunset: {
    bg1: "#fff7e7",
    bg2: "#ffe8ee",
    accent: "#ff8a5c",
    ink: "#3b2f2f"
  },
  mint: {
    bg1: "#ebfff8",
    bg2: "#ddf4ff",
    accent: "#2ea789",
    ink: "#1f3932"
  },
  sky: {
    bg1: "#ecf4ff",
    bg2: "#dff0ff",
    accent: "#377dff",
    ink: "#22324d"
  },
  rose: {
    bg1: "#fff0f5",
    bg2: "#ffe3ea",
    accent: "#d85f86",
    ink: "#4f2a35"
  }
};

const SETTINGS_KEY = "bunny-notes-settings-v1";
const PIN_KEY = "bunny-notes-pin-v1";
const PERSONALIZATION_KEY = "bunny-notes-personalization-v1";
const DEFAULT_RECIPIENT = "Rebecca";
const DEFAULT_SENDER = "Michael";

const messageText = document.getElementById("messageText");
const bunnyImage = document.getElementById("bunnyImage");
const bunnyTint = document.getElementById("bunnyTint");
const prevBtn = document.getElementById("prevBtn");
const nextBtn = document.getElementById("nextBtn");
const shuffleBunnyBtn = document.getElementById("shuffleBunnyBtn");
const installBtn = document.getElementById("installBtn");
const settingsBtn = document.getElementById("settingsBtn");
const settingsModal = document.getElementById("settingsModal");
const fontSizeInput = document.getElementById("fontSizeInput");
const signatureToggle = document.getElementById("signatureToggle");
const themeSelect = document.getElementById("themeSelect");
const bunnyColorInput = document.getElementById("bunnyColorInput");
const bunnyColorToggle = document.getElementById("bunnyColorToggle");
const saveSettingsBtn = document.getElementById("saveSettingsBtn");
const closeSettingsBtn = document.getElementById("closeSettingsBtn");
const changePinBtn = document.getElementById("changePinBtn");
const removePinBtn = document.getElementById("removePinBtn");

const pinOverlay = document.getElementById("pinOverlay");
const pinTitle = document.getElementById("pinTitle");
const pinHint = document.getElementById("pinHint");
const pinInput = document.getElementById("pinInput");
const pinConfirmInput = document.getElementById("pinConfirmInput");
const pinError = document.getElementById("pinError");
const pinSubmitBtn = document.getElementById("pinSubmitBtn");
const recipientNameInput = document.getElementById("recipientNameInput");
const senderNameInput = document.getElementById("senderNameInput");
const signatureToggleLabel = document.getElementById("signatureToggleLabel");
const shareLinkBtn = document.getElementById("shareLinkBtn");
const shareLinkStatus = document.getElementById("shareLinkStatus");

let index = Math.floor(Math.random() * MESSAGES.length);
let deferredPrompt = null;
let appUnlocked = false;
let pinMode = "unlock";

const personalization = {
  recipient: DEFAULT_RECIPIENT,
  sender: DEFAULT_SENDER
};

const settings = {
  fontSize: 18,
  showSignature: true,
  theme: "sunset",
  bunnyColor: "#d9a5ff",
  bunnyColorEnabled: false
};

function loadSettings() {
  try {
    const parsed = JSON.parse(localStorage.getItem(SETTINGS_KEY) || "{}");
    if (Number.isFinite(parsed.fontSize)) {
      settings.fontSize = Math.min(30, Math.max(14, Number(parsed.fontSize)));
    }
    if (typeof parsed.showSignature === "boolean") {
      settings.showSignature = parsed.showSignature;
    }
    if (typeof parsed.theme === "string" && THEME_MAP[parsed.theme]) {
      settings.theme = parsed.theme;
    }
    if (typeof parsed.bunnyColor === "string" && /^#[0-9a-fA-F]{6}$/.test(parsed.bunnyColor)) {
      settings.bunnyColor = parsed.bunnyColor;
    }
    if (typeof parsed.bunnyColorEnabled === "boolean") {
      settings.bunnyColorEnabled = parsed.bunnyColorEnabled;
    }
  } catch {
    // Keep defaults when storage is unavailable.
  }
}

function saveSettings() {
  localStorage.setItem(SETTINGS_KEY, JSON.stringify(settings));
}

function loadPersonalization() {
  const params = new URLSearchParams(window.location.search);
  const toParam = params.get("to");
  const fromParam = params.get("from");

  if (toParam || fromParam) {
    personalization.recipient = toParam ? toParam.slice(0, 40) : DEFAULT_RECIPIENT;
    personalization.sender = fromParam ? fromParam.slice(0, 40) : DEFAULT_SENDER;
    localStorage.setItem(PERSONALIZATION_KEY, JSON.stringify(personalization));
    return;
  }

  try {
    const parsed = JSON.parse(localStorage.getItem(PERSONALIZATION_KEY) || "{}");
    if (typeof parsed.recipient === "string" && parsed.recipient.trim()) {
      personalization.recipient = parsed.recipient.trim();
    }
    if (typeof parsed.sender === "string" && parsed.sender.trim()) {
      personalization.sender = parsed.sender.trim();
    }
  } catch {
    // Keep defaults when storage is unavailable.
  }
}

function savePersonalization() {
  localStorage.setItem(PERSONALIZATION_KEY, JSON.stringify(personalization));
}

function buildShareUrl() {
  const url = new URL(window.location.href);
  url.search = "";
  url.searchParams.set("to", personalization.recipient);
  url.searchParams.set("from", personalization.sender);
  return url.toString();
}

function applyTheme(themeName) {
  const theme = THEME_MAP[themeName] || THEME_MAP.sunset;
  const root = document.documentElement;
  root.style.setProperty("--bg-1", theme.bg1);
  root.style.setProperty("--bg-2", theme.bg2);
  root.style.setProperty("--accent", theme.accent);
  root.style.setProperty("--ink", theme.ink);
}

function applyBunnyTint() {
  bunnyTint.style.setProperty("--bunny-color", settings.bunnyColor);
  bunnyTint.style.setProperty("--bunny-mask-image", `url("${bunnyImage.getAttribute("src")}")`);
  bunnyTint.classList.toggle("active", settings.bunnyColorEnabled);
}

function applySettingsToUI() {
  document.documentElement.style.setProperty("--message-font-size", `${settings.fontSize}px`);
  applyTheme(settings.theme);
  fontSizeInput.value = String(settings.fontSize);
  signatureToggle.checked = settings.showSignature;
  themeSelect.value = settings.theme;
  bunnyColorInput.value = settings.bunnyColor;
  bunnyColorToggle.checked = settings.bunnyColorEnabled;
  recipientNameInput.value = personalization.recipient;
  senderNameInput.value = personalization.sender;
  signatureToggleLabel.textContent = `Show signature (- ${personalization.sender})`;
  applyBunnyTint();
}

function renderMessage() {
  const template = MESSAGES[index];
  const withName = template.replace(/\{name\}/g, personalization.recipient);
  const signature = settings.showSignature ? ` - ${personalization.sender}` : "";
  messageText.textContent = `${withName}${signature}`;
}

function nextMessage() {
  if (!appUnlocked) {
    return;
  }
  index = (index + 1) % MESSAGES.length;
  renderMessage();
}

function prevMessage() {
  if (!appUnlocked) {
    return;
  }
  index = (index - 1 + MESSAGES.length) % MESSAGES.length;
  renderMessage();
}

function randomBunny() {
  if (!appUnlocked) {
    return;
  }
  const current = bunnyImage.getAttribute("src");
  const options = BUNNY_IMAGES.filter((src) => src !== current);
  const next = options[Math.floor(Math.random() * options.length)] || BUNNY_IMAGES[0];
  bunnyImage.setAttribute("src", next);
  applyBunnyTint();
}

function openSettings() {
  if (!appUnlocked) {
    return;
  }
  settingsModal.classList.remove("hidden");
  settingsModal.setAttribute("aria-hidden", "false");
}

function closeSettings() {
  settingsModal.classList.add("hidden");
  settingsModal.setAttribute("aria-hidden", "true");
}

function readPin() {
  return localStorage.getItem(PIN_KEY) || "";
}

function showPinOverlay(mode) {
  pinMode = mode;
  pinOverlay.classList.remove("hidden");
  pinOverlay.setAttribute("aria-hidden", "false");
  pinError.textContent = "";
  pinInput.value = "";
  pinConfirmInput.value = "";

  if (mode === "create") {
    pinTitle.textContent = "Create PIN";
    pinHint.textContent = "Create a 4-8 digit PIN for this phone.";
    pinConfirmInput.classList.remove("hidden");
    pinSubmitBtn.textContent = "Save PIN";
  } else {
    pinTitle.textContent = "Unlock Bunny Notes";
    pinHint.textContent = "Enter your PIN to continue.";
    pinConfirmInput.classList.add("hidden");
    pinSubmitBtn.textContent = "Unlock";
  }

  setTimeout(() => pinInput.focus(), 60);
}

function hidePinOverlay() {
  pinOverlay.classList.add("hidden");
  pinOverlay.setAttribute("aria-hidden", "true");
}

function handlePinSubmit() {
  const first = pinInput.value.trim();
  const second = pinConfirmInput.value.trim();

  if (!/^\d{4,8}$/.test(first)) {
    pinError.textContent = "PIN must be 4-8 digits.";
    return;
  }

  if (pinMode === "create") {
    if (first !== second) {
      pinError.textContent = "PIN entries do not match.";
      return;
    }
    localStorage.setItem(PIN_KEY, first);
    appUnlocked = true;
    hidePinOverlay();
    renderMessage();
    return;
  }

  if (first !== readPin()) {
    pinError.textContent = "Incorrect PIN.";
    return;
  }

  appUnlocked = true;
  hidePinOverlay();
  renderMessage();
}

function setupInitialLockState() {
  const existingPin = readPin();
  if (existingPin) {
    showPinOverlay("unlock");
  } else {
    showPinOverlay("create");
  }
}

nextBtn.addEventListener("click", nextMessage);
prevBtn.addEventListener("click", prevMessage);
shuffleBunnyBtn.addEventListener("click", randomBunny);
bunnyImage.addEventListener("click", nextMessage);
messageText.addEventListener("click", nextMessage);
settingsBtn.addEventListener("click", openSettings);
closeSettingsBtn.addEventListener("click", closeSettings);

saveSettingsBtn.addEventListener("click", () => {
  settings.fontSize = Number(fontSizeInput.value);
  settings.showSignature = signatureToggle.checked;
  settings.theme = themeSelect.value;
  settings.bunnyColor = bunnyColorInput.value;
  settings.bunnyColorEnabled = bunnyColorToggle.checked;
  personalization.recipient = recipientNameInput.value.trim().slice(0, 40) || DEFAULT_RECIPIENT;
  personalization.sender = senderNameInput.value.trim().slice(0, 40) || DEFAULT_SENDER;
  saveSettings();
  savePersonalization();
  applySettingsToUI();
  renderMessage();
  closeSettings();
});

shareLinkBtn.addEventListener("click", async () => {
  personalization.recipient = recipientNameInput.value.trim().slice(0, 40) || DEFAULT_RECIPIENT;
  personalization.sender = senderNameInput.value.trim().slice(0, 40) || DEFAULT_SENDER;
  const shareUrl = buildShareUrl();

  if (navigator.share) {
    try {
      await navigator.share({
        title: "Bunny Notes",
        text: `A Bunny Notes note for ${personalization.recipient}`,
        url: shareUrl
      });
      shareLinkStatus.textContent = "Shared!";
      return;
    } catch {
      // Fall through to clipboard copy if sharing was cancelled or unsupported.
    }
  }

  try {
    await navigator.clipboard.writeText(shareUrl);
    shareLinkStatus.textContent = "Link copied to clipboard.";
  } catch {
    shareLinkStatus.textContent = shareUrl;
  }
});

changePinBtn.addEventListener("click", () => {
  closeSettings();
  appUnlocked = false;
  showPinOverlay("create");
});

removePinBtn.addEventListener("click", () => {
  localStorage.removeItem(PIN_KEY);
  closeSettings();
});

pinSubmitBtn.addEventListener("click", handlePinSubmit);
pinInput.addEventListener("keydown", (event) => {
  if (event.key === "Enter") {
    handlePinSubmit();
  }
});
pinConfirmInput.addEventListener("keydown", (event) => {
  if (event.key === "Enter") {
    handlePinSubmit();
  }
});

let startX = 0;
window.addEventListener(
  "touchstart",
  (event) => {
    startX = event.changedTouches[0].clientX;
  },
  { passive: true }
);

window.addEventListener(
  "touchend",
  (event) => {
    if (!appUnlocked) {
      return;
    }
    const endX = event.changedTouches[0].clientX;
    const delta = endX - startX;
    if (Math.abs(delta) < 40) {
      return;
    }
    if (delta < 0) {
      nextMessage();
    } else {
      prevMessage();
    }
  },
  { passive: true }
);

window.addEventListener("beforeinstallprompt", (event) => {
  event.preventDefault();
  deferredPrompt = event;
  installBtn.hidden = false;
});

installBtn.addEventListener("click", async () => {
  if (!deferredPrompt) {
    return;
  }
  deferredPrompt.prompt();
  await deferredPrompt.userChoice;
  deferredPrompt = null;
  installBtn.hidden = true;
});

if ("serviceWorker" in navigator) {
  navigator.serviceWorker.register("service-worker.js").catch(() => {
    // Ignore registration failures to keep the app usable.
  });
}

loadSettings();
loadPersonalization();
applySettingsToUI();
renderMessage();
randomBunny();
setupInitialLockState();
