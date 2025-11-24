# Docker‑Compose Quick Start for Whitaker & Cassandra

This guide explains how to use the **docker‑compose.yml** file in the project root to spin up the two required services:

| Service | Purpose | Exposed Port | Key Environment Variables |
|---------|---------|--------------|---------------------------|
| **cassandra** | Apache Cassandra database | `9042` (host) → `9042` (container) | `CASSANDRA_BROADCAST_ADDRESS=cassandra`<br>`CASSANDRA_CLUSTER_NAME=AugustineCluster` |
| **whitaker‑server** | Flask API that serves Whitaker data | `9090` (host) → `9090` (container) | `FLASK_ENV=production` |

Both services include healthchecks to ensure they are ready before you start using them.

## 1️⃣ Start the services

```bash
# From the project root:
docker compose up -d cassandra whitaker-server
```

- `-d` runs the containers in detached mode.
- Only the two services needed for local development are started.

## 2️⃣ Verify they are running

```bash
# List running containers
docker compose ps

# Check logs (replace <service> with cassandra or whitaker-server)
docker compose logs <service>
```

You should see healthcheck status **healthy** for both services:

```bash
$ docker compose ps
NAME                     IMAGE               COMMAND                  SERVICE            CREATED          STATUS                    PORTS
ai-coder-cassandra-1     cassandra:4.1       "docker-entrypoint.s…"   cassandra          5 seconds ago    health: starting          0.0.0.0:9042->9042/tcp
ai-coder-whitaker-server-1  whitaker-server   "python whitaker_se…"    whitaker-server    5 seconds ago    healthy (0 seconds)      0.0.0.0:9090->9090/tcp
```

## 3️⃣ Interact with the Whitaker API

The API is reachable at `http://localhost:9090`. A simple health check:

```bash
curl http://localhost:9090/health
# Expected output: {"status":"ok"}
```

## 4️⃣ Stop & clean up

```bash
docker compose down
```

- This stops the containers and removes the network.
- The Cassandra data volume (`cassandra_data`) is **persisted**; it will stay on your machine unless you explicitly remove it:

```bash
docker volume rm $(docker volume ls -qf name=cassandra_data)
```

## 5️⃣ Tips & Common Issues

- **Port conflicts** – Ensure nothing else is using ports `9042` or `9090` on your host.
- **Cassandra startup time** – The first start may take a minute while the DB initializes. The healthcheck will keep retrying until it’s ready.
- **Rebuilding the Whitaker image** – If you modify the source code in `services/whitaker-server`, rebuild the image before bringing the service up:

```bash
docker compose build whitaker-server
docker compose up -d whitaker-server
```

---

Now you have a quick reference to bring up the Whitaker and Cassandra services with Docker‑Compose. Happy coding!
