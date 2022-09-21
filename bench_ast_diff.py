#!/usr/bin/env python3
import re
import argparse
import sys
import csv
import os as os

import subprocess as sp
from shutil import which,rmtree
from pathlib import Path

frama_c_config = which("frama-c-config")

if frama_c_config is None:
    print("Error: Cannot find frama-c-config in the path")
    exit(1)

def run_and_check(args):
    proc = sp.Popen(args,stdout=sp.PIPE,stderr=sp.STDOUT)
    out,_ = proc.communicate()
    if proc.returncode != 0:
        printf(f"Error: {args} returned {proc.returncode}: {out}")
        exit(1)
    return out.decode()

frama_c_share = Path(run_and_check([frama_c_config,"-print-share-path"]))

sys.path.append(str(frama_c_share / 'analysis-scripts'))

import frama_c_results as fcres

targets = run_and_check(["/usr/bin/make", "display-targets"]).split()

def create_csv(file,rows):
    with open("comparison.csv", 'w', newline='') as file:
        fieldnames = [ "name", "user_time_standard", "user_time_ast_diff", "gain" ]
        writer = csv.DictWriter(file,fieldnames=fieldnames,extrasaction='ignore')
        writer.writeheader()
        writer.writerows(rows)

def process_target(target):
    print(f"now processing {target}")
    if os.access(target,os.F_OK):
        rmtree(Path(target),ignore_errors=True)
    print("standard pass")
    res=sp.run(["/usr/bin/make", target], stdout=sp.DEVNULL, stderr=sp.DEVNULL)
    row={ 'name': target }
    if res.returncode == 0:
        standard=fcres.load(target+"/stats.txt")
        timeout=60
        if 'user_time' in standard:
            row['user_time_standard'] = standard['user_time']
            baseline = float(standard['user_time'])
            timeout=baseline * 5
            env=os.environ.copy()
            env["AST_DIFF"]="1"
            print("AST diff pass")
            try:
                sp.run(["/usr/bin/make", target],env=env,timeout=timeout,stdout=sp.DEVNULL,stderr=sp.DEVNULL)
                ast_diff=fcres.load(target+"/stats.txt")
                if 'user_time' in ast_diff:
                    row['user_time_ast_diff'] = ast_diff['user_time']
                    with_ast_diff = float(row['user_time_ast_diff'])
                    row['gain'] = (baseline - with_ast_diff) / baseline
                else:
                    row['user_time_ast_diff'] = 'FAILURE'
            except sp.TimeoutExpired:
                row['user_time_ast_diff']  = 'TIMEOUT'
        return row

def run_bench():
    total_standard=0
    total_ast_diff=0
    rows=[]
    for t in targets:
        row=process_target(t)
        if 'gain' in row:
            total_standard+=float(row['user_time_standard'])
            total_ast_diff+=float(row['user_time_ast_diff'])
        rows += row
    rows += {
        'name': 'total when both succeed',
        'user_time_standard': total_standard,
        'user_time_ast_diff': total_ast_diff,
        'gain' : (total_standard - total_ast_diff) / total_standard
    }
    return rows

parser = argparse.ArgumentParser(
    description="Run analyses first in normal mode "
                "and then in incremental mode "
                "(without syntactic diff)")
parser.add_argument("-o", "--output",
    action="store", metavar="PATH", type=Path,
    help="store results in the given file")

args = parser.parse_args()
res = run_bench()
if args.output is not None:
    create_csv(args.output,res)
else:
    print("Results:")
    print("name,user_time_standard,user_time_ast_diff,gain")
    for row in res:
        print(f"{row['name']},{row['user_time_standard']},{row['user_time_ast_diff']},{row['gain']}")
