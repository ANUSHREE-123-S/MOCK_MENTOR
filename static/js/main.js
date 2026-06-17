/* ============================================================
   MockMentor – Main JavaScript
   Handles: Dark mode, score bar colors, auto-dismiss alerts,
            form validation, smooth interactions
   ============================================================ */

// ── Dark Mode ─────────────────────────────────────────────────
const DARK_KEY = 'mm_dark_mode';
const html     = document.documentElement;
const darkBtn  = document.getElementById('darkToggle');
const darkIcon = document.getElementById('darkIcon');

function applyTheme(dark) {
    html.setAttribute('data-theme', dark ? 'dark' : 'light');
    if (darkIcon) {
        darkIcon.className = dark ? 'bi bi-sun-fill' : 'bi bi-moon-stars';
    }
    localStorage.setItem(DARK_KEY, dark ? '1' : '0');
}

// Load saved preference
const savedDark = localStorage.getItem(DARK_KEY);
if (savedDark === '1') {
    applyTheme(true);
} else if (savedDark === null) {
    // Respect OS preference if no saved choice
    const prefDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    applyTheme(prefDark);
}

if (darkBtn) {
    darkBtn.addEventListener('click', () => {
        const isDark = html.getAttribute('data-theme') === 'dark';
        applyTheme(!isDark);
    });
}

// ── Auto-dismiss Flash Alerts ─────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
    const alerts = document.querySelectorAll('.mm-alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
            if (bsAlert) bsAlert.close();
        }, 5000);
    });

    // ── Color Score Bars Based on Value ──────────────────────
    document.querySelectorAll('.score-bar').forEach(bar => {
        const score = parseFloat(bar.dataset.score || bar.style.width);
        if (score >= 70) {
            bar.style.background = 'linear-gradient(90deg, #1e8e3e, #34a853)';
        } else if (score >= 40) {
            bar.style.background = 'linear-gradient(90deg, #f9ab00, #ff8f00)';
        } else {
            bar.style.background = 'linear-gradient(90deg, #d93025, #ea4335)';
        }
    });

    // ── Active Nav Link Highlighting ──────────────────────────
    const path = window.location.pathname;
    document.querySelectorAll('.mm-navbar .nav-link').forEach(link => {
        const href = link.getAttribute('href');
        if (href && path.startsWith(href) && href !== '/') {
            link.style.color = 'var(--primary)';
            link.style.background = 'var(--primary-light)';
        }
    });

    // ── Client-side Password Match Validation ─────────────────
    const pwd1 = document.getElementById('pwd1');
    const pwd2 = document.getElementById('pwd2');
    if (pwd1 && pwd2) {
        function checkMatch() {
            if (pwd2.value && pwd1.value !== pwd2.value) {
                pwd2.setCustomValidity('Passwords do not match');
                pwd2.classList.add('is-invalid');
            } else {
                pwd2.setCustomValidity('');
                pwd2.classList.remove('is-invalid');
            }
        }
        pwd1.addEventListener('input', checkMatch);
        pwd2.addEventListener('input', checkMatch);
    }

    // ── Animated Counter for Stat Cards ──────────────────────
    document.querySelectorAll('.stat-value').forEach(el => {
        const text = el.textContent.trim();
        const num  = parseFloat(text.replace(/[^0-9.]/g, ''));
        if (!isNaN(num) && num > 0) {
            const prefix = text.replace(/[0-9.]+.*/, '');
            const suffix = text.slice(text.indexOf(num.toString()) + num.toString().length);
            let start = 0;
            const duration = 800;
            const step = 16;
            const increment = (num / (duration / step));
            const timer = setInterval(() => {
                start = Math.min(start + increment, num);
                el.textContent = prefix + (Number.isInteger(num) ? Math.round(start) : start.toFixed(1)) + suffix;
                if (start >= num) clearInterval(timer);
            }, step);
        }
    });

    // ── Smooth page load ──────────────────────────────────────
    document.body.style.opacity = '0';
    document.body.style.transition = 'opacity 0.25s ease';
    requestAnimationFrame(() => { document.body.style.opacity = '1'; });

    // ── Tooltip initialization (Bootstrap) ───────────────────
    const tooltipEls = document.querySelectorAll('[data-bs-toggle="tooltip"]');
    tooltipEls.forEach(el => new bootstrap.Tooltip(el));

    // ── Interview answer character counter ────────────────────
    const answerBox = document.getElementById('answerBox');
    if (answerBox) {
        const counter = document.createElement('div');
        counter.className = 'text-muted small mt-1 text-end';
        counter.textContent = '0 words';
        answerBox.parentNode.insertBefore(counter, answerBox.nextSibling);
        answerBox.addEventListener('input', () => {
            const words = answerBox.value.trim().split(/\s+/).filter(w => w).length;
            counter.textContent = `${words} word${words !== 1 ? 's' : ''}`;
            counter.style.color = words > 5 ? 'var(--success)' : 'var(--text-muted)';
        });
    }
});

// ── Utility: confirm delete with nicer UX ────────────────────
function confirmDelete(name) {
    return confirm(`Are you sure you want to delete "${name}"? This action cannot be undone.`);
}

// ── Print / PDF helper ────────────────────────────────────────
function printReport() {
    window.print();
}

// ============================================================
// UPGRADE JS – Coding editor, company filter, resume upload
// ============================================================

// ── Highlight active nav link (upgrade-aware) ─────────────────
document.addEventListener('DOMContentLoaded', () => {
    const path = window.location.pathname;
    document.querySelectorAll('.mm-navbar .nav-link').forEach(link => {
        const href = link.getAttribute('href') || '';
        if (href.length > 1 && path.startsWith(href)) {
            link.style.color      = 'var(--primary)';
            link.style.background = 'var(--primary-light)';
            link.style.borderRadius = 'var(--radius-sm)';
        }
    });

    // ── Accordion smooth open (company questions) ─────────────
    document.querySelectorAll('.accordion-button').forEach(btn => {
        btn.addEventListener('click', () => {
            // Small vibration-like highlight
            btn.closest('.accordion-item').style.transition = 'box-shadow 0.2s';
            btn.closest('.accordion-item').style.boxShadow = '0 0 0 2px var(--primary)';
            setTimeout(() => {
                btn.closest('.accordion-item').style.boxShadow = '';
            }, 600);
        });
    });

    // ── Auto-resize code editor textarea ──────────────────────
    const codeEditor = document.getElementById('codeEditor');
    if (codeEditor) {
        codeEditor.addEventListener('input', () => {
            // Sync line count display if present
        });
    }

    // ── Problem list search (client-side instant filter) ──────
    const problemSearch = document.querySelector('input[name="search"]');
    if (problemSearch && document.querySelector('.mm-table tbody')) {
        problemSearch.addEventListener('input', function() {
            const q = this.value.toLowerCase();
            document.querySelectorAll('.mm-table tbody tr').forEach(row => {
                row.style.display = row.textContent.toLowerCase().includes(q) ? '' : 'none';
            });
        });
    }
});

// ── Copy code button helper (for code snippets) ───────────────
function copyCode(text) {
    navigator.clipboard.writeText(text).then(() => {
        const tip = document.createElement('div');
        tip.textContent = 'Copied!';
        tip.style.cssText = 'position:fixed;top:80px;right:20px;background:#1e8e3e;color:white;padding:8px 18px;border-radius:99px;font-size:.85rem;font-weight:600;z-index:9999;animation:slideInRight .3s ease';
        document.body.appendChild(tip);
        setTimeout(() => tip.remove(), 1800);
    });
}
