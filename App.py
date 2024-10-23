# Importamos FastAPI para crear la API.
from fastapi import FastAPI

# Importamos las funciones y clases necesarias de sympy para manejar expresiones matemáticas simbólicas,
# hacer integrales y trabajar con funciones matemáticas comunes como sin, cos, log, etc.
from sympy import symbols, integrate, sin, cos, log, tan, exp, sympify, lambdify

# Pydantic se usa para definir modelos de datos en FastAPI, en este caso, para manejar las solicitudes de integrales.
from pydantic import BaseModel

# Importamos el middleware de CORS para permitir solicitudes desde cualquier origen. Esto es útil si la API se consume desde diferentes dominios.
from fastapi.middleware.cors import CORSMiddleware

# Matplotlib se utiliza para generar gráficos, y en este caso, se usa para graficar las funciones originales e integrales.
import matplotlib.pyplot as plt

# Numpy nos permite trabajar con arreglos numéricos y realizar operaciones matemáticas de forma eficiente.
import numpy as np

# La librería io se usa para manejar flujos de entrada/salida, en este caso, para crear un buffer para guardar la imagen del gráfico.
import io

# StreamingResponse se utiliza para enviar el gráfico generado como una respuesta de imagen.
from fastapi.responses import StreamingResponse

# Inicializamos la aplicación FastAPI
app = FastAPI()

# Definimos el modelo de datos que se espera recibir en la solicitud de la API.
# En este caso, incluye la expresión matemática a integrar y, opcionalmente, los límites de integración.
class IntegralRequest(BaseModel):
    expression: str
    lower_limit: float = None  # Límite inferior de la integral definida (opcional)
    upper_limit: float = None  # Límite superior de la integral definida (opcional)

# Habilitamos CORS para permitir que la API reciba peticiones de cualquier origen.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permitir todas las solicitudes de cualquier origen
    allow_credentials=True,
    allow_methods=["*"],  # Permitir todos los métodos HTTP (GET, POST, etc.)
    allow_headers=["*"],  # Permitir todos los encabezados en las solicitudes
)

# Variable global para almacenar el gráfico generado más recientemente, lo que nos permitirá devolverlo cuando se solicite.
graph_buffer = None

# Ruta para calcular la integral, donde recibimos una expresión matemática en formato string.
@app.post("/calculate-integral")
async def calculate_integral(request: IntegralRequest):
    global graph_buffer  # Usamos una variable global para manejar el buffer de la gráfica

    # Definimos la variable simbólica 'x' que usaremos en las expresiones matemáticas.
    x = symbols('x')
    
    try:
        # Usamos sympy.sympify para convertir la expresión matemática de texto a una expresión simbólica que podamos trabajar.
        # Reemplazamos 'e**' con 'exp' para asegurar que las funciones exponenciales sean correctamente interpretadas.
        original_function = sympify(request.expression.replace("e**", "exp"))
    except Exception as e:
        # Si hay un error en la expresión (por ejemplo, un formato incorrecto), devolvemos un mensaje de error.
        return {"error": "Error en la expresión matemática proporcionada."}

    # Calculamos la integral indefinida (sin límites) de la función recibida.
    integrated_function = integrate(original_function, x)

    # Creamos una lista para almacenar los pasos que explicarán cómo se resolvió la integral en formato LaTeX.
    steps = []

    # Paso 1: Mostramos la integral original en formato LaTeX.
    steps.append(f"Problema: \\( \\int {request.expression.replace('**', '^').replace('*', '\\,')} \\, dx \\)")

    # Dividimos la expresión en términos si es una suma para descomponer la integral, lo que facilita su resolución.
    terms = request.expression.split('+')
    if len(terms) > 1:
        steps.append("1. Descomponer la integral en términos:")
        for term in terms:
            # Añadimos cada término de la suma por separado para resolverlo individualmente.
            steps.append(f"   \\( \\int {term.strip().replace('**', '^').replace('*', '\\,')} \\, dx \\)")
    else:
        steps.append(f"1. Resolver la integral directamente para \\( \\int {request.expression.replace('**', '^').replace('*', '\\,')} \\, dx \\)")

    # Paso 2: Explicamos las reglas que aplicamos a cada término, según su tipo.
    for term in terms:
        term = term.strip()  # Limpiamos el término para evitar espacios en blanco.

        # Si el término contiene funciones trigonométricas, aplicamos las reglas de integración trigonométrica.
        if 'sin' in term or 'cos' in term or 'tan' in term:
            steps.append(f"2. Aplicar la regla de integración trigonométrica a \\( {term.replace('**', '^').replace('*', '\\,')} \\):")
            if 'sin' in term:
                steps.append("   \\( \\int \\sin(x) \\, dx = -\\cos(x) \\)")
            elif 'cos' in term:
                steps.append("   \\( \\int \\cos(x) \\, dx = \\sin(x) \\)")
            elif 'tan' in term:
                steps.append("   \\( \\int \\tan(x) \\, dx = \\ln(\\cos(x)) \\)")

        # Si el término contiene logaritmos, aplicamos la regla de integración por partes.
        elif 'log' in term or 'ln' in term:
            steps.append(f"2. Aplicar la integración por partes a \\( {term.replace('**', '^').replace('*', '\\,')} \\):")
            steps.append("   \\( \\int \\ln(x) \\, dx = x \\ln(x) - x + C \\)")

        # Si el término es una función exponencial, aplicamos la regla correspondiente.
        elif 'exp' in term or 'e^' in term:
            steps.append(f"2. Aplicar la regla de integración exponencial a \\( {term.replace('**', '^').replace('*', '\\,')} \\):")
            steps.append("   \\( \\int e^x \\, dx = e^x \\)")

        # Para términos polinomiales (x**n), aplicamos la regla de potencias.
        elif 'x**' in term:
            steps.append(f"2. Aplicar la regla de integración de potencias a \\( {term.replace('**', '^').replace('*', '\\,')} \\):")
            steps.append("   \\( \\int x^n \\, dx = \\frac{x^{n+1}}{n+1} \\)")

        # Si es un término lineal como 'ax', aplicamos la regla de integración lineal.
        elif 'x' in term:
            steps.append(f"2. Aplicar la regla de integración lineal a \\( {term.replace('**', '^').replace('*', '\\,')} \\):")
            steps.append("   \\( \\int ax \\, dx = \\frac{ax^2}{2} \\)")

        # Para constantes simples, usamos la regla de integración de constantes.
        else:
            steps.append(f"2. Aplicar la regla para constantes a \\( {term.replace('**', '^').replace('*', '\\,')} \\):")
            steps.append("   \\( \\int a \\, dx = ax \\)")

    # Paso 3: Sumar los resultados de la integración de cada término.
    steps.append("3. Sumar los resultados parciales:")
    steps.append(f"   Resultado final: \\( {str(integrated_function).replace('**', '^').replace('*', '\\,')} + C \\)")

    # Si se proporcionan los límites inferior y superior, calculamos la integral definida.
    if request.lower_limit is not None and request.upper_limit is not None:
        try:
            # Calculamos la integral definida utilizando los límites proporcionados.
            defined_integral = integrate(original_function, (x, request.lower_limit, request.upper_limit))
            steps.append(f"4. Valor de la integral definida con límites \\( {request.lower_limit} \\) y \\( {request.upper_limit} \\):")
            steps.append(f"   \\( \\int_{{{request.lower_limit}}}^{{{request.upper_limit}}} {request.expression.replace('**', '^').replace('*', '\\,')} \\, dx = {defined_integral} \\)")
        except Exception as e:
            # Si ocurre un error al calcular la integral definida, devolvemos el mensaje de error.
            return {"error": f"Error al calcular la integral definida: {e}"}
    else:
        defined_integral = None  # Si no hay límites, no se calcula la integral definida.

    # Ahora, creamos los gráficos de la función original y de la integral.
    # Convertimos las expresiones simbólicas a funciones numéricas utilizando lambdify para poder graficarlas.
    original_function_np = lambdify(x, original_function, {"sin": np.sin, "cos": np.cos, "tan": np.tan, "exp": np.exp, "log": np.log})
    integrated_function_np = lambdify(x, integrated_function, {"sin": np.sin, "cos": np.cos, "tan": np.tan, "exp": np.exp, "log": np.log})
    
    # Generamos un conjunto de valores de X entre -10 y 10 para la gráfica.
    X_vals = np.linspace(-10, 10, 400)
    
    try:
        # Evaluamos los valores de la función original e integral para graficarlos.
        original_Y_vals = original_function_np(X_vals)
        integrated_Y_vals = integrated_function_np(X_vals)

        # Verificamos que las dimensiones de los resultados sean correctas.
        if len(original_Y_vals) != len(X_vals) or len(integrated_Y_vals) != len(X_vals):
            raise ValueError("La dimensión de X_vals no coincide con la de Y_vals.")
        
    except Exception as e:
        # Si ocurre algún error durante la evaluación de las funciones, devolvemos el mensaje de error.
        return {"error": f"Error al evaluar la función: {e}"}
    
    # Creamos la figura del gráfico con matplotlib.
    plt.figure(figsize=(10, 6))
    # Graficamos la función original en azul.
    plt.plot(X_vals, original_Y_vals, label=f"Original: {request.expression.replace('**', '^').replace('*', ' ')}", color="blue")
    # Graficamos la función integral en rojo con una línea punteada.
    plt.plot(X_vals, integrated_Y_vals, label=f"Integral: {str(integrated_function).replace('**', '^').replace('*', ' ')}", color="red", linestyle="--")
    plt.title("Gráfica de la función original e integral")
    plt.xlabel("x")
    plt.ylabel("f(x)")
    plt.legend()
    plt.grid(True)

    # Guardamos el gráfico en un objeto BytesIO para luego enviarlo como respuesta.
    graph_buffer = io.BytesIO()
    plt.savefig(graph_buffer, format="png")
    graph_buffer.seek(0)
    plt.close()

    # Retornamos la integral indefinida y, si fue calculada, la integral definida, junto con la explicación paso a paso.
    return {
        "indefinite_integral": str(integrated_function).replace('**', '^').replace('*', '\\,'),  # Integral indefinida
        "defined_integral": str(defined_integral) if defined_integral is not None else "No se proporcionaron límites",  # Integral definida
        "explanation": steps  # Explicación paso a paso en formato LaTeX
    }

# Ruta para obtener la gráfica generada. Si no hay gráfica disponible, se devuelve un error.
@app.get("/get-graph")
async def get_graph():
    global graph_buffer
    if graph_buffer:
        # Enviamos el gráfico como una respuesta de imagen.
        return StreamingResponse(graph_buffer, media_type="image/png")
    else:
        return {"error": "No hay gráfica generada."}
