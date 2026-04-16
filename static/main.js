// ═══════════════════════════════════════
//  TECHSERV — main.js (ESTABLE)
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
  if (typeof verificarSesion === "function") verificarSesion();
  activarAnimaciones();
});

// ── SESIÓN ─────────────────────────────
function verificarSesion() {
  fetch('/api/sesion')
    .then(r => r.json())
    .then(data => {
      if (data.autenticado) {
        mostrarUsuario(data.nombre, data.rol);
        cargarConteoCarrito && cargarConteoCarrito();
      }
    })
    .catch(() => {});
}

function mostrarUsuario(nombre, rol) {
  const guest = document.getElementById('nav-guest');
  const user = document.getElementById('nav-user');

  if (!guest || !user) return;

  guest.style.display = 'none';
  user.style.display = 'flex';

  const bienvenida = document.getElementById('nav-bienvenida');
  if (bienvenida) {
    bienvenida.textContent = `Hola, ${nombre || 'Usuario'}`;
  }

  const adminLink = document.getElementById('nav-admin-link');
  if (rol === 'admin' && adminLink) {
    adminLink.style.display = 'inline-block';
  }
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

    select.className = "estado-select estado-" + nuevoEstado.replace(" ", "-");

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

      const p = data.pedido;
      const items = data.items;

      if (!p) {
        alert("❌ No se pudo cargar el pedido");
        return;
      }

      // ✅ NOTA SEGURA
      let notaHTML = '<span style="color:#999">Sin nota</span>';
      if (p.notas && p.notas.trim() !== "") {
        notaHTML = p.notas;
      }

      const detalleInfo = document.getElementById('detalle-info');
      const detalleItems = document.getElementById('detalle-items');

      if (!detalleInfo || !detalleItems) return;

      // 🔥 INFO
      detalleInfo.innerHTML = `
        <p><strong>Cliente:</strong> ${p.nombre}</p>
        <p><strong>Correo:</strong> ${p.correo}</p>
        <p><strong>Total:</strong> $${Number(p.total).toLocaleString('es-CO')}</p>
        <p><strong>Estado:</strong> ${p.estado}</p>

        <hr style="margin:10px 0">

        <p><strong>📝 Nota del cliente:</strong></p>
        <div style="
          background:#f7f7f7;
          padding:10px;
          border-radius:8px;
          font-size:13px;
          color:#444;
        ">
          ${notaHTML}
        </div>
      `;

      // 🔥 ITEMS
      if (!items || items.length === 0) {
        detalleItems.innerHTML =
          `<p style="color:#999">No hay items registrados</p>`;
      } else {
        detalleItems.innerHTML = items.map(i => `
          <div style="display:flex; justify-content:space-between; margin-bottom:6px;">
            <span>${i.nombre}</span>
            <span>$${Number(i.precio).toLocaleString('es-CO')} x ${i.cantidad}</span>
          </div>
        `).join('');
      }

      const modal = document.getElementById('modal-detalle');
      if (modal) modal.style.display = 'flex';
    })
    .catch(() => alert("Error cargando detalle"));
}

// ── ADMIN: CERRAR DETALLE ──────────────
function cerrarDetalle() {
  const modal = document.getElementById('modal-detalle');
  if (modal) modal.style.display = 'none';
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
