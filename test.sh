#!/bin/sh

set -x # short for `set -o xtrace` see `man bash` for '-o option-name'
set -e # exit when any command fails

python -m curiousbits.boolalg.expr
python -m curiousbits.boolalg.tools
python -m curiousbits.boolalg.tseytin
python -m curiousbits.boolalg.sat_solve
python -m curiousbits.boolalg.simplify_espresso
python -m curiousbits.boolalg.simplify_qm
python -m curiousbits.graphs.nxtools
