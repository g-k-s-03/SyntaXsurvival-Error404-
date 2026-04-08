
const state = {
  phone: '',
  generatedOTP: '',
  otpAttempts: 0,
  timerInterval: null,
  timerSeconds: 60,

  knownUsers: {
    '9999999999': { name: 'Rahul Sharma', bloodGroup: 'A+', role: 'donor', donations: 3, lastActive: '2 days ago' },
    '8888888888': { name: 'City Hospital', bloodGroup: null, role: 'hospital', lastActive: '5 hours ago' },
  }
};


function showScreen(id, delay = 0) {
  setTimeout(() => {
    document.querySelectorAll('.screen').forEach(s => {
      s.classList.remove('active', 'exit');
      s.classList.add('exit');
    });
    const target = document.getElementById(id);
    target.classList.remove('exit');
    target.classList.add('active');
  }, delay);
}

function goBack(screenId) {
  clearTimer();
  showScreen(screenId);
}


window.addEventListener('DOMContentLoaded', () => {
  
  setTimeout(() => {
    showScreen('screen-phone');
    startCounters();
  }, 2600);
});


function startCounters() {
  document.querySelectorAll('.stat-num[data-target]').forEach(el => {
    const target = parseInt(el.dataset.target);
    const duration = 1800;
    const start = performance.now();
    function animate(now) {
      const elapsed = now - start;
      const progress = Math.min(elapsed / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      el.textContent = Math.floor(eased * target).toLocaleString();
      if (progress < 1) requestAnimationFrame(animate);
    }
    setTimeout(() => requestAnimationFrame(animate), 300);
  });
}


function sendOTP() {
  const input = document.getElementById('phone-input');
  const phone = input.value.replace(/\D/g, '');

  if (phone.length !== 10) {
    shakeElement(input.closest('.phone-row'));
    showToast('⚠️', 'Please enter a valid 10-digit number');
    return;
  }

  state.phone = phone;

 
  if (state.knownUsers[phone]) {
    const user = state.knownUsers[phone];
    populateReturningUser(user, phone);
    showScreen('screen-returning');
    startRedirectTimer();
    return;
  }

 
  state.generatedOTP = Math.floor(100000 + Math.random() * 900000).toString();
  state.otpAttempts = 0;
  console.info(`[DEV] OTP for +91 ${phone}: ${state.generatedOTP}`); // dev hint


  document.getElementById('otp-phone-display').textContent = `+91 ${phone.replace(/(\d{5})(\d{5})/, '$1 $2')}`;
  showScreen('screen-otp');
  setTimeout(() => {
    resetOTPBoxes();
    startTimer();
    document.querySelector('.otp-box').focus();
  }, 200);

  showToast('📲', `OTP sent to +91 ${phone.slice(0,5)}XXXXX`);
}

function setupOTPBoxes() {
  const boxes = document.querySelectorAll('.otp-box');
  boxes.forEach((box, i) => {
    box.addEventListener('input', e => {
      const val = e.target.value.replace(/\D/g, '');
      box.value = val;
      if (val) {
        box.classList.add('filled');
        if (i < boxes.length - 1) boxes[i + 1].focus();
      } else {
        box.classList.remove('filled');
      }
    });

    box.addEventListener('keydown', e => {
      if (e.key === 'Backspace' && !box.value && i > 0) {
        boxes[i - 1].focus();
        boxes[i - 1].value = '';
        boxes[i - 1].classList.remove('filled');
      }
      if (e.key === 'Enter') verifyOTP();
    });

    box.addEventListener('paste', e => {
      e.preventDefault();
      const pasted = (e.clipboardData || window.clipboardData).getData('text').replace(/\D/g, '').slice(0, 6);
      pasted.split('').forEach((ch, idx) => {
        if (boxes[idx]) {
          boxes[idx].value = ch;
          boxes[idx].classList.add('filled');
        }
      });
      boxes[Math.min(pasted.length, 5)].focus();
    });
  });
}

function getEnteredOTP() {
  return Array.from(document.querySelectorAll('.otp-box')).map(b => b.value).join('');
}

function resetOTPBoxes() {
  document.querySelectorAll('.otp-box').forEach(b => {
    b.value = '';
    b.classList.remove('filled', 'error', 'success');
  });
  document.getElementById('otp-status').textContent = '';
  document.getElementById('otp-status').className = 'otp-status';
}

function verifyOTP() {
  if (state.otpAttempts >= 3) return;

  const entered = getEnteredOTP();
  if (entered.length < 6) {
    showToast('⚠️', 'Please enter all 6 digits');
    return;
  }

  if (entered === state.generatedOTP) {
    // SUCCESS
    document.querySelectorAll('.otp-box').forEach(b => b.classList.add('success'));
    const statusEl = document.getElementById('otp-status');
    statusEl.textContent = '✓ Verified successfully!';
    statusEl.className = 'otp-status success';
    clearTimer();
    showToast('✅', 'Identity verified! Welcome to BloodConnect');

    setTimeout(() => {
    
      showNewUserWelcome();
    }, 1200);

  } else {
    
    state.otpAttempts++;
    const remaining = 3 - state.otpAttempts;
    document.querySelectorAll('.otp-box').forEach(b => b.classList.add('error'));
    setTimeout(() => document.querySelectorAll('.otp-box').forEach(b => b.classList.remove('error')), 500);

    const statusEl = document.getElementById('otp-status');
    statusEl.className = 'otp-status error';

    document.getElementById('attempts-left').textContent = `${remaining} attempt${remaining !== 1 ? 's' : ''} left`;

    if (remaining === 0) {
      statusEl.textContent = '✗ Maximum attempts reached. Request a new OTP.';
      clearTimer();
      document.getElementById('btn-verify').disabled = true;
      document.querySelectorAll('.otp-box').forEach(b => b.disabled = true);
      document.getElementById('btn-resend').disabled = false;
      showToast('🚫', 'Too many wrong attempts. Please resend OTP.');
    } else {
      statusEl.textContent = `✗ Incorrect code — ${remaining} attempt${remaining !== 1 ? 's' : ''} left`;
      showToast('❌', `Wrong OTP. ${remaining} attempt${remaining !== 1 ? 's' : ''} remaining`);
      resetOTPBoxes();
      document.querySelector('.otp-box').focus();
    }
  }
}


function startTimer() {
  state.timerSeconds = 60;
  state.otpAttempts = 0;
  clearTimer();
  updateTimerDisplay();

  state.timerInterval = setInterval(() => {
    state.timerSeconds--;
    updateTimerDisplay();
    if (state.timerSeconds <= 0) {
      clearTimer();
      const timerEl = document.getElementById('otp-timer');
      timerEl.textContent = 'Expired';
      timerEl.classList.add('expired');
      document.getElementById('btn-resend').disabled = false;
      document.getElementById('btn-verify').disabled = true;
      showToast('⏰', 'OTP expired. Tap Resend to get a new one.');
    }
  }, 1000);
}

function updateTimerDisplay() {
  const el = document.getElementById('otp-timer');
  if (el) el.textContent = `${state.timerSeconds}s`;
}

function clearTimer() {
  if (state.timerInterval) {
    clearInterval(state.timerInterval);
    state.timerInterval = null;
  }
}

function resendOTP() {
  state.generatedOTP = Math.floor(100000 + Math.random() * 900000).toString();
  state.otpAttempts = 0;
  console.info(`[DEV] New OTP for +91 ${state.phone}: ${state.generatedOTP}`);

  resetOTPBoxes();
  document.querySelectorAll('.otp-box').forEach(b => b.disabled = false);
  document.getElementById('btn-verify').disabled = false;
  document.getElementById('btn-resend').disabled = true;
  document.getElementById('attempts-left').textContent = '3 attempts left';
  const timerEl = document.getElementById('otp-timer');
  timerEl.classList.remove('expired');
  startTimer();

  document.querySelector('.otp-box').focus();
  showToast('📲', `New OTP sent to +91 ${state.phone.slice(0,5)}XXXXX`);
}


function populateReturningUser(user, phone) {
  document.getElementById('returning-name').textContent = user.name;
  document.getElementById('last-active').textContent = user.lastActive;

  const roleLabel = document.getElementById('returning-role-label');
  const avatar = document.getElementById('returning-avatar');

  if (user.role === 'donor') {
    roleLabel.innerHTML = `<span class="role-chip donor">🩸 Registered Donor</span>`;
    avatar.textContent = user.bloodGroup || 'D';
  } else {
    roleLabel.innerHTML = `<span class="role-chip hospital">🏥 Hospital / Patient</span>`;
    avatar.textContent = 'H+';
    avatar.style.background = 'linear-gradient(135deg, #FF8C00, #C05000)';
  }
}

function startRedirectTimer() {
  setTimeout(() => {
    goToDashboard();
  }, 3200);
}

function goToDashboard() {
  showToast('🏠', 'Loading your dashboard…');
  setTimeout(() => {
    showNewUserWelcome(); 
  }, 800);
}

function showRoleLock(existingRole) {
  document.getElementById('locked-role-name').textContent =
    existingRole === 'donor' ? 'Donor' : 'Hospital/Patient';
  document.getElementById('locked-role-btn').textContent =
    existingRole === 'donor' ? 'Donor' : 'Hospital/Patient';
  showScreen('screen-rolelock');
}

function continueLocked() {
  showToast('✅', 'Continuing with your existing role');
  setTimeout(showNewUserWelcome, 600);
}

function showNewUserWelcome() {

  document.body.innerHTML += `
  <div id="screen-dashboard" class="screen active" style="
    display:flex; align-items:center; justify-content:center;
    min-height:100vh;
    background: radial-gradient(ellipse at center, #1C0505 0%, #0A0101 60%);
    flex-direction: column; gap: 24px; padding: 40px 20px; text-align: center;
  ">
    <div style="
      animation: scaleIn 0.5s ease;
      background: var(--card-bg);
      border: 1px solid rgba(255,59,59,0.2);
      border-radius: 24px;
      padding: 48px 40px;
      max-width: 460px;
      width: 100%;
      box-shadow: var(--shadow-glow);
    ">
      <div style="font-size:64px; margin-bottom: 8px; filter: drop-shadow(0 0 20px rgba(255,59,59,0.5));">🩸</div>
      <h1 style="font-family: var(--font-display); font-size: 42px; letter-spacing:3px; color: white; margin-bottom: 8px;">BLOODCONNECT</h1>
      <p style="font-family: var(--font-mono); font-size: 11px; letter-spacing: 2px; color: var(--text-muted); text-transform: uppercase; margin-bottom: 28px;">Real-time Emergency Blood Matching</p>
      
      <div style="
        background: rgba(46,204,113,0.06);
        border: 1px solid rgba(46,204,113,0.2);
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 28px;
      ">
        <div style="font-size: 28px; margin-bottom: 6px;">✅</div>
        <p style="font-size: 15px; color: var(--success); font-weight: 600; margin-bottom: 4px;">Authentication Successful</p>
        <p style="font-size: 12px; color: var(--text-muted);">You're now inside the BloodConnect network</p>
      </div>
      
      <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 10px; margin-bottom: 28px;">
        <div style="background: rgba(255,59,59,0.06); border: 1px solid rgba(255,59,59,0.15); border-radius: 10px; padding: 14px 8px; text-align: center;">
          <div style="font-family: var(--font-display); font-size: 26px; color: var(--red);">🗺️</div>
          <div style="font-size: 11px; color: var(--text-muted); margin-top: 4px; text-transform: uppercase; letter-spacing: 1px;">Live Map</div>
        </div>
        <div style="background: rgba(255,140,0,0.06); border: 1px solid rgba(255,140,0,0.15); border-radius: 10px; padding: 14px 8px; text-align: center;">
          <div style="font-family: var(--font-display); font-size: 26px; color: var(--accent);">🚨</div>
          <div style="font-size: 11px; color: var(--text-muted); margin-top: 4px; text-transform: uppercase; letter-spacing: 1px;">SOS Alert</div>
        </div>
        <div style="background: rgba(46,204,113,0.06); border: 1px solid rgba(46,204,113,0.15); border-radius: 10px; padding: 14px 8px; text-align: center;">
          <div style="font-family: var(--font-display); font-size: 26px; color: var(--success);">📊</div>
          <div style="font-size: 11px; color: var(--text-muted); margin-top: 4px; text-transform: uppercase; letter-spacing: 1px;">Stats</div>
        </div>
      </div>
      
      <p style="font-size: 12px; color: var(--text-dim); font-family: var(--font-mono); line-height: 1.6;">
        🏆 PS-17 Hackathon Demo &nbsp;|&nbsp; Screens L1–L3, L7, L8 implemented<br/>
        <span style="color: rgba(255,59,59,0.5);">Try phone: 9999999999 for returning user demo</span><br/>
        <span style="color: rgba(255,59,59,0.5);">OTP is logged in browser console (F12)</span>
      </p>
    </div>
  </div>`;
}

function demoLogin() {
  document.getElementById('phone-input').value = '7777777777';
  showToast('🎭', 'Demo mode — use console for OTP');
  setTimeout(sendOTP, 300);
}


function showToast(icon, msg) {
  const toast = document.getElementById('toast');
  document.getElementById('toast-icon').textContent = icon;
  document.getElementById('toast-msg').textContent = msg;
  toast.classList.add('show');
  clearTimeout(toast._timeout);
  toast._timeout = setTimeout(() => toast.classList.remove('show'), 3500);
}

function shakeElement(el) {
  el.style.animation = 'shake 0.4s ease';
  setTimeout(() => el.style.animation = '', 400);
}

document.addEventListener('DOMContentLoaded', () => {
  setupOTPBoxes();

 
  const phoneInput = document.getElementById('phone-input');
  if (phoneInput) {
    phoneInput.addEventListener('input', e => {
      e.target.value = e.target.value.replace(/\D/g, '');
    });
    phoneInput.addEventListener('keydown', e => {
      if (e.key === 'Enter') sendOTP();
    });
  }
});
