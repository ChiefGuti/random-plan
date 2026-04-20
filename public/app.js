const btn = document.getElementById("plan-btn");
const btnText = document.getElementById("btn-text");
const btnSpinner = document.getElementById("btn-spinner");
const errorMsg = document.getElementById("error-msg");

let activeCategory = "";
let currentPlan = null;

// ── Category filters ──────────────────────────────────────────────
document.querySelectorAll(".filter-btn").forEach(filterBtn => {
  filterBtn.addEventListener("click", () => {
    activeCategory = filterBtn.dataset.category;
    document.querySelectorAll(".filter-btn").forEach(b => {
      b.classList.remove("border-indigo-400", "text-white");
      b.classList.add("border-zinc-600", "text-zinc-400");
    });
    filterBtn.classList.remove("border-zinc-600", "text-zinc-400");
    filterBtn.classList.add("border-indigo-400", "text-white");
  });
});

btn.addEventListener("click", fetchPlan);

// ── Fetch ─────────────────────────────────────────────────────────
async function fetchPlan() {
  setLoading(true);
  hideError();

  try {
    const url = activeCategory
      ? `/api/random-plan?category=${encodeURIComponent(activeCategory)}`
      : "/api/random-plan";
    const res = await fetch(url);

    if (res.status === 429) { showError("Too many requests — take a breath and try again in a minute."); return; }
    if (res.status === 404) { showError("No plans available right now. Check back soon."); return; }
    if (res.status === 503) { showError("Service temporarily unavailable. Try again in a moment."); return; }
    if (!res.ok) { showError("Something went wrong. Please try again."); return; }

    currentPlan = await res.json();
    renderPlan(currentPlan);
  } catch {
    showError("Could not reach the server. Check your connection.");
  } finally {
    setLoading(false);
  }
}

// ── Render ────────────────────────────────────────────────────────
const CATEGORY_GRADIENTS = {
  "Food":    "from-orange-600/30 to-zinc-900/60",
  "Event":   "from-emerald-600/30 to-zinc-900/60",
  "Oddity":  "from-violet-600/30 to-zinc-900/60",
  "Outdoor": "from-amber-600/30 to-zinc-900/60",
};

const PRICE_LABELS = {
  "FREE":     "Free",
  "BUDGET":   "Budget",
  "MODERATE": "Mid-range",
  "EXPENSIVE": "Splurge",
};

function renderPlan(plan) {
  // Hero image / gradient
  const img = document.getElementById("plan-image");
  const gradient = document.getElementById("plan-hero-gradient");
  if (plan.image_url) {
    img.src = plan.image_url;
    img.classList.remove("hidden");
  } else {
    img.classList.add("hidden");
    img.src = "";
  }
  const gradClass = CATEGORY_GRADIENTS[plan.category] || "from-indigo-600/30 to-zinc-900/60";
  gradient.className = `absolute inset-0 bg-gradient-to-br ${gradClass}`;

  // Core fields
  document.getElementById("plan-category").textContent = plan.category;
  document.getElementById("plan-title").textContent = plan.title;
  document.getElementById("plan-description").textContent = plan.description;
  document.getElementById("plan-maps").href = plan.maps_url;
  document.getElementById("plan-source").href = plan.source_url;

  // Event date
  setPill("plan-date-pill", "plan-date-text", plan.event_date ? formatDate(plan.event_date) : null);

  // Metadata pills
  setPill("plan-neighborhood-pill", "plan-neighborhood-text", plan.neighborhood || null);
  setPill("plan-duration-pill", "plan-duration-text", plan.duration_minutes ? `${plan.duration_minutes} min` : null);
  setPill("plan-price-pill", "plan-price-text", plan.price_range ? (PRICE_LABELS[plan.price_range] || plan.price_range) : null);

  // Tips
  const tipsWrapper = document.getElementById("plan-tips-wrapper");
  const tipsBody = document.getElementById("plan-tips-body");
  const tipsChevron = document.getElementById("plan-tips-chevron");
  if (plan.tips) {
    document.getElementById("plan-tips-text").textContent = plan.tips;
    tipsWrapper.classList.remove("hidden");
    tipsBody.classList.add("hidden");
    tipsChevron.style.transform = "";
  } else {
    tipsWrapper.classList.add("hidden");
  }

  // Save button
  const saveBtn = document.getElementById("plan-save");
  saveBtn.classList.remove("hidden");
  updateSaveButton(plan.id);

  // Share button
  const shareBtn = document.getElementById("plan-share");
  if (navigator.share) {
    shareBtn.classList.remove("hidden");
    shareBtn.textContent = "Share";
    shareBtn.onclick = () => navigator.share({
      title: plan.title,
      text: plan.description,
      url: plan.source_url,
    }).catch(() => {});
  } else {
    shareBtn.classList.remove("hidden");
    shareBtn.textContent = "Copy Link";
    shareBtn.onclick = () => {
      navigator.clipboard.writeText(plan.source_url).then(() => {
        shareBtn.textContent = "Copied!";
        setTimeout(() => { shareBtn.textContent = "Copy Link"; }, 2000);
      });
    };
  }

  // Reveal card
  const card = document.getElementById("plan-card");
  card.classList.remove("opacity-0", "-translate-y-2", "pointer-events-none");
  card.classList.add("opacity-100", "translate-y-0");

  btnText.textContent = "Give Me Another Plan";
}

function setPill(pillId, textId, value) {
  const pill = document.getElementById(pillId);
  if (value) {
    document.getElementById(textId).textContent = value;
    pill.classList.remove("hidden");
    pill.classList.add("inline-flex");
  } else {
    pill.classList.add("hidden");
    pill.classList.remove("inline-flex");
  }
}

function formatDate(iso) {
  try {
    return new Date(iso).toLocaleDateString("en-SE", { weekday: "short", month: "short", day: "numeric" });
  } catch {
    return iso;
  }
}

// ── Tips toggle ───────────────────────────────────────────────────
document.getElementById("plan-tips-toggle").addEventListener("click", () => {
  const body = document.getElementById("plan-tips-body");
  const chevron = document.getElementById("plan-tips-chevron");
  const isOpen = !body.classList.contains("hidden");
  body.classList.toggle("hidden", isOpen);
  chevron.style.transform = isOpen ? "" : "rotate(90deg)";
});

// ── Save for Later ────────────────────────────────────────────────
function getSaved() {
  try { return JSON.parse(localStorage.getItem("saved-plans") || "[]"); }
  catch { return []; }
}

function setSaved(saved) {
  localStorage.setItem("saved-plans", JSON.stringify(saved));
}

function updateSaveButton(planId) {
  const btn = document.getElementById("plan-save");
  const saved = getSaved();
  const isSaved = saved.some(s => s.id === planId);
  btn.textContent = isSaved ? "🔖" : "🔖";
  btn.classList.toggle("text-amber-400", isSaved);
  btn.classList.toggle("border-amber-500/50", isSaved);
  btn.classList.toggle("text-zinc-400", !isSaved);
  btn.classList.toggle("border-zinc-700", !isSaved);
  btn.title = isSaved ? "Remove from saved" : "Save for later";
  btn.onclick = () => toggleSave(planId);
}

function toggleSave(planId) {
  if (!currentPlan || currentPlan.id !== planId) return;
  const saved = getSaved();
  const idx = saved.findIndex(s => s.id === planId);
  if (idx === -1) {
    saved.push({ id: planId, title: currentPlan.title, neighborhood: currentPlan.neighborhood || null });
  } else {
    saved.splice(idx, 1);
  }
  setSaved(saved);
  updateSaveButton(planId);
  renderSavedSection();
}

function renderSavedSection() {
  const saved = getSaved();
  const section = document.getElementById("saved-section");
  const countEl = document.getElementById("saved-count");
  const list = document.getElementById("saved-list");

  if (saved.length === 0) {
    section.classList.add("hidden");
    document.getElementById("saved-drawer").classList.add("hidden");
    return;
  }

  section.classList.remove("hidden");
  countEl.textContent = `(${saved.length})`;
  list.innerHTML = saved.map(s => `
    <li class="flex items-center justify-between gap-2">
      <span class="text-sm text-zinc-300 truncate">${s.title}${s.neighborhood ? ` <span class="text-zinc-500 text-xs">· ${s.neighborhood}</span>` : ""}</span>
      <button onclick="removeSaved('${s.id}')" class="text-xs text-zinc-500 hover:text-red-400 transition flex-shrink-0">✕</button>
    </li>
  `).join("");
}

function removeSaved(planId) {
  const saved = getSaved().filter(s => s.id !== planId);
  setSaved(saved);
  if (currentPlan && currentPlan.id === planId) updateSaveButton(planId);
  renderSavedSection();
}

document.getElementById("saved-pill").addEventListener("click", () => {
  const drawer = document.getElementById("saved-drawer");
  drawer.classList.toggle("hidden");
});

// ── Loading state ─────────────────────────────────────────────────
function setLoading(isLoading) {
  btn.disabled = isLoading;
  btnSpinner.classList.toggle("hidden", !isLoading);
  const hasCard = !document.getElementById("plan-card").classList.contains("opacity-0");
  btnText.textContent = isLoading
    ? "Finding something..."
    : (hasCard ? "Give Me Another Plan" : "Give Me a Plan");
}

function showError(msg) {
  errorMsg.textContent = msg;
  errorMsg.classList.remove("hidden");
}

function hideError() {
  errorMsg.classList.add("hidden");
}

// Init saved section on load
renderSavedSection();
