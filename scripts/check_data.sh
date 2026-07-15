set -eux

echo "=== HOST VIEW ==="
echo "HOST PWD=$(pwd)"
ls -l ./data || true
ls -l ./data/ready || true
