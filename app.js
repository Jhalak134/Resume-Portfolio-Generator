/* app.js — PortfolioBuilder interactivity */

// ─── Hamburger / Mobile Menu ──────────────────────────────
const hamburger  = document.getElementById('hamburger-btn');
const mobileMenu = document.getElementById('mobile-menu');

hamburger?.addEventListener('click', () => {
  const isOpen = mobileMenu.classList.toggle('open');
  hamburger.classList.toggle('open', isOpen);
  hamburger.setAttribute('aria-expanded', isOpen);
  mobileMenu.setAttribute('aria-hidden', !isOpen);
});

// Close mobile menu when a link is clicked
mobileMenu?.querySelectorAll('a').forEach(link => {
  link.addEventListener('click', () => {
    mobileMenu.classList.remove('open');
    hamburger?.classList.remove('open');
    hamburger?.setAttribute('aria-expanded', 'false');
    mobileMenu.setAttribute('aria-hidden', 'true');
  });
});

// ─── File Upload Logic ────────────────────────────────────
const uploadZone   = document.getElementById('upload-zone');
const fileInput    = document.getElementById('resume-file-input');
const chooseBtn    = document.getElementById('choose-file-btn');
const fileChosen   = document.getElementById('file-chosen');
const fileNameDisp = document.getElementById('file-name-display');
const removeBtn    = document.getElementById('remove-file-btn');
const dragOverlay  = document.getElementById('drag-overlay');

// Open file picker when "Choose File" button clicked
chooseBtn?.addEventListener('click', (e) => {
  e.stopPropagation();
  fileInput?.click();
});

// Keyboard accessible zone
uploadZone?.addEventListener('keydown', (e) => {
  if (e.key === 'Enter' || e.key === ' ') {
    e.preventDefault();
    fileInput?.click();
  }
});

// File selected via input
fileInput?.addEventListener('change', () => {
  if (fileInput.files.length > 0) handleFile(fileInput.files[0]);
});

function handleFile(file) {
  const maxBytes = 10 * 1024 * 1024; // 10 MB
  const allowed  = ['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'text/plain'];
  const extOk    = /\.(pdf|docx|txt)$/i.test(file.name);

  if (!extOk) {
    showNotification('❌ Please upload a PDF, DOCX, or TXT file.', 'error');
    return;
  }
  if (file.size > maxBytes) {
    showNotification('❌ File exceeds 10MB limit.', 'error');
    return;
  }

  // Show chosen file strip
  fileNameDisp.textContent = file.name;
  fileChosen.removeAttribute('hidden');
  uploadZone.classList.remove('dragging');
  showNotification('✅ Resume uploaded! Generating your portfolio…', 'success');
}

// Remove file
removeBtn?.addEventListener('click', () => {
  fileInput.value = '';
  fileChosen.setAttribute('hidden', '');
});

// ─── Drag & Drop ──────────────────────────────────────────
const dropTarget = document.getElementById('upload-card');

['dragenter', 'dragover'].forEach(evt =>
  dropTarget?.addEventListener(evt, (e) => {
    e.preventDefault();
    uploadZone?.classList.add('dragging');
  })
);

['dragleave', 'dragend', 'drop'].forEach(evt =>
  dropTarget?.addEventListener(evt, (e) => {
    uploadZone?.classList.remove('dragging');
  })
);

dropTarget?.addEventListener('drop', (e) => {
  e.preventDefault();
  const file = e.dataTransfer?.files?.[0];
  if (file) handleFile(file);
});

// ─── Toast Notification ───────────────────────────────────
function showNotification(message, type = 'info') {
  const existing = document.getElementById('toast-notification');
  existing?.remove();

  const toast = document.createElement('div');
  toast.id = 'toast-notification';
  toast.setAttribute('role', 'alert');
  toast.setAttribute('aria-live', 'polite');
  toast.style.cssText = `
    position: fixed;
    bottom: 28px;
    left: 50%;
    transform: translateX(-50%) translateY(20px);
    background: ${type === 'error' ? '#fef2f2' : '#f0fdf4'};
    color: ${type === 'error' ? '#b91c1c' : '#15803d'};
    border: 1px solid ${type === 'error' ? '#fecaca' : '#bbf7d0'};
    border-radius: 12px;
    padding: 12px 24px;
    font-size: .92rem;
    font-weight: 600;
    box-shadow: 0 8px 24px rgba(0,0,0,.12);
    z-index: 9999;
    opacity: 0;
    transition: opacity .3s ease, transform .3s ease;
    font-family: 'Inter', sans-serif;
    white-space: nowrap;
  `;
  toast.textContent = message;
  document.body.appendChild(toast);

  requestAnimationFrame(() => {
    requestAnimationFrame(() => {
      toast.style.opacity = '1';
      toast.style.transform = 'translateX(-50%) translateY(0)';
    });
  });

  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateX(-50%) translateY(10px)';
    setTimeout(() => toast.remove(), 300);
  }, 3500);
}

// ─── Scroll Reveal ────────────────────────────────────────
const revealEls = document.querySelectorAll(
  '.feature-item, .template-card, .stat-card, .about-text, .about-stats'
);
revealEls.forEach(el => el.classList.add('reveal'));

const observer = new IntersectionObserver((entries) => {
  entries.forEach((entry, i) => {
    if (entry.isIntersecting) {
      setTimeout(() => entry.target.classList.add('visible'), i * 80);
      observer.unobserve(entry.target);
    }
  });
}, { threshold: 0.1 });

revealEls.forEach(el => observer.observe(el));

// ─── Active nav highlight on scroll ──────────────────────
const sections = document.querySelectorAll('section[id]');
const navLinks  = document.querySelectorAll('.nav-link');

const navObserver = new IntersectionObserver((entries) => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      navLinks.forEach(link => link.classList.remove('nav-active'));
      const active = document.querySelector(`.nav-link[href="#${entry.target.id}"]`);
      active?.classList.add('nav-active');
    }
  });
}, { rootMargin: '-40% 0px -55% 0px' });

sections.forEach(s => navObserver.observe(s));
