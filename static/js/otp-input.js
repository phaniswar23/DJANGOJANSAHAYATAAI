/**
 * Interactive Segmented OTP Input Component for Django Templates.
 * Provides identical UI/UX to the React OtpInput component:
 * - Dynamic box count (e.g. 4 or 6)
 * - Auto-advance on input
 * - Smart backspace (clears current or moves back & clears previous)
 * - Arrow key navigation
 * - Clipboard paste distribution
 * - Auto-focus
 */

function createOtpInput(containerId, options = {}) {
  const container = document.getElementById(containerId);
  if (!container) return null;

  const length = options.length || 6;
  const onComplete = options.onComplete || function() {};
  const onChange = options.onChange || function() {};

  container.innerHTML = '';
  container.className = 'flex items-center justify-center gap-2 sm:gap-2.5';

  const inputs = [];

  for (let i = 0; i < length; i++) {
    const input = document.createElement('input');
    input.type = 'text';
    input.inputMode = 'numeric';
    input.pattern = '[0-9]*';
    input.maxLength = 1;
    input.setAttribute('aria-label', `Digit ${i + 1} of ${length}`);
    if (i === 0) input.setAttribute('autocomplete', 'one-time-code');

    const sizeClass = length === 4
      ? 'w-12 h-14 sm:w-14 sm:h-16 text-2xl sm:text-3xl'
      : 'w-10 h-12 sm:w-12 sm:h-14 text-xl sm:text-2xl';

    input.className = `${sizeClass} font-mono font-bold text-center select-none rounded-xl border-2 border-slate-300 bg-white text-slate-800 transition-all duration-150 outline-none focus:border-[#0b2545] focus:ring-4 focus:ring-blue-100/70 focus:bg-white hover:border-slate-400`;

    input.addEventListener('focus', () => input.select());
    input.addEventListener('click', () => input.select());

    input.addEventListener('input', (e) => {
      const val = e.target.value.replace(/\D/g, '');
      if (val.length > 0) {
        input.value = val[val.length - 1];
        input.classList.remove('border-slate-300', 'bg-white');
        input.classList.add('border-[#0b2545]', 'bg-blue-50/20', 'text-[#0b2545]');
        if (i < length - 1) {
          inputs[i + 1].focus();
          inputs[i + 1].select();
        }
      } else {
        input.value = '';
        input.classList.remove('border-[#0b2545]', 'bg-blue-50/20', 'text-[#0b2545]');
        input.classList.add('border-slate-300', 'bg-white');
      }

      const fullOtp = inputs.map(inp => inp.value).join('');
      onChange(fullOtp);
      if (fullOtp.length === length) {
        onComplete(fullOtp);
      }
    });

    input.addEventListener('keydown', (e) => {
      if (e.key === 'Backspace') {
        if (!input.value && i > 0) {
          e.preventDefault();
          inputs[i - 1].value = '';
          inputs[i - 1].classList.remove('border-[#0b2545]', 'bg-blue-50/20');
          inputs[i - 1].classList.add('border-slate-300', 'bg-white');
          inputs[i - 1].focus();
          onChange(inputs.map(inp => inp.value).join(''));
        }
      } else if (e.key === 'ArrowLeft' && i > 0) {
        e.preventDefault();
        inputs[i - 1].focus();
        inputs[i - 1].select();
      } else if (e.key === 'ArrowRight' && i < length - 1) {
        e.preventDefault();
        inputs[i + 1].focus();
        inputs[i + 1].select();
      }
    });

    input.addEventListener('paste', (e) => {
      e.preventDefault();
      const paste = (e.clipboardData || window.clipboardData).getData('text') || '';
      const clean = paste.replace(/\D/g, '').slice(0, length);
      if (!clean) return;

      clean.split('').forEach((char, idx) => {
        if (inputs[idx]) {
          inputs[idx].value = char;
          inputs[idx].classList.remove('border-slate-300', 'bg-white');
          inputs[idx].classList.add('border-[#0b2545]', 'bg-blue-50/20', 'text-[#0b2545]');
        }
      });

      const nextEmpty = inputs.findIndex(inp => !inp.value);
      const target = nextEmpty === -1 ? inputs[length - 1] : inputs[nextEmpty];
      target.focus();
      target.select();

      const fullOtp = inputs.map(inp => inp.value).join('');
      onChange(fullOtp);
      if (fullOtp.length === length) {
        onComplete(fullOtp);
      }
    });

    container.appendChild(input);
    inputs.push(input);

    // Add subtle divider after 3rd digit if 6 digits
    if (length === 6 && i === 2) {
      const divider = document.createElement('span');
      divider.className = 'text-slate-300 font-bold select-none px-0.5 sm:px-1 text-sm sm:text-base';
      divider.textContent = '–';
      container.appendChild(divider);
    }
  }

  // Auto focus first input
  if (options.autoFocus !== false && inputs[0]) {
    inputs[0].focus();
  }

  return {
    getValue: () => inputs.map(inp => inp.value).join(''),
    clear: () => {
      inputs.forEach(inp => {
        inp.value = '';
        inp.classList.remove('border-[#0b2545]', 'bg-blue-50/20', 'text-[#0b2545]');
        inp.classList.add('border-slate-300', 'bg-white');
      });
      if (inputs[0]) inputs[0].focus();
    },
    setError: (hasError) => {
      inputs.forEach(inp => {
        if (hasError) {
          inp.classList.add('border-red-500', 'bg-red-50/30', 'text-red-700');
        } else {
          inp.classList.remove('border-red-500', 'bg-red-50/30', 'text-red-700');
        }
      });
    }
  };
}
window.createOtpInput = createOtpInput;
