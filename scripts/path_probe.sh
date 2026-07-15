# --- path_probe.sh ---
set -eux

echo "=== HOST VIEW ==="
echo "HOST PWD=$(pwd)"
ls -l ./data || true
ls -l ./data/ready || true

echo "=== EFFECTIVE COMPOSE (volumes only) ==="
docker compose -f docker-compose.yml ${EXTRA_COMPOSE:+"-f $EXTRA_COMPOSE"} config \
  | awk '/services:/,0' | sed -n '/volumes:/,/networks:/p' || true

for svc in worker test; do
  if docker compose ps --services | grep -q "^${svc}$"; then
    echo "=== CONTAINER VIEW: $svc ==="
    docker compose exec -T "$svc" sh -lc '
      echo "PWD=$(pwd)"
      echo "id=$(id)"
      echo "DATA_DIR=$DATA_DIR"
      ls -ld /data || true
      ls -l /data/ready || true
    '
  fi
done
