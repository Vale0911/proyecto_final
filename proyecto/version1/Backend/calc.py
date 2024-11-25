import pygame
from pygame.locals import *
import json
import os
import csv

# Configuración inicial de Pygame
pygame.init()
pantalla = pygame.display.set_mode((800, 600))
pygame.display.set_caption("Gestión de Usuarios y Nómina")
fps = pygame.time.Clock()

# Colores
BLANCO = (255, 255, 255)
NEGRO = (0, 0, 0)
ROJO = (255, 0, 0)
AZUL = (0, 0, 255)
VERDE = (0, 255, 0)

# Variables globales
pagina_actual = "inicio"
usuario_texto = ""
contrasena_texto = ""
escribiendo = None
mensaje = ""

# Clase para manejar la base de datos
class BaseDeDatos:
    def __init__(self):
        self.archivo = 'usuarios.json'
        self.usuarios = self.cargar_usuarios()

    def cargar_usuarios(self):
        if os.path.exists(self.archivo):
            with open(self.archivo, 'r') as f:
                return json.load(f)
        return {}

    def guardar_usuarios(self):
        with open(self.archivo, 'w') as f:
            json.dump(self.usuarios, f)

    def agregar_usuario(self, usuario, contrasena):
        if usuario in self.usuarios:
            return False
        self.usuarios[usuario] = contrasena
        self.guardar_usuarios()
        return True

    def validar_usuario(self, usuario, contrasena):
        return self.usuarios.get(usuario) == contrasena

db = BaseDeDatos()

# Funciones utilitarias
def crear_boton(texto, x, y, ancho, alto, color_fondo, color_texto):
    fuente = pygame.font.Font(None, 36)
    rect = pygame.Rect(x, y, ancho, alto)
    pygame.draw.rect(pantalla, color_fondo, rect)
    texto_renderizado = fuente.render(texto, True, color_texto)
    pantalla.blit(texto_renderizado, texto_renderizado.get_rect(center=rect.center))
    return rect

def mostrar_texto(texto, x, y, color=NEGRO):
    fuente = pygame.font.Font(None, 36)
    texto_renderizado = fuente.render(texto, True, color)
    pantalla.blit(texto_renderizado, (x, y))

# Funciones para las páginas
def manejar_pagina_inicio():
    pantalla.fill(BLANCO)
    mostrar_texto("Gestión de Usuarios y Nómina", 240, 50, NEGRO)
    boton_crear_usuario = crear_boton("Crear Usuario", 300, 200, 200, 50, AZUL, BLANCO)
    boton_iniciar_sesion = crear_boton("Iniciar Sesión", 300, 300, 200, 50, VERDE, BLANCO)
    return {"crear_usuario": boton_crear_usuario, "iniciar_sesion": boton_iniciar_sesion}

def manejar_pagina_crear_usuario():
    pantalla.fill(BLANCO)
    mostrar_texto("Crear Usuario", 320, 50)
    rect_usuario = crear_boton(f"Usuario: {usuario_texto}", 200, 200, 400, 50, BLANCO, NEGRO)
    rect_contrasena = crear_boton(f"Contraseña: {'*' * len(contrasena_texto)}", 200, 300, 400, 50, BLANCO, NEGRO)
    boton_registrar = crear_boton("Registrar", 300, 400, 200, 50, AZUL, BLANCO)
    boton_volver = crear_boton("Volver", 50, 500, 100, 50, ROJO, BLANCO)
    mostrar_texto(mensaje, 200, 500, ROJO)
    return {"usuario": rect_usuario, "contrasena": rect_contrasena, "registrar": boton_registrar, "volver": boton_volver}

def manejar_pagina_iniciar_sesion():
    pantalla.fill(BLANCO)
    mostrar_texto("Iniciar Sesión", 320, 50)
    rect_usuario = crear_boton(f"Usuario: {usuario_texto}", 200, 200, 400, 50, BLANCO, NEGRO)
    rect_contrasena = crear_boton(f"Contraseña: {'*' * len(contrasena_texto)}", 200, 300, 400, 50, BLANCO, NEGRO)
    boton_login = crear_boton("Iniciar Sesión", 300, 400, 200, 50, VERDE, BLANCO)
    boton_volver = crear_boton("Volver", 50, 500, 100, 50, ROJO, BLANCO)
    mostrar_texto(mensaje, 200, 500, ROJO)
    return {"usuario": rect_usuario, "contrasena": rect_contrasena, "iniciar": boton_login, "volver": boton_volver}

# Cargar datos desde un archivo
def cargar_datos():
    with open("datos_nomina.txt", "r") as archivo:
        lineas = archivo.readlines()
        texto_id_empleado = lineas[0].strip()
        return texto_id_empleado

# Revisar si el ID de empleado coincide
def revisar_empleado_id(empleado_id, row):
    # Elimina espacios en blanco y compara los valores
    print(f"Comparando: Ingresado '{empleado_id.strip()}' vs CSV '{row[0].strip()}'")  # Depuración
    return empleado_id.strip() == row[0].strip()

def cargar_csv_y_buscar_empleado(empleado_id, archivo_csv):
    """
    Carga un archivo CSV y busca al empleado por ID.
    Ignora filas vacías y usa los índices correctos del archivo actualizado.
    """
    encontrado = False
    nombre_empleado = "No encontrado"
    salario_base_hora = 0
    salario_hora_extra = 0

    with open(archivo_csv, mode='r', encoding='utf-8') as file:
        reader = csv.reader(file)
        next(reader)  # Saltar encabezados
        for row in reader:
            # Ignorar filas vacías
            if not row or len(row) < 5:
                continue

            # Depuración avanzada para identificar discrepancias
            print(f"ID ingresado: {repr(empleado_id.strip())}, ID en archivo: {repr(row[2].strip())}")

            # Comparar con la columna del ID
            if str(empleado_id).strip() == str(row[2]).strip():
                encontrado = True
                nombre_empleado = f"{row[0]} {row[1]}"  # Combinar nombre y apellido
                salario_base_hora = float(row[3])  # Pago por hora
                salario_hora_extra = float(row[4])  # Pago por hora extra
                break

    return encontrado, nombre_empleado, salario_base_hora, salario_hora_extra


def calculador_nomina():
    """
    Captura datos del usuario, busca al empleado en el CSV,
    calcula los salarios y muestra los resultados.
    """
    # Configuración inicial
    c_base = (0, 0, 0)  # Negro
    c_rectangulo = (169, 169, 169)  # Gris
    c_texto = (255, 255, 255)  # Blanco
    fuente = pygame.font.Font(None, 36)

    global texto_id_empleado, texto_horas_trabajadas, texto_horas_extras
    texto_id_empleado = ""
    texto_horas_trabajadas = ""
    texto_horas_extras = ""

    input_rects = [pygame.Rect(600, 100, 300, 50), pygame.Rect(600, 200, 300, 50), pygame.Rect(600, 300, 300, 50)]
    input_activo = [False, False, False]

    screen = pygame.display.set_mode((1000, 700))
    pygame.display.set_caption('Calculador de Nómina')

    def texto_id():
        pygame.draw.rect(screen, c_rectangulo, (100, 100, 300, 50))
        texto = fuente.render("ID del Empleado", True, c_texto)
        screen.blit(texto, (110, 110))

    def texto_horas():
        pygame.draw.rect(screen, c_rectangulo, (100, 200, 300, 50))
        texto = fuente.render("Horas trabajadas", True, c_texto)
        screen.blit(texto, (110, 210))

    def texto_extras():
        pygame.draw.rect(screen, c_rectangulo, (100, 300, 300, 50))
        texto = fuente.render("Horas extras", True, c_texto)
        screen.blit(texto, (110, 310))

    def dibujar_input_rects():
        textos = [texto_id_empleado, texto_horas_trabajadas, texto_horas_extras]
        for i, rect in enumerate(input_rects):
            pygame.draw.rect(screen, c_rectangulo, rect)
            texto = fuente.render(textos[i], True, c_base)
            screen.blit(texto, (rect.x + 10, rect.y + 15))

    # Botón para guardar
    boton_guardar = crear_boton("Guardar Datos", 600, 400, 200, 50, AZUL, BLANCO)

    # Captura interactiva
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return
            if event.type == pygame.MOUSEBUTTONDOWN:
                for i, rect in enumerate(input_rects):
                    if rect.collidepoint(event.pos):
                        input_activo[:] = [False] * len(input_rects)
                        input_activo[i] = True
                        break
                if boton_guardar.collidepoint(event.pos):
                    running = False  # Terminar captura

            if event.type == pygame.KEYDOWN:
                for i, activo in enumerate(input_activo):
                    if activo:
                        if event.key == pygame.K_BACKSPACE:
                            if i == 0:
                                texto_id_empleado = texto_id_empleado[:-1]
                            elif i == 1:
                                texto_horas_trabajadas = texto_horas_trabajadas[:-1]
                            elif i == 2:
                                texto_horas_extras = texto_horas_extras[:-1]
                        elif event.key == pygame.K_RETURN:
                            input_activo[i] = False
                        else:
                            if i == 0:
                                texto_id_empleado += event.unicode
                            elif i == 1:
                                texto_horas_trabajadas += event.unicode
                            elif i == 2:
                                texto_horas_extras += event.unicode

        screen.fill(c_base)
        texto_id()
        texto_horas()
        texto_extras()
        dibujar_input_rects()
        pygame.draw.rect(screen, c_rectangulo, boton_guardar)
        texto_boton_guardar = fuente.render("Guardar Datos", True, c_texto)
        screen.blit(texto_boton_guardar, (boton_guardar.x + 10, boton_guardar.y + 10))

        pygame.display.flip()

    # Validar entrada de datos
    if not texto_id_empleado or not texto_horas_trabajadas or not texto_horas_extras:
        print("Error: Todos los campos deben estar llenos.")
        return

    try:
        horas_trabajadas = float(texto_horas_trabajadas.strip())
        horas_extras = float(texto_horas_extras.strip())
    except ValueError:
        print("Error: Las horas trabajadas o extras deben ser números válidos.")
        return

    # Buscar al empleado
    archivo_csv = "C:/Users/Thomas/Documents/Poryecto final progeamacion/MOCK_DATA.csv"  # Ruta ajustada
    encontrado, nombre_empleado, salario_base_hora, salario_hora_extra = cargar_csv_y_buscar_empleado(
        texto_id_empleado.strip(), archivo_csv
    )

    # Depuración: Confirmar si el empleado fue encontrado
    print(f"Depuración: encontrado={encontrado}, nombre_empleado={nombre_empleado}, salario_base_hora={salario_base_hora}, salario_hora_extra={salario_hora_extra}")

    # Mostrar resultados
    screen.fill((0, 0, 0))
    if encontrado:
        salario_base = horas_trabajadas * salario_base_hora
        salario_extras = horas_extras * salario_hora_extra
        salario_total = salario_base + salario_extras

        mostrar_texto(f"Empleado: {nombre_empleado} (ID: {texto_id_empleado})", 100, 100, BLANCO)
        mostrar_texto(f"Salario base: ${salario_base:.2f}", 100, 200, BLANCO)
        mostrar_texto(f"Salario por extras: ${salario_extras:.2f}", 100, 300, BLANCO)
        mostrar_texto(f"Salario total: ${salario_total:.2f}", 100, 400, BLANCO)
    else:
        mostrar_texto("Empleado no encontrado.", 100, 100, BLANCO)

    # Botón volver
    boton_volver = crear_boton("Volver", 350, 500, 100, 50, ROJO, BLANCO)

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if boton_volver.collidepoint(event.pos):
                    running = False

        pygame.display.flip()
    



# Lógica principal
def main():
    global pagina_actual, usuario_texto, contrasena_texto, escribiendo, mensaje

    running = True
    botones = {}

    while running:
        pantalla.fill(BLANCO)

        if pagina_actual == "inicio":
            botones = manejar_pagina_inicio()
        elif pagina_actual == "crear_usuario":
            botones = manejar_pagina_crear_usuario()
        elif pagina_actual == "iniciar_sesion":
            botones = manejar_pagina_iniciar_sesion()

        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                running = False

            elif evento.type == pygame.MOUSEBUTTONDOWN:
                pos = pygame.mouse.get_pos()
                if pagina_actual == "inicio":
                    if botones["crear_usuario"].collidepoint(pos):
                        pagina_actual = "crear_usuario"
                        usuario_texto = ""
                        contrasena_texto = ""
                        mensaje = ""
                    elif botones["iniciar_sesion"].collidepoint(pos):
                        pagina_actual = "iniciar_sesion"
                        usuario_texto = ""
                        contrasena_texto = ""
                        mensaje = ""

                elif pagina_actual == "crear_usuario":
                    if botones["usuario"].collidepoint(pos):
                        escribiendo = "usuario"
                    elif botones["contrasena"].collidepoint(pos):
                        escribiendo = "contrasena"
                    elif botones["registrar"].collidepoint(pos):
                        if usuario_texto and contrasena_texto:
                            if db.agregar_usuario(usuario_texto, contrasena_texto):
                                mensaje = "Usuario registrado exitosamente."
                            else:
                                mensaje = "El usuario ya existe."
                        else:
                            mensaje = "Complete ambos campos."
                    elif botones["volver"].collidepoint(pos):
                        pagina_actual = "inicio"
                        escribiendo = None

                elif pagina_actual == "iniciar_sesion":
                    if botones["usuario"].collidepoint(pos):
                        escribiendo = "usuario"
                    elif botones["contrasena"].collidepoint(pos):
                        escribiendo = "contrasena"
                    elif botones["iniciar"].collidepoint(pos):
                        if usuario_texto and contrasena_texto:
                            if db.validar_usuario(usuario_texto, contrasena_texto):
                                calculador_nomina()
                            else:
                                mensaje = "Usuario o contraseña incorrectos."
                        else:
                            mensaje = "Complete ambos campos."
                    elif botones["volver"].collidepoint(pos):
                        pagina_actual = "inicio"
                        escribiendo = None

            elif evento.type == pygame.KEYDOWN:
                if escribiendo == "usuario":
                    if evento.key == pygame.K_BACKSPACE:
                        usuario_texto = usuario_texto[:-1]
                    else:
                        usuario_texto += evento.unicode
                elif escribiendo == "contrasena":
                    if evento.key == pygame.K_BACKSPACE:
                        contrasena_texto = contrasena_texto[:-1]
                    else:
                        contrasena_texto += evento.unicode

        pygame.display.flip()
        fps.tick(30)

    pygame.quit()

if __name__ == "__main__":
    main()