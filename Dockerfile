# Imagem base
FROM python:3.12-slim

# Evita criar arquivos .pyc
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Define diretório de trabalho
WORKDIR /app

# Instala dependências do sistema (Firebird client)
RUN apt-get update && apt-get install -y \
    libfbclient2 \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# (Opcional) Define caminho explícito da lib do Firebird
ENV FIREBIRD_LIB=/usr/lib/x86_64-linux-gnu/libfbclient.so.2

# Copia requirements primeiro (melhor cache)
COPY requirements.txt .

# Instala dependências Python
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copia o restante do projeto
COPY . .

# Expõe porta
EXPOSE 8000

# Comando para iniciar a aplicação
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
