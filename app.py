from flask import Flask, render_template, request, jsonify, session, redirect
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import os
import psycopg
import psycopg.rows

app = Flask(__name__)
app.secret_key = 'techserv_secret_2025'

app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'


def get_db_connection():
    try:
        return psycopg.connect(DATABASE_URL, sslmode="require")
    except Exception as e:
        print("Error conexión DB:", e)
        raise

# ── Conexión PostgreSQL ──────────────────────────────────────
DATABASE_URL = os.getenv("DATABASE_URL")

def get_db_connection():
    return psycopg.connect(DATABASE_URL, sslmode="require")

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
    conn = get_db_connection()
    cur = conn.cursor(row_factory=psycopg.rows.dict_row)
    cur.execute("SELECT * FROM servicios WHERE activo = TRUE")
    servicios = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('index.html', servicios=servicios)

# ── Registro ─────────────────────────────────────────────────
@app.route('/api/registro', methods=['POST'])
def registro():
    data = request.json
    nombre = data.get('nombre', '').strip()
    telefono = data.get('telefono', '').strip()
    correo = data.get('correo', '').strip().lower()
    contrasena = data.get('contrasena', '')

    if not all([nombre, telefono, correo, contrasena]):
        return jsonify({'error': 'Todos los campos son obligatorios'}), 400

    if len(contrasena) < 6:
        return jsonify({'error': 'Mínimo 6 caracteres'}), 400

    conn = get_db_connection()
    cur = conn.cursor(row_factory=psycopg.rows.dict_row)

    cur.execute("SELECT id FROM usuarios WHERE correo = %s", (correo,))
    if cur.fetchone():
        cur.close()
        conn.close()
        return jsonify({'error': 'Correo ya registrado'}), 409

    hashed = generate_password_hash(contrasena)

    cur.execute(
        "INSERT INTO usuarios (nombre, telefono, correo, contrasena) VALUES (%s, %s, %s, %s) RETURNING id",
        (nombre, telefono, correo, hashed)
    )
    nuevo_id = cur.fetchone()['id']
    conn.commit()

    cur.close()
    conn.close()

    session['usuario_id'] = nuevo_id
    session['nombre'] = nombre
    session['correo'] = correo
    session['rol'] = 'usuario'

    return jsonify({'mensaje': f'Bienvenido {nombre}'})

# ── Login ────────────────────────────────────────────────────
@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    correo = data.get('correo', '').strip().lower()
    contrasena = data.get('contrasena', '')

    conn = get_db_connection()
    cur = conn.cursor(row_factory=psycopg.rows.dict_row)

    cur.execute("SELECT * FROM usuarios WHERE correo = %s", (correo,))
    usuario = cur.fetchone()

    cur.close()
    conn.close()

    if not usuario or not check_password_hash(usuario['contrasena'], contrasena):
        return jsonify({'error': 'Credenciales incorrectas'}), 401

    session['usuario_id'] = usuario['id']
    session['nombre'] = usuario['nombre']
    session['correo'] = usuario['correo']
    session['rol'] = usuario['rol']

    return jsonify({'mensaje': f'Bienvenido {usuario["nombre"]}'})

# ── Logout ───────────────────────────────────────────────────
@app.route('/api/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'mensaje': 'Sesión cerrada'})

# ── Sesión ───────────────────────────────────────────────────
@app.route('/api/sesion')
def sesion():
    if 'usuario_id' in session:
        return jsonify({
            'autenticado': True,
            'nombre': session['nombre'],
            'rol': session['rol']
        })
    return jsonify({'autenticado': False})

# ── Ver carrito ──────────────────────────────────────────────
@app.route('/api/carrito')
@login_required
def ver_carrito():
    conn = get_db_connection()
    cur = conn.cursor(row_factory=psycopg.rows.dict_row)

    cur.execute("""
        SELECT c.id, s.nombre, s.precio, s.icono, c.cantidad,
        (s.precio * c.cantidad) AS subtotal
        FROM carrito c
        JOIN servicios s ON c.servicio_id = s.id
        WHERE c.usuario_id = %s
    """, (session['usuario_id'],))

    items = cur.fetchall()
    cur.close()
    conn.close()

    total = sum(float(i['subtotal']) for i in items)

    return jsonify({'items': items, 'total': total})

# ── Agregar carrito ──────────────────────────────────────────
@app.route('/api/carrito/agregar', methods=['POST'])
@login_required
def agregar_carrito():
    servicio_id = request.json.get('servicio_id')

    conn = get_db_connection()
    cur = conn.cursor(row_factory=psycopg.rows.dict_row)

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

    conn.commit()
    cur.close()
    conn.close()

    return jsonify({'mensaje': 'Agregado al carrito'})

# ── Eliminar carrito ─────────────────────────────────────────
@app.route('/api/carrito/eliminar/<int:item_id>', methods=['DELETE'])
@login_required
def eliminar_carrito(item_id):
    conn = get_db_connection()
    cur = conn.cursor(row_factory=psycopg.rows.dict_row)

    cur.execute(
        "DELETE FROM carrito WHERE id=%s AND usuario_id=%s",
        (item_id, session['usuario_id'])
    )

    conn.commit()
    cur.close()
    conn.close()

    return jsonify({'mensaje': 'Eliminado'})

# ── Confirmar pedido ─────────────────────────────────────────
@app.route('/api/carrito/confirmar', methods=['POST'])
@login_required
def confirmar_pedido():
    notas = request.json.get('notas', '')

    conn = get_db_connection()
    cur = conn.cursor(row_factory=psycopg.rows.dict_row)

    cur.execute("""
        SELECT c.servicio_id, c.cantidad, s.precio
        FROM carrito c
        JOIN servicios s ON c.servicio_id = s.id
        WHERE c.usuario_id = %s
    """, (session['usuario_id'],))

    items = cur.fetchall()

    if not items:
        cur.close()
        conn.close()
        return jsonify({'error': 'Carrito vacío'}), 400

    total = sum(float(i['precio']) * i['cantidad'] for i in items)

    cur.execute(
        "INSERT INTO pedidos (usuario_id, total, notas) VALUES (%s, %s, %s) RETURNING id",
        (session['usuario_id'], total, notas)
    )
    pedido_id = cur.fetchone()['id']

    for item in items:
        cur.execute(
            "INSERT INTO pedido_detalle (pedido_id, servicio_id, cantidad, precio_unitario) VALUES (%s, %s, %s, %s)",
            (pedido_id, item['servicio_id'], item['cantidad'], item['precio'])
        )

    cur.execute("DELETE FROM carrito WHERE usuario_id = %s", (session['usuario_id'],))

    conn.commit()
    cur.close()
    conn.close()

    return jsonify({'mensaje': 'Pedido confirmado', 'pedido_id': pedido_id})

# ── Admin ────────────────────────────────────────────────────
@app.route('/admin')
@admin_required
def admin():
    conn = get_db_connection()
    cur = conn.cursor(row_factory=psycopg.rows.dict_row)

    cur.execute("SELECT * FROM usuarios ORDER BY fecha_registro DESC")
    usuarios = cur.fetchall()

    cur.execute("""
        SELECT p.*, u.nombre, u.correo
        FROM pedidos p
        JOIN usuarios u ON p.usuario_id = u.id
        ORDER BY p.fecha DESC
    """)
    pedidos = cur.fetchall()

    cur.execute("SELECT COUNT(*) AS total FROM usuarios WHERE rol='usuario'")
    total_usuarios = cur.fetchone()['total']

    cur.execute("SELECT COUNT(*) AS total FROM pedidos")
    total_pedidos = cur.fetchone()['total']

    cur.execute("SELECT COALESCE(SUM(total),0) AS total FROM pedidos WHERE estado='completado'")
    ingresos = cur.fetchone()['total']

    cur.close()
    conn.close()

    return render_template('admin.html',
        usuarios=usuarios,
        pedidos=pedidos,
        total_usuarios=total_usuarios,
        total_pedidos=total_pedidos,
        ingresos=ingresos
    )

# ── Ping ─────────────────────────────────────────────────────
@app.route('/ping')
def ping():
    return "Flask está vivo ✅"

if __name__ == '__main__':
    app.run(debug=True)
