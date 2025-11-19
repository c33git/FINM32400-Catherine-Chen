"""Calculate per-exchange execution metrics from fills CSV file.

This script processes execution fills data and computes average price improvement
and execution speed metrics grouped by exchange (LastMkt).
"""
import argparse
import pandas as pd
import os
import sys
from datetime import datetime


def parse_time(time_string):
	"""Parse a time string in FIX format to a datetime object.
	
	Args:
		time_string: Time string in format "YYYYMMDD-HH:MM:SS.microseconds"
		
	Returns:
		datetime object if parsing succeeds, None otherwise
	"""
	try:
		return datetime.strptime(time_string, "%Y%m%d-%H:%M:%S.%f")
	except (ValueError, TypeError):
		return None	


def calculate_price_improvement(limit_price, avg_price, side):
	"""Calculate price improvement based on order side.
	
	For buy orders (Side='1'): improvement = LimitPrice - AvgPx
	For sell orders (Side='2'): improvement = AvgPx - LimitPrice
	
	Args:
		limit_price: The limit price of the order
		avg_price: The average execution price
		side: Order side ('1' for buy, '2' for sell)
		
	Returns:
		Non-negative price improvement value
	"""
	limit_price = float(limit_price)
	avg_price = float(avg_price)
	
	if side == '1':  # Buy order
		improvement = limit_price - avg_price
	elif side == '2':  # Sell order
		improvement = avg_price - limit_price
	else:
		# Unknown side, default to 0
		improvement = 0.0
	
	return max(0.0, improvement)


def main():
	"""Main function to calculate and output execution metrics."""
	parser = argparse.ArgumentParser(
		description='Calculate per-exchange execution metrics from fills CSV'
	)
	parser.add_argument(
		'--input_csv_file',
		required=True,
		help='Path to input fills CSV'
	)
	parser.add_argument(
		'--output_metrics_file',
		required=True,
		help='Path to output metrics CSV'
	)
	args = parser.parse_args()

	if not os.path.isfile(args.input_csv_file):
		print(
			f'Input file not found: {args.input_csv_file}',
			file=sys.stderr
		)
		return 2

	# Read fills CSV
	fills_df = pd.read_csv(args.input_csv_file)

	# Calculate execution speed in seconds for each row
	fills_df['OrderTransactTime_dt'] = fills_df['OrderTransactTime'].apply(
		parse_time
	)
	fills_df['ExecutionTransactTime_dt'] = fills_df['ExecutionTransactTime'].apply(
		parse_time
	)
	fills_df['ExecSpeedSecs'] = (
		fills_df['ExecutionTransactTime_dt'] - fills_df['OrderTransactTime_dt']
	).apply(
		lambda time_delta: time_delta.total_seconds()
		if time_delta is not None
		else None
	)

	# Calculate price improvement based on order side
	fills_df['PriceImprovement'] = fills_df.apply(
		lambda row: calculate_price_improvement(
			row['LimitPrice'],
			row['AvgPx'],
			row['Side']
		),
		axis=1
	)

	# Group by exchange/broker (LastMkt) and compute averages
	metrics_df = fills_df.groupby('LastMkt').agg({
		'PriceImprovement': 'mean',
		'ExecSpeedSecs': 'mean',
	}).reset_index()

	metrics_df.rename(columns={
		'PriceImprovement': 'AvgPriceImprovement',
		'ExecSpeedSecs': 'AvgExecSpeedSecs',
	}, inplace=True)

	# Write output CSV
	metrics_df.to_csv(args.output_metrics_file, index=False)
	return 0
 
if __name__ == '__main__':
	raise SystemExit(main())
