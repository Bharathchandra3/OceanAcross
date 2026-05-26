# 🐳 DOCKER DEPLOYMENT GUIDE

## Your Docker Setup

**Docker Hub Username**: `praveenkumar257`
**Image Name**: `praveenkumar257/conversation-evaluator:latest`

---

## 📋 Prerequisites

1. **Docker Installed** - [Download Docker Desktop](https://www.docker.com/products/docker-desktop)
2. **Docker Hub Account** - You have: `praveenkumar257`
3. **Docker Logged In** - Run: `docker login`

---

## 🚀 Option 1: Build & Push to Docker Hub (Recommended for Production)

### Step 1: Build the Image
```bash
cd c:\Users\prave\Downloads\OceanAcross
docker build -t praveenkumar257/conversation-evaluator:latest .
```

### Step 2: Push to Docker Hub
```bash
docker push praveenkumar257/conversation-evaluator:latest
```

### Step 3: Run from Docker Hub
```bash
# Just run docker-compose, it will pull your image
docker-compose up
```

---

## 🚀 Option 2: Run Locally (Without Pushing)

### Direct Docker Build
```bash
docker build -t conversation-evaluator:local .
docker run -p 8501:8501 -p 8000:8000 conversation-evaluator:local
```

### Or Use Docker Compose (Local)
```bash
docker-compose up
```

---

## 📊 What Gets Deployed

### Services
| Service | Port | Purpose |
|---------|------|---------|
| API | 8000 | FastAPI backend (REST endpoints) |
| UI | 8501 | Streamlit web interface |
| Ollama | 11434 | LLM backend (optional) |

### Volumes
- `./data:/app/data` - Facets and conversations
- `./output:/app/output` - Evaluation results
- `ollama-data:/root/.ollama` - Ollama models

---

## ✅ Verify Deployment

### Check Services Running
```bash
docker-compose ps
```

Expected output:
```
NAME                            STATUS          PORTS
conversation-evaluator-api      Up              0.0.0.0:8000->8000/tcp
conversation-evaluator-ui       Up              0.0.0.0:8501->8501/tcp
ollama-service                  Up              0.0.0.0:11434->11434/tcp
```

### Test API
```bash
curl http://localhost:8000/health
# Should return: {"status": "healthy"}
```

### Access UI
Open browser to: http://localhost:8501

### Check Logs
```bash
docker-compose logs -f api
docker-compose logs -f ui
docker-compose logs -f ollama
```

---

## 🔧 Common Commands

### Start Services
```bash
docker-compose up
# Or in background:
docker-compose up -d
```

### Stop Services
```bash
docker-compose down
```

### Rebuild After Changes
```bash
docker-compose down
docker build -t praveenkumar257/conversation-evaluator:latest .
docker-compose up
```

### View Logs
```bash
# All services
docker-compose logs

# Specific service
docker-compose logs api
docker-compose logs ui

# Follow logs (live)
docker-compose logs -f api
```

### Execute Commands in Container
```bash
# Run pipeline
docker-compose exec api python run_pipeline.py

# Access shell
docker-compose exec api /bin/bash

# Check Python version
docker-compose exec api python --version
```

---

## 🔐 Environment Variables

Located in `docker-compose.yml`:

```yaml
environment:
  - API_HOST=0.0.0.0
  - API_PORT=8000
  - DEBUG=false
  - PYTHONUNBUFFERED=1
  - STREAMLIT_SERVER_PORT=8501
  - STREAMLIT_SERVER_ADDRESS=0.0.0.0
```

To modify, edit `docker-compose.yml` and restart:
```bash
docker-compose restart
```

---

## 🐳 Using Your Docker Hub Image

### Push New Version
```bash
# Build
docker build -t praveenkumar257/conversation-evaluator:v1.0 .

# Push
docker push praveenkumar257/conversation-evaluator:v1.0

# Update docker-compose.yml image tag
```

### Pull and Run Elsewhere
```bash
# On another machine
docker pull praveenkumar257/conversation-evaluator:latest
docker run -p 8501:8501 -p 8000:8000 praveenkumar257/conversation-evaluator:latest
```

---

## 🐳 Docker Best Practices

### 1. Tag Versions
```bash
docker build -t praveenkumar257/conversation-evaluator:latest .
docker build -t praveenkumar257/conversation-evaluator:v1.0 .
docker push praveenkumar257/conversation-evaluator:latest
docker push praveenkumar257/conversation-evaluator:v1.0
```

### 2. Use .dockerignore
Create `.dockerignore`:
```
__pycache__
*.pyc
.pytest_cache
.git
.gitignore
README.md
*.md
.env.example
```

### 3. Optimize Image Size
- Use `python:3.11-slim` (not `python:3.11`)
- Remove dev dependencies in production
- Clean package cache

---

## 🎯 Production Deployment Steps

### Step 1: Build Image
```bash
docker build -t praveenkumar257/conversation-evaluator:latest .
```

### Step 2: Test Locally
```bash
docker-compose up
# Test at http://localhost:8501
```

### Step 3: Push to Docker Hub
```bash
docker push praveenkumar257/conversation-evaluator:latest
```

### Step 4: Deploy on Server
```bash
# On production server
docker pull praveenkumar257/conversation-evaluator:latest
docker-compose up -d
```

### Step 5: Monitor
```bash
docker-compose logs -f
docker-compose ps
```

---

## 🚨 Troubleshooting

### Image Won't Build
```bash
# Clear cache and rebuild
docker system prune -a
docker build --no-cache -t praveenkumar257/conversation-evaluator:latest .
```

### Port Already in Use
```bash
# Change ports in docker-compose.yml
# Or kill existing process:
docker-compose down
docker ps  # Check for lingering containers
docker-compose up
```

### Out of Disk Space
```bash
docker system prune --all --volumes
docker image prune --all
```

### Container Exits Immediately
```bash
# Check logs
docker-compose logs api
docker-compose logs ui

# Run interactively to debug
docker-compose exec api /bin/bash
```

---

## 📈 Scaling Considerations

### Multiple Instances
```bash
# Run multiple API instances
docker-compose up --scale api=3
```

### Memory Limits
Edit `docker-compose.yml`:
```yaml
services:
  api:
    deploy:
      resources:
        limits:
          cpus: '1'
          memory: 1G
```

### Persistent Storage
Data volumes are already configured:
```yaml
volumes:
  - ./data:/app/data
  - ./output:/app/output
```

---

## 🔐 Security Best Practices

1. **Never commit secrets** - Use `.env` files
2. **Use specific image versions** - Not `latest` in production
3. **Regular updates** - Keep base image updated
4. **Scan images** - Use `docker scan`
5. **Minimal permissions** - Run as non-root if possible

---

## 📚 Quick Reference

| Command | Purpose |
|---------|---------|
| `docker build -t name:tag .` | Build image |
| `docker push name:tag` | Push to registry |
| `docker-compose up` | Start all services |
| `docker-compose down` | Stop all services |
| `docker-compose logs -f` | View live logs |
| `docker-compose ps` | Show running services |
| `docker exec <container> <cmd>` | Run command in container |

---

## 🎯 Your Next Steps

1. **Build Image**
   ```bash
   docker build -t praveenkumar257/conversation-evaluator:latest .
   ```

2. **Test Locally**
   ```bash
   docker-compose up
   ```

3. **Push to Docker Hub**
   ```bash
   docker login  # If not already logged in
   docker push praveenkumar257/conversation-evaluator:latest
   ```

4. **Deploy Anywhere**
   ```bash
   docker pull praveenkumar257/conversation-evaluator:latest
   docker-compose up
   ```

---

## 🎊 You're Ready!

Your system is now:
- ✅ Containerized
- ✅ Ready for Docker Hub
- ✅ Production-deployable
- ✅ Scalable
- ✅ Easy to share

Push to Docker Hub and deploy anywhere Docker runs! 🚀

---

**Questions?** Check Docker docs: https://docs.docker.com/
