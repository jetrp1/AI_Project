#!/bin/env bash

valid_file=$1
log_file=$2

echo "Out File = " $valid_file
echo "log File = " $log_file
echo ' '

echo "Total Valid Entries:      " `wc -l $valid_file`
echo "Failed due to DNS check:  " `grep 'DNS' $log_file | wc -l`
echo "Failed due to port check: " `grep 'PORT' $log_file | wc -l` 
echo "Failed due to error:      " `grep 'Error' $log_file | wc -l` 
echo "Total Number of checks:   " `wc -l $log_file`
