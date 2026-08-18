/* app.js — PortfolioBuilder interactivity */

// ─── State ────────────────────────────────────────────────
let resumeFile       = null;          // the actual File object
let selectedTemplate = 'template1.html';

// ─── Hamburger / Mobile Menu ──────────────────────────────
const hamburger  = document.getElementById('hamburger-btn');
const mobileMenu = document.getElementById('mobile-menu');

hamburger?.addEventListener('click', () => {
  const isOpen = mobileMenu.classList.toggle('open');
  hamburger.classList.toggle('open', isOpen);
  hamburger.setAttribute('aria-expanded', isOpen);
  mobileMenu.setAttribute('aria-hidden', !isOpen);
});
mobileMenu?.querySelectorAll('a').forEach(link => {
  link.addEventListener('click', () => {
    mobileMenu.classList.remove('open');
    hamburger?.classList.remove('open');
    hamburger?.setAttribute('aria-expanded', 'false');
    mobileMenu.setAttribute('aria-hidden', 'true');
  });
});

// ─── File Upload Logic ────────────────────────────────────
const uploadZone      = document.getElementById('upload-zone');
const fileInput       = document.getElementById('resume-file-input');
const chooseBtn       = document.getElementById('choose-file-btn');
const fileChosen      = document.getElementById('file-chosen');
const fileNameDisp    = document.getElementById('file-name-display');
const removeBtn       = document.getElementById('remove-file-btn');
const postUploadPanel = document.getElementById('post-upload-panel');
const pupFilename     = document.getElementById('pup-filename');
const generateMainBtn = document.getElementById('btn-generate-main');

chooseBtn?.addEventListener('click', (e) => {
  e.stopPropagation();
  fileInput?.click();
});

uploadZone?.addEventListener('keydown', (e) => {
  if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); fileInput?.click(); }
});

fileInput?.addEventListener('change', () => {
  if (fileInput.files.length > 0) handleFile(fileInput.files[0]);
});

function handleFile(file) {
  const extOk = /\.(pdf|docx|txt)$/i.test(file.name);
  if (!extOk) { showNotification('❌ Please upload a PDF, DOCX, or TXT file.', 'error'); return; }
  if (file.size > 10 * 1024 * 1024) { showNotification('❌ File exceeds 10MB limit.', 'error'); return; }

  resumeFile = file;

  // Update file-chosen strip (legacy)
  fileNameDisp.textContent = file.name;
  fileChosen.removeAttribute('hidden');
  uploadZone.classList.remove('dragging');

  // Show the post-upload panel
  pupFilename.textContent = file.name;
  postUploadPanel.removeAttribute('hidden');

  showNotification('✅ Resume uploaded! Choose a template and generate your portfolio.', 'success');
}

removeBtn?.addEventListener('click', resetUpload);

function resetUpload() {
  fileInput.value = '';
  fileChosen.setAttribute('hidden', '');
  postUploadPanel.setAttribute('hidden', '');
  resumeFile = null;
}

// ─── Drag & Drop ──────────────────────────────────────────
const dropTarget = document.getElementById('upload-card');
['dragenter', 'dragover'].forEach(evt =>
  dropTarget?.addEventListener(evt, (e) => { e.preventDefault(); uploadZone?.classList.add('dragging'); })
);
['dragleave', 'dragend', 'drop'].forEach(evt =>
  dropTarget?.addEventListener(evt, () => uploadZone?.classList.remove('dragging'))
);
dropTarget?.addEventListener('drop', (e) => {
  e.preventDefault();
  const file = e.dataTransfer?.files?.[0];
  if (file) handleFile(file);
});

// ─── Template Chip Selection (inside post-upload panel) ───
document.querySelectorAll('.pup-chip:not(.pup-chip-disabled)').forEach(chip => {
  chip.addEventListener('click', () => {
    document.querySelectorAll('.pup-chip').forEach(c => c.classList.remove('pup-chip-active'));
    chip.classList.add('pup-chip-active');
    selectedTemplate = chip.dataset.template || 'template1.html';
  });
});

// ─── Template Card Selection (templates section) ──────────
document.querySelectorAll('.template-card:not(.coming-soon-card)').forEach(card => {
  card.addEventListener('click', (e) => {
    if (e.target.closest('.btn-preview-tmpl')) return;
    document.querySelectorAll('.template-card').forEach(c => {
      c.classList.remove('active-template');
      c.setAttribute('aria-pressed', 'false');
    });
    card.classList.add('active-template');
    card.setAttribute('aria-pressed', 'true');
    selectedTemplate = card.dataset.template || 'template1.html';

    // Sync the chip in the panel
    document.querySelectorAll('.pup-chip').forEach(c => c.classList.remove('pup-chip-active'));
    const matchingChip = document.querySelector(`.pup-chip[data-template="${selectedTemplate}"]`);
    matchingChip?.classList.add('pup-chip-active');

    showNotification('✅ Template selected!', 'success');
  });
  card.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); card.click(); }
  });
});

// ─── Generate Portfolio — Main Action ────────────────────
generateMainBtn?.addEventListener('click', async () => {
  if (!resumeFile) {
    showNotification('❌ Please upload a resume first.', 'error');
    return;
  }

  setGeneratingState(true);

  try {
    // ─ Try the backend first (best quality: real AI parsing)
    let portfolioData = null;

    try {
      portfolioData = await generateViaBackend(resumeFile);
    } catch (err) {
      console.warn('Backend unavailable, using client-side fallback:', err.message);
    }

    // ─ Client-side fallback for all file types
    if (!portfolioData) {
      const resumeText = await readFileAsText(resumeFile);
      const meaningfulText = resumeText.replace(/[\s\n\r\t]+/g, '').trim();
      if (meaningfulText.length < 50) {
        setGeneratingState(false);
        showBigError(
          "Nah, can't work with this 😅",
          resumeFile.size === 0
            ? 'The file you uploaded is completely empty. Please add your resume content and try again.'
            : 'Not enough content found in this file. Make sure your resume has actual text — scanned image PDFs or blank files won\'t work.'
        );
        return;
      }
      portfolioData = parseResumeClientSide(resumeText);
    }

    // ─ Store and navigate
    localStorage.setItem('portfolioData', JSON.stringify(portfolioData));
    localStorage.setItem('portfolioTemplate', selectedTemplate);
    showNotification('🎉 Portfolio generated! Opening...', 'success');
    setTimeout(() => { window.location.href = selectedTemplate; }, 800);

  } catch (err) {
    console.error('Portfolio generation error:', err);
    showNotification('❌ Could not process the file. Please try again.', 'error');
  } finally {
    setGeneratingState(false);
  }
});


function setGeneratingState(isLoading) {
  if (!generateMainBtn) return;
  if (isLoading) {
    generateMainBtn.classList.add('loading');
    generateMainBtn.innerHTML = `
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" class="spin" aria-hidden="true">
        <circle cx="12" cy="12" r="10" stroke="rgba(255,255,255,.3)" stroke-width="2.5"/>
        <path d="M12 2a10 10 0 0 1 10 10" stroke="#fff" stroke-width="2.5" stroke-linecap="round"/>
      </svg>
      Generating…`;
  } else {
    generateMainBtn.classList.remove('loading');
    generateMainBtn.innerHTML = `
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" aria-hidden="true">
        <path d="M13 2L4.09 12.26 12 12l-1 10L21 11.74 13 12l1-10z" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/>
      </svg>
      Generate My Portfolio
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" aria-hidden="true">
        <path d="M5 12h14M12 5l7 7-7 7" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
      </svg>`;
  }
}

// ─── Backend: one-shot file → portfolio JSON ──────────────
async function generateViaBackend(file) {
  const formData = new FormData();
  formData.append('resume', file);

  const res = await fetch('/api/generate-portfolio', {
    method: 'POST',
    body: formData
  });

  if (!res.ok) {
    const errBody = await res.json().catch(() => ({}));
    throw new Error(errBody.error || `Server error ${res.status}`);
  }

  return res.json();
}

// ─── Read File as Text (client-side fallback) ─────────────
// Uses PDF.js for PDFs, Mammoth.js for DOCX, FileReader for TXT
async function readFileAsText(file) {
  const ext = file.name.split('.').pop().toLowerCase();

  if (ext === 'pdf') {
    return await extractPdfText(file);
  }

  if (ext === 'docx') {
    return await extractDocxText(file);
  }

  // TXT and everything else
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload  = e => resolve(e.target.result);
    reader.onerror = reject;
    reader.readAsText(file);
  });
}

async function extractPdfText(file) {
  // PDF.js needs its worker; point it at the CDN copy
  if (typeof pdfjsLib === 'undefined') throw new Error('PDF.js not loaded');
  pdfjsLib.GlobalWorkerOptions.workerSrc =
    'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js';

  const arrayBuffer = await file.arrayBuffer();
  const pdf = await pdfjsLib.getDocument({ data: arrayBuffer }).promise;
  const pages = [];
  for (let i = 1; i <= pdf.numPages; i++) {
    const page = await pdf.getPage(i);
    const content = await page.getTextContent();
    pages.push(content.items.map(item => item.str).join(' '));
  }
  return pages.join('\n');
}

async function extractDocxText(file) {
  if (typeof mammoth === 'undefined') throw new Error('Mammoth.js not loaded');
  const arrayBuffer = await file.arrayBuffer();
  const result = await mammoth.extractRawText({ arrayBuffer });
  return result.value || '';
}


// ─── Client-side Resume Parser (fallback) ─────────────────
function parseResumeClientSide(text) {
  const lines = text.split('\n').map(l => l.trim()).filter(Boolean);

  // Heuristic extraction
  const emailMatch    = text.match(/[\w.+-]+@[\w-]+\.[a-zA-Z]{2,}/);
  const phoneMatch    = text.match(/(\+?\d[\d\s\-().]{8,15}\d)/);
  const linkedInMatch = text.match(/linkedin\.com\/in\/[\w-]+/i);
  const githubMatch   = text.match(/github\.com\/[\w-]+/i);

  // Try to find name (first non-empty line, or line before email)
  const name = lines[0] || 'Your Name';

  // Skills detection: look for lines with comma-separated short items
  const skillKeywords = ['javascript','python','react','node','java','c++','html','css','sql',
    'typescript','vue','angular','django','flask','aws','docker','git','linux','figma','mongodb'];
  const foundSkills = [];
  text.toLowerCase().split(/[\n,|•·]/g).forEach(chunk => {
    const trimmed = chunk.trim();
    if (trimmed.length < 40) {
      skillKeywords.forEach(kw => {
        if (trimmed.includes(kw) && !foundSkills.includes(kw)) foundSkills.push(kw);
      });
    }
  });

  return {
    name:       name,
    title:      detectTitle(text) || 'Software Engineer',
    bio:        detectBio(lines),
    email:      emailMatch   ? emailMatch[0]   : 'your@email.com',
    phone:      phoneMatch   ? phoneMatch[0]   : '+91 00000 00000',
    location:   detectLocation(text),
    linkedin:   linkedInMatch ? 'https://' + linkedInMatch[0] : '#',
    github:     githubMatch   ? 'https://' + githubMatch[0]   : '#',
    skills:     foundSkills.length ? foundSkills.map(s => capitalize(s)) : ['Skill 1','Skill 2','Skill 3','Skill 4'],
    education:  detectEducation(text),
    experience: detectExperience(text),
    projects:   detectProjects(text),
    achievements: detectAchievements(text),
  };
}

function detectTitle(text) {
  const titles = ['software engineer','frontend developer','backend developer','full stack',
    'data scientist','ml engineer','devops','product manager','ui/ux designer','web developer',
    'mobile developer','android developer','ios developer','cloud engineer'];
  const lower = text.toLowerCase();
  return titles.find(t => lower.includes(t)) ? capitalize(titles.find(t => lower.includes(t))) : null;
}

function detectBio(lines) {
  // Objective / Summary section
  const idx = lines.findIndex(l => /objective|summary|profile|about/i.test(l));
  if (idx !== -1 && lines[idx+1]) return lines.slice(idx+1, idx+3).join(' ');
  return 'A passionate professional with a drive for excellence and innovation.';
}

function detectLocation(text) {
  const match = text.match(/([A-Z][a-z]+(?:\s[A-Z][a-z]+)?,\s*(?:[A-Z]{2}|[A-Za-z]+))/);
  return match ? match[0] : 'Your Location';
}

function detectEducation(text) {
  const degreePattern = /(B\.?Tech|M\.?Tech|B\.?Sc|M\.?Sc|BE|ME|BCA|MCA|MBA|B\.?E|B\.?Com|Bachelor|Master|PhD|Diploma)[^\n]*/gi;
  const matches = [...text.matchAll(degreePattern)];
  if (matches.length === 0) return [{ degree: 'Degree / Course Name', school: 'Institution Name', year: 'Year – Year' }];
  return matches.slice(0,3).map(m => ({
    degree: m[0].trim().substring(0, 60),
    school: 'Institution',
    year: detectYear(m[0]) || 'Year – Year'
  }));
}

function detectExperience(text) {
  const expSection = text.match(/(?:experience|work history|employment)([\s\S]{0,2000}?)(?:education|skills|projects|$)/i);
  if (!expSection) return [{ role: 'Job Title', company: 'Company Name', duration: 'Year – Year', bullets: ['Key responsibility.'] }];
  const lines = expSection[1].split('\n').map(l => l.trim()).filter(Boolean);
  // Very basic: take first few lines as job title / company
  return [{
    role: lines[0] || 'Job Title',
    company: lines[1] || 'Company Name',
    duration: detectYear(expSection[1]) || 'Year – Year',
    bullets: lines.slice(2, 5).filter(l => l.length > 10).map(l => l.replace(/^[•\-*]\s*/, '')) || ['Key responsibility.']
  }];
}

function detectProjects(text) {
  const projSection = text.match(/projects?([\s\S]{0,2000}?)(?:experience|education|skills|achievements|$)/i);
  if (!projSection) return [{ name: 'Project Title', tech: 'Tech Stack', github: '#', demo: '#' }];
  const lines = projSection[1].split('\n').map(l => l.trim()).filter(l => l.length > 3);
  const projects = [];
  for (let i = 0; i < Math.min(lines.length, 6) && projects.length < 3; i++) {
    if (lines[i].length > 3 && lines[i].length < 60) {
      projects.push({ name: lines[i], tech: lines[i+1] || 'Tech Stack', github: '#', demo: '#' });
    }
  }
  return projects.length ? projects : [{ name: 'Project Title', tech: 'Tech Stack', github: '#', demo: '#' }];
}

function detectAchievements(text) {
  const achSection = text.match(/(?:achievements?|certifications?|awards?|honors?)([\s\S]{0,1500}?)(?:experience|education|projects|$)/i);
  if (!achSection) return [];
  return achSection[1].split('\n')
    .map(l => l.trim().replace(/^[•\-*]\s*/, ''))
    .filter(l => l.length > 5 && l.length < 100)
    .slice(0,5)
    .map(title => ({ title, sub: '' }));
}

function detectYear(text) {
  const m = text.match(/\d{4}\s*[-–]\s*(?:\d{4}|Present|Current)/i);
  return m ? m[0] : null;
}
function capitalize(s) { return s.charAt(0).toUpperCase() + s.slice(1); }

// ─── Toast Notification ───────────────────────────────────
function showNotification(message, type = 'info') {
  const existing = document.getElementById('toast-notification');
  existing?.remove();
  const toast = document.createElement('div');
  toast.id = 'toast-notification';
  toast.setAttribute('role', 'alert');
  toast.style.cssText = `
    position:fixed;bottom:28px;left:50%;
    transform:translateX(-50%) translateY(20px);
    background:${type === 'error' ? '#fef2f2' : '#f0fdf4'};
    color:${type === 'error' ? '#b91c1c' : '#15803d'};
    border:1px solid ${type === 'error' ? '#fecaca' : '#bbf7d0'};
    border-radius:12px;padding:12px 24px;font-size:.92rem;font-weight:600;
    box-shadow:0 8px 24px rgba(0,0,0,.12);z-index:9999;opacity:0;
    transition:opacity .3s ease,transform .3s ease;
    font-family:'Inter',sans-serif;white-space:nowrap;max-width:90vw;`;
  toast.textContent = message;
  document.body.appendChild(toast);
  requestAnimationFrame(() => requestAnimationFrame(() => {
    toast.style.opacity = '1';
    toast.style.transform = 'translateX(-50%) translateY(0)';
  }));
  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateX(-50%) translateY(10px)';
    setTimeout(() => toast.remove(), 300);
  }, 3800);
}

// ─── Big Error Modal (empty file, unreadable, etc.) ───────
function showBigError(title, message) {
  document.getElementById('big-error-modal')?.remove();

  const overlay = document.createElement('div');
  overlay.id = 'big-error-modal';
  overlay.style.cssText = `
    position:fixed;inset:0;z-index:10000;
    display:flex;align-items:center;justify-content:center;
    background:rgba(17,17,27,.55);backdrop-filter:blur(6px);
    padding:24px;opacity:0;transition:opacity .25s ease;`;

  overlay.innerHTML = `
    <div id="big-error-card" style="
      background:#fff;border-radius:20px;padding:36px 32px 28px;
      max-width:420px;width:100%;text-align:center;
      box-shadow:0 24px 64px rgba(0,0,0,.22);
      transform:translateY(24px);transition:transform .3s cubic-bezier(.34,1.56,.64,1);">
      <div style="
        width:56px;height:56px;border-radius:50%;
        background:#fef2f2;border:1.5px solid #fecaca;
        display:flex;align-items:center;justify-content:center;
        margin:0 auto 18px;font-size:1.6rem;line-height:1;">😅</div>
      <h3 style="
        font-family:'Fraunces','Georgia',serif;font-size:1.18rem;
        font-weight:800;color:#17171f;margin-bottom:10px;letter-spacing:-.3px;">${title}</h3>
      <p style="
        font-size:.88rem;color:#6f6b78;line-height:1.65;
        margin-bottom:26px;">${message}</p>
      <button id="big-error-close" style="
        display:inline-flex;align-items:center;gap:7px;
        background:linear-gradient(135deg,#4f46e5,#3730a3);color:#fff;
        font-size:.88rem;font-weight:700;padding:11px 28px;
        border:none;border-radius:100px;cursor:pointer;
        box-shadow:0 8px 20px rgba(79,70,229,.35);
        transition:transform .18s ease,box-shadow .18s ease;">
        Got it, I'll fix the file
      </button>
    </div>`;

  document.body.appendChild(overlay);

  // Animate in
  requestAnimationFrame(() => requestAnimationFrame(() => {
    overlay.style.opacity = '1';
    overlay.querySelector('#big-error-card').style.transform = 'translateY(0)';
  }));

  // Close handlers
  const close = () => {
    overlay.style.opacity = '0';
    overlay.querySelector('#big-error-card').style.transform = 'translateY(16px)';
    setTimeout(() => overlay.remove(), 250);
  };
  overlay.querySelector('#big-error-close').addEventListener('click', close);
  overlay.addEventListener('click', (e) => { if (e.target === overlay) close(); });
}

// ─── Spin animation for loading ───────────────────────────
const spinStyle = document.createElement('style');
spinStyle.textContent = `@keyframes spin{to{transform:rotate(360deg)}} .spin{animation:spin .8s linear infinite}`;
document.head.appendChild(spinStyle);

// ─── Scroll Reveal ────────────────────────────────────────
const revealEls = document.querySelectorAll('.feature-item,.template-card,.stat-card,.about-text,.about-stats,.generate-cta,.step-item');
revealEls.forEach(el => el.classList.add('reveal'));
const observer = new IntersectionObserver((entries) => {
  entries.forEach((entry, i) => {
    if (entry.isIntersecting) {
      setTimeout(() => entry.target.classList.add('visible'), i * 80);
      observer.unobserve(entry.target);
    }
  });
}, { threshold: 0.08 });
revealEls.forEach(el => observer.observe(el));

// ─── Active nav highlight on scroll ──────────────────────
const sections = document.querySelectorAll('section[id]');
const navLinks  = document.querySelectorAll('.nav-link');
const navObserver = new IntersectionObserver((entries) => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      navLinks.forEach(l => l.classList.remove('nav-active'));
      document.querySelector(`.nav-link[href="#${entry.target.id}"]`)?.classList.add('nav-active');
    }
  });
}, { rootMargin: '-40% 0px -55% 0px' });
sections.forEach(s => navObserver.observe(s));

// ─── Marquee: duplicate track for seamless loop ─────────────
const marqueeTrack = document.getElementById('marquee-track');
if (marqueeTrack) {
  marqueeTrack.innerHTML += marqueeTrack.innerHTML;
}

// ─── Header: shadow on scroll ───────────────────────────────
const pageHeader = document.querySelector('.header');
if (pageHeader) {
  const onScroll = () => pageHeader.classList.toggle('scrolled', window.scrollY > 8);
  window.addEventListener('scroll', onScroll, { passive: true });
  onScroll();
}

// ─── Hero showcase: gentle mouse parallax (desktop only) ────
const showcaseStage = document.getElementById('showcase-stage');
const showcaseCard = document.getElementById('showcase-card');
if (showcaseStage && showcaseCard && window.matchMedia('(min-width: 1000px)').matches) {
  const hero = document.getElementById('hero');
  hero?.addEventListener('mousemove', (e) => {
    const r = hero.getBoundingClientRect();
    const x = (e.clientX - r.left) / r.width - 0.5;
    const y = (e.clientY - r.top) / r.height - 0.5;
    showcaseCard.style.transition = 'transform .12s linear';
    showcaseCard.style.transform = `rotate(${2.5 - x * 4}deg) translateY(${y * -12}px)`;
  });
  hero?.addEventListener('mouseleave', () => {
    showcaseCard.style.transition = '';
    showcaseCard.style.transform = 'rotate(2.5deg)';
  });
}
