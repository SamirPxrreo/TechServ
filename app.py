from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_mysqldb import MySQL
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import os

app = Flask(__name__)
app.secret_key = 'techserv_secret_2025'

# ── Configuración MySQL ──────────────────────────────────────
# Cambia estos valores según tu servidor MySQL
app.config['MYSQL_HOST'] = 'dpg-d70n6gk50q8c73aaq7c0-a'
app.config['MYSQL_USER'] = 'techserv_user'
app.config['MYSQL_PASSWORD'] = 'fOnl3nLsbrfQazL0oJxrUUmM2PvBVnJ6'  # tu contraseña
app.config['MYSQL_DB'] = 'techserv_fy9t'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
app.config['MYSQL_CHARSET'] = 'utf8mb4'

mysql = MySQL(app)

# ── Decoradores ──────────────────────────────────────────────
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'usuario_id' not in session:
            return jsonify({'error': 'No autenticado'}), 401
        return f(*args, **kwargs)
    return decorated

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'usuario_id' not in session or session.get('rol') != 'admin':
            return redirect('/')
        return f(*args, **kwargs)
    return decorated

# ── Rutas principales ────────────────────────────────────────
@app.route('/')
def index():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM servicios WHERE activo = 1")
    servicios = cur.fetchall()
    cur.close()
    return render_template('index.html', servicios=servicios)

# ── Auth: Registro ───────────────────────────────────────────
@app.route('/api/registro', methods=['POST'])
def registro():
    data = request.json
    nombre    = data.get('nombre', '').strip()
    telefono  = data.get('telefono', '').strip()
    correo    = data.get('correo', '').strip().lower()
    contrasena = data.get('contrasena', '')

    if not all([nombre, telefono, correo, contrasena]):
        return jsonify({'error': 'Todos los campos son obligatorios'}), 400

    if len(contrasena) < 6:
        return jsonify({'error': 'La contraseña debe tener al menos 6 caracteres'}), 400

    cur = mysql.connection.cursor()
    cur.execute("SELECT id FROM usuarios WHERE correo = %s", (correo,))
    if cur.fetchone():
        cur.close()
        return jsonify({'error': 'El correo ya está registrado'}), 409

    hashed = generate_password_hash(contrasena)
    cur.execute(
        "INSERT INTO usuarios (nombre, telefono, correo, contrasena) VALUES (%s, %s, %s, %s)",
        (nombre, telefono, correo, hashed)
    )
    mysql.connection.commit()
    nuevo_id = cur.lastrowid
    cur.close()

    session['usuario_id'] = nuevo_id
    session['nombre']     = nombre
    session['correo']     = correo
    session['rol']        = 'usuario'

    return jsonify({'mensaje': f'Bienvenido, {nombre}!', 'nombre': nombre, 'rol': 'usuario'})

# ── Auth: Login ──────────────────────────────────────────────
@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    correo    = data.get('correo', '').strip().lower()
    contrasena = data.get('contrasena', '')

    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM usuarios WHERE correo = %s", (correo,))
    usuario = cur.fetchone()
    cur.close()

    if not usuario or not check_password_hash(usuario['contrasena'], contrasena):
        return jsonify({'error': 'Correo o contraseña incorrectos'}), 401

    session['usuario_id'] = usuario['id']
    session['nombre']     = usuario['nombre']
    session['correo']     = usuario['correo']
    session['rol']        = usuario['rol']

    return jsonify({
        'mensaje': f'Bienvenido, {usuario["nombre"]}!',
        'nombre': usuario['nombre'],
        'rol': usuario['rol']
    })

# ── Auth: Logout ─────────────────────────────────────────────
@app.route('/api/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'mensaje': 'Sesión cerrada'})

# ── Auth: Estado sesión ──────────────────────────────────────
@app.route('/api/sesion')
def estado_sesion():
    if 'usuario_id' in session:
        return jsonify({
            'autenticado': True,
            'nombre': session['nombre'],
            'rol': session['rol']
        })
    return jsonify({'autenticado': False})

# ── Carrito: Ver ─────────────────────────────────────────────
@app.route('/api/carrito')
@login_required
def ver_carrito():
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT c.id, s.nombre, s.precio, s.icono, c.cantidad,
               (s.precio * c.cantidad) AS subtotal
        FROM carrito c
        JOIN servicios s ON c.servicio_id = s.id
        WHERE c.usuario_id = %s
    """, (session['usuario_id'],))
    items = cur.fetchall()
    cur.close()
    total = sum(float(i['subtotal']) for i in items)
    return jsonify({'items': items, 'total': total})

# ── Carrito: Agregar ─────────────────────────────────────────
@app.route('/api/carrito/agregar', methods=['POST'])
@login_required
def agregar_carrito():
    servicio_id = request.json.get('servicio_id')
    cur = mysql.connection.cursor()
    # Si ya existe, incrementar cantidad
    cur.execute(
        "SELECT id, cantidad FROM carrito WHERE usuario_id=%s AND servicio_id=%s",
        (session['usuario_id'], servicio_id)
    )
    existente = cur.fetchone()
    if existente:
        cur.execute(
            "UPDATE carrito SET cantidad = cantidad + 1 WHERE id = %s",
            (existente['id'],)
        )
    else:
        cur.execute(
            "INSERT INTO carrito (usuario_id, servicio_id) VALUES (%s, %s)",
            (session['usuario_id'], servicio_id)
        )
    mysql.connection.commit()
    cur.close()
    return jsonify({'mensaje': 'Servicio agregado al carrito'})

# ── Carrito: Eliminar ────────────────────────────────────────
@app.route('/api/carrito/eliminar/<int:item_id>', methods=['DELETE'])
@login_required
def eliminar_carrito(item_id):
    cur = mysql.connection.cursor()
    cur.execute(
        "DELETE FROM carrito WHERE id = %s AND usuario_id = %s",
        (item_id, session['usuario_id'])
    )
    mysql.connection.commit()
    cur.close()
    return jsonify({'mensaje': 'Item eliminado'})

# ── Carrito: Confirmar pedido ────────────────────────────────
@app.route('/api/carrito/confirmar', methods=['POST'])
@login_required
def confirmar_pedido():
    notas = request.json.get('notas', '')
    cur = mysql.connection.cursor()

    # Obtener carrito
    cur.execute("""
        SELECT c.servicio_id, c.cantidad, s.precio
        FROM carrito c JOIN servicios s ON c.servicio_id = s.id
        WHERE c.usuario_id = %s
    """, (session['usuario_id'],))
    items = cur.fetchall()

    if not items:
        cur.close()
        return jsonify({'error': 'El carrito está vacío'}), 400

    total = sum(float(i['precio']) * i['cantidad'] for i in items)

    # Crear pedido
    cur.execute(
        "INSERT INTO pedidos (usuario_id, total, notas) VALUES (%s, %s, %s)",
        (session['usuario_id'], total, notas)
    )
    pedido_id = cur.lastrowid

    # Guardar detalle
    for item in items:
        cur.execute(
            "INSERT INTO pedido_detalle (pedido_id, servicio_id, cantidad, precio_unitario) VALUES (%s,%s,%s,%s)",
            (pedido_id, item['servicio_id'], item['cantidad'], item['precio'])
        )

    # Vaciar carrito
    cur.execute("DELETE FROM carrito WHERE usuario_id = %s", (session['usuario_id'],))
    mysql.connection.commit()
    cur.close()

    return jsonify({'mensaje': 'Pedido confirmado exitosamente', 'pedido_id': pedido_id})

# ── Admin ────────────────────────────────────────────────────
@app.route('/admin')
@admin_required
def admin():
    cur = mysql.connection.cursor()
    cur.execute("SELECT id, nombre, telefono, correo, rol, fecha_registro FROM usuarios ORDER BY fecha_registro DESC")
    usuarios = cur.fetchall()
    cur.execute("""
        SELECT p.id, u.nombre, u.correo, p.total, p.estado, p.fecha, p.notas
        FROM pedidos p JOIN usuarios u ON p.usuario_id = u.id
        ORDER BY p.fecha DESC
    """)
    pedidos = cur.fetchall()
    cur.execute("SELECT COUNT(*) AS total FROM usuarios WHERE rol='usuario'") 
    total_usuarios = cur.fetchone()['total']
    cur.execute("SELECT COUNT(*) AS total FROM pedidos")
    total_pedidos = cur.fetchone()['total']
    cur.execute("SELECT SUM(total) AS total FROM pedidos WHERE estado='completado'")
    ingresos = cur.fetchone()['total'] or 0
    cur.close()
    return render_template('admin.html',
        usuarios=usuarios, pedidos=pedidos,
        total_usuarios=total_usuarios, total_pedidos=total_pedidos, ingresos=ingresos
    )

@app.route('/api/admin/pedido/<int:pedido_id>', methods=['PUT'])
@admin_required
def actualizar_pedido(pedido_id):
    estado = request.json.get('estado')
    cur = mysql.connection.cursor()
    cur.execute("UPDATE pedidos SET estado=%s WHERE id=%s", (estado, pedido_id))
    mysql.connection.commit()
    cur.close()
    return jsonify({'mensaje': 'Estado actualizado'})

if __name__ == '__main__':
    app.run(debug=True)


