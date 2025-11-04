# Base image: Python 3.9 slim (versi lightweight)
FROM python:3.9-slim

# Set working directory di dalam container
WORKDIR /app

# Copy requirements.txt dulu (untuk caching layer)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy semua file aplikasi ke container
COPY . .

# Expose port 8001 (port yang dipakai FastAPI)
EXPOSE 8001

# Command untuk menjalankan aplikasi
CMD ["python", "internal_assistant_app.py"]