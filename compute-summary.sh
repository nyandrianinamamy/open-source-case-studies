#!/usr/bin/env bash

# Compute a summary table listing general information about each directory
# Requires Git, Perl and POSIX utilities; uses a local version of cloc

targets=$(ls -d -- */ | tr -d '/' | LC_ALL=C sort)

out=summary.md
rm -f $out
# Compute a summary for each directory, using `cloc`

echo "| Directory | Description | URL | #Eva targets | #Eva alarms | #.c/.h files | #LoC | Tags |" > $out
echo "| --------- | ----------- | --- |          --- |         --- |          --- |  --- | ---  |" >> $out
for t in $targets
do
    if [ ! -d $t/.frama-c -o ! -f $t/OSCS-README.txt ]; then
        echo "$t: no .frama-c or OSCS-README.txt, skipping"
        continue
    fi
    echo "Processing $t..."
    csv="$(cd $t && git ls-files '*.[ch]' | ../cloc-2.00.pl --list-file=- --csv | grep -A9999 ^files | tail -1)"
    desc="$(cd $t && sed '1!d' OSCS-README.txt)"
    url="$(cd $t && sed '2!d' OSCS-README.txt)"
    ntargets="$(cd $t && make -C .frama-c display-targets --no-print-directory | wc -w | tr -d "[:blank:]")"
    # special case: mbedtls is not currently run by the CI, so we skip it
    if [ "$t" == "mbedtls" ]; then
        nalarms=-1
    else
        # Note: we add /dev/null to the list of files to ensure wc will display
        #       the 'total' line even if there is only one '.eva' directory
        ncsvlines=$(cd $t && \
                        wc -l /dev/null .frama-c/*.eva/alarms.csv | \
                            grep "total$" | sed 's/ */ /' | cut -d' ' -f2)
        nalarms="$(($ncsvlines - $ntargets))"
    fi
    nfiles=$(echo $csv | cut -d',' -f1)
    loc=$(echo $csv | cut -d',' -f5)
    tags="$(cd $t && sed '3!d' OSCS-README.txt)"
    echo "|$t|$desc|$url|$ntargets|$nalarms|$nfiles|$loc|$tags|" >> $out
done

cat >>$out <<EOF

Note: the 'Tags' column refers to code features that may be found in the code.
      A few examples are presented below.

- REM_RECURSION: the code contains recursive calls, but they were removed or
  commented in the current Eva test cases.
- UNUSED_RECURSION: the code contains recursive calls (either in the main
  application/library, or in test cases), but the current Eva targets do
  not call them.
EOF

echo "Saved table to $out."
# Avoid accidentally modifying the file by hand
chmod -w $out
