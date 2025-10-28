set -euo pipefail
CSV="/opt/assignment3/executions.csv"
FIX="/opt/assignment1/trading.fix"
symcol_awker='
BEGIN{IGNORECASE=1}
NR==1{
  for(i=1;i<=NF;i++) if($i=="symbol"){c=i; break}
}
{ print $c }
'
wc -l "$CSV" > a3_line_count.txt
wc -l "$FIX" >> a3_line_count.txt
grep 'MSFT' "$CSV" | head -n 10 > a3_msft_count.txt
grep 'MSFT' "$FIX" | head -n 10 >> a3_msft_count.txt
awk -F, "$symcol_awker" "$CSV" | sort | uniq > a3_unique_symbols.txt
awk -F, "$symcol_awker" "$CSV" | sort | uniq -c > a3_symbols_count.txt
awk -F, "$symcol_awker" "$CSV" | grep '^NVDA$' > a3_only_nvda.txt
awk -F, "$symcol_awker" "$CSV" | grep -v '^NVDA$' > a3_all_except_nvda.txt
