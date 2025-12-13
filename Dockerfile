FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install dependencies
RUN pip install --no-cache-dir fit_tool

# Copy converter scripts
COPY convert_pwx_to_tcx.py .
COPY convert_pwx_to_fit.py .
COPY monitor_and_convert.py .
COPY logo.png /data/logo.png

# Create directories for volume mounting
RUN mkdir -p /data/original /data/converted /data/processed /data/failed

# Set environment variable for base directory
ENV BASE_DIRECTORY=/data

# Run the monitor script
CMD ["python", "-u", "monitor_and_convert.py", "/data"]
