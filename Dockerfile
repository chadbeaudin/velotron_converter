FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Add label for Unraid icon
LABEL org.opencontainers.image.icon="https://raw.githubusercontent.com/chadbeaudin/velotron_converter/refs/heads/master/logo.png"

# Install dependencies
RUN pip install --no-cache-dir fit_tool requests

# Copy converter scripts
COPY convert_pwx_to_tcx.py .
COPY convert_pwx_to_fit.py .
COPY monitor_and_convert.py .
COPY strava_uploader.py .
COPY strava_setup.py .

# Allow specifying the logo filename at build time (default: logo.png)
ARG LOGO_FILE=logo.png
# Copy the build-time-specified logo into the image
COPY ${LOGO_FILE} /usr/share/velotron/logo.png

# Set version environment variable
ARG VERSION=unknown
ENV APP_VERSION=${VERSION}

# Create directories for volume mounting
RUN mkdir -p /data/original /data/converted /data/processed /data/failed

# Set environment variable for monitor directory
ENV MONITOR_PATH=/veloMonitor
ENV PUID=99
ENV PGID=100

# Run the monitor script
# Run the monitor script
CMD ["python", "-u", "monitor_and_convert.py"]
