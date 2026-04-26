/* =============================================
   PRESENTLY — main.js
   presently.at
   ============================================= */

(function () {
  'use strict';

  /* -----------------------------------------------
     1. Navigation: hamburger + scroll behavior
  ----------------------------------------------- */
  const nav = document.querySelector('.nav');
  const hamburger = document.querySelector('.nav__hamburger');
  const navLinks = document.querySelector('.nav__links');

  // Hamburger toggle
  if (hamburger && navLinks) {
    hamburger.addEventListener('click', () => {
      const isOpen = navLinks.classList.toggle('nav__links--open');
      hamburger.classList.toggle('nav__hamburger--open', isOpen);
      hamburger.setAttribute('aria-expanded', isOpen);
      document.body.style.overflow = isOpen ? 'hidden' : '';
    });

    // Close on outside click
    document.addEventListener('click', (e) => {
      if (!nav.contains(e.target) && navLinks.classList.contains('nav__links--open')) {
        navLinks.classList.remove('nav__links--open');
        hamburger.classList.remove('nav__hamburger--open');
        hamburger.setAttribute('aria-expanded', 'false');
        document.body.style.overflow = '';
      }
    });

    // Close on link click (mobile)
    navLinks.querySelectorAll('a').forEach(link => {
      link.addEventListener('click', () => {
        navLinks.classList.remove('nav__links--open');
        hamburger.classList.remove('nav__hamburger--open');
        hamburger.setAttribute('aria-expanded', 'false');
        document.body.style.overflow = '';
      });
    });
  }

  // Nav scroll behavior: add shadow on scroll
  let lastScrollY = 0;
  let ticking = false;

  function updateNav() {
    if (!nav) return;
    const scrollY = window.scrollY;

    if (scrollY > 10) {
      nav.classList.add('nav--scrolled');
    } else {
      nav.classList.remove('nav--scrolled');
    }

    // Hide nav on scroll down, show on scroll up
    if (scrollY > lastScrollY && scrollY > 80) {
      nav.classList.add('nav--hidden');
    } else {
      nav.classList.remove('nav--hidden');
    }

    lastScrollY = scrollY;
    ticking = false;
  }

  window.addEventListener('scroll', () => {
    if (!ticking) {
      requestAnimationFrame(updateNav);
      ticking = true;
    }
  }, { passive: true });

  /* -----------------------------------------------
     2. Table of Contents: active state on scroll
  ----------------------------------------------- */
  const tocLinks = document.querySelectorAll('.article-toc a[href^="#"]');
  const headings = document.querySelectorAll('.article-body h2[id], .article-body h3[id]');

  if (tocLinks.length && headings.length) {
    const observerOptions = {
      rootMargin: '-80px 0px -60% 0px',
      threshold: 0
    };

    const headingObserver = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          const id = entry.target.getAttribute('id');
          tocLinks.forEach(link => {
            link.classList.toggle('active', link.getAttribute('href') === `#${id}`);
          });
        }
      });
    }, observerOptions);

    headings.forEach(h => headingObserver.observe(h));
  }

  /* -----------------------------------------------
     3. Smooth scroll for anchor links
  ----------------------------------------------- */
  document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
      const targetId = this.getAttribute('href').slice(1);
      if (!targetId) return;
      const target = document.getElementById(targetId);
      if (target) {
        e.preventDefault();
        const navHeight = nav ? nav.offsetHeight : 0;
        const top = target.getBoundingClientRect().top + window.scrollY - navHeight - 16;
        window.scrollTo({ top, behavior: 'smooth' });
      }
    });
  });

  /* -----------------------------------------------
     4. Hero scroll hint fade
  ----------------------------------------------- */
  const heroScroll = document.querySelector('.hero__scroll');
  if (heroScroll) {
    window.addEventListener('scroll', () => {
      heroScroll.style.opacity = window.scrollY > 60 ? '0' : '1';
    }, { passive: true });
  }

  /* -----------------------------------------------
     5. Lazy load images (native + fallback)
  ----------------------------------------------- */
  if ('loading' in HTMLImageElement.prototype) {
    // Native lazy load supported — nothing to do
  } else {
    // Fallback: IntersectionObserver
    const lazyImages = document.querySelectorAll('img[loading="lazy"]');
    if (lazyImages.length) {
      const imgObserver = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
          if (entry.isIntersecting) {
            const img = entry.target;
            if (img.dataset.src) img.src = img.dataset.src;
            observer.unobserve(img);
          }
        });
      });
      lazyImages.forEach(img => imgObserver.observe(img));
    }
  }

  /* -----------------------------------------------
     6. Active nav link based on current page
  ----------------------------------------------- */
  const currentPath = window.location.pathname;
  document.querySelectorAll('.nav__links a').forEach(link => {
    const href = link.getAttribute('href');
    if (!href) return;
    // Exact match or blog with category param
    if (href === currentPath ||
       (currentPath.includes('blog.html') && href.includes('blog.html')) ||
       (currentPath === '/' && href === '/')) {
      link.classList.add('nav__link--active');
    }
  });

  /* -----------------------------------------------
     7. Reading progress bar (for article pages)
  ----------------------------------------------- */
  const articleBody = document.querySelector('.article-body');
  if (articleBody) {
    // Create progress bar
    const bar = document.createElement('div');
    bar.className = 'reading-progress';
    bar.setAttribute('role', 'progressbar');
    bar.setAttribute('aria-label', '읽기 진행도');
    bar.style.cssText = `
      position: fixed;
      top: 0;
      left: 0;
      width: 0%;
      height: 2px;
      background: var(--accent);
      z-index: 9999;
      transition: width 0.1s linear;
      pointer-events: none;
    `;
    document.body.prepend(bar);

    window.addEventListener('scroll', () => {
      const articleStart = articleBody.offsetTop;
      const articleHeight = articleBody.offsetHeight;
      const scrolled = window.scrollY - articleStart;
      const progress = Math.min(100, Math.max(0, (scrolled / articleHeight) * 100));
      bar.style.width = `${progress}%`;
    }, { passive: true });
  }

  /* -----------------------------------------------
     8. Copy link button (for articles)
  ----------------------------------------------- */
  const shareBtn = document.querySelector('.share-btn');
  if (shareBtn) {
    shareBtn.addEventListener('click', async () => {
      const url = window.location.href;
      try {
        if (navigator.share) {
          await navigator.share({ url, title: document.title });
        } else {
          await navigator.clipboard.writeText(url);
          shareBtn.textContent = '✓ 링크 복사됨';
          setTimeout(() => { shareBtn.textContent = '링크 복사'; }, 2000);
        }
      } catch (_) {
        // Fallback: select the URL manually
      }
    });
  }

})();
