/* ============================================================
   GateKeeper - Client-side JavaScript
   PIN Pad, Auto-timeout, Side Navigation
   ============================================================ */

// --- Side Navigation ---
function toggleSideNav() {
    document.getElementById('sideNav').classList.toggle('open');
    document.getElementById('sideNavOverlay').classList.toggle('open');
}

function closeSideNav() {
    document.getElementById('sideNav').classList.remove('open');
    document.getElementById('sideNavOverlay').classList.remove('open');
}

// Close side nav on Escape key
document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') {
        closeSideNav();
    }
});


// --- PIN Numpad ---
let pinValue = '';
const MAX_PIN_LENGTH = 4;

function numpadPress(digit) {
    if (pinValue.length >= MAX_PIN_LENGTH) return;

    pinValue += digit;
    updatePinDisplay();
    updatePinInput();
}

function numpadClear() {
    if (pinValue.length === 0) return;
    pinValue = pinValue.slice(0, -1);
    updatePinDisplay();
    updatePinInput();
}

function updatePinDisplay() {
    for (let i = 0; i < MAX_PIN_LENGTH; i++) {
        const dot = document.getElementById('dot' + i);
        if (dot) {
            if (i < pinValue.length) {
                dot.classList.add('filled');
            } else {
                dot.classList.remove('filled');
            }
        }
    }
}

function updatePinInput() {
    const input = document.getElementById('pinInput');
    if (input) {
        input.value = pinValue;
    }

    const submitBtn = document.getElementById('numpadSubmit');
    if (submitBtn) {
        submitBtn.disabled = pinValue.length < MAX_PIN_LENGTH;
    }
}


// --- Signature Pad ---
let signatureCanvas = null;
let signatureCtx = null;
let isDrawing = false;
let hasSigned = false;

function initSignaturePad() {
    signatureCanvas = document.getElementById('signaturePad');
    if (!signatureCanvas) return;

    signatureCtx = signatureCanvas.getContext('2d');

    // Set canvas resolution to match display size
    function resizeCanvas() {
        const wrapper = signatureCanvas.parentElement;
        const rect = wrapper.getBoundingClientRect();
        const dpr = window.devicePixelRatio || 1;
        signatureCanvas.width = rect.width * dpr;
        signatureCanvas.height = 160 * dpr;
        signatureCanvas.style.width = rect.width + 'px';
        signatureCanvas.style.height = '160px';
        signatureCtx.scale(dpr, dpr);
        signatureCtx.lineWidth = 2.5;
        signatureCtx.lineCap = 'round';
        signatureCtx.lineJoin = 'round';
        signatureCtx.strokeStyle = '#1e293b';
    }

    resizeCanvas();
    window.addEventListener('resize', function () {
        if (!hasSigned) resizeCanvas();
    });

    // Mouse events
    signatureCanvas.addEventListener('mousedown', startDraw);
    signatureCanvas.addEventListener('mousemove', draw);
    signatureCanvas.addEventListener('mouseup', stopDraw);
    signatureCanvas.addEventListener('mouseleave', stopDraw);

    // Touch events (iPad / finger / Apple Pencil)
    signatureCanvas.addEventListener('touchstart', function (e) {
        e.preventDefault();
        const touch = e.touches[0];
        startDraw(touch);
    }, { passive: false });

    signatureCanvas.addEventListener('touchmove', function (e) {
        e.preventDefault();
        const touch = e.touches[0];
        draw(touch);
    }, { passive: false });

    signatureCanvas.addEventListener('touchend', function (e) {
        e.preventDefault();
        stopDraw();
    }, { passive: false });

    // Submit form via fetch to guarantee signature data is sent
    const form = document.getElementById('checkinForm');
    if (form) {
        form.addEventListener('submit', function (e) {
            e.preventDefault();

            // Block check-in if any health question answered "yes"
            var healthBlocked = false;
            var yesChecked = document.querySelectorAll('input[name^="hq_"][value="yes"]:checked');
            if (yesChecked.length > 0) {
                healthBlocked = true;
            }
            if (healthBlocked) {
                var hwModal = document.getElementById('healthWarningModal');
                if (hwModal) hwModal.showModal();
                return;
            }

            // Validate signature
            if (!hasSigned) {
                var errEl = document.getElementById('signatureError');
                if (errEl) errEl.style.display = 'block';
                signatureCanvas.scrollIntoView({ behavior: 'smooth', block: 'center' });
                return;
            }

            // Build FormData manually to ensure signature is included
            var formData = new FormData(form);
            // Remove any empty signature_data and add the real one
            formData.delete('signature_data');
            formData.set('signature_data', signatureCanvas.toDataURL('image/png'));

            fetch(form.action, {
                method: 'POST',
                body: formData,
                redirect: 'follow'
            }).then(function (response) {
                // Follow the redirect to success page
                if (response.redirected) {
                    clearCheckinDraft();
                    window.location.href = response.url;
                } else if (response.ok) {
                    clearCheckinDraft();
                    window.location.href = response.url;
                } else {
                    // Re-render the page (validation errors)
                    response.text().then(function (html) {
                        var parser = new DOMParser();
                        var doc = parser.parseFromString(html, 'text/html');
                        document.documentElement.innerHTML = doc.documentElement.innerHTML;
                    });
                }
            }).catch(function () {
                alert('Fehler beim Einchecken. Bitte versuchen Sie es erneut.');
            });
        });
    }
}

function getCanvasCoords(event) {
    const rect = signatureCanvas.getBoundingClientRect();
    return {
        x: (event.clientX || event.pageX) - rect.left,
        y: (event.clientY || event.pageY) - rect.top
    };
}

function startDraw(e) {
    isDrawing = true;
    var coords = getCanvasCoords(e);
    signatureCtx.beginPath();
    signatureCtx.moveTo(coords.x, coords.y);
}

function draw(e) {
    if (!isDrawing) return;
    var coords = getCanvasCoords(e);
    signatureCtx.lineTo(coords.x, coords.y);
    signatureCtx.stroke();
    if (!hasSigned) {
        hasSigned = true;
        var errEl = document.getElementById('signatureError');
        if (errEl) errEl.style.display = 'none';
    }
}

function stopDraw() {
    if (isDrawing) {
        // Save signature data every time user lifts pen/finger
        saveSignatureToField();
    }
    isDrawing = false;
}

function saveSignatureToField() {
    if (!signatureCanvas || !hasSigned) return;
    var dataInput = document.getElementById('signatureData');
    if (dataInput) {
        dataInput.value = signatureCanvas.toDataURL('image/png');
    }
}

function clearSignature() {
    if (!signatureCanvas || !signatureCtx) return;
    var dpr = window.devicePixelRatio || 1;
    signatureCtx.clearRect(0, 0, signatureCanvas.width / dpr, signatureCanvas.height / dpr);
    hasSigned = false;
    var dataInput = document.getElementById('signatureData');
    if (dataInput) dataInput.value = '';
}


// --- Check-in Form Persistence (localStorage) ---
var CHECKIN_STORAGE_KEY = 'gk_checkin_draft';

function saveCheckinDraft() {
    var form = document.getElementById('checkinForm');
    if (!form) return;
    var data = {};
    ['first_name', 'last_name', 'company', 'contact_person'].forEach(function (id) {
        var el = document.getElementById(id);
        if (el) data[id] = el.value;
    });
    // Save dynamic health question answers (hq_*)
    var hqRadios = form.querySelectorAll('input[name^="hq_"]:checked');
    hqRadios.forEach(function (radio) {
        data[radio.name] = radio.value;
    });
    ['dsgvo_consent', 'hygiene_consent', 'safety_consent'].forEach(function (id) {
        var el = document.getElementById(id);
        if (el) data[id] = el.checked;
    });
    localStorage.setItem(CHECKIN_STORAGE_KEY, JSON.stringify(data));
}

function restoreCheckinDraft() {
    var form = document.getElementById('checkinForm');
    if (!form) return;
    var saved = localStorage.getItem(CHECKIN_STORAGE_KEY);
    if (!saved) return;
    try {
        var data = JSON.parse(saved);
        ['first_name', 'last_name', 'company', 'contact_person'].forEach(function (id) {
            var el = document.getElementById(id);
            if (el && data[id]) el.value = data[id];
        });
        // Restore dynamic health question answers (hq_*)
        Object.keys(data).forEach(function (key) {
            if (key.indexOf('hq_') === 0 && data[key]) {
                var radio = document.querySelector('input[name="' + key + '"][value="' + data[key] + '"]');
                if (radio) radio.checked = true;
            }
        });
        ['dsgvo_consent', 'hygiene_consent', 'safety_consent'].forEach(function (id) {
            var el = document.getElementById(id);
            if (el) el.checked = !!data[id];
        });
    } catch (e) {}
}

function clearCheckinDraft() {
    localStorage.removeItem(CHECKIN_STORAGE_KEY);
}

function initCheckinDraft() {
    var form = document.getElementById('checkinForm');
    if (!form) return;

    // Restore saved data on page load
    restoreCheckinDraft();

    // Save on every change
    form.addEventListener('input', saveCheckinDraft);
    form.addEventListener('change', saveCheckinDraft);
}


// --- Auto-redirect Countdown ---
function startCountdown(seconds, redirectUrl) {
    const el = document.getElementById('countdown');
    if (!el) return;

    let remaining = seconds;
    el.textContent = remaining;

    const interval = setInterval(function () {
        remaining--;
        el.textContent = remaining;

        if (remaining <= 0) {
            clearInterval(interval);
            window.location.href = redirectUrl;
        }
    }, 1000);
}


// --- Init on DOM Ready ---
document.addEventListener('DOMContentLoaded', function () {
    // Auto-dismiss flash messages
    const flashes = document.querySelectorAll('.flash-message');
    flashes.forEach(function (flash) {
        setTimeout(function () {
            flash.style.opacity = '0';
            flash.style.transform = 'translateY(-10px)';
            setTimeout(function () {
                flash.remove();
            }, 300);
        }, 5000);
    });

    // Initialize signature pad if present
    initSignaturePad();

    // Restore check-in form draft if present
    initCheckinDraft();
});
