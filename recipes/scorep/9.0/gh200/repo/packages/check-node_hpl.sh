#!/usr/bin/env bash

set -euo pipefail

vboost_val=1
power_val=660
thp_wrong_val=never
stat_interval=120

vboost="$( nvidia-smi boost-slider -l | grep vboost | awk '{ print $5 }' )"
vboost_str="$( echo "$vboost" | sort -u )"
if [[ "$( echo "$vboost_str" | wc -l )" -gt 1 ]] || [[ "$vboost_str" -ne "$vboost_val" ]]; then
  echo "error, node $( hostname ) has vboosts set to $( echo "$vboost" | tr '\n' ',' )"
fi

power="$( nvidia-smi -q -d POWER | grep -A3 'Module Power' | grep Current | awk '{ print $5 }' )"
power_str="$( echo "$power" | sort -u )"
if [[ "$( echo "$power_str" | wc -l )" -gt 1 ]] || (( $(echo "$power_str < $power_val" | bc -l) )); then
  echo "error, node $( hostname ) has power lims set to $( echo "$power" | tr '\n' ',' )"
fi

thp_str="$( cat /sys/kernel/mm/transparent_hugepage/enabled | sed 's/.*\[\(.*\)\].*/\1/' )"
if [[ "$thp_str" == "$thp_wrong_val" ]]; then
  echo "error, node $( hostname ) has thp set to $thp_str"
fi

stat_str="$( cat /proc/sys/vm/stat_interval )"
if [[ "$stat_str" -lt "$stat_interval" ]]; then
  echo "error, node $( hostname ) has stat_internal set to $stat_str, less than $stat_interval"
fi

