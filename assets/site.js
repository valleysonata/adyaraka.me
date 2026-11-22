// Content is visible by default, including without JavaScript or on API failure.
const reduceMotion = matchMedia('(prefers-reduced-motion: reduce)');
const reveals = [...document.querySelectorAll('.reveal')];
if (!reduceMotion.matches && 'IntersectionObserver' in window) {
  const observer = new IntersectionObserver(entries => {
    entries.forEach(entry => {
      if (!entry.isIntersecting) return;
      entry.target.classList.add('in');
      observer.unobserve(entry.target);
    });
  }, {threshold: 0.08, rootMargin: '0px 0px -24px 0px'});
  document.documentElement.classList.add('motion-ready');
  document.querySelectorAll('.featured-project').forEach((card, index) => {
    card.style.setProperty('--reveal-delay', `${index * 70}ms`);
  });
  reveals.forEach(element => observer.observe(element));
  // A tall hero must remain visible even if it exceeds the viewport.
  document.querySelector('.hero')?.classList.add('in');
}
reduceMotion.addEventListener('change', event => {
  if (event.matches) document.documentElement.classList.remove('motion-ready');
});

const portraitControl = document.querySelector('.portrait-control');
if (portraitControl) {
  const portrait = portraitControl.querySelector('.hero-portrait');
  const lines = [...portrait.querySelectorAll('tspan')];
  const originals = lines.map(line => line.textContent);
  const glyphs = '@%#*+=:.-';
  let frame = 0;
  const restore = () => {
    cancelAnimationFrame(frame);
    frame = 0;
    lines.forEach((line, index) => { line.textContent = originals[index]; });
    portrait.classList.remove('is-playing');
  };
  const scramble = (clicked = false) => {
    if (reduceMotion.matches || (!clicked && frame)) return;
    restore();
    if (clicked) portrait.classList.add('is-playing');
    const start = performance.now();
    const duration = clicked ? 850 : 520;
    let lastUpdate = -50;
    const tick = now => {
      const elapsed = now - start;
      if (elapsed >= duration) { restore(); return; }
      if (elapsed - lastUpdate >= 45) {
        const chance = .45 * (1 - elapsed / duration);
        lines.forEach((line, index) => {
          line.textContent = originals[index].replace(/\S/g, character =>
            Math.random() < chance ? glyphs[Math.floor(Math.random() * glyphs.length)] : character);
        });
        lastUpdate = elapsed;
      }
      frame = requestAnimationFrame(tick);
    };
    tick(start);
  };
  portraitControl.addEventListener('pointerenter', event => {
    if (event.pointerType !== 'touch') scramble();
  });
  portraitControl.addEventListener('focus', () => scramble());
  portraitControl.addEventListener('click', () => scramble(true));
  addEventListener('pagehide', restore);
  reduceMotion.addEventListener('change', restore);
}

const nav = document.querySelector('.site-nav');
if (nav) {
  nav.setAttribute('data-highlight', '');
  const highlight = nav.querySelector('.site-nav-highlight');
  const links = [...nav.querySelectorAll(':scope > a')];
  const active = links.find(link => link.hasAttribute('aria-current'));
  const place = link => {
    if (!link) { highlight.style.opacity = '0'; return; }
    highlight.style.width = `${link.offsetWidth}px`;
    highlight.style.height = `${link.offsetHeight}px`;
    highlight.style.transform = `translate(${link.offsetLeft}px, ${link.offsetTop}px)`;
    highlight.style.opacity = '1';
  };
  links.forEach(link => {
    link.addEventListener('pointerenter', () => place(link));
    link.addEventListener('focus', () => place(link));
  });
  nav.addEventListener('pointerleave', () => place(active));
  nav.addEventListener('focusout', event => {
    if (!nav.contains(event.relatedTarget)) place(active);
  });
  new ResizeObserver(() => place(active)).observe(nav);
  document.fonts.ready.then(() => place(active));
}

// Never remove the scroll cue: it returns every time the viewport returns home.
const scrollHint = document.getElementById('scroll-hint');
if (scrollHint) {
  const updateHint = () => {
    const atTop = scrollY <= 24;
    scrollHint.classList.toggle('hidden', !atTop);
    scrollHint.tabIndex = atTop ? 0 : -1;
    scrollHint.setAttribute('aria-hidden', String(!atTop));
  };
  scrollHint.addEventListener('click', () => {
    document.querySelector('.status').scrollIntoView({
      behavior: matchMedia('(prefers-reduced-motion: reduce)').matches ? 'instant' : 'smooth',
      block: 'start'
    });
  });
  addEventListener('scroll', updateHint, {passive: true});
  addEventListener('pageshow', updateHint);
  updateHint();
}

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
