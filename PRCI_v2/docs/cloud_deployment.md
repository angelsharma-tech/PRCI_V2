# PRCI v2 Cloud Deployment Plan

## Overview

This document outlines the strategy for deploying PRCI v2 to cloud environments, covering containerization, orchestration, CI/CD, monitoring, and scaling strategies.

## Deployment Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Client Layer                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │   Web App    │  │ Mobile App  │  │   Streamlit UI      │  │
│  │  (React/Vue) │  │  (Flutter)  │  │  (Internal Tools)   │  │
│  └──────┬──────┘  └──────┬──────┘  └──────────┬──────────┘  │
│         └──────────────────┴─────────────────────┘             │
│                    Cloudflare / AWS CloudFront                    │
└─────────────────────────────────────────────────────────────────┘
                          │
┌─────────────────────────┼──────────────────────────────────────┐
│                         ▼                                      │
│                   Load Balancer (ALB/NLB)                       │
│              SSL Termination / Health Checks                   │
└─────────────────────────┬──────────────────────────────────────┘
                          │
┌─────────────────────────┼──────────────────────────────────────┐
│                         ▼                                      │
│              Kubernetes Cluster (EKS / GKE / AKS)              │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                   Ingress Controller                       │  │
│  │              (nginx-ingress / traefik)                   │  │
│  └──────────────────────────────────────────────────────────┘  │
│                          │                                      │
│  ┌───────────────────────┼───────────────────────────────────┐│
│  │                   API Pods (FastAPI)                         ││
│  │  ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐       ││
│  │  │Pod 1│ │Pod 2│ │Pod 3│ │Pod 4│ │Pod 5│ │Pod 6│       ││
│  │  └─────┘ └─────┘ └─────┘ └─────┘ └─────┘ └─────┘       ││
│  │         Horizontal Pod Autoscaler (HPA)                  ││
│  │         Min: 3, Max: 20, Target CPU: 70%                 ││
│  └──────────────────────────────────────────────────────────┘│
│                          │                                      │
│  ┌───────────────────────┼───────────────────────────────────┐│
│  │              Background Workers (Celery)                     ││
│  │  ┌─────┐ ┌─────┐ ┌─────┐                                  ││
│  │  │Worker│ │Worker│ │Worker│   Redis/RabbitMQ Queue      ││
│  │  └─────┘ └─────┘ └─────┘                                  ││
│  │         Tasks: Reports, Emails, Analytics                  ││
│  └──────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
                          │
┌─────────────────────────┼──────────────────────────────────────┐
│                         ▼                                      │
│                    Data Layer                                   │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────┐ │
│  │   PostgreSQL     │  │      Redis       │  │   S3/MinIO   │ │
│  │   (Primary DB)   │  │   (Cache/Queue)  │  │  (File Store)│ │
│  │   RDS/Cloud SQL  │  │   ElastiCache    │  │              │ │
│  └──────────────────┘  └──────────────────┘  └──────────────┘ │
│  ┌──────────────────┐  ┌──────────────────┐                    │
│  │  Read Replica    │  │   Elasticsearch  │                   │
│  │  (Analytics)     │  │   (Search/Logs)  │                   │
│  └──────────────────┘  └──────────────────┘                    │
└─────────────────────────────────────────────────────────────────┘
                          │
┌─────────────────────────┼──────────────────────────────────────┐
│                    Monitoring & Observability                    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐ │
│  │  Prometheus  │  │    Grafana   │  │   ELK Stack / Loki   │ │
│  │  (Metrics)   │  │Dashboards    │  │   (Logs)            │ │
│  └──────────────┘  └──────────────┘  └──────────────────────┘ │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐ │
│  │    Sentry    │  │DataDog/Cloud │  │    PagerDuty         │ │
│  │  (Errors)    │  │   Watch      │  │   (Alerts)          │ │
│  └──────────────┘  └──────────────┘  └──────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

## Containerization

### Dockerfile
```dockerfile
# Multi-stage build for production optimization
FROM python:3.11-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Production stage
FROM python:3.11-slim

WORKDIR /app

# Copy dependencies from builder
COPY --from=builder /root/.local /root/.local

# Copy application code
COPY . .

# Make sure scripts are executable
ENV PATH=/root/.local/bin:$PATH

# Non-root user for security
RUN groupadd -r prci && useradd -r -g prci prci
RUN chown -R prci:prci /app
USER prci

# Environment
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health/live')"

EXPOSE 8000

# Start application
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

### docker-compose.yml (Development)
```yaml
version: '3.8'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://prci:password@db:5432/prci_v2
      - REDIS_URL=redis://redis:6379
      - SECRET_KEY=dev-secret-key
    depends_on:
      - db
      - redis
    volumes:
      - .:/app
    command: uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload

  db:
    image: postgres:15-alpine
    environment:
      - POSTGRES_USER=prci
      - POSTGRES_PASSWORD=password
      - POSTGRES_DB=prci_v2
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  celery_worker:
    build: .
    command: celery -A tasks worker --loglevel=info
    environment:
      - DATABASE_URL=postgresql://prci:password@db:5432/prci_v2
      - REDIS_URL=redis://redis:6379
    depends_on:
      - db
      - redis

volumes:
  postgres_data:
```

## Kubernetes Deployment

### Namespace and Config
```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: prci-v2
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: prci-config
  namespace: prci-v2
data:
  DATABASE_URL: "postgresql://..."
  REDIS_URL: "redis://..."
  LOG_LEVEL: "INFO"
---
apiVersion: v1
kind: Secret
metadata:
  name: prci-secrets
  namespace: prci-v2
type: Opaque
stringData:
  SECRET_KEY: "production-secret-key"
  SMTP_PASSWORD: "..."
```

### Deployment
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: prci-api
  namespace: prci-v2
spec:
  replicas: 3
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  selector:
    matchLabels:
      app: prci-api
  template:
    metadata:
      labels:
        app: prci-api
    spec:
      containers:
      - name: api
        image: registry/prci-v2:latest
        ports:
        - containerPort: 8000
        envFrom:
        - configMapRef:
            name: prci-config
        envFrom:
        - secretRef:
            name: prci-secrets
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /health/live
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health/ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
```

### Service and Ingress
```yaml
apiVersion: v1
kind: Service
metadata:
  name: prci-api-service
  namespace: prci-v2
spec:
  selector:
    app: prci-api
  ports:
  - port: 80
    targetPort: 8000
  type: ClusterIP
---
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: prci-ingress
  namespace: prci-v2
  annotations:
    kubernetes.io/ingress.class: nginx
    cert-manager.io/cluster-issuer: letsencrypt
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
spec:
  tls:
  - hosts:
    - api.prci.ai
    secretName: prci-tls
  rules:
  - host: api.prci.ai
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: prci-api-service
            port:
              number: 80
```

### HPA (Horizontal Pod Autoscaler)
```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: prci-api-hpa
  namespace: prci-v2
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: prci-api
  minReplicas: 3
  maxReplicas: 20
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
  behavior:
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
      - type: Percent
        value: 50
        periodSeconds: 60
```

## CI/CD Pipeline

### GitHub Actions Workflow
```yaml
name: CI/CD Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install -r requirements-test.txt
    
    - name: Run tests
      run: pytest --cov=prci --cov-report=xml
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3

  build:
    needs: test
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Build Docker image
      run: |
        docker build -t prci-v2:${{ github.sha }} .
        docker tag prci-v2:${{ github.sha }} prci-v2:latest
    
    - name: Push to registry
      run: |
        echo ${{ secrets.REGISTRY_PASSWORD }} | docker login -u ${{ secrets.REGISTRY_USERNAME }} --password-stdin
        docker push prci-v2:${{ github.sha }}
        docker push prci-v2:latest

  deploy:
    needs: build
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Deploy to Kubernetes
      run: |
        kubectl set image deployment/prci-api api=prci-v2:${{ github.sha }} -n prci-v2
        kubectl rollout status deployment/prci-api -n prci-v2
```

## Cloud Provider Specifics

### AWS Deployment
- **EKS**: Managed Kubernetes
- **RDS PostgreSQL**: Managed database with Multi-AZ
- **ElastiCache Redis**: Managed cache
- **S3**: File storage for reports
- **CloudFront**: CDN for static assets
- **ALB**: Application Load Balancer
- **Route 53**: DNS management
- **CloudWatch**: Monitoring and logging
- **Secrets Manager**: Secure secret storage

### GCP Deployment
- **GKE**: Google Kubernetes Engine
- **Cloud SQL**: Managed PostgreSQL
- **Memorystore**: Managed Redis
- **Cloud Storage**: File storage
- **Cloud CDN**: Content delivery
- **Cloud Load Balancing**: Global load balancer
- **Cloud DNS**: DNS management
- **Cloud Monitoring**: Monitoring and logging
- **Secret Manager**: Secure secret storage

### Azure Deployment
- **AKS**: Azure Kubernetes Service
- **Azure Database for PostgreSQL**: Managed database
- **Azure Cache for Redis**: Managed cache
- **Azure Blob Storage**: File storage
- **Azure CDN**: Content delivery
- **Application Gateway**: Load balancer
- **Azure DNS**: DNS management
- **Azure Monitor**: Monitoring and logging
- **Azure Key Vault**: Secret storage

## Database Migration Strategy

### Zero-Downtime Migrations
1. **Schema Changes**: Add new columns/tables first
2. **Dual Write**: Write to both old and new schema
3. **Backfill**: Migrate existing data
4. **Switch Read**: Point reads to new schema
5. **Cleanup**: Remove old columns/tables

### Migration Tooling
```bash
# Alembic migrations
alembic revision --autogenerate -m "migration_name"
alembic upgrade head

# Pre-deployment validation
python -m scripts.validate_migrations

# Database backup before migration
pg_dump -Fc prci_v2 > backup_$(date +%Y%m%d_%H%M%S).dump
```

## Scaling Strategy

### Horizontal Scaling
- **API Layer**: Auto-scale pods based on CPU/memory/RPS
- **Database**: Read replicas for read-heavy workloads
- **Cache**: Redis Cluster for distributed caching
- **Queue**: Celery workers scale based on queue depth

### Vertical Scaling
- **API Pods**: Increase CPU/memory for compute-intensive tasks
- **Database**: Scale up instance size for complex queries
- **Cache**: Larger Redis instances for more data

### Database Sharding (Future)
- Shard by user_id for user data
- Shard by date for time-series data (assessments, reports)

## Backup and Disaster Recovery

### Backup Strategy
- **Database**: Daily automated backups, 30-day retention
- **Files**: S3 versioning, cross-region replication
- **Configuration**: Infrastructure as Code (Terraform) in Git

### Disaster Recovery
- **RTO (Recovery Time Objective)**: 1 hour
- **RPO (Recovery Point Objective)**: 15 minutes
- **Multi-Region**: Standby in secondary region
- **Runbook**: Documented procedures for common scenarios

## Security in Production

### Network Security
- **VPC**: Private subnets for database and cache
- **Security Groups**: Restrict traffic between services
- **WAF**: Web Application Firewall for DDoS protection
- **DDoS Protection**: Cloudflare or AWS Shield

### Data Security
- **Encryption at Rest**: Database encryption, S3 SSE
- **Encryption in Transit**: TLS 1.3 for all communications
- **Secrets Management**: Kubernetes secrets, cloud secret managers
- **Key Rotation**: Automatic key rotation every 90 days

### Compliance
- **HIPAA**: If handling PHI (future consideration)
- **GDPR**: Data deletion, right to be forgotten
- **SOC 2**: Security controls and audit trail
- **Penetration Testing**: Annual security audits

## Cost Optimization

### Resource Optimization
- **Spot Instances**: Use spot instances for non-critical workloads
- **Reserved Capacity**: Reserve instances for predictable workloads
- **Auto-shutdown**: Scale to zero during low-traffic periods
- **Right-sizing**: Regular resource usage review

### Cost Monitoring
- **Budget Alerts**: Cloud spend alerts at 80%, 100%
- **Resource Tagging**: Track costs by service/environment
- **Usage Analytics**: Identify and optimize expensive queries

## Monitoring and Alerting

### Metrics
- **Application**: Request rate, latency, error rate
- **Database**: Query time, connection pool, replication lag
- **Infrastructure**: CPU, memory, disk I/O, network
- **Business**: Active users, assessments, reports generated

### Alerts
- **Critical**: Database down, 5xx errors, high latency
- **Warning**: High CPU, slow queries, low disk space
- **Info**: Deployments, scaling events, backup completion

### Dashboards
- **Operations**: System health, error rates, performance
- **Business**: User growth, engagement, conversion
- **Security**: Login attempts, suspicious activity

## Deployment Checklist

### Pre-Deployment
- [ ] All tests passing
- [ ] Security scan completed
- [ ] Database migrations tested
- [ ] Performance benchmarks met
- [ ] Documentation updated

### Deployment
- [ ] Blue-green or canary deployment
- [ ] Health checks passing
- [ ] Smoke tests completed
- [ ] Monitoring confirmed
- [ ] Rollback plan ready

### Post-Deployment
- [ ] Error rates normal
- [ ] Latency within SLA
- [ ] User reports verified
- [ ] Metrics dashboards reviewed
- [ ] Incident response on standby

## Future Enhancements

### Multi-Region Deployment
- Active-active for global users
- Data residency compliance
- Edge computing for ML inference

### Serverless Options
- AWS Lambda for async tasks
- Cloud Functions for webhooks
- Fargate for variable workloads

### Edge Computing
- Cloudflare Workers for API edge caching
- TensorFlow.js for client-side inference
- CDN-optimized static assets

### AI/ML Infrastructure
- GPU nodes for model training
- Model serving with KServe
- Feature store for ML features
