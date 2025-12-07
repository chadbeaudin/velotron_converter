# Docker Deployment for Unraid

This guide explains how to run the Velotron Converter as a Docker container on Unraid.

## Quick Start (Unraid Community Applications)

### Option 1: Docker Compose (Recommended)

1. **Install Docker Compose Plugin** (if not already installed):
   - In Unraid, go to Apps → Search for "Docker Compose Manager"
   - Install the plugin

2. **Create the Stack**:
   - Navigate to Docker → Compose
   - Click "Add New Stack"
   - Name it "velotron-converter"
   - Copy the contents of `docker-compose.yml` into the editor
   - Update the volume path to your Unraid share:
     ```yaml
     volumes:
       - /mnt/user/appdata/velotron:/data
     ```
   - Click "Compose Up"

### Option 2: Unraid Docker Template

1. **Build the Docker Image**:
   ```bash
   cd /mnt/user/appdata/velotron-converter
   docker build -t velotron-converter .
   ```

2. **Add Container in Unraid UI**:
   - Go to Docker → Add Container
   - **Name**: `velotron-converter`
   - **Repository**: `velotron-converter:latest`
   - **Network Type**: `bridge`
   - **Add Path**:
     - Container Path: `/data`
     - Host Path: `/mnt/user/appdata/velotron`
     - Access Mode: `Read/Write`
   - **Add Variable**:
     - Key: `TZ`
     - Value: `America/Denver` (or your timezone)
   - Click "Apply"

## Directory Structure on Unraid

Once running, you'll have these directories in your mapped path:

```
/mnt/user/appdata/velotron/
├── original/     # Drop PWX files here
├── converted/    # Get TCX/FIT files here
├── processed/    # Archived PWX files
└── failed/       # Failed conversions
```

## Usage

1. **Drop PWX files** into `/mnt/user/appdata/velotron/original/`
2. **Retrieve converted files** from `/mnt/user/appdata/velotron/converted/`
3. **Monitor logs**: `docker logs -f velotron-converter`

## Updating the Container

```bash
cd /mnt/user/appdata/velotron-converter
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

## Troubleshooting

**Check if container is running:**
```bash
docker ps | grep velotron
```

**View logs:**
```bash
docker logs velotron-converter
```

**Restart container:**
```bash
docker restart velotron-converter
```

**Access container shell:**
```bash
docker exec -it velotron-converter /bin/bash
```

## Unraid Share Integration

For automatic file handling, you can:

1. **Map to Dropbox/Cloud Share**:
   - Set host path to your cloud sync folder
   - Files will auto-convert when synced

2. **Use Unraid User Scripts**:
   - Create a script to copy files from your bike computer
   - Schedule it to run automatically

3. **SMB/NFS Access**:
   - Access the `original/` folder from your local network
   - Drop files directly from any device
