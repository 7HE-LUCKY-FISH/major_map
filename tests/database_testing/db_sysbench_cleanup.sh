#!/bin/bash

set -e
source ./db_sysbench.env

echo "Cleaning benchmark tables..."

sysbench oltp_read_write \
  --db-driver=mysql \
  --mysql-host=$DB_HOST \
  --mysql-port=$DB_PORT \
  --mysql-db=$DB_NAME \
  --mysql-user=$DB_USER \
  --mysql-password=$DB_PASS \
  --mysql-ssl-ca=global-bundle.pem \
  --tables=$TABLES \
  cleanup

echo "Cleanup complete."