/* ===========================================
   CONFIGURACIÓN CENTRALIZADA
   =========================================== */
const CONFIG = {
  businessName: 'Proveesur',
  slogan: 'Pinturería de barrio con alma',
  whatsapp: '5491155553333',
  phone: '(011) 0000-0000',
  email: 'hola@proveesur.com',
  address: 'Av. Siempre Viva 1234, Barrio Sur',
  hours: 'Lun a Vie: 8:00 – 19:00 | Sáb: 8:30 – 13:30',
  mapQuery: 'Plaza+de+Mayo,+Buenos+Aires',
  social: {
    instagram: '#',
    facebook: '#',
  },
  analytics: null,
};

/* ===========================================
   WHATSAPP DINÁMICO
   =========================================== */
function getWhatsAppUrl(context, data = {}) {
  const base = `https://wa.me/${CONFIG.whatsapp}?text=`;
  const messages = {
    hero: 'Hola!%20Quiero%20asesoramiento%20sobre%20pinturas',
    calculator: `Hola!%20Necesito%20cotizar%20pintura%20para%20${data.area || 'mi%20pared'}%20(${data.liters || ''}%20litros%20estimados)`,
    contact: 'Hola!%20Quiero%20hacer%20una%20consulta',
    footer: 'Hola!%20Quiero%20consultar%20por%20productos',
  };
  return base + encodeURIComponent(decodeURIComponent(messages[context] || messages.contact));
}

document.addEventListener('DOMContentLoaded', () => {

  lucide.createIcons();

  /* ===========================================
     MENÚ MÓVIL
     =========================================== */
  const menuToggle = document.getElementById('menu-toggle');
  const mobileMenu = document.getElementById('mobile-menu');
  if (menuToggle && mobileMenu) {
    menuToggle.addEventListener('click', () => {
      mobileMenu.classList.toggle('open');
    });
    mobileMenu.querySelectorAll('a').forEach(link => {
      link.addEventListener('click', () => mobileMenu.classList.remove('open'));
    });
  }

  /* ===========================================
     NAVBAR SOMBRA AL HACER SCROLL
     =========================================== */
  const navbar = document.getElementById('navbar');
  window.addEventListener('scroll', () => {
    if (window.scrollY > 20) {
      navbar.style.boxShadow = '0 4px 20px rgba(0,0,0,0.06)';
    } else {
      navbar.style.boxShadow = 'none';
    }
  });

  /* ===========================================
     ANIMACIONES REVEAL AL HACER SCROLL
     =========================================== */
  const reveals = document.querySelectorAll('.reveal');
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('visible');
        observer.unobserve(entry.target);
      }
    });
  }, { threshold: 0.12 });
  reveals.forEach(el => observer.observe(el));

  /* ===========================================
     ANIMACIÓN CONTADOR STATS
     =========================================== */
  const statNumbers = document.querySelectorAll('.stat-number');
  const statObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        const el = entry.target;
        const target = parseInt(el.dataset.target, 10);
        const suffix = el.dataset.suffix || '';
        animateCounter(el, target, suffix);
        statObserver.unobserve(el);
      }
    });
  }, { threshold: 0.5 });

  statNumbers.forEach(el => statObserver.observe(el));

  function animateCounter(el, target, suffix) {
    const duration = 1500;
    const start = performance.now();
    function update(now) {
      const elapsed = now - start;
      const progress = Math.min(elapsed / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      const current = Math.round(eased * target);
      el.textContent = current + suffix;
      if (progress < 1) requestAnimationFrame(update);
    }
    requestAnimationFrame(update);
  }

  /* ===========================================
     CALCULADORA DE PINTURA
     =========================================== */
  const calcBtn = document.getElementById('calc-btn');
  const widthInput = document.getElementById('width');
  const heightInput = document.getElementById('height');
  const doorsInput = document.getElementById('doors');
  const windowsInput = document.getElementById('windows');
  const coatsInput = document.getElementById('coats');
  const surfaceTypeRadios = document.querySelectorAll('input[name="surface"]');

  const resultPlaceholder = document.getElementById('result-placeholder');
  const resultBox = document.getElementById('result-box');
  const litersResult = document.getElementById('liters-result');
  const cansResult = document.getElementById('cans-result');
  const areaResult = document.getElementById('area-result');
  const coatsResult = document.getElementById('coats-result');
  const calcWhatsAppBtn = document.getElementById('calc-whatsapp-btn');

  if (calcBtn) {
    calcBtn.addEventListener('click', () => {
      const w = parseFloat(widthInput.value);
      const h = parseFloat(heightInput.value);
      const doors = parseInt(doorsInput.value) || 0;
      const windows = parseInt(windowsInput.value) || 0;
      const coats = parseInt(coatsInput.value) || 2;

      let surfaceFactor = 1;
      surfaceTypeRadios.forEach(r => { if (r.checked) surfaceFactor = parseFloat(r.value); });

      [widthInput, heightInput].forEach(el => el.classList.remove('error'));

      if (!w || !h || w <= 0 || h <= 0) {
        showFlash('Ingresá medidas válidas (ancho y alto mayor a 0).', 'error');
        if (!w || w <= 0) widthInput.classList.add('error');
        if (!h || h <= 0) heightInput.classList.add('error');
        return;
      }

      const minW = parseFloat(widthInput.min) || 0.1;
      const minH = parseFloat(heightInput.min) || 0.1;
      if (w < minW || h < minH) {
        showFlash('Las medidas deben ser mayores a 0.', 'error');
        return;
      }

      calcBtn.disabled = true;
      calcBtn.innerHTML = '<span class="spinner"></span> Calculando...';

      setTimeout(() => {
        const totalArea = w * h;
        const openingsArea = (doors * 2) + (windows * 1.5);
        const paintableArea = Math.max(0, totalArea - openingsArea);
        const coverage = 10 / surfaceFactor;
        const litersNeeded = (paintableArea / coverage) * coats;
        const cans = Math.ceil(litersNeeded / 4);

        litersResult.textContent = litersNeeded.toFixed(1);
        cansResult.textContent = cans;
        areaResult.textContent = paintableArea.toFixed(1) + ' m²';
        coatsResult.textContent = coats;

        resultPlaceholder.classList.add('hidden');
        resultBox.classList.remove('hidden');

        resultBox.style.animation = 'none';
        resultBox.offsetHeight;
        resultBox.style.animation = '';

        if (calcWhatsAppBtn) {
          calcWhatsAppBtn.href = getWhatsAppUrl('calculator', {
            area: paintableArea.toFixed(1) + '%20m²',
            liters: litersNeeded.toFixed(1)
          });
        }

        calcBtn.disabled = false;
        calcBtn.innerHTML = '<i data-lucide="calculator" class="w-5 h-5"></i> Calcular litros';
        lucide.createIcons();
      }, 400);
    });
  }

  /* ===========================================
     FORMULARIO DE CONTACTO
     =========================================== */
  const form = document.getElementById('contact-form');
  if (form) {
    form.addEventListener('submit', (e) => {
      e.preventDefault();
      const name = document.getElementById('name').value.trim();
      const email = document.getElementById('email').value.trim();
      const message = document.getElementById('message').value.trim();

      [document.getElementById('name'), document.getElementById('email'), document.getElementById('message')].forEach(el => el.classList.remove('error'));

      if (!name || !email || !message) {
        showFlash('Completá los campos obligatorios.', 'error');
        if (!name) document.getElementById('name').classList.add('error');
        if (!email) document.getElementById('email').classList.add('error');
        if (!message) document.getElementById('message').classList.add('error');
        return;
      }
      if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
        showFlash('Ingresá un email válido.', 'error');
        document.getElementById('email').classList.add('error');
        return;
      }

      const submitBtn = form.querySelector('button[type="submit"]');
      const originalContent = submitBtn.innerHTML;
      submitBtn.disabled = true;
      submitBtn.innerHTML = '<span class="spinner"></span> Enviando...';

      setTimeout(() => {
        showFlash('¡Gracias ' + name + '! Te respondemos enseguida.', 'success');
        form.reset();
        submitBtn.disabled = false;
        submitBtn.innerHTML = originalContent;
      }, 800);
    });
  }

  /* ===========================================
     FLASH MESSAGE
     =========================================== */
  const flash = document.getElementById('flash');
  const flashText = document.getElementById('flash-text');
  function showFlash(text, type = 'success') {
    if (!flash || !flashText) return;
    flashText.textContent = text;
    flash.style.borderColor = type === 'success' ? 'var(--green)' : 'var(--red)';
    flash.querySelector('i').style.color = type === 'success' ? 'var(--green)' : 'var(--red)';
    flash.classList.add('show');
    clearTimeout(flash._timer);
    flash._timer = setTimeout(() => flash.classList.remove('show'), 3500);
  }

  /* ===========================================
     SERVICE WORKER
     =========================================== */
  if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('sw.js').then(reg => {
      const swStatus = document.getElementById('sw-status');
      if (swStatus) {
        swStatus.textContent = '✓ App lista para usar sin conexión';
        swStatus.classList.add('visible');
        setTimeout(() => swStatus.classList.remove('visible'), 5000);
      }
    }).catch(() => {
      // SW no disponible
    });
  }

});
