// ═══════════════════════════════════════
//  TECHSERV — main.js FINAL FUNCIONAL
// ═══════════════════════════════════════


// ── LOADER ─────────────────────────────
window.addEventListener('load', () => {
  const loader = document.getElementById('loader');
  if (loader) loader.style.display = 'none';
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

      const user = document.getElementById('nav-user');
      const guest = document.getElementById('nav-guest');

      if (!data.autenticado) {
        if (guest) guest.style.display = 'flex';
        if (user) user.style.display = 'none';
        return;
      }

      if (guest) guest.style.display = 'none';
      if (user) user.style.display = 'flex';

      document.getElementById('nav-bienvenida').textContent =
        `Hola, ${data.nombre}`;

      if (data.rol === 'admin') {
        const adminLink = document.getElementById('nav-admin-link');
        if (adminLink) adminLink.style.display = 'inline-block';
      }

      cargarCarrito();
    });
}


// ── MODALES ────────────────────────────
function abrirModal(tipo) {
  document.getElementById(`modal-${tipo}`).style.display = 'flex';
}

function cerrarModal(tipo) {
  document.getElementById(`modal-${tipo}`).style.display = 'none';
}

function cerrarModalOverlay(e, tipo) {
  if (e.target.id === `modal-${tipo}`) cerrarModal(tipo);
}


// ── LOGIN ──────────────────────────────
function doLogin() {
  fetch('/api/login', {
    method: 'POST',
    headers: {'Content-Type':'application/json'},
    body: JSON.stringify({
      correo: document.getElementById('login-correo').value,
      contrasena: document.getElementById('login-pass').value
    })
  })
  .then(r => r.json())
  .then(data => {
    if (data.error) {
      alert(data.error);
      return;
    }
    location.reload();
  });
}


// ── REGISTRO ───────────────────────────
function doRegistro() {
  fetch('/api/registro', {
    method: 'POST',
    headers: {'Content-Type':'application/json'},
    body: JSON.stringify({
      nombre: document.getElementById('reg-nombre').value,
      telefono: document.getElementById('reg-telefono').value,
      correo: document.getElementById('reg-correo').value,
      contrasena: document.getElementById('reg-pass').value
    })
  })
  .then(r => r.json())
  .then(data => {
    if (data.error) {
      alert(data.error);
      return;
    }
    location.reload();
  });
}


// ── LOGOUT ─────────────────────────────
function cerrarSesion() {
  fetch('/api/logout', { method: 'POST' })
    .then(() => location.reload());
}


// ── CARRITO ────────────────────────────
function agregarAlCarrito(id) {
  fetch('/api/carrito/agregar', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({ servicio_id: id })
  })
  .then(r => r.json())
  .then(() => {
    mostrarToast("Agregado al carrito");
    cargarCarrito();
  });
}


function cargarCarrito() {
  fetch('/api/carrito')
    .then(r => r.json())
    .then(data => {

      const cont = document.getElementById('carrito-count');
      if (cont) cont.textContent = data.items.length;

      const itemsDiv = document.getElementById('carrito-items');
      const footer = document.getElementById('carrito-footer');

      if (!itemsDiv) return;

      if (data.items.length === 0) {
        itemsDiv.innerHTML = '<p class="carrito-vacio">Vacío</p>';
        if (footer) footer.style.display = 'none';
        return;
      }

      itemsDiv.innerHTML = data.items.map(i => `
        <div class="carrito-item">
          <span>${i.nombre}</span>
          <span>$${Number(i.precio).toLocaleString()} x ${i.cantidad}</span>
        </div>
      `).join('');

      document.getElementById('carrito-total').textContent =
        '$' + Number(data.total).toLocaleString();

      if (footer) footer.style.display = 'block';
    });
}


function toggleCarrito() {
  const panel = document.getElementById('carrito-panel');
  panel.style.display = panel.style.display === 'none' ? 'block' : 'none';
}


function confirmarPedido() {
  const notas = document.getElementById('carrito-notas').value;

  fetch('/api/carrito/confirmar', {
    method: 'POST',
    headers: {'Content-Type':'application/json'},
    body: JSON.stringify({ notas })
  })
  .then(r => r.json())
  .then(data => {
    alert("Pedido #" + data.pedido_id + " creado");
    cargarCarrito();
  });
}


// ── TOAST ──────────────────────────────
function mostrarToast(msg) {
  const toast = document.getElementById('toast');
  if (!toast) return;

  toast.textContent = msg;
  toast.classList.add('show');
  setTimeout(() => toast.classList.remove('show'), 2000);
}


// ── ANIMACIONES ────────────────────────
function activarAnimaciones() {
  const observer = new IntersectionObserver(entries => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('show');
      }
    });
  });

  document.querySelectorAll('.anim').forEach(el => observer.observe(el));
}
