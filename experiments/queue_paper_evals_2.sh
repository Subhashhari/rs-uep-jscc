#!/usr/bin/env bash
# Second CPU queue: waits for queue_paper_evals.sh, then the burst study and the no-RS (24-channel) models.
# The no-RS checkpoints come from the Kaggle nors2_* jobs; the queue waits until they are placed in results/nors2.
set -u
cd "$(dirname "$0")/.."
PY=.venv/Scripts/python
[ -x "$PY" ] || PY=python
mkdir -p results/queue
until grep -q "queue done" results/queue/queue.log 2>/dev/null; do sleep 60; done

if [ ! -f results/coding/burst_seed42/burst_truncation.json ]; then
  echo "$(date +%T) start burst"
  $PY -m experiments.eval_burst_truncation --checkpoint results/gpu/models/seed42/best_val.pth \
      --oracle_ranking_file results/gpu/models/seed42/oracle_ranking.json \
      --allocations results/coding/seed42/allocations.json --threads 14 \
      --output_dir results/coding/burst_seed42 > results/queue/burst.log 2>&1
  echo "$(date +%T) end burst (exit $?)"
fi

until [ -f results/nors2/READY ]; do sleep 60; done
run() {  # name checkpoint ranking sources
  local out=results/coding/trunc/$1
  [ -f "$out/truncation.json" ] && { echo "skip $1"; return; }
  echo "$(date +%T) start $1"
  $PY -m experiments.eval_truncation --checkpoint "$2" --oracle_ranking_file "$3" --sources "$4" --threads 14 \
      --output_dir "$out" > "results/queue/$1.log" 2>&1
  echo "$(date +%T) end $1 (exit $?)"
}
while read -r name ckpt rank sources; do
  [ -f "$ckpt" ] && run "$name" "$ckpt" "$rank" "$sources"
done < results/nors2/READY
echo "$(date +%T) queue2 done"
