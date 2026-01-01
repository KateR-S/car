# Use official Python runtime as base image
FROM python:3.11-slim

# Set working directory in container
WORKDIR /app

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY .  .

# Create data directory for JSON fallback
RUN mkdir -p /app/data

# Expose Streamlit's default port
EXPOSE 8501

# Set environment variable to prevent Streamlit from opening browser
ENV STREAMLIT_SERVER_HEADLESS=true

# Health check to ensure the app is running
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8501/_stcore/health || exit 1

# Run streamlit
CMD ["streamlit", "run", "app.py", "--server.address", "0.0.0.0"]