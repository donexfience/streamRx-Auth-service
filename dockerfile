# Use the official Python image from Docker Hub
FROM python:3.11-slim AS base

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PATH="/app/.venv/bin:$PATH"

# Create a working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt /app/
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Copy the application code into the container
COPY . /app/

# Build stage for AWS Lambda
FROM ubuntu:22.04 AS lambda
ARG DEBIAN_FRONTEND=noninteractive
WORKDIR /

# Install Python and required packages
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    python3 \
    python3-pip \
    python3-dev && \
    rm -rf /var/lib/apt/lists/*

# Copy the application code and dependencies
COPY --from=base /app /app
COPY requirements.txt /

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade -r /requirements.txt

# Copy the Lambda entry script
COPY lambda_entry_script.sh /
RUN chmod +x /lambda_entry_script.sh

# Set the entry point for the Lambda function
ENTRYPOINT ["/lambda_entry_script.sh", "main.handler"]

# Build stage for FastAPI app
FROM base AS fastapi
# Expose the port the app runs on
EXPOSE 8000

# Command to run the FastAPI app with Uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]