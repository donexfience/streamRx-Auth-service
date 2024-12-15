#!/bin/bash

# wait-for-it.sh

host="$1"
shift
cmd="$@"

until nc -z "$host" 5672; do
  echo "Waiting for RabbitMQ to be ready..."
  sleep 2
done

exec $cmd
