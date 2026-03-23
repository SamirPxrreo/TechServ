# ⬡ TechServ — Guía de Instalación

## Requisitos
- Python 3.8 o superior
- MySQL Server instalado y corriendo

---

## Paso 1 — Instalar dependencias Python
```bash
pip install -r requirements.txt
```

---

## Paso 2 — Crear la base de datos
Abre tu cliente MySQL (MySQL Workbench, XAMPP, consola...) y ejecuta:
```bash
mysql -u root -p < schema.sql
```
O copia y pega el contenido de `schema.sql` en tu cliente MySQL.

---

## Paso 3 — Configurar conexión MySQL
Abre `app.py` y edita estas líneas con tus datos:
```python
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'TU_CONTRASEÑA_AQUI'
app.config['MYSQL_DB'] = 'techserv'
```

---

## Paso 4 — Actualizar contraseña del Admin
En `schema.sql` el admin se crea con una contraseña placeholder.
Después de correr la app, regístrate con el correo `admin@techserv.com`
o actualiza la contraseña directamente en MySQL:

```sql
USE techserv;
UPDATE usuarios 
SET contrasena = 'pbkdf2:sha256:...'   -- genera esto con werkzeug
WHERE correo = 'admin@techserv.com';
```

**Forma más fácil:** Cambia el rol de tu usuario a 'admin' desde MySQL:
```sql
UPDATE usuarios SET rol = 'admin' WHERE correo = 'tu@correo.com';
```

---

## Paso 5 — Correr la aplicación
```bash
python app.py
```

Abre en el navegador: **http://localhost:5000**
Panel de admin: **http://localhost:5000/admin**

---

## Estructura del proyecto
```
techserv/
├── app.py              ← Servidor Flask + rutas + lógica
├── schema.sql          ← Base de datos MySQL
├── requirements.txt    ← Dependencias Python
├── templates/
│   ├── index.html      ← Página principal (hero, servicios, modales)
│   └── admin.html      ← Panel de administrador
└── static/
    ├── css/style.css   ← Todos los estilos
    └── js/main.js      ← Lógica de modales, carrito, auth
```

---

## Funcionalidades
- ✅ Registro de usuarios (nombre, teléfono, correo, contraseña encriptada)
- ✅ Login / Logout con sesiones
- ✅ Carrito de servicios por usuario (persiste en MySQL)
- ✅ Confirmación de pedidos
- ✅ Panel de administrador con usuarios y pedidos
- ✅ Cambio de estado de pedidos (pendiente → en proceso → completado)
- ✅ Diseño responsive
