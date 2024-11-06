# Usar la imagen de Python 3.11.5
FROM python:3.11.5-slim

# Establecer el directorio de trabajo
WORKDIR /app

# Copiar los archivos de requirements para instalar las dependencias
COPY requirements.txt .

# Instalar las dependencias
RUN pip install --no-cache-dir -r requirements.txt

# Copiar todo el contenido de la aplicación al contenedor
COPY . .

# Exponer el puerto 50001
EXPOSE 50001

# Comando para correr la aplicación con uvicorn
CMD ["uvicorn", "app:app", "--reload", "--host", "0.0.0.0", "--port", "50001"]
