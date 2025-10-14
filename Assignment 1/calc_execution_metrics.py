import argparse
import pandas as pd
import os
import sys
from datetime import datetime

def parse_time(s):
	try:
		return datetime.strptime(s, "%Y%m%d-%H:%M:%S.%f")
	except Exception:
		return None

def main():
	parser = argparse.ArgumentParser(description='Calculate per-exchange execution metrics from fills CSV')
	parser.add_argument('--input_csv_file', required=True, help='Path to input fills CSV')
	parser.add_argument('--output_metrics_file', required=True, help='Path to output metrics CSV')
	# arguments
	args = parser.parse_args()

	if not os.path.isfile(args.input_csv_file):
		print(f'Input file not found: {args.input_csv_file}', file=sys.stderr)
		return 2

	# Read fills CSV
	df = pd.read_csv(args.input_csv_file)

	# Calculate execution speed in seconds for each row
	df['OrderTransactTime_dt'] = df['OrderTransactTime'].apply(parse_time)
	df['ExecutionTransactTime_dt'] = df['ExecutionTransactTime'].apply(parse_time)
	df['ExecSpeedSecs'] = (df['ExecutionTransactTime_dt'] - df['OrderTransactTime_dt']).apply(lambda x: x.total_seconds() if x is not None else None)

	# Calculate price improvement (never negative)
	df['PriceImprovement'] = (df['LimitPrice'].astype(float) - df['AvgPx'].astype(float)).clip(lower=0)

	# Group by exchange/broker (LastMkt) and compute averages
	metrics = df.groupby('LastMkt').agg({
		'PriceImprovement': 'mean',
		'ExecSpeedSecs': 'mean',
	}).reset_index()

	metrics.rename(columns={
		'PriceImprovement': 'AvgPriceImprovement',
		'ExecSpeedSecs': 'AvgExecSpeedSecs',
	}, inplace=True)

	# Write output CSV
	metrics.to_csv(args.output_metrics_file, index=False)
 
if __name__ == '__main__':
	raise SystemExit(main())
