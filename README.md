# Calculadora de Integrales API

Esta API permite calcular integrales indefinidas y definidas de expresiones matemáticas simbólicas, así como generar gráficas de las funciones originales y sus respectivas integrales.

## Requisitos

Antes de comenzar, asegúrate de tener lo siguiente instalado en tu máquina:

- **Python 3.7+**: Necesario para ejecutar el código de la API.
- **pip**: El administrador de paquetes de Python, que se utiliza para instalar las dependencias del proyecto.

## Instalación

Sigue estos pasos para instalar las dependencias y configurar el entorno:

1. **Clona este repositorio o descarga los archivos**.
2. **Instala las dependencias**:

   Abre una terminal en el directorio del proyecto y ejecuta el siguiente comando para instalar las dependencias desde el archivo `requirements.txt`:

   ```bash
   pip install -r requirements.txt
   ```

## Ejecutar la API

Ejecuta el siguiente comando para iniciar el servidor de FastAPI utilizando uvicorn:

uvicorn App:app --reload
