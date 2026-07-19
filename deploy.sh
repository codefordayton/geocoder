#!/usr/bin/env bash
#
# Deploy the geocoder web service to Google Cloud Run.
#
# Prerequisites:
#   - gcloud CLI installed and authenticated:  gcloud auth login
#   - a GCP project selected:                  gcloud config set project YOUR_PROJECT
#   - geocoder.db built locally:               python build_index.py
#
# Cloud Run builds the image from the Dockerfile (via Cloud Build), so the
# ~29MB geocoder.db is baked into the read-only container image. No volumes,
# no external database. The service scales to zero when idle.
#
set -euo pipefail

SERVICE_NAME="${SERVICE_NAME:-parcel-geocoder}"
REGION="${REGION:-us-central1}"

if [[ ! -f geocoder.db ]]; then
  echo "geocoder.db not found. Run 'python build_index.py' first." >&2
  exit 1
fi

echo "Deploying '${SERVICE_NAME}' to Cloud Run in ${REGION}..."
gcloud run deploy "${SERVICE_NAME}" \
  --source . \
  --region "${REGION}" \
  --allow-unauthenticated \
  --memory 256Mi \
  --cpu 1 \
  --max-instances 3

echo
echo "Done. Test it:"
echo "  URL=\$(gcloud run services describe ${SERVICE_NAME} --region ${REGION} --format='value(status.url)')"
echo "  curl \"\$URL/health\""
