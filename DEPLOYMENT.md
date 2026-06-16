# Deployment Guide

## 🐳 Docker Deployment

### Quick Start with Docker Compose

1. **Prepare environment:**

```bash
cd summary\ pro
cp backend/.env.example backend/.env
# Edit backend/.env and add your GOOGLE_API_KEY
```

2. **Build and run:**

```bash
docker-compose up -d
```

3. **Check status:**

```bash
docker-compose ps
docker-compose logs -f
```

4. **Access:**

- Frontend: http://localhost:5173
- Backend: http://localhost:8000
- API Docs: http://localhost:8000/docs

### Stopping

```bash
docker-compose down
```

### Rebuild images

```bash
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

## 🖥️ Production Deployment

### Heroku Deployment

1. **Install Heroku CLI:**

```bash
npm install -g heroku
heroku login
```

2. **Create app:**

```bash
heroku create your-app-name
```

3. **Set environment variables:**

```bash
heroku config:set GOOGLE_API_KEY=your_key
```

4. **Create Procfile in root:**

```
web: cd backend && gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app --bind 0.0.0.0:$PORT
```

5. **Deploy:**

```bash
git push heroku main
```

### AWS Deployment

#### Using EC2 + Docker

1. **Launch EC2 instance (Ubuntu 22.04)**

2. **Install Docker:**

```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker ubuntu
```

3. **Clone repository:**

```bash
git clone <repo-url>
cd summary\ pro
cp backend/.env.example backend/.env
# Edit .env with your configuration
```

4. **Run with Docker Compose:**

```bash
docker-compose up -d
```

5. **Setup reverse proxy (Nginx):**

```bash
sudo apt-get install nginx
```

Create `/etc/nginx/sites-available/default`:

```nginx
upstream backend {
    server 127.0.0.1:8000;
}

upstream frontend {
    server 127.0.0.1:5173;
}

server {
    listen 80 default_server;
    listen [::]:80 default_server;

    server_name _;

    location /api {
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location / {
        proxy_pass http://frontend;
        proxy_set_header Host $host;
    }
}
```

```bash
sudo nginx -t
sudo systemctl restart nginx
```

### DigitalOcean App Platform

1. **Push to GitHub**

2. **Connect in DigitalOcean App Platform:**
   - Create new app
   - Connect GitHub repo
   - Configure components:
     - Backend: `docker-compose` service
     - Frontend: `docker-compose` service

3. **Set environment variables in UI**

## 🔒 Security for Production

### 1. Update CORS settings

```env
# In backend/.env
CORS_ORIGINS=https://yourdomain.com
```

### 2. Use HTTPS

- Install SSL certificate (Let's Encrypt)
- Update nginx config with SSL

### 3. Rate limiting

```env
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_PERIOD=60
```

### 4. Secure API Key storage

- Never commit `.env` files
- Use environment-specific vaults
- Rotate API keys regularly

## 📊 Monitoring & Logging

### View logs

```bash
docker-compose logs -f backend
docker-compose logs -f frontend
```

### Check health

```bash
curl http://localhost:8000/health
curl http://localhost:8000/api/status
```

## 🔄 Backup & Restore

### Backup data

```bash
cp -r backend/data backend/data.backup.$(date +%Y%m%d)
docker-compose exec backend tar -czf /tmp/data.tar.gz ./data
docker cp <container-id>:/tmp/data.tar.gz ./data.backup.tar.gz
```

### Restore data

```bash
docker-compose exec backend rm -rf ./data
docker cp ./data.backup.tar.gz <container-id>:/tmp/
docker-compose exec backend tar -xzf /tmp/data.backup.tar.gz
```

## 📈 Scaling

### Multiple backend instances

Use Docker Swarm or Kubernetes:

```yaml
# docker-compose.prod.yml
version: "3.8"

services:
  backend:
    build: .
    deploy:
      replicas: 3
    # ... rest of config
```

### Load balancing

- Use Nginx/HAProxy in front
- Distribute requests across instances
- Use shared volume for data

## 🆘 Troubleshooting

### Port already in use

```bash
# Find what's using port 8000
lsof -i :8000
# Kill process
kill -9 <PID>
```

### Out of memory

- Reduce `CHUNK_SIZE`
- Use lighter embeddings model
- Increase server RAM

### Slow responses

- Increase `LLM_MAX_TOKENS`
- Check network connectivity
- Monitor API rate limits

### Database issues

```bash
# Clear and reinitialize
docker-compose down -v
docker-compose up -d
```
