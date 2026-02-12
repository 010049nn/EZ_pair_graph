# EZ_pair_graph - Python-based visualization pipeline
FROM python:3.11-slim

# Install system dependencies for matplotlib
RUN apt-get update && apt-get install -y --no-install-recommends \
    libfreetype6-dev \
    libpng-dev \
    libjpeg-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Install Python packages
RUN pip install --no-cache-dir \
    numpy \
    pandas \
    matplotlib \
    scipy

# Set working directory
WORKDIR /app

# Copy all files from the repository
COPY . /app/

# Make shell script executable
RUN chmod +x pipeline_for_EZ_plot.sh

# Create output directory
RUN mkdir -p /app/output_EZ

# Default command
CMD ["/bin/bash"]
