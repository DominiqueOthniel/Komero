#!/usr/bin/env python3
"""Create or update Komero API on Render from RENDER_API_KEY.

Usage:
  RENDER_API_KEY=rnd_... python scripts/deploy_render.py
"""

from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.request

API = "https://api.render.com/v1"
REPO = "https://github.com/DominiqueOthniel/Komero"


def req(method: str, path: str, token: str, body: dict | None = None):
    data = None if body is None else json.dumps(body).encode()
    request = urllib.request.Request(
        f"{API}{path}",
        data=data,
        method=method,
        headers={
            "Accept": "application/json",
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            raw = response.read().decode()
            return response.status, json.loads(raw) if raw else None
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode()
        raise SystemExit(f"Render API {method} {path} failed: {exc.code} {detail}") from exc


def main() -> None:
    token = os.environ.get("RENDER_API_KEY", "").strip()
    if not token:
        raise SystemExit("Missing RENDER_API_KEY")

    status, owners = req("GET", "/owners?limit=20", token)
    owner_id = None
    for item in owners or []:
        owner = item.get("owner") or item
        if owner.get("email") or owner.get("id"):
            owner_id = owner.get("id")
            break
    if not owner_id and owners:
        owner_id = (owners[0].get("owner") or owners[0]).get("id")
    if not owner_id:
        raise SystemExit("No Render owner/workspace found for this API key")

    print(f"Using owner {owner_id}")

    _, services = req("GET", "/services?limit=50", token)
    existing = None
    for item in services or []:
        service = item.get("service") or item
        if service.get("name") == "komero-api":
            existing = service
            break

    if existing:
        service_id = existing["id"]
        print(f"Service already exists: {service_id}")
    else:
        payload = {
            "type": "web_service",
            "name": "komero-api",
            "ownerId": owner_id,
            "repo": REPO,
            "autoDeploy": "yes",
            "branch": "main",
            "rootDir": "backend",
            "serviceDetails": {
                "env": "docker",
                "plan": "free",
                "region": "oregon",
                "healthCheckPath": "/health",
                "dockerContext": ".",
                "dockerfilePath": "./Dockerfile",
            },
            "envVars": [
                {"key": "APP_ENV", "value": "production"},
                {"key": "APP_NAME", "value": "Komero"},
                {"key": "API_PREFIX", "value": "/api/v1"},
                {"key": "CURRENCY_DEFAULT", "value": "XAF"},
                {"key": "WHATSAPP_ADAPTER", "value": "mock"},
                {"key": "AI_PROVIDER", "value": "mock"},
                {"key": "STORAGE_PROVIDER", "value": "local"},
                {"key": "RUN_SEED", "value": "true"},
                {"key": "FRONTEND_URL", "value": "https://komero.netlify.app"},
                {
                    "key": "CORS_ORIGINS",
                    "value": "https://komero.netlify.app,http://localhost:3000,http://127.0.0.1:3000",
                },
                {"key": "WHATSAPP_VERIFY_TOKEN", "value": "komero-verify-token"},
                {"key": "SECRET_KEY", "generateValue": True},
                {"key": "TOKEN_ENCRYPTION_KEY", "generateValue": True},
            ],
        }
        _, created = req("POST", "/services", token, payload)
        service_id = (created or {}).get("service", created)["id"]
        print(f"Created service {service_id}")

    # Ensure Postgres exists
    _, dbs = req("GET", "/postgres?limit=50", token)
    db = None
    for item in dbs or []:
        postgres = item.get("postgres") or item
        if postgres.get("name") == "komero-db":
            db = postgres
            break
    if not db:
        _, created_db = req(
            "POST",
            "/postgres",
            token,
            {
                "name": "komero-db",
                "ownerId": owner_id,
                "plan": "free",
                "region": "oregon",
                "version": "16",
                "databaseName": "komero",
                "databaseUser": "komero",
            },
        )
        db = (created_db or {}).get("postgres", created_db)
        print(f"Created database {db.get('id')}")
    else:
        print(f"Database exists: {db.get('id')}")

    connection = db.get("connectionString") or db.get("connectionInfo", {}).get(
        "externalConnectionString"
    )
    if connection:
        req(
            "PUT",
            f"/services/{service_id}/env-vars/DATABASE_URL",
            token,
            {"value": connection},
        )
        print("Attached DATABASE_URL")

    # Trigger deploy
    _, deploy = req("POST", f"/services/{service_id}/deploys", token, {"clearCache": "do_not_clear"})
    deploy_id = (deploy or {}).get("id")
    print(f"Deploy started: {deploy_id}")

    service_url = None
    for _ in range(60):
        _, svc = req("GET", f"/services/{service_id}", token)
        service = (svc or {}).get("service", svc) or {}
        service_url = (
            service.get("serviceDetails", {}).get("url")
            or service.get("url")
        )
        if service_url and service_url.startswith("http"):
            break
        time.sleep(5)

    if service_url:
        print(f"SERVICE_URL={service_url}")
    else:
        print("SERVICE_URL=pending")


if __name__ == "__main__":
    main()
