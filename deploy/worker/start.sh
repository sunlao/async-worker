#!/bin/sh
set -u

SERVICE="${APP_CODE}-api" uvicorn src.api.main:api \
    --host 0.0.0.0 \
    --port "$API_PORT" \
    --reload &
api_pid=$!

SERVICE="${APP_CODE}-worker" taskiq worker worker:queue \
    --workers "$TASKIQ_WORKERS" \
    --max-async-tasks "$TASKIQ_MAX_ASYNC_TASKS" \
    --max-prefetch "$TASKIQ_MAX_PREFETCH" \
    --ack-type "$ACK_TYPE" \
    --reload &
worker_pid=$!

shutdown() {
    trap - TERM INT EXIT
    kill -TERM "$api_pid" "$worker_pid" 2>/dev/null || true
    wait "$api_pid" 2>/dev/null || true
    wait "$worker_pid" 2>/dev/null || true
}

trap shutdown TERM INT EXIT

while kill -0 "$api_pid" 2>/dev/null &&
      kill -0 "$worker_pid" 2>/dev/null; do
    sleep 1
done

exit 1