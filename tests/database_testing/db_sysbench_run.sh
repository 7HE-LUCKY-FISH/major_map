#!/bin/bash

set -e
source ./db_sysbench.env

mkdir -p ../../docs/evaluation/database_results

echo "Running Sysbench Load Test on AWS RDS..."

sysbench oltp_read_only \
  --db-driver=mysql \
  --mysql-host=$DB_HOST \
  --mysql-port=$DB_PORT \
  --mysql-db=$DB_NAME \
  --mysql-user=$DB_USER \
  --mysql-password=$DB_PASS \
  --mysql-ssl-ca=global-bundle.pem \
  --tables=$TABLES \
  --table-size=$TABLE_SIZE \
  --threads=$THREADS \
  --time=$TIME \
  --report-interval=$REPORT_INTERVAL \
  run | tee ../../docs/evaluation/sysbench-results.txt

echo "Results saved to docs/evaluation/sysbench-results.txt"