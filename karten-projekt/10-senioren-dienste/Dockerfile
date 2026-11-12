# SPDX-License-Identifier: Apache-2.0
# Bestell-Server fuer Google Cloud Run. Keine Abhaengigkeiten ausser Python.
FROM python:3.12-slim
WORKDIR /app
COPY server.py katalog-sen.json ./
ENV PYTHONUNBUFFERED=1
# Cloud Run setzt PORT selbst; 8080 ist nur der lokale Standard.
EXPOSE 8080
USER nobody
CMD ["python3", "server.py"]

# Lokal:   docker build -t karten-server . && docker run -p 8080:8080 karten-server
# Deploy:  gcloud run deploy karten-server --source . --region europe-west3 --allow-unauthenticated
# Hinweis: Dateisystem auf Cloud Run ist fluechtig -> fuer echten Betrieb Firestore/Cloud Storage.
