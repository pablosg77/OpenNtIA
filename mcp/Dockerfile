FROM python:3.11-slim

WORKDIR /app

# Install minimal build dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Force generic x86-64 (no advanced CPU features)
ENV CFLAGS="-O2 -march=x86-64 -mtune=generic"
ENV CXXFLAGS="-O2 -march=x86-64 -mtune=generic"
ENV NPY_DISABLE_CPU_FEATURES="AVX,AVX2,AVX512F,FMA3"
ENV OPENBLAS_CORETYPE=Prescott

COPY requirements.txt .

# Install NumPy from source without CPU optimizations
RUN pip install --no-cache-dir --no-binary :all: numpy==1.24.3

# Install scikit-learn (will use our NumPy)
RUN pip install --no-cache-dir scikit-learn==1.3.2

# Install remaining requirements
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000 3334

CMD ["sh", "-c", "uvicorn api:app --host 0.0.0.0 --port 8000 & fastmcp run server.py --host 0.0.0.0 --port 3334"]
