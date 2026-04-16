// ═══════════════════════════════════════
//  TECHSERV — main.js FINAL (FIX ADMIN)
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
  const guest = document.getElementById('nav-guest');
  const user = document.getElementById('nav-user');

  if (!guest || !user) return;

  guest.style.display = 'none';
  user.style.display = 'flex';

  document.getElementById('nav-bienvenida').textContent = `Hola, ${nombre || 'Usuario'}`;

  if (rol === 'admin') {
    document.getElementById('nav-admin-link').style.display = 'inline-block';
  }
}

// ── MODALES ────────────────────────────
function abrirModal(tipo) {
  document.getElementById(`modal-${tipo}`).classList.add('active');
  document.body.style.overflow = 'hidden';
}

function cerrarModal(tipo) {
  document.getElementById(`modal-${tipo}`).classList.remove('active');
  document.body.style.overflow = '';
}

// ── ADMIN: CAMBIAR ESTADO ──────────────
function cambiarEstado(pedidoId, select) {
  const nuevoEstado = select.value;

  fetch(`/api/admin/pedido/${pedidoId}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ estado: nuevoEstado })
  })
  .then(res => res.json())
  .then(data => {
    if (data.error) {
      alert('❌ ' + data.error);
      return;
    }

    // 🔥 CAMBIAR COLOR DINÁMICO
    select.className = "estado-select estado-" + nuevoEstado.replace(" ", "-");

    // feedback visual
    select.style.border = "2px solid #00c853";
    setTimeout(() => select.style.border = "", 1000);
  })
  .catch(() => alert('Error de conexión'));
}

// ── ADMIN: VER DETALLE ─────────────────
function verDetalle(id) {
  fetch(`/api/admin/pedido/${id}`)
    .then(res => res.json())
    .then(data => {

      console.log("DEBUG PEDIDO:", data); // 🔥 para verificar

      const p = data.pedido || {};
      const items = data.items || [];

      // 🔥 MANEJO SEGURO DE NOTAS
      let notaTexto = 'Sin nota';

      if (p.notas && p.notas !== 'null' && p.notas.trim() !== '') {
        notaTexto = p.notas;
      }

      // 🔥 INFO GENERAL
      document.getElementById('detalle-info').innerHTML = `
        <p><strong>Cliente:</strong> ${p.nombre || '—'}</p>
        <p><strong>Correo:</strong> ${p.correo || '—'}</p>
        <p><strong>Total:</strong> $${Number(p.total || 0).toLocaleString('es-CO')}</p>
        <p><strong>Estado:</strong> ${p.estado || '—'}</p>
        <p><strong>Nota:</strong> <span style="color:#444">${notaTexto}</span></p>
      `;

      // 🔥 ITEMS
      if (!items.length) {
        document.getElementById('detalle-items').innerHTML = `
          <p style="color:#999">No hay items registrados</p>
        `;
      } else {
        document.getElementById('detalle-items').innerHTML = items.map(i => `
          <div style="display:flex; justify-content:space-between; margin-bottom:6px;">
            <span>${i.nombre}</span>
            <span>$${Number(i.precio).toLocaleString('es-CO')} x ${i.cantidad}</span>
          </div>
        `).join('');
      }

      document.getElementById('modal-detalle').style.display = 'flex';
    })
    .catch(err => {
      console.error(err);
      alert('Error cargando detalle');
    });
}

// ── ADMIN: CERRAR DETALLE ──────────────
function cerrarDetalle() {
  document.getElementById('modal-detalle').style.display = 'none';
}

// ── UTIL ───────────────────────────────
function mostrarToast(msg) {
  const toast = document.getElementById('toast');
  if (!toast) return;

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
