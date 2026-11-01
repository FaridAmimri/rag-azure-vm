#!/usr/bin/env bash
# deploy.sh - Create the container app on Azure Container Apps
#
# Prerequisites: az login, resource group and environment already created
# (see deploy.env), image pushed to ghcr.io as a public package.
# Run in Git Bash:  bash deploy.sh
#
# The keys are read from .env and stored as Container Apps secrets:
# they are never printed nor written in this file.

# Stop at the first error, on unset variables and on failed pipes
set -euo pipefail

source deploy.env

# Read one value from .env (leading spaces allowed, strip quotes and Windows \r)
# "|| true": a missing key gives an empty value, reported just below
read_env() {
    grep -E "^[[:space:]]*$1=" .env | cut -d= -f2- | tr -d '\r"' || true
}

MKEY=$(read_env MISTRAL_API_KEY)
AKEY=$(read_env API_KEY)

if [ -z "$MKEY" ] || [ -z "$AKEY" ]; then
    echo "MISTRAL_API_KEY or API_KEY is missing in .env" >&2
    exit 1
fi

# min-replicas 0: scales to zero when idle (no cost), cold start on first call
az containerapp create \
    --name "$APP_NAME" \
    --resource-group "$RG" \
    --environment "$ENV_NAME" \
    --image "$IMAGE" \
    --target-port 8000 \
    --ingress external \
    --cpu 0.5 --memory 1.0Gi \
    --min-replicas 0 --max-replicas 1 \
    --secrets mistral-api-key="$MKEY" api-key="$AKEY" \
    --env-vars MISTRAL_API_KEY=secretref:mistral-api-key API_KEY=secretref:api-key \
    --query properties.configuration.ingress.fqdn \
    --output tsv
