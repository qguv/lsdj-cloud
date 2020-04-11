function plural(n, unit) {
  return `${n} ${unit}${(n == 1) ? '' : 's'}`;
}

function sec2a(sec) {
  // under a minute, show countdown
  if (sec < 60) {
    return plural(sec, 'second');

  // under an hour, show minutes
  } else if (sec < 60 * 60) {
    return plural(Math.round(sec / 60), 'minute');

  // under a day, show hours
  } else if (sec < 60 * 60 * 24) {
    return plural(Math.round(sec / 60 / 60), 'hour');

  } else {
    return plural(Math.round(sec / 60 / 60 / 24), 'day');
  }
}

function update_timedelta(node) {
  let n = +node.dataset.seconds;
  if (n < 0) {
    window.location.reload();
    return;
  }
  node.innerHTML = sec2a(n);
}

function tick() {
  document.querySelectorAll("span.timedelta").forEach(node => {
    update_timedelta(node);
    node.dataset.seconds = node.dataset.seconds - 1;
  });
}

window.addEventListener("DOMContentLoaded", () => {
  tick();
  window.setInterval(tick, 1000);
});
