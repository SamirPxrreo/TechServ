from flask import Flask, render_template, request, jsonify, session, redirect
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import os
import psycopg
import psycopg.rows

app = Flask(__name__)

app.secret_key = 'techserv_secret_2025'
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise Exception("DATABASE_URL no configurada")


def get_db_connection():
    return psycopg.connect(DATABASE_URL, sslmode="require")


# ───────────────────────── AUTH ─────────────────────────

def admin_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if session.get('rol') != 'admin':
            return redirect('/')
        return f(*args, **kwargs)
    return wrapper


# ───────────────────────── HOME ─────────────────────────

@app.route('/')
def index():
    conn = get_db_connection()
    cur = conn.cursor(row_factory=psycopg.rows.dict_row)

    cur.execute("SELECT * FROM servicios WHERE activo = TRUE")
    servicios = cur.fetchall()

    cur.close()
    conn.close()

    return render_template('index.html', servicios=servicios)


# ───────────────────────── ADMIN ─────────────────────────

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
        SELECT COALESCE(SUM(total),0) AS ingresos FROM pedidos WHERE estado='completado'
    """)
    ingresos = cur.fetchone()['ingresos'] or 0

    cur.execute("""
        SELECT p.*, u.nombre, u.correo
        FROM pedidos p
        JOIN usuarios u ON p.usuario_id = u.id
        ORDER BY p.id DESC
        LIMIT 20
    """)
    pedidos = cur.fetchall()

    cur.execute("SELECT * FROM usuarios ORDER BY id DESC LIMIT 20")
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


# ───────────────────────── ADMIN API ─────────────────────────

@app.route('/api/admin/pedido/<int:id>', methods=['PUT'])
def actualizar_pedido(id):
    data = request.json
    estado = data.get('estado')

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("UPDATE pedidos SET estado=%s WHERE id=%s", (estado, id))
    conn.commit()

    cur.close()
    conn.close()

    return jsonify({'ok': True})


@app.route('/api/admin/pedido/<int:id>')
def detalle_pedido(id):
    conn = get_db_connection()
    cur = conn.cursor(row_factory=psycopg.rows.dict_row)

    cur.execute("""
        SELECT p.*, u.nombre, u.correo
        FROM pedidos p
        JOIN usuarios u ON p.usuario_id = u.id
        WHERE p.id = %s
    """, (id,))
    pedido = cur.fetchone()

    cur.execute("""
        SELECT nombre, precio, cantidad
        FROM pedido_items
        WHERE pedido_id = %s
    """, (id,))
    items = cur.fetchall()

    cur.close()
    conn.close()

    return jsonify({'pedido': pedido, 'items': items})


# ───────────────────────── AUTH ─────────────────────────

@app.route('/api/registro', methods=['POST'])
def registro():
    data = request.json

    conn = get_db_connection()
    cur = conn.cursor(row_factory=psycopg.rows.dict_row)

    hashed = generate_password_hash(data['contrasena'])

    cur.execute("""
        INSERT INTO usuarios (nombre, telefono, correo, contrasena, rol)
        VALUES (%s,%s,%s,%s,'usuario')
        RETURNING id
    """, (data['nombre'], data['telefono'], data['correo'], hashed))

    user_id = cur.fetchone()['id']
    conn.commit()

    session['usuario_id'] = user_id
    session['nombre'] = data['nombre']
    session['rol'] = 'usuario'

    cur.close()
    conn.close()

    return jsonify({'mensaje': 'Usuario creado'})


@app.route('/api/login', methods=['POST'])
def login():
    data = request.json

    conn = get_db_connection()
    cur = conn.cursor(row_factory=psycopg.rows.dict_row)

    cur.execute("SELECT * FROM usuarios WHERE correo=%s", (data['correo'],))
    user = cur.fetchone()

    cur.close()
    conn.close()

    if not user or not check_password_hash(user['contrasena'], data['contrasena']):
        return jsonify({'error': 'Credenciales inválidas'}), 401

    session['usuario_id'] = user['id']
    session['nombre'] = user['nombre']
    session['rol'] = user['rol']

    return jsonify({'mensaje': 'Login ok'})


@app.route('/api/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'ok': True})


@app.route('/api/sesion')
def sesion():
    return jsonify({
        'autenticado': 'usuario_id' in session,
        'nombre': session.get('nombre'),
        'rol': session.get('rol')
    })


# ───────────────────────── CARRITO ─────────────────────────

@app.route('/api/carrito/agregar', methods=['POST'])
def agregar():
    data = request.json
    servicio_id = data['servicio_id']

    conn = get_db_connection()
    cur = conn.cursor(row_factory=psycopg.rows.dict_row)

    cur.execute("SELECT * FROM servicios WHERE id=%s", (servicio_id,))
    s = cur.fetchone()

    carrito = session.get('carrito', [])

    carrito.append({
        'id': s['id'],
        'nombre': s['nombre'],
        'precio': float(s['precio']),
        'cantidad': 1,
        'subtotal': float(s['precio'])
    })

    session['carrito'] = carrito

    cur.close()
    conn.close()

    return jsonify({'ok': True})


@app.route('/api/carrito')
def ver_carrito():
    carrito = session.get('carrito', [])

    total = sum(i['precio'] * i['cantidad'] for i in carrito)

    return jsonify({'items': carrito, 'total': total})


@app.route('/api/carrito/eliminar/<int:id>', methods=['DELETE'])
def eliminar(id):
    carrito = session.get('carrito', [])
    carrito = [i for i in carrito if i['id'] != id]
    session['carrito'] = carrito
    return jsonify({'ok': True})


@app.route('/api/carrito/confirmar', methods=['POST'])
def confirmar():
    if 'usuario_id' not in session:
        return jsonify({'error': 'No login'}), 401

    data = request.json
    carrito = session.get('carrito', [])

    total = sum(i['precio'] * i['cantidad'] for i in carrito)

    conn = get_db_connection()
    cur = conn.cursor(row_factory=psycopg.rows.dict_row)

    cur.execute("""
        INSERT INTO pedidos (usuario_id, total, notas, estado)
        VALUES (%s,%s,%s,'pendiente')
        RETURNING id
    """, (session['usuario_id'], total, data.get('notas','')))

    pedido_id = cur.fetchone()['id']

    for i in carrito:
        cur.execute("""
            INSERT INTO pedido_items (pedido_id,nombre,precio,cantidad)
            VALUES (%s,%s,%s,%s)
        """, (pedido_id, i['nombre'], i['precio'], i['cantidad']))

    conn.commit()
    cur.close()
    conn.close()

    session['carrito'] = []

    return jsonify({'pedido_id': pedido_id})
