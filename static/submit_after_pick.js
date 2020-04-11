"use strict";

window.addEventListener('DOMContentLoaded', () => {

  const picker = document.querySelector('input[type="file"]');
  const submit = document.querySelector('form button:last-child');
  const form = picker.form;

  picker.addEventListener('change', () => {
    form.requestSubmit(submit);
  });

  form.addEventListener('submit', event => {
    submit.innerHTML = `
      <div class="spinner">
        <div class="rect1"></div>
        <div class="rect2"></div>
        <div class="rect3"></div>
        <div class="rect4"></div>
        <div class="rect5"></div>
      </div>
    `;
  });
});
