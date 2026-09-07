#!/usr/bin/env bash
# Oracle Knots Control Center apuntado a la cadena BLAKE2b.
#
# El build local de este repo es Knots 29.3.0, que NO entiende el fork, y ademas
# no esta compilado. Estas dos variables redirigen la GUI al nodo de produccion:
#
#   ORACLE_BITCOIN_BIN   binarios del fork, compilados CON wallet (build-wallet)
#   ORACLE_NODE_DATADIR  fija el nodo mainnet; sin esto la GUI podria engancharse
#                        al de testnet4 o al de regtest, que tambien estan vivos
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")" && pwd)"

export ORACLE_BITCOIN_BIN="${ORACLE_BITCOIN_BIN:-$HOME/experiments/blake2b-test/build-wallet/bin}"
export ORACLE_NODE_DATADIR="${ORACLE_NODE_DATADIR:-$HOME/.bitcoin}"

if [ ! -x "$ORACLE_BITCOIN_BIN/bitcoin-cli" ]; then
    echo "Error: no encuentro bitcoin-cli en $ORACLE_BITCOIN_BIN" >&2
    echo "Compila con: cmake --build build-wallet -j10" >&2
    exit 1
fi

# --serve: solo servidor web en localhost (util por SSH o tunel).
# --lan:   servidor web en 0.0.0.0 para verlo desde el iPhone en la LAN.
#          La wallet es watch-only (private_keys_enabled=false), asi que nadie en
#          la red puede gastar; pero SI expone saldo y direcciones a la LAN. Es tu
#          red de casa y sigue el patron de tus otros paneles (:7157, :8555).
case "${1:-}" in
    --serve|--lan)
        [ "$1" = "--lan" ] && HOST=0.0.0.0 || HOST=127.0.0.1
        PORT="${2:-8080}"
        LANIP="$(ip -4 addr show 2>/dev/null | grep -oP 'inet \K192\.168\.[0-9.]+' | head -1)"
        echo "Oracle Knots (watch-only) escuchando en $HOST:$PORT"
        [ "$HOST" = "0.0.0.0" ] && [ -n "$LANIP" ] && \
            echo "  Desde el iPhone (misma WiFi):  http://$LANIP:$PORT"
        echo "  (Ctrl-C para parar)"
        exec "$REPO_ROOT/gui-venv/bin/python" -c "
import sys; sys.path.insert(0, '$REPO_ROOT')
import gui  # registra las rutas @route en la app por defecto de bottle
from bottle import run
run(host='$HOST', port=$PORT, quiet=True)
"
        ;;
esac

exec "$REPO_ROOT/launch.sh"
