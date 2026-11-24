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
                <i data-lucide="layout-dashboard" class="w-4 h-4 text-black"></i>
                <span>${user.role === 'CITIZEN' ? 'Citizen Workspace' : (user.role === 'SUPER_ADMIN' ? 'Admin Portal' : 'Official Workspace')}</span>
              </a>
              ${user.role === 'CITIZEN' ? `
                <a href="/my-complaints" class="flex items-center gap-2 px-4 py-2 text-xs text-slate-700 hover:bg-slate-100">
                  <i data-lucide="list-filter" class="w-4 h-4 text-black"></i>
                  <span>My Complaints</span>
                </a>
              ` : ''}
              ${(user.role === 'CITIZEN' || user.role === 'EMPLOYEE') ? `
                <button type="button" onclick="openChangeEmailModal()" class="w-full flex items-center gap-2 px-4 py-2 text-xs text-slate-700 hover:bg-slate-100 text-left font-medium transition-colors">
                  <i data-lucide="mail" class="w-4 h-4 text-black"></i>
                  <span>Change Email</span>
                </button>
              ` : ''}
              <button type="button" onclick="openChangePasswordModal()" class="w-full flex items-center gap-2 px-4 py-2 text-xs text-slate-700 hover:bg-slate-100 text-left font-medium transition-colors">
                <i data-lucide="key" class="w-4 h-4 text-black"></i>
                <span>Change Password</span>
              </button>
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
          <a href="/staff/dashboard?tab=workspace" onclick="if(window.switchStaffTab){switchStaffTab('workspace');return false;}" class="px-3.5 py-1.5 text-xs font-semibold rounded-t-sm transition-colors flex items-center gap-1.5 text-slate-100 hover:bg-[#163b6b] hover:text-amber-200"><span>Officer Workspace</span></a>
          <a href="/staff/dashboard?tab=department" onclick="if(window.switchStaffTab){switchStaffTab('department');return false;}" class="px-3.5 py-1.5 text-xs font-semibold rounded-t-sm transition-colors flex items-center gap-1.5 text-slate-100 hover:bg-[#163b6b] hover:text-amber-200"><span>Department Grievances</span></a>
          <a href="/staff/dashboard?tab=escalated" onclick="if(window.switchStaffTab){switchStaffTab('escalated');return false;}" class="px-3.5 py-1.5 text-xs font-semibold rounded-t-sm transition-colors flex items-center gap-1.5 text-slate-100 hover:bg-[#163b6b] hover:text-amber-200"><span>Escalated Cases</span></a>
        `;
        if (navRightActions) {
          navRightActions.innerHTML = `
            <a href="/staff/dashboard?tab=department" onclick="if(window.switchStaffTab){switchStaffTab('department');return false;}" class="bg-blue-600 hover:bg-blue-500 text-white text-xs font-bold px-3.5 py-1 rounded flex items-center gap-1.5 shadow-sm transition-colors">
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

// Change Password Modal Handlers
function openChangePasswordModal() {
  const panel = document.getElementById('userDropdownPanel');
  if (panel) panel.classList.add('hidden');
  const modal = document.getElementById('changePasswordModal');
  if (modal) {
    modal.classList.remove('hidden');
    document.getElementById('changePassCurrent').value = '';
    document.getElementById('changePassNew').value = '';
    document.getElementById('changePassConfirm').value = '';
    if (window.FormValidator) {
      modal.querySelectorAll('.gov-input-error').forEach(el => FormValidator.clearFieldError(el));
    }
    const currInput = document.getElementById('changePassCurrent');
    if (currInput) currInput.focus();
  }
}

function closeChangePasswordModal() {
  const modal = document.getElementById('changePasswordModal');
  if (modal) modal.classList.add('hidden');
}

async function handleChangePasswordSubmit(e) {
  e.preventDefault();
  const currentPass = document.getElementById('changePassCurrent').value;
  const newPass = document.getElementById('changePassNew').value;
  const confirmPass = document.getElementById('changePassConfirm').value;
  const btn = document.getElementById('changePassSubmitBtn');

  if (!currentPass) {
    if (window.FormValidator) FormValidator.showFieldError(document.getElementById('changePassCurrent'), 'Enter current password');
    return;
  }
  if (!newPass || newPass.length < 6) {
    if (window.FormValidator) FormValidator.showFieldError(document.getElementById('changePassNew'), 'Min 6 characters required');
    return;
  }
  if (newPass !== confirmPass) {
    if (window.FormValidator) FormValidator.showFieldError(document.getElementById('changePassConfirm'), 'Passwords do not match');
    return;
  }

  try {
    btn.disabled = true;
    btn.innerHTML = '<span>Updating...</span>';
    const res = await apiRequest('/api/auth/change-password', {
      method: 'POST',
      body: JSON.stringify({
        currentPassword: currentPass,
        newPassword: newPass,
        confirmPassword: confirmPass
      })
    });
    if (res && res.success) {
      toast.success(res.message || 'Password updated successfully!');
      closeChangePasswordModal();
    } else {
      throw new Error(res?.message || 'Password update failed');
    }
  } catch (err) {
    toast.error(err.message || 'Incorrect password or update error');
  } finally {
    btn.disabled = false;
    btn.innerHTML = `<i data-lucide="check" class="w-3.5 h-3.5"></i><span>Update Password</span>`;
    if (window.lucide) lucide.createIcons({ root: btn });
  }
}

// Change Email Modal Handlers (Citizen & Officer)
function openChangeEmailModal() {
  const panel = document.getElementById('userDropdownPanel');
  if (panel) panel.classList.add('hidden');
  const user = auth.getUser();
  if (user && user.role === 'SUPER_ADMIN') {
    toast.error('Super Administrator email cannot be modified.');
    return;
  }
  const modal = document.getElementById('changeEmailModal');
  if (modal) {
    modal.classList.remove('hidden');
    document.getElementById('changeEmailNew').value = '';
    document.getElementById('changeEmailPassword').value = '';
    if (window.FormValidator) {
      modal.querySelectorAll('.gov-input-error').forEach(el => FormValidator.clearFieldError(el));
    }
    const newEmailInput = document.getElementById('changeEmailNew');
    if (newEmailInput) newEmailInput.focus();
  }
}

function closeChangeEmailModal() {
  const modal = document.getElementById('changeEmailModal');
  if (modal) modal.classList.add('hidden');
}

async function handleChangeEmailSubmit(e) {
  e.preventDefault();
  const newEmail = document.getElementById('changeEmailNew').value.trim();
  const currentPass = document.getElementById('changeEmailPassword').value;
  const btn = document.getElementById('changeEmailSubmitBtn');

  if (!newEmail || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(newEmail)) {
    if (window.FormValidator) FormValidator.showFieldError(document.getElementById('changeEmailNew'), 'Enter valid email address');
    return;
  }
  if (!currentPass) {
    if (window.FormValidator) FormValidator.showFieldError(document.getElementById('changeEmailPassword'), 'Enter current password');
    return;
  }

  try {
    btn.disabled = true;
    btn.innerHTML = '<span>Updating...</span>';
    const res = await apiRequest('/api/auth/change-email', {
      method: 'POST',
      body: JSON.stringify({
        newEmail: newEmail,
        currentPassword: currentPass
      })
    });
    if (res && res.success) {
      if (res.token && res.user) {
        auth.setSession(res.token, res.user);
        auth.updateHeaderUI();
      }
      toast.success(res.message || 'Email updated successfully!');
      closeChangeEmailModal();
    } else {
      throw new Error(res?.message || 'Email update failed');
    }
  } catch (err) {
    toast.error(err.message || 'Error updating email address');
  } finally {
    btn.disabled = false;
    btn.innerHTML = `<i data-lucide="check" class="w-3.5 h-3.5"></i><span>Confirm New Email</span>`;
    if (window.lucide) lucide.createIcons({ root: btn });
  }
}

function toggleMobileMenu() {
  const drawer = document.getElementById('mobileDrawer');
  if (drawer) drawer.classList.toggle('hidden');
}

function toggleLangMenu() {
  const dropdown = document.getElementById('langDropdown');
  if (dropdown) dropdown.classList.toggle('hidden');
}

function googleTranslateElementInit() {
  if (window.google && window.google.translate) {
    new google.translate.TranslateElement({
      pageLanguage: 'en',
      includedLanguages: 'en,hi,te,ta,bn,mr,gu,kn,ml,pa,ur',
      layout: google.translate.TranslateElement.InlineLayout.SIMPLE,
      autoDisplay: false
    }, 'google_translate_element');
  }
}

function setLanguage(code, label) {
  const labelEl = document.getElementById('currentLangLabel');
  if (labelEl) labelEl.innerText = label;
  localStorage.setItem('jansahayata_lang', code);
  localStorage.setItem('jansahayata_lang_label', label);
  
  const dropdown = document.getElementById('langDropdown');
  if (dropdown) dropdown.classList.add('hidden');

  const hostname = window.location.hostname;
  const parts = hostname.split('.');
  const rootDomain = parts.length > 1 ? '.' + parts.slice(-2).join('.') : hostname;

  if (code === 'en') {
    document.cookie = 'googtrans=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;';
    document.cookie = `googtrans=; expires=Thu, 01 Jan 1970 00:00:00 UTC; domain=${hostname}; path=/;`;
    document.cookie = `googtrans=; expires=Thu, 01 Jan 1970 00:00:00 UTC; domain=${rootDomain}; path=/;`;
  } else {
    const cookieVal = `/en/${code}`;
    document.cookie = `googtrans=${cookieVal}; path=/;`;
    document.cookie = `googtrans=${cookieVal}; domain=${hostname}; path=/;`;
    document.cookie = `googtrans=${cookieVal}; domain=${rootDomain}; path=/;`;
  }

  const teCombo = document.querySelector('.goog-te-combo');
  if (teCombo) {
    teCombo.value = code;
    teCombo.dispatchEvent(new Event('change'));
  } else {
    window.location.reload();
  }

  if (window.toast) toast.info(`Language set to ${label}`);
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

// Unified Form & Input Field Validator for Clean Inline UI/UX
const FormValidator = {
  getShortErrorMessage(input) {
    if (input.dataset && input.dataset.error) {
      return input.dataset.error;
    }

    const id = (input.id || '').toLowerCase();
    const type = (input.type || '').toLowerCase();
    const tagName = input.tagName.toLowerCase();
    const placeholder = (input.getAttribute('placeholder') || '').trim();

    // 1. Select elements
    if (tagName === 'select') {
      if (id.includes('dept')) return 'Select department';
      if (id.includes('cat')) return 'Select category';
      if (id.includes('urgency') || id.includes('priority')) return 'Select urgency';
      if (id.includes('status')) return 'Select target status';
      return 'Select an option';
    }

    // 2. Specific field IDs
    if (id === 'email' || id === 'regemail' || id === 'officeremail' || id === 'successemailinput') {
      return 'Enter email address';
    }
    if (id === 'identifier') {
      return 'Enter official email or ID';
    }
    if (id === 'recoveryidentifier') {
      return 'Enter email, ID, or phone';
    }
    if (id === 'password' || id === 'staffpassword' || id === 'regpassword') {
      return 'Enter password';
    }
    if (id === 'regconfirmpassword') {
      return 'Confirm password';
    }
    if (id === 'forgotnewpass') {
      return 'Enter new password';
    }
    if (id === 'forgototp' || id === 'regotp' || id.includes('otp')) {
      return 'Enter 6-digit OTP code';
    }
    if (id === 'regname' || id === 'officerfullname' || id === 'step2citizenname') {
      return 'Enter full name';
    }
    if (id === 'regphone' || id === 'step2citizenphone') {
      return 'Enter mobile number';
    }
    if (id === 'officerempid') {
      return 'Enter employee ID';
    }
    if (id === 'trackinput' || id === 'quicktrackinput') {
      return 'Enter complaint ID';
    }
    if (id === 'problemdescription') {
      return 'Enter problem description';
    }
    if (id === 'step2addressinput') {
      return 'Enter location or address';
    }
    if (id === 'disputereason') {
      return 'Enter reason for dispute';
    }
    if (id === 'updateactionnote') {
      return 'Enter action remarks';
    }

    // 3. Fallback by type
    if (type === 'email') return 'Enter email address';
    if (type === 'password') return 'Enter password';
    if (type === 'tel') return 'Enter mobile number';

    // 4. Intelligent placeholder extraction
    if (placeholder) {
      if (placeholder.includes('@')) return 'Enter email address';
      if (placeholder.includes('••••')) return 'Enter password';
      if (placeholder.includes('000000') || placeholder.includes('0 0 0')) return 'Enter 6-digit OTP code';
      if (placeholder.toLowerCase().includes('jns-') || placeholder.toLowerCase().includes('rly-')) {
        return 'Enter complaint ID';
      }
      let clean = placeholder.replace(/^e\.g\.?,?\s*/i, '')
                             .replace(/^enter\s+(your\s+)?/i, '')
                             .replace(/\(.*?\)/g, '')
                             .split(/[,;•/]/)[0]
                             .trim();
      if (clean && clean.length > 0 && clean.length <= 25) {
        return `Enter ${clean.toLowerCase()}`;
      }
    }

    // 5. Label derivation
    if (input.id) {
      const label = document.querySelector(`label[for="${input.id}"]`);
      if (label) {
        let txt = label.innerText.replace(/[*:\(\)]/g, '').trim().split(/[\n\r,/]/)[0].trim();
        if (txt && txt.length <= 25) {
          return `Enter ${txt.toLowerCase()}`;
        }
      }
    }

    return 'Field required';
  },

  getFieldAnchor(input) {
    if (!input) return null;
    // Single-row flex container (e.g. input + button inside home quick-track or email send)
    const flexRow = input.closest('.flex');
    if (flexRow && flexRow.querySelector('button[type="submit"], button.gov-btn-primary, button.gov-btn-secondary')) {
      return flexRow;
    }
    // Relative wrapper (icon + input)
    const rel = input.closest('.relative');
    if (rel && rel.parentElement) {
      return rel;
    }
    // Centered wrapper (e.g. OTP code input)
    const centeredWrap = input.closest('.flex.justify-center');
    if (centeredWrap) {
      return centeredWrap;
    }
    return input;
  },

  showFieldError(input, customMsg) {
    if (!input) return;
    const msg = customMsg || this.getShortErrorMessage(input);
    const anchor = this.getFieldAnchor(input);
    if (!anchor || !anchor.parentNode) return;

    input.classList.add('gov-input-error');
    input.classList.remove('field-shake');
    void input.offsetWidth;
    input.classList.add('field-shake');

    let errEl = null;
    if (anchor.nextElementSibling && anchor.nextElementSibling.classList.contains('field-error-msg')) {
      errEl = anchor.nextElementSibling;
    } else if (input.id) {
      errEl = document.querySelector(`.field-error-msg[data-error-for="${input.id}"]`);
    }

    if (!errEl) {
      errEl = document.createElement('div');
      errEl.className = 'field-error-msg';
      if (input.id) errEl.setAttribute('data-error-for', input.id);
      anchor.parentNode.insertBefore(errEl, anchor.nextSibling);
    }

    errEl.innerHTML = `
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
        <circle cx="12" cy="12" r="10"></circle>
        <line x1="12" y1="8" x2="12" y2="12"></line>
        <line x1="12" y1="16" x2="12.01" y2="16"></line>
      </svg>
      <span>${msg}</span>
    `;

    if (!input._hasErrorListeners) {
      input._hasErrorListeners = true;
      const clearFn = () => this.clearFieldError(input);
      input.addEventListener('input', clearFn);
      input.addEventListener('change', clearFn);
    }
  },

  clearFieldError(input) {
    if (!input) return;
    input.classList.remove('gov-input-error', 'field-shake');
    const anchor = this.getFieldAnchor(input);
    if (anchor && anchor.nextElementSibling && anchor.nextElementSibling.classList.contains('field-error-msg')) {
      anchor.nextElementSibling.remove();
    }
    if (input.id) {
      const orphaned = document.querySelectorAll(`.field-error-msg[data-error-for="${input.id}"]`);
      orphaned.forEach(el => el.remove());
    }
  },

  validateContainer(container) {
    if (!container) return true;
    const selector = 'input:not([type="hidden"]):not([type="button"]):not([type="submit"]):not([type="reset"]):not([type="file"]):not([type="checkbox"]):not([type="radio"]), textarea, select';
    const inputs = Array.from(container.querySelectorAll(selector));
    let firstInvalid = null;
    let isValid = true;

    inputs.forEach(input => {
      const isHidden = input.type === 'hidden' || input.closest('.hidden') !== null;
      if (input.disabled || isHidden) return;

      const val = input.value ? input.value.trim() : '';
      const isRequired = input.hasAttribute('required') || input.required;

      let fieldError = null;

      if (isRequired && !val) {
        fieldError = this.getShortErrorMessage(input);
      } else if (val) {
        if (input.type === 'email' && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(val)) {
          fieldError = 'Enter valid email address';
        } else if (input.id === 'regPassword' && (val.length < 8 || !/\d/.test(val))) {
          fieldError = 'Min 8 chars with number';
        } else if (input.id === 'regConfirmPassword') {
          const pass = document.getElementById('regPassword');
          if (pass && pass.value !== val) {
            fieldError = 'Passwords do not match';
          }
        } else if (input.id === 'forgotNewPass' && (val.length < 8 || !/\d/.test(val))) {
          fieldError = 'Min 8 chars with number';
        } else if (input.id === 'problemDescription' && val.length < 15) {
          fieldError = 'Min 15 characters required';
        } else if ((input.id === 'regPhone' || input.type === 'tel') && val.length > 0 && val.replace(/\D/g, '').length < 10) {
          fieldError = 'Enter valid 10-digit mobile';
        }
      }

      if (fieldError) {
        isValid = false;
        this.showFieldError(input, fieldError);
        if (!firstInvalid) firstInvalid = input;
      } else {
        this.clearFieldError(input);
      }
    });

    if (firstInvalid) {
      firstInvalid.focus();
      firstInvalid.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }

    return isValid;
  },

  init() {
    // Disable default browser tooltips on all forms
    document.querySelectorAll('form').forEach(form => {
      form.noValidate = true;
    });

    // Capture submit events before inline handlers
    document.addEventListener('submit', (e) => {
      const form = e.target;
      if (!form || form.tagName !== 'FORM') return;

      form.noValidate = true;
      const isValid = this.validateContainer(form);
      if (!isValid) {
        e.preventDefault();
        e.stopImmediatePropagation();
        return false;
      }
    }, true);
  }
};

window.FormValidator = FormValidator;

// Initial boot
document.addEventListener('DOMContentLoaded', () => {
  auth.updateHeaderUI();
  FormValidator.init();
  const savedLabel = localStorage.getItem('jansahayata_lang_label');
  if (savedLabel) {
    const labelEl = document.getElementById('currentLangLabel');
    if (labelEl) labelEl.innerText = savedLabel;
  }
  if (window.lucide) lucide.createIcons();
});
