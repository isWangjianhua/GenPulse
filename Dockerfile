FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
# libpq-dev is for psycopg2/asyncpg building if needed.
# curl/git often useful.
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy project definition
COPY pyproject.toml README.md README_CN.md ./

# Copy source code
COPY src ./src

# Install dependencies and the project itself
# We install with [dev] or standard. Let's do standard for prod image.
RUN pip install --no-cache-dir .

# Create a non-root user for security
RUN useradd -m -u 1000 genpulse
RUN chown -R genpulse:genpulse /app
USER genpulse

# Expose API and Flower ports
EXPOSE 8000 5555

# Default entrypoint to the CLI
ENTRYPOINT ["genpulse"]
CMD ["api"]
