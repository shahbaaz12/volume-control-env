# Use official Python image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy all files
COPY . .

# Install dependencies
RUN pip install --no-cache-dir "openenv-core[core]>=0.2.2" uvicorn requests pydantic openai

# Expose port
EXPOSE 8000

# Start server
CMD ["python", "-m", "server.app"]
