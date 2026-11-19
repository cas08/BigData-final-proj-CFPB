#!/usr/bin/env bash
# Крок 10. Експеримент CSV проти Parquet на повному датасеті.
# Одна зміна: --format csv | parquet. Решта (код, конфіг, local[4], driver 2g) однакова.
# 1 прогрівальний запуск кожного варіанта (не рахується), далі 3 + 3 почергово, щоб кеш ОС не грав на користь одного.
# Запуск з каталогу проєкту:  DATA_DIR=./data bash scripts/10_experiment.sh
set -euo pipefail
: "${DATA_DIR:?задайте DATA_DIR - каталог з complaints.csv і complaints_parquet}"

run() {  # $1 = формат, $2 = тег
  local input=/data/complaints.csv
  [ "$1" = parquet ] && input=/data/complaints_parquet
  echo "=== $2 ($(date +%H:%M:%S)) ==="
  docker compose run --rm -T job spark-submit scripts/05_job.py --input "$input" --format "$1" --tag "$2" \
    2>&1 | grep -E "пар, у рейтингу" || true
}

run csv exp-warmup-csv
run parquet exp-warmup-parquet
for i in 1 2 3; do
  run csv "exp-csv-$i"
  run parquet "exp-parquet-$i"
done

python3 scripts/07_stage_metrics.py --app-prefix final-05-exp- --summary --out out/10_experiment_runs.md
