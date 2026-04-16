// ═══════════════════════════════════════
//  TECHSERV — main.js FINAL
// ═══════════════════════════════════════

// ── LOADER ─────────────────────────────
window.addEventListener('load', () => {
  const loader = document.getElementById('loader');
  if (loader) loader.style.display = 'none';
});

// ── NAV SCROLL ─────────────────────────
window.addEventListener('scroll', () => {
  const nav = document.querySelector('.nav');
  if (!nav) return;

  if (window.scrollY > 50) {
    nav.classList.add('nav-scrolled');
  } else {
    nav.classList.remove('nav-scrolled');
  }
});

// ── INIT ───────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  verificarSesion();
  activarAnimaciones();
});

// ── SESIÓN ─────────────────────────────
function verificarSesion() {
  fetch('/api/sesion')
    .then(r => r.json())
    .then(data => {
      if (data.autenticado) {
        mostrarUsuario(data.nombre, data.rol);
        cargarConteoCarrito();
      }
    });
}

function mostrarUsuario(nombre, rol) {
  document.getElementById('nav-guest').style.display = 'none';
  document.getElementById('nav-user').style.display = 'flex';
  document.getElementById('nav-bienvenida').textContent = `Hola, ${nombre}`;

  if (rol === 'admin') {
    document.getElementById('nav-admin-link').style.display = 'inline-block';
  }
}

// ── MODALES (ORIGINAL) ─────────────────
function abrirModal(tipo) {
  document.getElementById(`modal-${tipo}`).classList.add('active');
  document.body.style.overflow = 'hidden';
}

function cerrarModal(tipo) {
  document.getElementById(`modal-${tipo}`).classList.remove('active');
  document.body.style.overflow = '';

  const err = document.getElementById(`${tipo}-error`);
  if (err) {
    err.style.display = 'none';
    err.textContent = '';
  }
}

function cerrarModalOverlay(event, tipo) {
  if (event.target === event.currentTarget) cerrarModal(tipo);
}

function switchModal(desde, hacia) {
  cerrarModal(desde);
  setTimeout(() => abrirModal(hacia), 150);
}

// ── LOGIN (ORIGINAL) ───────────────────
function doLogin() {
  const correo = document.getElementById('login-correo').value.trim();
  const contrasena = document.getElementById('login-pass').value;
  const errEl = document.getElementById('login-error');

  if (!correo || !contrasena) {
    mostrarError(errEl, 'Por favor completa todos los campos');
    return;
  }

  fetch('/api/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ correo, contrasena })
  })
  .then(async r => {
    const data = await r.json();

    if (!r.ok) throw data;
    return data;
  })
  .then(data => {
    cerrarModal('login');

    // 🔥 FORZAMOS sesión correcta
    verificarSesion();

    mostrarToast(`✅ ${data.mensaje}`);
  })
  .catch(err => {
    mostrarError(errEl, err.error || 'Error de conexión');
  });
}

// ── REGISTRO (ORIGINAL) ────────────────
function doRegistro() {
  const nombre = document.getElementById('reg-nombre').value.trim();
  const telefono = document.getElementById('reg-telefono').value.trim();
  const correo = document.getElementById('reg-correo').value.trim();
  const contrasena = document.getElementById('reg-pass').value;
  const errEl = document.getElementById('registro-error');

  if (!nombre || !telefono || !correo || !contrasena) {
    mostrarError(errEl, 'Por favor completa todos los campos');
    return;
  }

  fetch('/api/registro', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ nombre, telefono, correo, contrasena })
  })
  .then(r => r.json())
  .then(data => {
    if (data.error) {
      mostrarError(errEl, data.error);
    } else {
      cerrarModal('registro');
      mostrarUsuario(data.nombre, data.rol);
      mostrarToast(`🎉 ${data.mensaje}`);
    }
  })
  .catch(() => mostrarError(errEl, 'Error de conexión'));
}

// ── LOGOUT ─────────────────────────────
function cerrarSesion() {
  fetch('/api/logout', { method: 'POST' })
    .then(() => {
      document.getElementById('nav-guest').style.display = 'flex';
      document.getElementById('nav-user').style.display = 'none';
      document.getElementById('nav-admin-link').style.display = 'none';
      document.getElementById('carrito-panel').style.display = 'none';
      mostrarToast('👋 Sesión cerrada');
    });
}

// ── CARRITO (ORIGINAL FUNCIONAL) ───────
function agregarAlCarrito(servicioId, nombre, btn = null) {
  fetch('/api/sesion')
    .then(r => r.json())
    .then(sesion => {
      if (!sesion.autenticado) {
        abrirModal('login');
        mostrarToast('🔐 Inicia sesión');
        return;
      }

      fetch('/api/carrito/agregar', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ servicio_id: servicioId })
      })
      .then(r => r.json())
      .then(() => {
        mostrarToast(`✅ ${nombre} agregado`);
        cargarConteoCarrito();
        cargarCarrito();

        if (btn) animarAlCarrito(btn); // 🔥 aquí se activa animación
      });
    });
}

function cargarConteoCarrito() {
  fetch('/api/carrito')
    .then(r => r.json())
    .then(data => {
      document.getElementById('carrito-count').textContent =
        data.items ? data.items.length : 0;
    });
}

function toggleCarrito() {
  const panel = document.getElementById('carrito-panel');

  if (panel.style.display === 'none' || panel.style.display === '') {
    panel.style.display = 'block';
    cargarCarrito();
  } else {
    panel.style.display = 'none';
  }
}

function cargarCarrito() {
  fetch('/api/carrito')
    .then(r => r.json())
    .then(data => {
      const container = document.getElementById('carrito-items');
      const footer = document.getElementById('carrito-footer');
      const totalEl = document.getElementById('carrito-total');

      if (!data.items || data.items.length === 0) {
        container.innerHTML = '<p class="carrito-vacio">🛒 Tu carrito está vacío</p>';
        footer.style.display = 'none';
        return;
      }

      container.innerHTML = data.items.map(item => `
        <div class="carrito-item">
          <div class="ci-info">
            <div class="ci-nombre">${item.icono} ${item.nombre}</div>
            <div class="ci-precio">$${Number(item.precio).toLocaleString('es-CO')} × ${item.cantidad}</div>
          </div>
          <div style="font-weight:700">$${Number(item.subtotal).toLocaleString('es-CO')}</div>
          <button class="ci-del" onclick="eliminarDelCarrito(${item.id})">×</button>
        </div>
      `).join('');

      totalEl.textContent = `$${Number(data.total).toLocaleString('es-CO')}`;
      footer.style.display = 'block';
    });
}

function eliminarDelCarrito(id) {
  fetch(`/api/carrito/eliminar/${id}`, { method: 'DELETE' })
    .then(() => {
      cargarCarrito();
      cargarConteoCarrito();
      mostrarToast('🗑️ Eliminado');
    });
}

function confirmarPedido() {
  const notas = document.getElementById('carrito-notas').value;

  fetch('/api/carrito/confirmar', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ notas })
  })
  .then(r => r.json())
  .then(data => {
    if (data.error) {
      mostrarToast(`❌ ${data.error}`);
    } else {
      document.getElementById('carrito-panel').style.display = 'none';
      document.getElementById('carrito-count').textContent = '0';
      mostrarToast(`🎉 Pedido #${data.pedido_id} confirmado`);
    }
  });
}

// ── UTIL ───────────────────────────────
function mostrarError(el, msg) {
  el.textContent = msg;
  el.style.display = 'block';
}

function mostrarToast(msg) {
  const toast = document.getElementById('toast');
  toast.textContent = msg;
  toast.classList.add('show');
  setTimeout(() => toast.classList.remove('show'), 3000);
}

// ── ANIMACIONES ────────────────────────
function activarAnimaciones() {
  const observer = new IntersectionObserver(entries => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('show');
      }
    });
  }, { threshold: 0.2 });

  document.querySelectorAll('.anim').forEach(el => observer.observe(el));
}

function animarAlCarrito(btn) {
  const carrito = document.querySelector('.carrito-btn');
  if (!carrito) return;

  const rectBtn = btn.getBoundingClientRect();
  const rectCart = carrito.getBoundingClientRect();

  const fly = document.createElement('div');
  fly.className = 'fly-item';
  fly.innerText = '🛒';

  fly.style.left = rectBtn.left + 'px';
  fly.style.top = rectBtn.top + 'px';

  document.body.appendChild(fly);

  setTimeout(() => {
    fly.style.left = rectCart.left + 'px';
    fly.style.top = rectCart.top + 'px';
    fly.style.opacity = '0';
    fly.style.transform = 'scale(0.5)';
  }, 10);

  setTimeout(() => fly.remove(), 800);
}
