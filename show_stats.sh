#!/bin/bash -eu

usage () {
    echo "usage: $0 dir target1 [target2 ...]"
    echo "   or: $0 all"
    exit 1
}

#if [ ( $# -lt 2 ) -o ( ( $# -eq 1 ) -a ( "$1" != "all" ) ) ]; then
if [ $# -lt 1 ]; then
    usage
elif [ $# -eq 1 ] && [ "$1" != "all" ]; then
    usage
fi

dir="$1"
shift

# prevent issues with locale-specific numeric separators
LC_ALL=C

print_stats () {
    local dir target secs maxmem stats_file
    dir=$1
    target=$2
    stats_file="$dir/.frama-c/$target/stats.txt"
    if [ -f "$stats_file" ]; then
        secs=$(grep '^user_time=' "$stats_file" | cut -d= -f2-)
        maxmem=$(grep '^memory=' "$stats_file" | cut -d= -f2-)
        printf "$dir/$target: user time %.2fs, memory %d KiB\n" "$secs" "$maxmem"
    fi
}

if [ "$dir" = "all" ]; then
    SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
    pushd "$SCRIPT_DIR" > /dev/null
    find . -type d -path "./*/.frama-c/*.parse" -o -path "./*/.frama-c/*.eva" | \
        cut -d/ -f2,4 | \
        sort | \
    while read -r dirtarget; do
        IFS='/' read -r -a t <<< "$dirtarget"
        print_stats "${t[0]}" "${t[1]}"
    done
    popd > /dev/null
else
    for target in "$@"; do
        print_stats "$dir" "$target"
    done
fi
