const btn = document.getElementById("plan-btn");
const btnText = document.getElementById("btn-text");
const btnSpinner = document.getElementById("btn-spinner");
const planCard = document.getElementById("plan-card");
const errorMsg = document.getElementById("error-msg");

btn.addEventListener("click", fetchPlan);

async function fetchPlan() {
  setLoading(true);
  hideError();

  try {
    const res = await fetch("/api/random-plan");

    if (res.status === 429) {
      showError("Too many requests — take a breath and try again in a minute.");
      return;
    }
    if (res.status === 404) {
      showError("No plans available right now. Check back soon.");
      return;
    }
    if (!res.ok) {
      showError("Something went wrong. Please try again.");
      return;
    }

    const plan = await res.json();
    renderPlan(plan);
  } catch {
    showError("Could not reach the server. Check your connection.");
  } finally {
    setLoading(false);
  }
}

function renderPlan(plan) {
  document.getElementById("plan-category").textContent = plan.category;
  document.getElementById("plan-title").textContent = plan.title;
  document.getElementById("plan-description").textContent = plan.description;
  document.getElementById("plan-maps").href = plan.maps_url;
  document.getElementById("plan-source").href = plan.source_url;
  planCard.classList.remove("hidden");
  btnText.textContent = "Give Me Another Plan";
}

function setLoading(isLoading) {
  btn.disabled = isLoading;
  btnSpinner.classList.toggle("hidden", !isLoading);
  btnText.textContent = isLoading ? "Finding something..." : (planCard.classList.contains("hidden") ? "Give Me a Plan" : "Give Me Another Plan");
}

function showError(msg) {
  errorMsg.textContent = msg;
  errorMsg.classList.remove("hidden");
}

function hideError() {
  errorMsg.classList.add("hidden");
}
