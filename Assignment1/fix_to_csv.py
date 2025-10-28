import argparse
import csv
import logging
import os
import sys
from typing import Dict, Iterable


# Known separators that may appear in FIX logs
SOH_CHARS: Iterable[str] = ['\x01', '\u0001', '|']

# This function is used to parse a single FIX message line into a dictionary of tag-value pairs
def split_fix_message(line: str) -> Dict[str, str]:
	# Breaking down a single FIX message line into a dict
	# sep represents the detected separator character
	# c represents each character in SOH_CHARS
	sep = None
	for c in SOH_CHARS:
		if c in line:
			sep = c
			break

	if sep is None:
		# No SOH-like character detected, assume whitespace-separated 'tag=val' pairs
		parts = line.strip().split()
	else:
		parts = line.strip().split(sep)

	# Create a dictionary of tag-value pairs
	fields: Dict[str, str] = {}

	# p stands for each part in parts
	for p in parts:
		if not p:
			continue
		if '=' not in p:
			# Not a tag=value token -> skip it silently
			continue
		tag, val = p.split('=', 1)
		fields[tag] = val
	
	return fields


# This function processes the FIX file and writes matched fills to a CSV file
def process_fix_file(input_path: str, output_path: str) -> None:
	
	# Store required order fields per ClOrdID
	orders: Dict[str, Dict[str, str]] = {}

	header = [
		'OrderID',
		'OrderTransactTime',
		'ExecutionTransactTime',
		'Symbol',
		'Side',
		'OrderQty',
		'LimitPrice',
		'AvgPx',
		'LastMkt',
	]

	# Open input FIX file and output CSV file
	with open(input_path, 'r', encoding='utf-8', errors='replace') as fin, open(output_path, 'w', newline='', encoding='utf-8') as fout:
		writer = csv.writer(fout)
		writer.writerow(header)

		# Process each line in the FIX file
		for lineno, raw in enumerate(fin, start=1): # fin stands for file input
			line = raw.rstrip('\n')
			if not line:
				# skip empty lines
				continue
			
			# Store the FIX message into a dict of fields
			msg = split_fix_message(line)
			# get the message type, 35 stands for MsgType
			# Limit orders being sent to the market - MsgType (35) = NewOrderSingle (D)
			msg_type = msg.get('35')

			if msg_type == 'D':
				# NewOrderSingle: record the fields we'll need when the order fills.
				clord = msg.get('11')
				if not clord:
					# logging.warning('Line %d: NewOrderSingle without ClOrdID, skipping', lineno)
					continue

				# Store relevant fields for later use when processing fills
				orders[clord] = {
					'11': clord,
					'60': msg.get('60', ''),  # Order TransactTime
					'55': msg.get('55', ''),  # Symbol
					'54': msg.get('54', ''),  # Side
					'38': msg.get('38', ''),  # OrderQty
					'44': msg.get('44', ''),  # LimitPrice
				}

			elif msg_type == '8':
				# ExecutionReport: only consider full fills of limit orders
				# Fills received on those orders (ignore partial fills) - MsgType (35) = ExecutionReport (8) 
				# ExecType (150) = FILL (2) and OrderStatus (39) = FILLED (2) and OrdType (40) = LIMIT (2)
				if msg.get('150') != '2' or msg.get('39') != '2' or msg.get('40') != '2':
					continue

				clord = msg.get('11')
				if not clord:
					# logging.warning('Line %d: ExecutionReport fill without ClOrdID, skipping', lineno)
					continue

				order = orders.get(clord)
				if not order:
					# We only output fills where we have the original NewOrderSingle.
					# logging.warning('Line %d: Fill for ClOrdID %s but no matching NewOrderSingle found; skipping', lineno, clord)
					continue

				# Build CSV row using order values first, falling back to exec fields.
				order_id = clord
				order_tx = order.get('60', '')
				exec_tx = msg.get('60', '')
				symbol = order.get('55', '') or msg.get('55', '')
				side = order.get('54', '') or msg.get('54', '')
				order_qty = order.get('38', '') or msg.get('38', '')
				limit_price = order.get('44', '') or msg.get('44', '')
				avg_px = msg.get('6', '')
				last_mkt = msg.get('30', '')

				writer.writerow([
					order_id,
					order_tx,
					exec_tx,
					symbol,
					side,
					order_qty,
					limit_price,
					avg_px,
					last_mkt,
				])


# the main function to handle command-line arguments and initiate processing
def main(argv=None):
	parser = argparse.ArgumentParser(description='Convert FIX (NewOrderSingle + ExecutionReport fills) to CSV')
	parser.add_argument('--input_fix_file', required=True, help='Path to input FIX file')
	parser.add_argument('--output_csv_file', required=True, help='Path to output CSV file')
	args = parser.parse_args(argv)

	if not os.path.isfile(args.input_fix_file):
		print(f'Input file not found: {args.input_fix_file}', file=sys.stderr)
		return 2

	# Warnings are used for missing/unmatched records; the user can increase
	# verbosity if they want more diagnostic output
	logging.basicConfig(level=logging.WARNING, format='%(levelname)s: %(message)s')

	process_fix_file(args.input_fix_file, args.output_csv_file)
	return 0


if __name__ == '__main__':
	raise SystemExit(main())


