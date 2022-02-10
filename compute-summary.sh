#!/usr/bin/env bash

# Compute a summary table listing general information about each directory
# Requires 'cloc' and POSIX utilities

targets=$(find . -mindepth 1 -maxdepth 1 -name ".*" -prune -o \
               -type d -printf '%P\n' | \
              sort | \
              grep -v tutorials | grep -v frama-c)

out=summary.md
rm -f $out
# Compute a summary for each directory, using `cloc`

echo "| Directory | Description | URL | #Eva targets | #.c/.h files | #LoC |" > $out
echo "| --------- | ----------- | --- |          --- |          --- |  --- |" >> $out
for t in $targets
do
    echo "Processing $t..."
    csv="$(cloc --include-ext=c,h --csv $t | grep -A9999 ^files | tail -1)"
    desc="$(cd $t && sed '1!d' OSCS-README.txt)"
    url="$(cd $t && sed '2!d' OSCS-README.txt)"
    ntargets="$(cd $t && make -C .frama-c display-targets --no-print-directory | wc -w)"
    nfiles=$(echo $csv | cut -d',' -f1)
    loc=$(echo $csv | cut -d',' -f5)
    echo "|$t|$desc|$url|$ntargets|$nfiles|$loc|" >> $out
done

echo "Saved table to $out."
# Avoid accidentally modifying the file by hand
chmod -w $out
