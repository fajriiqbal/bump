document.addEventListener("DOMContentLoaded", () => {
  const loader = document.getElementById("page-loader");
  if (!loader) return;

  let timer = null;
  let submitDelay = null;

  const showLoader = () => {
    clearTimeout(timer);
    loader.classList.add("is-active");
    document.body.classList.add("is-navigating");
  };

  const hideLoader = () => {
    clearTimeout(timer);
    clearTimeout(submitDelay);
    loader.classList.remove("is-active");
    document.body.classList.remove("is-navigating");
  };

  document.addEventListener("click", (event) => {
    const link = event.target.closest("a[href]");
    if (!link) return;
    if (link.hasAttribute("download")) return;
    if (link.target && link.target !== "_self") return;
    if (link.dataset.noLoading === "true") return;
    if (event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;

    const url = new URL(link.href, window.location.href);
    if (url.origin !== window.location.origin) return;
    if (url.pathname === window.location.pathname && url.hash) return;

    event.preventDefault();
    showLoader();
    window.setTimeout(() => {
      window.location.href = link.href;
    }, 180);
  }, true);

  document.addEventListener("submit", (event) => {
    const form = event.target;
    if (!(form instanceof HTMLFormElement)) return;
    if (form.dataset.noLoading === "true") return;
    if (form.noValidate || form.checkValidity()) {
      event.preventDefault();
      showLoader();
      clearTimeout(submitDelay);
      submitDelay = window.setTimeout(() => {
        form.submit();
      }, 180);
    }
  }, true);

  window.addEventListener("pageshow", hideLoader);
  window.addEventListener("beforeunload", showLoader);
});
