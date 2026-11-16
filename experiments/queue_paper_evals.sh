#!/usr/bin/env bash
# Sequential CPU evaluation queue behind the paper's multi-model tables (run detached; survives a closed
# terminal). Waits for any running coding_controls test stage, then runs every truncation evaluation that
# is not finished yet. Logs: results/queue/<name>.log; a finished run leaves <output_dir>/truncation.json.
#     nohup bash experiments/queue_paper_evals.sh > results/queue/queue.log 2>&1 &
set -u
cd "$(dirname "$0")/.."
PY=.venv/Scripts/python
[ -x "$PY" ] || PY=python
mkdir -p results/queue

# Let the seed-42 coding-controls test stage (started separately) finish first: it needs the CPU.
until [ -f results/coding/seed42/coding_controls_test.json ] || grep -q "Traceback" results/coding_seed42_test.err 2>/dev/null; do
  sleep 60
done

run() {  # name checkpoint ranking sources [extra args...]
  local name=$1 ckpt=$2 rank=$3 sources=$4; shift 4
  local out=results/coding/trunc/$name
  if [ -f "$out/truncation.json" ]; then echo "skip $name"; return; fi
  echo "$(date +%T) start $name"
  $PY -m experiments.eval_truncation --checkpoint "$ckpt" --oracle_ranking_file "$rank" --sources "$sources" \
      --threads 14 --output_dir "$out" "$@" > "results/queue/$name.log" 2>&1
  echo "$(date +%T) end $name (exit $?)"
}

# ADJSCC-Q model seeds (published GPU family; seed 2024 did not converge)
for s in 42 100 7 13 21; do
  run "adjsccq_seed$s" "results/gpu/models/seed$s/best_val.pth" "results/gpu/models/seed$s/oracle_ranking.json" \
      "static:oracle,energy,random,attention"
done
# DeepJSCC-Q on the same hardware (T4); seeds 42 and 13 did not converge but are evaluated and labelled
for s in 100 7 21 42 13; do
  run "deepjsccq_seed$s" "results/g1t4/models/deepjsccq_seed$s/best_val.pth" \
      "results/g1t4/models/deepjsccq_seed$s/oracle_ranking.json" "static:oracle,energy,random"
done
# ordered (tail-drop) models: also rank by channel index
run adjsccq_td05 results/ordered/adjsccq_seed42_td05/best_val.pth results/ordered/adjsccq_seed42_td05/oracle_ranking.json \
    "static:oracle,energy,random,attention" --index_order
run deepjsccq_td05 results/ordered/deepjsccq_seed42_td05/best_val.pth results/ordered/deepjsccq_seed42_td05/oracle_ranking.json \
    "static:oracle,energy,random" --index_order
# erasure-fine-tuned 1,024-byte model + RS
run adjsccq_kn16_robust results/nors/adjsccq_kn16_seed42_robust/adjsccq_erasure_robust.pth \
    results/nors/adjsccq_kn16_seed42_robust/oracle_ranking.json "static:oracle,energy,random"
echo "$(date +%T) queue done"
