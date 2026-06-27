# Dockerfile for building Oracle Knots
FROM ubuntu:24.04 as builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    libboost-dev \
    libssl-dev \
    libevent-dev \
    libsqlite3-dev \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy source files
COPY . .

# Configure and build
RUN cmake -B build -DCMAKE_BUILD_TYPE=Release \
    && cmake --build build -j$(nproc)

# final image containing only the binaries
FROM ubuntu:24.04

RUN apt-get update && apt-get install -y \
    libevent-2.1-7t64 \
    libsqlite3-0 \
    libssl3 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /bin

COPY --from=builder /app/build/src/bitcoind .
COPY --from=builder /app/build/src/bitcoin-cli .
COPY --from=builder /app/build/src/bitcoin-tx .
COPY --from=builder /app/build/src/bitcoin-wallet .

EXPOSE 8332 8333 9332

ENTRYPOINT ["/bin/bitcoind"]
