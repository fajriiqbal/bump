document.addEventListener("DOMContentLoaded", () => {
  const toast = document.getElementById("app-toast");
  if (!toast) return;

  const closeButtons = toast.querySelectorAll("[data-toast-close]");
  let hideTimer = null;

  const hideToast = () => {
    clearTimeout(hideTimer);
    toast.classList.remove("is-visible");
  }

  window.setTimeout(() => {
    toast.classList.add("is-visible");
  }, 500);

  hideTimer = window.setTimeout(() => {
    hideToast();
  }, 7000);

  closeButtons.forEach((button) => {
    button.addEventListener("click", hideToast);
  });
});
