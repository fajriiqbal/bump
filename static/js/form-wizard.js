document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll("[data-form-wizard]").forEach((wizard) => {
    const steps = Array.from(wizard.querySelectorAll("[data-wizard-step]"));
    const chips = Array.from(wizard.querySelectorAll("[data-wizard-chip]"));
    const prevButton = wizard.querySelector("[data-wizard-prev]");
    const nextButton = wizard.querySelector("[data-wizard-next]");
    const submitButton = wizard.querySelector("[data-wizard-submit]");
    const currentLabel = wizard.querySelector("[data-wizard-current]");
    const totalLabel = wizard.querySelector("[data-wizard-total]");
    const progress = wizard.querySelector("[data-wizard-progress]");

    if (!steps.length) return;

    const firstErrorIndex = steps.findIndex((step) => step.querySelector(".text-red-600"));
    let index = firstErrorIndex >= 0 ? firstErrorIndex : 0;

    if (totalLabel) totalLabel.textContent = String(steps.length).padStart(2, "0");

    const render = () => {
      steps.forEach((step, stepIndex) => {
        step.hidden = stepIndex !== index;
      });

      chips.forEach((chip, stepIndex) => {
        chip.classList.toggle("wizard-chip-active", stepIndex === index);
        chip.classList.toggle("wizard-chip-complete", stepIndex < index);
      });

      if (currentLabel) currentLabel.textContent = String(index + 1).padStart(2, "0");
      if (progress) progress.style.width = `${((index + 1) / steps.length) * 100}%`;
      if (prevButton) prevButton.disabled = index === 0;
      if (nextButton) nextButton.hidden = index >= steps.length - 1;
      if (submitButton) submitButton.hidden = index < steps.length - 1;
    };

    const goTo = (nextIndex) => {
      index = Math.max(0, Math.min(nextIndex, steps.length - 1));
      render();
      wizard.scrollIntoView({ behavior: "smooth", block: "start" });
    };

    prevButton?.addEventListener("click", () => goTo(index - 1));
    nextButton?.addEventListener("click", () => goTo(index + 1));
    chips.forEach((chip, stepIndex) => chip.addEventListener("click", () => goTo(stepIndex)));

    render();
  });
});
