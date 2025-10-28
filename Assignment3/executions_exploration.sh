#!/usr/bin/env bash
set -euo pipefail

CSV=/opt/assignment3/executions.csv
FIX=/opt/assignment1/trading.fix
SYMCOL=4
wc -l "$CSV" > a3_line_count.txt
wc -l "$FIX" >> a3_line_count.txt

grep -F 'MSFT' "$CSV" | head -n 10 > a3_msft_count.txt || :
grep -F 'MSFT' "$FIX" | head -n 10 >> a3_msft_count.txt || :

cut -d, -f"$SYMCOL" "$CSV" | sort | uniq > a3_unique_symbols.txt
cut -d, -f"$SYMCOL" "$CSV" | sort | uniq -c > a3_symbols_count.txt
cut -d, -f"$SYMCOL" "$CSV" | grep -F 'NVDA' > a3_only_nvda.txt || :
cut -d, -f"$SYMCOL" "$CSV" | grep -F -v 'NVDA' > a3_all_except_nvda.txt || :
