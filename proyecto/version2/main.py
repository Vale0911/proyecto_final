import csv
import hashlib
from flask import Flask, render_template, request, redirect, url_for, session
import codecs

app = Flask(__name__)

# Configuración de la clave secreta para sesiones
app.secret_key = 'mi_clave_secreta'

# Crear archivo de usuarios si no existe
def inicializar_archivo_usuarios():
    try:
        with open('usuarios.csv', mode='x', newline='') as archivo:
            escritor = csv.writer(archivo)
            escritor.writerow(['email', 'password_hash'])  # Cabecera inicial
    except FileExistsError:
        pass  # Si el archivo ya existe, no hacer nada

# Leer usuarios desde el archivo CSV
def leer_usuarios():
    usuarios = {}
    with open('usuarios.csv', mode='r', newline='', encoding='utf-8') as archivo:
        filas = list(csv.reader(archivo))  # Lee todas las filas
        
        # Verificar si el archivo tiene la cabecera correcta
        if filas and (filas[0][0] != 'email' or filas[0][1] != 'password_hash'):
            filas.insert(0, ['email', 'password_hash'])  # Agregar cabecera si no existe

        archivo.seek(0)  # Volver al principio del archivo
        reader = csv.DictReader(archivo)  # Usar DictReader para leer como diccionario
        for row in reader:
            if 'password_hash' in row:  # Asegúrate de que 'password_hash' exista
                usuarios[row['email']] = row['password_hash']
            else:
                print("La columna 'password_hash' no está en el archivo CSV.")
                
    return usuarios


# Agregar un nuevo usuario
def agregar_usuario(email, password_hash):
    with open('usuarios.csv', mode='a', newline='') as archivo:
        escritor = csv.writer(archivo)
        escritor.writerow([email, password_hash])

def leer_empleados():
    empleados = []
    with codecs.open('empleados.csv', mode='r', encoding='utf-8-sig') as csvfile:
        reader = csv.DictReader(csvfile, delimiter=';')

        for row in reader:
            print(f"Leyendo empleado: {row['Full_name']}")  # Debug: Ver nombre
            try:
                row['Horas_extra_diurnas'] = float(row['Horas_extra_diurnas'])  # Cambiado a leer las horas extras reales
                print(f"Horas extra diurnas: {row['Horas_extra_diurnas']}")  # Debug
            except ValueError:
                row['Horas_extra_diurnas'] = 0

            try:
                row['Horas_extra_nocturnas'] = float(row['Horas_extra_nocturnas'])  # Cambiado a leer las horas extras reales
                print(f"Horas extra nocturnas: {row['Horas_extra_nocturnas']}")  # Debug
            except ValueError:
                row['Horas_extra_nocturnas'] = 0

            empleados.append(row)
    return empleados


# Ruta de inicio
@app.route("/")
def inicio():
    return render_template("inicio.html")

# Ruta de login
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form['email']
        password = request.form['password']
        usuarios = leer_usuarios()  # Leer los usuarios del archivo
        
        if email in usuarios:
            # Verificar la contraseña encriptada
            if usuarios[email] == hashlib.sha256(password.encode()).hexdigest():
                session['usuario'] = email
                return redirect(url_for('generar_nomina'))
            else:
                return "Contraseña incorrecta", 403
        else:
            return "Usuario no encontrado", 404

    return render_template("login.html")

# Ruta de crear perfil
@app.route("/crear_perfil", methods=["GET", "POST"])
def crear_perfil():
    if request.method == "POST":
        email = request.form['email']
        password = request.form['password']
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        usuarios = leer_usuarios()
        if email in usuarios:
            return "Este correo ya está registrado.", 400
        agregar_usuario(email, password_hash)
        session['usuario'] = email
        return redirect(url_for('login'))
    return render_template("crear_perfil.html")

# Ruta para generar nómina
@app.route('/generar_nomina', methods=['GET', 'POST'])
def generar_nomina():
    if 'usuario' not in session:
        return redirect(url_for('login'))

    empleados = leer_empleados()  # Leer los empleados del CSV
    empleado_seleccionado = None

    if request.method == 'POST':
        # Si estamos buscando un empleado por ID
        id_empleado = request.form.get('idEmpleado')
        if id_empleado:
            empleado_seleccionado = next((emp for emp in empleados if emp['id'] == id_empleado), None)

        # Si estamos viendo los detalles de un empleado
        elif request.form.get('verDetalles'):
            id_empleado = request.form.get('verDetalles')
            empleado_seleccionado = next((emp for emp in empleados if emp['id'] == id_empleado), None)

        # Calcular el total devengado
        if empleado_seleccionado:
            salario_total = float(empleado_seleccionado['salario_base']) + float(empleado_seleccionado['pago_horas_extra_diurnas']) + float(empleado_seleccionado['pago_horas_extra_nocturnas'])
            return render_template('generar_nomina.html', empleado=empleado_seleccionado, salario_total=salario_total, empleados=empleados)

    return render_template('generar_nomina.html', empleados=empleados, empleado=empleado_seleccionado)

def obtener_estadisticas_por_departamento(departamento, empleados):
    empleados_filtrados = [emp for emp in empleados if emp['Department'] == departamento]

    if not empleados_filtrados:
        return None  # Si no hay empleados en el departamento

    # Calcular las métricas que necesitamos
    salarios = [float(emp['salario_base']) for emp in empleados_filtrados]
    horas_extra_diurnas = [float(emp['Horas_extra_diurnas']) for emp in empleados_filtrados]  # Usar las horas extras trabajadas (no el pago)
    horas_extra_nocturnas = [float(emp['Horas_extra_nocturnas']) for emp in empleados_filtrados]  # Usar las horas extras trabajadas (no el pago)
    faltas = [int(emp['Ausencias']) for emp in empleados_filtrados]
    horas_entrada = [convertir_a_horas(emp['Hora_entrada']) for emp in empleados_filtrados]
    horas_salida = [convertir_a_horas(emp['Hora_salida']) for emp in empleados_filtrados]
    
    # Calcular el total neto de pago para cada empleado
    total_pagos = [
        (float(emp['salario_base']) + float(emp['pago_horas_extra_diurnas']) + float(emp['pago_horas_extra_nocturnas']))
        for emp in empleados_filtrados
    ]
    
    # Empleado con el mayor total neto
    max_pago = max(total_pagos)
    max_pago_empleado = empleados_filtrados[total_pagos.index(max_pago)]
    
    # Empleado con el menor total neto
    min_pago = min(total_pagos)
    min_pago_empleado = empleados_filtrados[total_pagos.index(min_pago)]
    
    # Empleado con más horas extra diurnas (usamos las horas reales)
    max_horas_extra_diurnas = max(horas_extra_diurnas)
    max_horas_extra_diurnas_empleado = empleados_filtrados[horas_extra_diurnas.index(max_horas_extra_diurnas)]
    
    # Empleado con más horas extra nocturnas (usamos las horas reales)
    max_horas_extra_nocturnas = max(horas_extra_nocturnas)
    max_horas_extra_nocturnas_empleado = empleados_filtrados[horas_extra_nocturnas.index(max_horas_extra_nocturnas)]
    
    # Empleado con más faltas
    max_faltas = max(faltas)
    max_faltas_empleado = empleados_filtrados[faltas.index(max_faltas)]
    
    # Empleado que entra más temprano
    min_entrada = min(horas_entrada)
    min_entrada_empleado = empleados_filtrados[horas_entrada.index(min_entrada)]
    
    # Empleado que sale más tarde
    max_salida = max(horas_salida)
    max_salida_empleado = empleados_filtrados[horas_salida.index(max_salida)]

    # Cálculos finales, asegurarse de pasar todas las claves que usa la plantilla
    return {
        'departamento': departamento,
        'max_salario_empleado': max_pago_empleado,
        'min_salario_empleado': min_pago_empleado,
        'max_horas_extra_diurnas_empleado': max_horas_extra_diurnas_empleado,
        'max_horas_extra_nocturnas_empleado': max_horas_extra_nocturnas_empleado,
        'max_faltas_empleado': max_faltas_empleado,
        'min_entrada_empleado': min_entrada_empleado,
        'max_salida_empleado': max_salida_empleado,
        'promedio_entrada': calcular_promedio_hora(horas_entrada),
        'promedio_salida': calcular_promedio_hora(horas_salida)
    }


# Calcular el promedio de las horas en formato HH:MM
def calcular_promedio_hora(horas):
    total_minutos = 0
    for hora in horas:
        hora_convertida = convertir_a_horas(hora)  # Aseguramos la conversión correcta
        h, m = divmod(hora_convertida * 60, 60)  # Convertir a horas y minutos
        total_minutos += h * 60 + m

    promedio_minutos = total_minutos / len(horas)
    horas_promedio = promedio_minutos // 60
    minutos_promedio = promedio_minutos % 60
    return f"{int(horas_promedio):02d}:{int(minutos_promedio):02d}"


def convertir_a_horas(hora, departamento=None):
    # Verifica si 'hora' es una cadena no vacía
    if isinstance(hora, str) and hora.strip():
        try:
            # Si la hora contiene segundos, manejamos ambos formatos (HH:MM:SS o HH:MM)
            if len(hora.split(":")) == 2:  # Formato HH:MM
                horas, minutos = map(int, hora.split(":"))
                return horas + minutos / 60
            elif len(hora.split(":")) == 3:  # Formato HH:MM:SS
                horas, minutos, segundos = map(int, hora.split(":"))
                return horas + minutos / 60 + segundos / 3600
        except ValueError:
            # Si no puede hacer el split correctamente, muestra un error
            print(f"Error al convertir hora para departamento {departamento}: {hora}")
            return 0  # Asignar un valor predeterminado si no se puede convertir
    elif isinstance(hora, (int, float)):  # Si ya es un número, devolverlo como está
        return hora
    else:
        print(f"Formato de hora incorrecto para departamento {departamento}: {hora}")
        return 0  # Retornar 0 en caso de error




@app.route('/filtrar_departamento', methods=['GET', 'POST'])
def filtrar_departamento():
    empleados = leer_empleados()  # Leer empleados desde el CSV

    # Obtener las estadísticas adicionales
    estadisticas_adicionales = obtener_estadisticas_adicionales(empleados)
    print(f"Estadísticas adicionales: {estadisticas_adicionales}")  # Debug

    if request.method == 'POST':
        departamento = request.form['departamento']
        estadisticas = obtener_estadisticas_por_departamento(departamento, empleados)

        if estadisticas:
            return render_template('filtrar_departamento.html', estadisticas=estadisticas, 
                                   estadisticas_adicionales=estadisticas_adicionales)
        else:
            return render_template('filtrar_departamento.html', error="Departamento no encontrado.", 
                                   estadisticas_adicionales=estadisticas_adicionales)

    return render_template('filtrar_departamento.html', estadisticas_adicionales=estadisticas_adicionales)


def obtener_estadisticas_adicionales(empleados):
    departamentos = set(emp['Department'] for emp in empleados)
    
    # Inicializar las variables para las estadísticas generales
    departamento_mas_cobra = None
    max_total_neto_pagar = 0

    departamento_mas_ausencias = None
    max_ausencias = 0

    departamento_mas_temprano = None
    hora_promedio_entrada_early = float('inf')  # Iniciar con un valor alto

    departamento_mas_tarde = None
    hora_promedio_salida_late = float('-inf')  # Iniciar con un valor bajo

    departamento_mas_horas_extra = None
    max_horas_extra = 0

    for departamento in departamentos:
        empleados_filtrados = [emp for emp in empleados if emp['Department'] == departamento]

        # Calcular el total neto a pagar para el departamento
        total_neto_pagar_departamento = sum(float(emp['Total_neto_a_pagar']) for emp in empleados_filtrados)

        if total_neto_pagar_departamento > max_total_neto_pagar:
            max_total_neto_pagar = total_neto_pagar_departamento
            departamento_mas_cobra = departamento

        # Calcular las ausencias totales por departamento
        total_faltas_departamento = sum(int(emp['Ausencias']) for emp in empleados_filtrados)

        if total_faltas_departamento > max_ausencias:
            max_ausencias = total_faltas_departamento
            departamento_mas_ausencias = departamento

        # Calcular el promedio de la hora de entrada
        horas_entrada = [convertir_a_horas(emp['Hora_entrada']) for emp in empleados_filtrados]
        promedio_entrada_departamento = calcular_promedio_hora(horas_entrada)

        if promedio_entrada_departamento < hora_promedio_entrada_early:
            hora_promedio_entrada_early = promedio_entrada_departamento
            departamento_mas_temprano = departamento

        # Calcular el promedio de la hora de salida
        horas_salida = [convertir_a_horas(emp['Hora_salida']) for emp in empleados_filtrados]
        promedio_salida_departamento = calcular_promedio_hora(horas_salida)

        if promedio_salida_departamento > hora_promedio_salida_late:
            hora_promedio_salida_late = promedio_salida_departamento
            departamento_mas_tarde = departamento

        # Sumar todas las horas extra del departamento
        horas_extra_diurnas = [float(emp['Horas_extra_diurnas']) for emp in empleados_filtrados]
        horas_extra_nocturnas = [float(emp['Horas_extra_nocturnas']) for emp in empleados_filtrados]
        total_horas_extra_departamento = sum(horas_extra_diurnas) + sum(horas_extra_nocturnas)

        if total_horas_extra_departamento > max_horas_extra:
            max_horas_extra = total_horas_extra_departamento
            departamento_mas_horas_extra = departamento

    # Convertir las horas promedio a formato de 24 horas (HH:MM)
    hora_promedio_entrada_early_str = convertir_a_hora_formato(hora_promedio_entrada_early)
    hora_promedio_salida_late_str = convertir_a_hora_formato(hora_promedio_salida_late)

    # Retornar las estadísticas generales
    return {
        'departamento_mas_cobra': departamento_mas_cobra,
        'max_total_neto_pagar': max_total_neto_pagar,
        'departamento_mas_ausencias': departamento_mas_ausencias,
        'max_ausencias': max_ausencias,
        'departamento_mas_temprano': departamento_mas_temprano,
        'hora_promedio_entrada_early': hora_promedio_entrada_early_str,
        'departamento_mas_tarde': departamento_mas_tarde,
        'hora_promedio_salida_late': hora_promedio_salida_late_str,
        'departamento_mas_horas_extra': departamento_mas_horas_extra,
        'max_horas_extra': max_horas_extra
    }

def convertir_a_horas(hora_str):
    """Convierte una cadena de hora en formato 'HH:MM' a un valor numérico decimal."""
    try:
        hora, minuto = map(int, hora_str.split(':'))
        return hora + minuto / 60
    except ValueError:
        return 0  # Si no se puede convertir, retornamos 0

def convertir_a_hora_formato(decimal_hora):
    """Convierte una hora decimal a formato 'HH:MM'."""
    horas = int(decimal_hora)  # Parte entera es la hora
    minutos = int((decimal_hora - horas) * 60)  # Parte decimal es los minutos
    return f"{horas:02}:{minutos:02}"  # Formato HH:MM, aseguramos dos dígitos

def calcular_promedio_hora(horas):
    """Calcula el promedio de una lista de horas representadas como decimales."""
    if horas:
        return sum(horas) / len(horas)
    return 0  # Si la lista está vacía, retornamos 0

def convertir_a_horas(hora_str):
    """Convierte una cadena de hora en formato 'HH:MM' a un valor numérico decimal."""
    try:
        hora, minuto = map(int, hora_str.split(':'))
        return hora + minuto / 60
    except ValueError:
        return 0  # Si no se puede convertir, retornamos 0

def calcular_promedio_hora(horas):
    """Calcula el promedio de una lista de horas representadas como decimales."""
    if horas:
        return sum(horas) / len(horas)
    return 0  # Si la lista está vacía, retornamos 0


if __name__ == '__main__':
    inicializar_archivo_usuarios()
    app.run(debug=True)
