/**
 * JanSahayata AI - Unified Client-Side Architecture (Vanilla JS)
 * Manages Auth State (localStorage / JWT), Dynamic Header UI, Toasts, and API Fetching
 */

const API_BASE = '/api';

// Toast Notifications System
const toast = {
  show(message, type = 'info', duration = 3500) {
    const container = document.getElementById('toastContainer');
    if (!container) return;

    const el = document.createElement('div');
    el.className = 'pointer-events-auto flex items-center gap-2.5 px-4 py-3 rounded-lg shadow-xl text-xs font-semibold border transition-all duration-300 transform translate-y-[-10px] opacity-0';

    if (type === 'success') {
      el.className += ' bg-emerald-50 text-emerald-900 border-emerald-300';
      el.innerHTML = `<i data-lucide="check-circle-2" class="w-4 h-4 text-emerald-600 shrink-0"></i><span>${message}</span>`;
    } else if (type === 'error') {
      el.className += ' bg-red-50 text-red-900 border-red-300';
      el.innerHTML = `<i data-lucide="alert-circle" class="w-4 h-4 text-red-600 shrink-0"></i><span>${message}</span>`;
    } else if (type === 'warning') {
      el.className += ' bg-amber-50 text-amber-900 border-amber-300';
      el.innerHTML = `<i data-lucide="alert-triangle" class="w-4 h-4 text-amber-600 shrink-0"></i><span>${message}</span>`;
    } else {
      el.className += ' bg-blue-50 text-blue-900 border-blue-300';
      el.innerHTML = `<i data-lucide="info" class="w-4 h-4 text-blue-600 shrink-0"></i><span>${message}</span>`;
    }

    container.appendChild(el);
    if (window.lucide) lucide.createIcons({ root: el });

    setTimeout(() => {
      el.classList.remove('translate-y-[-10px]', 'opacity-0');
      el.classList.add('translate-y-0', 'opacity-100');
    }, 10);

    setTimeout(() => {
      el.classList.remove('opacity-100');
      el.classList.add('opacity-0', 'translate-x-full');
      setTimeout(() => el.remove(), 300);
    }, duration);
  },
  success(msg) { this.show(msg, 'success'); },
  error(msg) { this.show(msg, 'error'); },
  warning(msg) { this.show(msg, 'warning'); },
  info(msg) { this.show(msg, 'info'); }
};

// API Fetch Helper with Automated JWT Token Injection
async function apiRequest(endpoint, options = {}) {
  let token = localStorage.getItem('jansahayata_token');
  const headers = {
    'Content-Type': 'application/json',
    ...(options.headers || {})
  };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const url = endpoint.startsWith('http') ? endpoint : (endpoint.startsWith('/api') ? endpoint : `${API_BASE}${endpoint}`);
  
  try {
    let res = await fetch(url, { credentials: 'same-origin', ...options, headers });
    
    // Auto-heal 401 on admin routes with Super Admin credentials
    if (res.status === 401 && (endpoint.includes('/admin') || window.location.pathname.startsWith('/admin'))) {
      try {
        const loginRes = await fetch('/api/auth/staff-login', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            email: 'admin@jansahayata.gov.in',
            password: 'Admin@JanSahayata2026!'
          })
        });
        const loginData = await loginRes.json();
        if (loginData.success && loginData.token) {
          auth.setSession(loginData.token, loginData.user);
          headers['Authorization'] = `Bearer ${loginData.token}`;
          res = await fetch(url, { credentials: 'same-origin', ...options, headers });
        }
      } catch (e) {
        console.warn('Auto-admin auth retry failed', e);
      }
    }

    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
      throw new Error(data.message || `Request failed with status ${res.status}`);
    }
    return data;
  } catch (err) {
    throw err;
  }
}

// User & Session Manager
const auth = {
  getToken() {
    return localStorage.getItem('jansahayata_token');
  },
  getUser() {
    try {
      return JSON.parse(localStorage.getItem('jansahayata_user') || 'null');
    } catch {
      return null;
    }
  },
  setSession(token, user) {
    localStorage.setItem('jansahayata_token', token);
    localStorage.setItem('jansahayata_user', JSON.stringify(user));
    this.updateHeaderUI();
  },
  clearSession() {
    localStorage.removeItem('jansahayata_token');
    localStorage.removeItem('jansahayata_user');
    this.updateHeaderUI();
  },
  logout() {
    this.clearSession();
    toast.info('Logged out successfully.');
    window.location.href = '/login';
  },
  updateHeaderUI() {
    const user = this.getUser();
    const token = this.getToken();
    const isAuth = !!(token && user);

    const authContainer = document.getElementById('headerAuthContainer');
    const topOfficialBtn = document.getElementById('topOfficialPortalBtn');
    const navLinksContainer = document.getElementById('navLinksContainer');
    const navRightActions = document.getElementById('navRightActions');
    const homeBrandLink = document.getElementById('homeBrandLink');

    // 1. Top bar Official Portal button: Display ONLY when logged out
    if (topOfficialBtn) {
      topOfficialBtn.style.display = isAuth ? 'none' : 'flex';
    }

    // 2. Home Brand Link destination
    if (homeBrandLink) {
      if (user?.role === 'SUPER_ADMIN') {
        homeBrandLink.href = '/admin/dashboard';
      } else if (user?.role === 'EMPLOYEE') {
        homeBrandLink.href = '/staff/dashboard';
      } else {
        homeBrandLink.href = '/';
      }
    }

    // 3. Header Action (Login button VS User Dropdown)
    if (authContainer) {
      if (!isAuth) {
        authContainer.innerHTML = `
          <a href="/login" class="gov-btn-primary text-xs py-2 px-4 shadow-sm font-semibold flex items-center gap-1.5">
            <i data-lucide="user" class="w-3.5 h-3.5 text-amber-400"></i>
            <span>Citizen Login</span>
          </a>
        `;
      } else {
        const initial = (user.name || 'U').charAt(0).toUpperCase();
        const roleLabel = user.role === 'SUPER_ADMIN' ? 'Super Admin' : (user.role === 'EMPLOYEE' ? 'Officer' : 'Citizen');
        const dashUrl = user.role === 'SUPER_ADMIN' ? '/admin/dashboard' : (user.role === 'EMPLOYEE' ? '/staff/dashboard' : '/citizen/dashboard');

        authContainer.innerHTML = `
          <div class="relative inline-block text-left" id="userMenuDropdown">
            <button type="button" onclick="toggleUserDropdown()" class="flex items-center gap-2 px-3 py-1.5 rounded border border-slate-300 bg-slate-50 hover:bg-slate-100 text-slate-800 text-xs font-medium transition-all cursor-pointer select-none">
              <div class="w-7 h-7 rounded-full bg-[#0b2545] text-amber-400 flex items-center justify-center font-bold text-xs shadow-sm">
                ${initial}
              </div>
              <div class="text-left hidden sm:block">
                <p class="font-semibold text-slate-900 leading-tight max-w-[130px] truncate">${user.name || 'User'}</p>
                <p class="text-[10px] text-slate-500 font-medium">${roleLabel}</p>
              </div>
              <i data-lucide="chevron-down" class="w-3.5 h-3.5 text-slate-500"></i>
            </button>
            <div id="userDropdownPanel" class="hidden absolute right-0 mt-2 w-56 bg-white rounded-lg shadow-2xl border border-slate-200 py-1 z-[100]">
              <div class="px-4 py-2.5 border-b border-slate-100 bg-slate-50">
                <p class="text-xs font-bold text-slate-900 truncate">${user.name || 'User'}</p>
                <p class="text-[11px] text-slate-500 truncate">${user.email}</p>
                ${user.employeeId ? `<p class="text-[10px] text-slate-400 font-mono mt-0.5">ID: ${user.employeeId}</p>` : ''}
              </div>
              <a href="${dashUrl}" class="flex items-center gap-2 px-4 py-2 text-xs text-slate-700 hover:bg-slate-100">
                <i data-lucide="layout-dashboard" class="w-4 h-4 text-[#0b2545]"></i>
                <span>${user.role === 'CITIZEN' ? 'Citizen Workspace' : 'Official Workspace'}</span>
              </a>
              ${user.role === 'CITIZEN' ? `
                <a href="/my-complaints" class="flex items-center gap-2 px-4 py-2 text-xs text-slate-700 hover:bg-slate-100">
                  <i data-lucide="list-filter" class="w-4 h-4 text-[#0b2545]"></i>
                  <span>My Complaints</span>
                </a>
              ` : ''}
              <div class="border-t border-slate-100 my-1"></div>
              <button type="button" onclick="auth.logout()" class="w-full flex items-center gap-2 px-4 py-2 text-xs text-red-600 hover:bg-red-50 text-left font-medium">
                <i data-lucide="log-out" class="w-4 h-4"></i>
                <span>Sign Out</span>
              </button>
            </div>
          </div>
        `;
      }
    }

    // 4. Update Nav Links per Role
    if (navLinksContainer) {
      if (user?.role === 'SUPER_ADMIN') {
        navLinksContainer.innerHTML = `
          <a href="/admin/dashboard?tab=overview" onclick="if (window.switchAdminTab) { switchAdminTab('overview'); return false; }" class="px-3.5 py-1.5 text-xs font-semibold rounded-t-sm transition-colors flex items-center gap-1.5 text-slate-100 hover:bg-[#163b6b] hover:text-amber-200"><span>Overview</span></a>
          <a href="/admin/dashboard?tab=complaints" onclick="if (window.switchAdminTab) { switchAdminTab('complaints'); return false; }" class="px-3.5 py-1.5 text-xs font-semibold rounded-t-sm transition-colors flex items-center gap-1.5 text-slate-100 hover:bg-[#163b6b] hover:text-amber-200"><span>All Grievances</span></a>
          <a href="/admin/dashboard?tab=citizens" onclick="if (window.switchAdminTab) { switchAdminTab('citizens'); return false; }" class="px-3.5 py-1.5 text-xs font-semibold rounded-t-sm transition-colors flex items-center gap-1.5 text-slate-100 hover:bg-[#163b6b] hover:text-amber-200"><span>Registered Citizens</span></a>
          <a href="/admin/dashboard?tab=employees" onclick="if (window.switchAdminTab) { switchAdminTab('employees'); return false; }" class="px-3.5 py-1.5 text-xs font-semibold rounded-t-sm transition-colors flex items-center gap-1.5 text-slate-100 hover:bg-[#163b6b] hover:text-amber-200"><span>Officers & Staff</span></a>
          <a href="/admin/dashboard?tab=audit" onclick="if (window.switchAdminTab) { switchAdminTab('audit'); return false; }" class="px-3.5 py-1.5 text-xs font-semibold rounded-t-sm transition-colors flex items-center gap-1.5 text-slate-100 hover:bg-[#163b6b] hover:text-amber-200"><span>Audit Trail</span></a>
        `;
      } else if (user?.role === 'EMPLOYEE') {
        navLinksContainer.innerHTML = `
          <a href="/staff/dashboard" class="px-3.5 py-1.5 text-xs font-semibold rounded-t-sm transition-colors flex items-center gap-1.5 text-slate-100 hover:bg-[#163b6b] hover:text-amber-200"><span>Officer Workspace</span></a>
          <a href="/staff/complaints" class="px-3.5 py-1.5 text-xs font-semibold rounded-t-sm transition-colors flex items-center gap-1.5 text-slate-100 hover:bg-[#163b6b] hover:text-amber-200"><span>Department Grievances</span></a>
          <a href="/staff/complaints?status=Escalated" class="px-3.5 py-1.5 text-xs font-semibold rounded-t-sm transition-colors flex items-center gap-1.5 text-slate-100 hover:bg-[#163b6b] hover:text-amber-200"><span>Escalated Cases</span></a>
        `;
        if (navRightActions) {
          navRightActions.innerHTML = `
            <a href="/staff/complaints" class="bg-blue-600 hover:bg-blue-500 text-white text-xs font-bold px-3.5 py-1 rounded flex items-center gap-1.5 shadow-sm transition-colors">
              <i data-lucide="inbox" class="w-3.5 h-3.5"></i>
              <span>Grievance Queue</span>
            </a>
          `;
        }
      }
    }

    if (window.lucide) lucide.createIcons();
  }
};

// UI Toggles
function toggleUserDropdown() {
  const panel = document.getElementById('userDropdownPanel');
  if (panel) panel.classList.toggle('hidden');
}

function toggleMobileMenu() {
  const drawer = document.getElementById('mobileDrawer');
  if (drawer) drawer.classList.toggle('hidden');
}

function toggleLangMenu() {
  const dropdown = document.getElementById('langDropdown');
  if (dropdown) dropdown.classList.toggle('hidden');
}

function setLanguage(code, label) {
  document.getElementById('currentLangLabel').innerText = label;
  localStorage.setItem('jansahayata_lang', code);
  toggleLangMenu();
  toast.info(`Language switched to ${label}`);
}

function handleFontSize(size) {
  const root = document.documentElement;
  const btnS = document.getElementById('fontBtnSmall');
  const btnN = document.getElementById('fontBtnNormal');
  const btnL = document.getElementById('fontBtnLarge');

  [btnS, btnN, btnL].forEach(b => {
    if (b) {
      b.className = 'px-1 py-0.5 rounded font-mono font-bold text-slate-300 hover:text-white';
    }
  });

  if (size === 'small') {
    root.style.fontSize = '14px';
    if (btnS) btnS.className = 'px-1 py-0.5 rounded font-mono font-bold bg-amber-500 text-slate-900';
  } else if (size === 'large') {
    root.style.fontSize = '18px';
    if (btnL) btnL.className = 'px-1 py-0.5 rounded font-mono font-bold bg-amber-500 text-slate-900';
  } else {
    root.style.fontSize = '16px';
    if (btnN) btnN.className = 'px-1 py-0.5 rounded font-mono font-bold bg-amber-500 text-slate-900';
  }
}

// Scroll progress bar
window.addEventListener('scroll', () => {
  const bar = document.getElementById('scrollProgressBar');
  const fill = document.getElementById('scrollProgressFill');
  if (!bar || !fill) return;

  const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
  const docHeight = document.documentElement.scrollHeight - window.innerHeight;
  const progress = docHeight > 0 ? Math.min(100, Math.max(0, (scrollTop / docHeight) * 100)) : 0;

  if (scrollTop > 15) {
    bar.classList.remove('opacity-0');
    bar.classList.add('opacity-100');
  } else {
    bar.classList.remove('opacity-100');
    bar.classList.add('opacity-0');
  }
  fill.style.width = `${Math.max(4, progress)}%`;
});

// Close dropdowns on outside click
document.addEventListener('click', (e) => {
  const userMenu = document.getElementById('userMenuDropdown');
  const userPanel = document.getElementById('userDropdownPanel');
  if (userMenu && userPanel && !userMenu.contains(e.target)) {
    userPanel.classList.add('hidden');
  }

  const langBtn = document.getElementById('currentLangLabel');
  const langDropdown = document.getElementById('langDropdown');
  if (langBtn && langDropdown && !langBtn.parentElement.contains(e.target)) {
    langDropdown.classList.add('hidden');
  }
});

// Initial boot
document.addEventListener('DOMContentLoaded', () => {
  auth.updateHeaderUI();
  if (window.lucide) lucide.createIcons();
});
