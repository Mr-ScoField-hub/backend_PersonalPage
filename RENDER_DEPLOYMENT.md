# Render Deployment Guide

## Prerequisites
- Render account at https://render.com
- Git repository pushed to GitHub

## Deployment Steps

### 1. Connect Repository to Render
1. Go to https://dashboard.render.com
2. Click "New +" → "Web Service"
3. Connect your GitHub repository
4. Select the repository: `backend_PersonalPage`

### 2. Configure Service
- **Name**: `backend-personal-page` (or your preference)
- **Environment**: `Docker`
- **Region**: `Oregon` (or closest to you)
- **Branch**: `main`
- **Runtime**: `Docker`

### 3. Set Environment Variables
Add these in the Render dashboard:

```
FRONTEND_ORIGIN = https://your-frontend.vercel.app
PORT = 8080
```

### 4. Deploy
- Click "Create Web Service"
- Render will automatically build and deploy

## Monitoring

### Health Checks
- Service includes automatic health checks via `/health` endpoint
- Render will restart if checks fail

### Logs
- View logs in Render dashboard under "Logs"
- Check for any startup errors

## Size Optimization Results

**Before**: ~1.3GB
**After**: ~400-500MB (in Docker image)

### What was optimized:
- ✅ Removed ffmpeg (80MB+)
- ✅ Removed git dependency 
- ✅ Replaced CLIP with open-clip-torch (more efficient)
- ✅ Added .dockerignore to exclude cache files
- ✅ Pinned dependency versions
- ✅ Optimized layer caching

## Manual Deployment

If using render.yaml:
```bash
git push origin main
```

Render will automatically deploy based on the `render.yaml` configuration.

## Troubleshooting

### Model Loading Timeout
If startup takes too long:
1. Increase health check start period in Dockerfile
2. Consider using Render's Standard or higher plan

### Out of Memory
The service needs 2GB+ RAM. If on Starter plan (512MB), upgrade plan or reduce model size.

### CORS Issues
Update `FRONTEND_ORIGIN` env variable to match your frontend domain.
