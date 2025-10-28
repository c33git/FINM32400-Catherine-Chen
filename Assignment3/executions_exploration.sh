#!/usr/bin/env bash
set -euo pipefail

CSV="/opt/assignment3/executions.csv"
FIX="/opt/assignment1/trading.fix"

AWKFILE="$(mktemp)"
cat > "$AWKFILE" <<'AWK'
BEGIN{IGNORECASE=1;c=0}
NR==1{
  FS=","
  for(i=1;i<=NF;i++){
    f=$i
    gsub(/\r$/,"",f)
    gsub(/^[ \t"]+|[ \t"]+$/,"",f)
    if(tolower(f)=="symbol"){c=i;break}
  }
  if(c==0)c=1
}
{ print $c }
AWK
wc -l "$CSV" > a3_line_count.txt
wc -l "$FIX" >> a3_line_count.txt

( grep 'MSFT' "$CSV" | head -n 10 ) > a3_msft_count.txt || true
( grep 'MSFT' "$FIX" | head -n 10 ) >> a3_msft_count.txt || true

awk -F, -f "$AWKFILE" "$CSV" | sort | uniq > a3_unique_symbols.txt
awk -F, -f "$AWKFILE" "$CSV" | sort | uniq -c > a3_symbols_count.txt
awk -F, -f "$AWKFILE" "$CSV" | grep -x 'NVDA' > a3_only_nvda.txt || true
awk -F, -f "$AWKFILE" "$CSV" | grep -vx 'NVDA' > a3_all_except_nvda.txt || true

rm -f "$AWKFILE"
