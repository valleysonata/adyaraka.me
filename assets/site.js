// Native details keeps social links usable even without JavaScript.
const more = document.querySelector('.site-more');
if (more) {
  document.addEventListener('click', event => {
    if (!more.contains(event.target)) more.open = false;
  });
  more.addEventListener('keydown', event => {
    if (event.key === 'Escape') {
      more.open = false;
      more.querySelector('summary').focus();
    }
  });
}

const calendar = document.querySelector('.github-calendar');
if (calendar) {
  const days = [...calendar.querySelectorAll('.gh-day')];
  const tip = document.createElement('div');
  tip.className = 'github-tooltip';
  tip.setAttribute('role', 'tooltip');
  tip.hidden = true;
  document.body.append(tip);
  const show = day => {
    tip.textContent = day.getAttribute('aria-label');
    tip.hidden = false;
    const rect = day.getBoundingClientRect();
    tip.style.left = `${Math.max(8, Math.min(rect.left - tip.offsetWidth / 2 + rect.width / 2, innerWidth - tip.offsetWidth - 8))}px`;
    tip.style.top = `${rect.top - tip.offsetHeight - 8}px`;
  };
  days.forEach(day => {
    day.addEventListener('pointerenter', () => show(day));
    day.addEventListener('pointerleave', () => { tip.hidden = true; });
    day.addEventListener('focus', () => show(day));
    day.addEventListener('blur', () => { tip.hidden = true; });
    day.addEventListener('click', () => {
      days.forEach(cell => { cell.tabIndex = -1; });
      day.tabIndex = 0;
      show(day);
    });
  });
  calendar.addEventListener('keydown', event => {
    const index = days.indexOf(event.target);
    if (index < 0) return;
    const offsets = {ArrowLeft: -7, ArrowRight: 7, ArrowUp: -1, ArrowDown: 1};
    let next;
    if (event.key in offsets) next = Math.max(0, Math.min(days.length - 1, index + offsets[event.key]));
    else if (event.key === 'Home') next = 0;
    else if (event.key === 'End') next = days.length - 1;
    else if (event.key === 'Escape') { tip.hidden = true; return; }
    else return;
    event.preventDefault();
    days[index].tabIndex = -1;
    days[next].tabIndex = 0;
    days[next].focus();
  });
  addEventListener('scroll', () => { tip.hidden = true; }, {passive: true, capture: true});
  addEventListener('resize', () => { tip.hidden = true; }, {passive: true});
}
