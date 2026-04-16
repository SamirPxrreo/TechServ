// ═══════════════════════════════════════
//  TECHSERV — main.js FINAL LIMPIO
// ═══════════════════════════════════════

// ── LOADER ─────────────────────────────
window.addEventListener('load', () => {
  const loader = document.getElementById('loader');
  if (loader) loader.style.display = 'none';
});

// ── INIT ───────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  verificarSesion();
});


// ── SESIÓN ─────────────────────────────
function verificarSesion() {
  fetch('/api/sesion')
    .then(r => r.json())
    .then(data => {
      if (!data.autenticado) return;

      const user = document.getElementById('nav-user');
      const guest = document.getElementById('nav-guest');

      if (user && guest) {
        guest.style.display = 'none';
        user.style.display = 'flex';
      }

      if (data.rol === 'admin') {
        const adminLink = document.getElementById('nav-admin-link');
        if (adminLink) adminLink.style.display = 'inline-block';
      }
    });
}


// ── ADMIN: CAMBIAR ESTADO ──────────────
function cambiarEstado(id, select) {
  fetch(`/api/admin/pedido/${id}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ estado: select.value })
  })
  .then(res => res.json())
  .then(() => {
    select.className = "estado-select estado-" + select.value.replace(" ", "-");
  })
  .catch(() => alert('Error cambiando estado'));
}


// ── ADMIN: VER DETALLE ─────────────────
function verDetalle(id) {
  fetch(`/api/admin/pedido/${id}`)
    .then(r => r.json())
    .then(data => {

      const p = data.pedido;

      // INFO + NOTA
      document.getElementById('detalle-info').innerHTML = `
        <p><b>Cliente:</b> ${p.nombre}</p>
        <p><b>Correo:</b> ${p.correo}</p>
        <p><b>Total:</b> $${Number(p.total).toLocaleString('es-CO')}</p>
        <p><b>Estado:</b> ${p.estado}</p>

        <hr>

        <p><b>📝 Nota del cliente:</b></p>
        <div class="nota-box">
          ${p.notas && p.notas.trim() !== "" ? p.notas : 'Sin nota'}
        </div>
      `;

      // ITEMS
      if (!data.items || data.items.length === 0) {
        document.getElementById('detalle-items').innerHTML =
          `<p style="color:#999">No hay items</p>`;
      } else {
        document.getElementById('detalle-items').innerHTML =
          data.items.map(i => `
            <div style="display:flex; justify-content:space-between;">
              <span>${i.nombre}</span>
              <span>$${Number(i.precio).toLocaleString('es-CO')} x ${i.cantidad}</span>
            </div>
          `).join('');
      }

      document.getElementById('modal-detalle').style.display = 'flex';
    })
    .catch(() => alert('Error cargando detalle'));
}


// ── ADMIN: CERRAR MODAL ────────────────
function cerrarDetalle() {
  document.getElementById('modal-detalle').style.display = 'none';
}


// ── LOGOUT ─────────────────────────────
function cerrarSesion() {
  fetch('/api/logout', { method: 'POST' })
    .then(() => location.href = '/');
}


// ── CARRITO ────────────────────────────
function agregarAlCarrito(id) {
  fetch('/api/carrito/agregar', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({ servicio_id: id })
  })
  .then(() => alert('Agregado al carrito'))
  .catch(() => alert('Error'));
}


function confirmarPedido() {
  const notas = document.getElementById('carrito-notas')?.value || '';

  fetch('/api/carrito/confirmar', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({ notas })
  })
  .then(r => r.json())
  .then(data => {
    alert("Pedido #" + data.pedido_id + " creado");
  });
}
