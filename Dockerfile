FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files 
COPY . .

# Create necessary directories
RUN mkdir -p data/vectordb

# Set environment variables
ENV PYTHONPATH=/app
ENV VECTOR_DB_PATH=/app/data/vectordb

# Expose port for Streamlit
EXPOSE 8501

# Run the application
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
