FROM python:3.10-slim

WORKDIR /app

# Install system dependencies for MySQL and building ML packages
RUN apt-get update && apt-get install -y \
    gcc \
    default-libmysqlclient-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

COPY ../data /app/data

# Generate required ML artifacts as per installation instructions
RUN python3 -m ml.train_ant

# Expose the port FastAPI runs on
EXPOSE 8000

# Run the application using uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
