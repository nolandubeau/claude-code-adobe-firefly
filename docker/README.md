# Docker Infrastructure for Sandbox Orchestration

This directory contains Docker Compose configuration for running the sandbox orchestration infrastructure locally.

## Services

| Service | Port | Description |
|---------|------|-------------|
| `temporal` | 7233 | Temporal Server (gRPC) |
| `temporal-ui` | 8080 | Temporal Web UI |
| `postgresql` | 5432 | PostgreSQL (Temporal persistence) |
| `prometheus` | 9090 | Metrics collection |
| `grafana` | 3000 | Dashboards and visualization |
| `sandbox-worker` | 9091 | Sandbox worker (optional) |

## Quick Start

### 1. Start Infrastructure

```bash
# Start all services (except worker)
docker-compose up -d

# Or start only Temporal
docker-compose up -d temporal temporal-ui

# View logs
docker-compose logs -f
```

### 2. Access Services

- **Temporal UI**: http://localhost:8080
- **Grafana**: http://localhost:3000 (admin/admin)
- **Prometheus**: http://localhost:9090

### 3. Run Worker Locally (Recommended)

```bash
cd ../apps/sandbox_temporal
export TEMPORAL_ADDRESS=localhost:7233
export E2B_API_KEY=your_key
export ANTHROPIC_API_KEY=your_key
uv run sandbox-worker
```

### 4. Or Run Worker in Docker

```bash
# Set environment variables
export E2B_API_KEY=your_key
export ANTHROPIC_API_KEY=your_key

# Start with worker profile
docker-compose --profile worker up -d
```

## Configuration

### Environment Variables

Create a `.env` file in this directory:

```bash
# Required
E2B_API_KEY=your_e2b_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key

# Optional
GITHUB_TOKEN=your_github_token
```

### Temporal Configuration

Temporal dynamic config is in `temporal/dynamicconfig/development.yaml`.

Key settings:
- `history.persistenceMaxQPS`: Max database queries per second
- `matching.numTaskqueueReadPartitions`: Task queue parallelism
- `system.archivalRetentionInDays`: How long to keep workflow history

### Prometheus Configuration

Prometheus config is in `prometheus/prometheus.yml`.

Scrape targets:
- `temporal:7233` - Temporal server metrics
- `sandbox-worker:9091` - Worker metrics (Docker)
- `host.docker.internal:9090` - Worker metrics (local)

### Grafana Dashboards

Pre-configured dashboards in `grafana/dashboards/`:
- `sandbox-orchestration.json` - Main dashboard

## Directory Structure

```
docker/
├── docker-compose.yaml           # Main compose file
├── temporal/
│   └── dynamicconfig/
│       └── development.yaml      # Temporal config
├── prometheus/
│   └── prometheus.yml            # Prometheus config
└── grafana/
    ├── provisioning/
    │   ├── datasources/
    │   │   └── datasources.yml   # Prometheus datasource
    │   └── dashboards/
    │       └── dashboards.yml    # Dashboard provisioning
    └── dashboards/
        └── sandbox-orchestration.json
```

## Commands

```bash
# Start all services
docker-compose up -d

# Stop all services
docker-compose down

# Stop and remove volumes (clean slate)
docker-compose down -v

# View logs
docker-compose logs -f temporal

# Restart a service
docker-compose restart temporal

# Scale workers (if using Docker workers)
docker-compose --profile worker up -d --scale sandbox-worker=3

# Check service status
docker-compose ps
```

## Troubleshooting

### Temporal not starting

Check if PostgreSQL is healthy:
```bash
docker-compose logs postgresql
```

### Worker can't connect to Temporal

Ensure `TEMPORAL_ADDRESS` is correct:
- In Docker: `temporal:7233`
- Locally: `localhost:7233`

### Metrics not showing in Grafana

1. Check Prometheus targets: http://localhost:9090/targets
2. Verify worker is exposing metrics on the configured port
3. Check Grafana datasource: Settings → Data sources → Prometheus

### Reset everything

```bash
docker-compose down -v
docker-compose up -d
```

## Production Considerations

For production deployments:

1. **Use Temporal Cloud** instead of self-hosted
2. **External PostgreSQL** with proper backups
3. **Proper TLS** for all connections
4. **Resource limits** on containers
5. **Persistent volumes** with backups
6. **Alerting** via Prometheus Alertmanager

See the [Temporal deployment guide](https://docs.temporal.io/self-hosted-guide) for more details.
