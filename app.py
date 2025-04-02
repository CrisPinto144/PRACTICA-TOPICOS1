from flask import Flask, render_template, request, redirect, session  
import mysql.connector  

app = Flask(__name__)  
app.secret_key = 'supersecretkey'  

def get_db_connection():  
    return mysql.connector.connect(  
        host="localhost",  
        user="root",  
        password="",  
        database="abarrotes_db"  
    )  

# ---------------- RUTA PRINCIPAL - LOGIN ----------------  
@app.route('/', methods=['GET', 'POST'])  
def login():  
    if request.method == 'POST':  
        usuario = request.form.get('usuario')  
        contraseña = request.form.get('contraseña')  
        
        conn = get_db_connection()  
        cursor = conn.cursor()  
        cursor.execute("SELECT * FROM usuarios WHERE usuario = %s AND contraseña = %s", (usuario, contraseña))  
        user = cursor.fetchone()  
        conn.close()  
        
        if user:  
            session['usuario'] = usuario  
            return redirect('/dashboard')  
        else:  
            return render_template('login.html', error="Usuario o contraseña incorrectos")  
    
    return render_template('login.html')  

@app.route('/logout')  
def logout():  
    session.pop('usuario', None)  
    return redirect('/')  

# ---------------- PANEL PRINCIPAL ----------------  
@app.route('/dashboard')  
def dashboard():  
    if 'usuario' not in session:  
        return redirect('/')  
    return render_template('dashboard.html')  

# ---------------- GESTIÓN DE PRODUCTOS ----------------  
@app.route('/productos')  
def productos():  
    conn = get_db_connection()  
    cursor = conn.cursor()  
    cursor.execute("SELECT * FROM productos")  
    productos = cursor.fetchall()  
    conn.close()  
    return render_template('productos.html', productos=productos)  

@app.route('/productos/agregar', methods=['POST'])  
def agregar_producto():  
    nombre = request.form['nombre']  
    precio = request.form['precio']  
    stock = request.form['stock']  
    
    conn = get_db_connection()  
    cursor = conn.cursor()  
    cursor.execute("INSERT INTO productos (nombre, precio, stock) VALUES (%s, %s, %s)", (nombre, precio, stock))  
    conn.commit()  
    conn.close()  
    return redirect('/productos')  

@app.route('/productos/eliminar/<int:id>')  
def eliminar_producto(id):  
    conn = get_db_connection()  
    cursor = conn.cursor()  
    cursor.execute("DELETE FROM productos WHERE id = %s", (id,))  
    conn.commit()  
    conn.close()  
    return redirect('/productos')  

# ---------------- REGISTRO DE VENTAS ----------------  
@app.route('/ventas')  
def ventas():  
    conn = get_db_connection()  
    cursor = conn.cursor()  
    cursor.execute("SELECT id, fecha, total FROM ventas")  # Cambiado para no depender de clientes  
    ventas = cursor.fetchall()  
    conn.close()  
    return render_template('ventas.html', ventas=ventas)  

@app.route('/ventas/nueva', methods=['GET', 'POST'])  
def nueva_venta():  
    conn = get_db_connection()  
    cursor = conn.cursor()  

    # Obtener productos para el formulario  
    cursor.execute("SELECT * FROM productos")  
    productos = cursor.fetchall()  

    if request.method == 'POST':  
        total = 0  
        productos_seleccionados = request.form.getlist('productos')  # IDs de productos  
        cantidades = request.form.getlist('cantidades')  # Cantidades  

        # Insertar nueva venta  
        cursor.execute("INSERT INTO ventas (fecha, total) VALUES (NOW(), 0)")  # Total se actualizará después  
        venta_id = cursor.lastrowid  
        
        detalles = []  # Para almacenar detalles de las ventas  

        for i in range(len(productos_seleccionados)):  
            cantidad = int(cantidades[i])  
            id_producto = productos_seleccionados[i]  
            cursor.execute("SELECT nombre, precio FROM productos WHERE id = %s", (id_producto,))  
            nombre, precio = cursor.fetchone()  # Obtener nombre y precio  
            
            total_producto = precio * cantidad  
            total += total_producto  
            
            # Guardar detalle  
            detalles.append((venta_id, id_producto, cantidad))  
        
        # Insertar detalles de la venta  
        cursor.executemany("INSERT INTO detalle_ventas (id_venta, id_producto, cantidad) VALUES (%s, %s, %s)", detalles)  

        # Actualizar total de la venta  
        cursor.execute("UPDATE ventas SET total = %s WHERE id = %s", (total, venta_id))  
        
        conn.commit()  
        conn.close()  
        return redirect('/ventas')  

    conn.close()  
    return render_template('nueva_venta.html', productos=productos)  

if __name__ == '__main__':  
    app.run(debug=True)   

