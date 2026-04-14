FROM python:3.11-slim
WORKDIR /app

# Create a non-root user and group
RUN apt-get update && apt-get upgrade -y && \
    apt-get clean && \
        rm -rf /var/lib/apt/lists/*
        RUN groupadd -r nonroot && useradd -m -r -g nonroot nonroot

        # Copy requirements and install
        COPY --chown=nonroot:nonroot backend/requirements.txt ./requirements.txt
        RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
            pip install --no-cache-dir -r requirements.txt && \
                pip uninstall -y setuptools wheel

                # Maintain host-like structure so parents[1] in codec.py points to the right place
                COPY --chown=nonroot:nonroot schemas ./schemas
                COPY --chown=nonroot:nonroot backend ./backend

                EXPOSE 8000
                USER nonroot:nonroot
                ENV PYTHONPATH=/app
                CMD ["uvicorn", "backend.api:app", "--host", "0.0.0.0", "--port", "8000"]
                
