document.addEventListener("DOMContentLoaded", function () {
  let seconds = 30; // cooldown time
  const countdownEl = document.getElementById("countdown");
  const resendBtn = document.getElementById("resend-btn");

  let isActive = false;
  const finalText = resendBtn.dataset.finalText || "Resend"; // fallback if not set

  // block clicks until active
  resendBtn.addEventListener("click", function (e) {
    if (!isActive) {
      e.preventDefault();
      return;
    }
  });

  let timer = setInterval(() => {
    seconds--;
    countdownEl.textContent = seconds;

    if (seconds <= 0) {
      clearInterval(timer);
      isActive = true;

      // enable styling
      resendBtn.classList.remove("bg-gray-400", "cursor-not-allowed");
      resendBtn.classList.add("bg-primary-600", "hover:bg-primary-700");

      // dynamic text
      resendBtn.textContent = finalText;
    }
  }, 1000);
});
