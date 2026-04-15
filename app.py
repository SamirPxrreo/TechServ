from flask import Flask, render_template, request, jsonify, session, redirect
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import os
import psycopg
import psycopg.rows

app = Flask(__name__)

app.config['PROPAGATE_EXCEPTIONS'] = True
app.secret_key = 'techserv_secret_2025'

app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'


# 🔥 DATABASE
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise Exception("DATABASE_URL no está configurada en Render")


def get_db_connection():
    return psycopg.connect(
        DATABASE_URL,
        sslmode="require",
        connect_timeout=10
    )


@app.route('/admin')
@admin_required
def admin():
    conn = get_db_connection()
    cur = conn.cursor(row_factory=psycopg.rows.dict_row)

    cur.execute("SELECT COUNT(*) AS total FROM usuarios")
    total_usuarios = cur.fetchone()['total']

    cur.execute("SELECT COUNT(*) AS total FROM pedidos")
    total_pedidos = cur.fetchone()['total']

    cur.execute("""
        SELECT COALESCE(SUM(total),0) AS ingresos
        FROM pedidos
        WHERE estado = 'completado'
    """)
    ingresos = cur.fetchone()['ingresos']

    cur.execute("""
        SELECT p.*, u.nombre, u.correo
        FROM pedidos p
        JOIN usuarios u ON p.usuario_id = u.id
        ORDER BY p.id DESC
    """)
    pedidos = cur.fetchall()

    cur.execute("SELECT * FROM usuarios ORDER BY id DESC")
    usuarios = cur.fetchall()

    cur.close()
    conn.close()

    return render_template(
        'admin.html',
        total_usuarios=total_usuarios,
        total_pedidos=total_pedidos,
        ingresos=ingresos,
        pedidos=pedidos,
        usuarios=usuarios
    )

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


# ── HOME ─────────────────────────────────────────────────────
@app.route('/')
def index():
    conn = get_db_connection()
    cur = conn.cursor(row_factory=psycopg.rows.dict_row)

    cur.execute("SELECT * FROM servicios WHERE activo = TRUE")
    servicios = cur.fetchall()

    cur.close()
    conn.close()

    return render_template('index.html', servicios=servicios)
# ── LOGIN TEST DB (DEBUG OPCIONAL) ───────────────────────────
@app.route('/ping-db')
def ping_db():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT 1")
        data = cur.fetchone()
        cur.close()
        conn.close()

        return f"DB OK ✅ {data}"

    except Exception as e:
        return f"DB ERROR ❌ {str(e)}"

# ── PING ─────────────────────────────────────────────────────
@app.route('/ping')
def ping():
    return "Flask está vivo ✅"


# ── REGISTRO ────────────────────────────────────────────────
@app.route('/api/registro', methods=['POST'])
def registro():
    data = request.json
    nombre = data.get('nombre', '').strip()
    telefono = data.get('telefono', '').strip()
    correo = data.get('correo', '').strip().lower()
    contrasena = data.get('contrasena', '')

    if not all([nombre, telefono, correo, contrasena]):
        return jsonify({'error': 'Todos los campos son obligatorios'}), 400

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

    return jsonify({
        'mensaje': f'Bienvenido {nombre}',
        'nombre': nombre,
        'rol': 'usuario'
    })


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

    return jsonify({
        'mensaje': f'Bienvenido {usuario["nombre"]}',
        'nombre': usuario['nombre'],
        'rol': usuario['rol']
    })


# ── LOGOUT ───────────────────────────────────────────────────
@app.route('/api/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'mensaje': 'Sesión cerrada'})


# ── SESIÓN ───────────────────────────────────────────────────
@app.route('/api/sesion')
def sesion():
    if 'usuario_id' in session:
        return jsonify({
            'autenticado': True,
            'mensaje': f'Bienvenido {session["nombre"]}',
            'nombre': session["nombre"],
            'rol': session["rol"]
        })

    return jsonify({
        'autenticado': False
    })


# ── CARRITO: AGREGAR ─────────────────────────────────────────
@app.route('/api/carrito/agregar', methods=['POST'])
def carrito_agregar():
    if 'usuario_id' not in session:
        return jsonify({'error': 'No autenticado'}), 401

    data = request.json
    servicio_id = data.get('servicio_id')

    if not servicio_id:
        return jsonify({'error': 'Servicio inválido'}), 400

    if 'carrito' not in session:
        session['carrito'] = []

    carrito = session['carrito']

    # verificar si ya existe
    for item in carrito:
        if item['servicio_id'] == servicio_id:
            item['cantidad'] += 1
            session['carrito'] = carrito
            session.modified = True
            return jsonify({'mensaje': 'Agregado'})

    # traer info del servicio
    conn = get_db_connection()
    cur = conn.cursor(row_factory=psycopg.rows.dict_row)

    cur.execute("SELECT id, nombre, precio FROM servicios WHERE id = %s", (servicio_id,))
    servicio = cur.fetchone()

    cur.close()
    conn.close()

    if not servicio:
        return jsonify({'error': 'Servicio no encontrado'}), 404

    carrito.append({
        'id': servicio['id'],
        'servicio_id': servicio['id'],
        'nombre': servicio['nombre'],
        'precio': float(servicio['precio']),
        'cantidad': 1,
        'icono': '🔧',
        'subtotal': float(servicio['precio'])
    })

    session['carrito'] = carrito
    session.modified = True

    return jsonify({'mensaje': 'Agregado al carrito'})


# ── CARRITO: OBTENER ─────────────────────────────────────────
@app.route('/api/carrito')
def carrito_ver():
    carrito = session.get('carrito', [])

    total = 0

    for item in carrito:
        item['subtotal'] = item['precio'] * item['cantidad']
        total += item['subtotal']

    return jsonify({
        'items': carrito,
        'total': total
    })


# ── CARRITO: ELIMINAR ────────────────────────────────────────
@app.route('/api/carrito/eliminar/<int:id>', methods=['DELETE'])
def carrito_eliminar(id):
    carrito = session.get('carrito', [])

    carrito = [item for item in carrito if item['id'] != id]

    session['carrito'] = carrito
    session.modified = True

    return jsonify({'mensaje': 'Eliminado'})


# ── CARRITO: CONFIRMAR ───────────────────────────────────────
@app.route('/api/carrito/confirmar', methods=['POST'])
def carrito_confirmar():
    if 'usuario_id' not in session:
        return jsonify({'error': 'No autenticado'}), 401

    carrito = session.get('carrito', [])

    if not carrito:
        return jsonify({'error': 'Carrito vacío'}), 400

    data = request.json
    notas = data.get('notas', '')

    total = sum(item['precio'] * item['cantidad'] for item in carrito)

    conn = get_db_connection()
    cur = conn.cursor(row_factory=psycopg.rows.dict_row)

    cur.execute("""
        INSERT INTO pedidos (usuario_id, total, notas, estado)
        VALUES (%s, %s, %s, 'pendiente')
        RETURNING id
    """, (session['usuario_id'], total, notas))

    pedido_id = cur.fetchone()['id']

    conn.commit()
    cur.close()
    conn.close()

    session['carrito'] = []
    session.modified = True

    return jsonify({
        'mensaje': 'Pedido creado',
        'pedido_id': pedido_id
    })





if __name__ == '__main__':
    app.run(debug=True)


