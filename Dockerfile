# Use official Python image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy all files
COPY . .

# Install dependencies
RUN pip install --no-cache-dir openenv-core uvicorn requests pydantic

# Expose port
EXPOSE 8000

# Start server
CMD ["python", "-m", "server.app"]