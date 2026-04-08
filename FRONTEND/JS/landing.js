'use strict';


(function initCursor() {
  const cursor   = document.getElementById('cursor');
  const follower = document.getElementById('cursorFollower');
  if (!cursor || !follower) return;

  let mouseX = 0, mouseY = 0;
  let followerX = 0, followerY = 0;

  document.addEventListener('mousemove', e => {
    mouseX = e.clientX;
    mouseY = e.clientY;
    cursor.style.left = mouseX + 'px';
    cursor.style.top  = mouseY + 'px';
  });


  function animateFollower() {
    followerX += (mouseX - followerX) * 0.12;
    followerY += (mouseY - followerY) * 0.12;
    follower.style.left = followerX + 'px';
    follower.style.top  = followerY + 'px';
    requestAnimationFrame(animateFollower);
  }
  animateFollower();

 
  const hoverEls = document.querySelectorAll('a, button, .feat-card, .role-card, .blood-option, .float-btn');
  hoverEls.forEach(el => {
    el.addEventListener('mouseenter', () => document.body.classList.add('cursor-hover'));
    el.addEventListener('mouseleave', () => document.body.classList.remove('cursor-hover'));
  });
})();



(function initNav() {
  const nav = document.getElementById('nav');
  if (!nav) return;

  let lastY = 0;
  window.addEventListener('scroll', () => {
    const y = window.scrollY;
    nav.classList.toggle('scrolled', y > 40);
    lastY = y;
  }, { passive: true });
})();


const hamburger  = document.getElementById('hamburger');
const mobileMenu = document.getElementById('mobileMenu');

if (hamburger && mobileMenu) {
  hamburger.addEventListener('click', () => {
    const isOpen = mobileMenu.classList.toggle('open');
    hamburger.classList.toggle('open', isOpen);
    document.body.style.overflow = isOpen ? 'hidden' : '';
  });
}

function closeMobile() {
  if (!mobileMenu || !hamburger) return;
  mobileMenu.classList.remove('open');
  hamburger.classList.remove('open');
  document.body.style.overflow = '';
}


(function initReveal() {
  const els = document.querySelectorAll('[data-reveal]');
  if (!els.length) return;

  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('revealed');
        observer.unobserve(entry.target);
      }
    });
  }, { threshold: 0.12, rootMargin: '0px 0px -40px 0px' });

  els.forEach(el => observer.observe(el));
})();



(function initCounters() {
  const counters = document.querySelectorAll('.hstat-val[data-count]');
  if (!counters.length) return;

  const easeOut = t => 1 - Math.pow(1 - t, 3);
  const formatNum = n => n >= 1000 ? (n / 1000).toFixed(0) + 'k' : String(n);

  function animateCounter(el) {
    const target   = parseInt(el.dataset.count, 10);
    const duration = 1800;
    const start    = performance.now();

    function tick(now) {
      const t   = Math.min((now - start) / duration, 1);
      const val = Math.round(easeOut(t) * target);
      el.textContent = formatNum(val);
      if (t < 1) requestAnimationFrame(tick);
    }
    requestAnimationFrame(tick);
  }

  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        animateCounter(entry.target);
        observer.unobserve(entry.target);
      }
    });
  }, { threshold: 0.5 });

  counters.forEach(el => observer.observe(el));
})();



(function initFloatCard() {
  const timeEl = document.getElementById('floatTime');
  if (!timeEl) return;

  let seconds = 0;
  setInterval(() => {
    seconds++;
    if      (seconds < 60)  timeEl.textContent = `${seconds}s ago`;
    else if (seconds < 3600) timeEl.textContent = `${Math.floor(seconds/60)}m ago`;
    else    timeEl.textContent = `just now`;
  }, 1000);
})();

function simulateAccept() {
  const btn    = document.querySelector('.float-btn.accept');
  const badge  = document.querySelector('.float-badge.critical');
  if (!btn || !badge) return;

  btn.textContent = '✓ Accepted!';
  btn.style.background = 'rgba(29,185,84,0.3)';
  btn.disabled = true;
  badge.textContent = '✓ CONFIRMED';
  badge.style.color = '#1DB954';
  badge.style.background = 'rgba(29,185,84,0.12)';
  badge.style.borderColor = 'rgba(29,185,84,0.3)';

  setTimeout(() => {
    btn.textContent = '✓ Accept';
    btn.style.background = '';
    btn.disabled = false;
    badge.textContent = '🚨 CRITICAL';
    badge.style.color = '';
    badge.style.background = '';
    badge.style.borderColor = '';
  }, 3000);
}


(function initTicker() {
  const track = document.getElementById('tickerTrack');
  if (!track) return;
  // Already duplicated in HTML — nothing extra needed
  // But pause on hover
  track.addEventListener('mouseenter', () => track.style.animationPlayState = 'paused');
  track.addEventListener('mouseleave', () => track.style.animationPlayState = 'running');
})();



document.querySelectorAll('a[href^="#"]').forEach(a => {
  a.addEventListener('click', e => {
    const id = a.getAttribute('href').slice(1);
    const el = document.getElementById(id);
    if (!el) return;
    e.preventDefault();
    closeMobile();
    const offset = 72; // nav height
    const top = el.getBoundingClientRect().top + window.scrollY - offset;
    window.scrollTo({ top, behavior: 'smooth' });
  });
});



window.addEventListener('DOMContentLoaded', () => {
  
  setTimeout(() => {
    document.querySelectorAll('.hero [data-reveal]').forEach(el => {
      el.classList.add('revealed');
    });
  }, 100);
});



document.querySelectorAll('.accent-line').forEach(el => {
  el.dataset.text = el.textContent;
});
