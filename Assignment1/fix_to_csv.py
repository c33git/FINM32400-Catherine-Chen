"""Convert FIX protocol messages to CSV format.

This module processes FIX (Financial Information eXchange) protocol messages
to extract limit order fills and convert them to CSV format for analysis.
"""
import argparse
import csv
import logging
import os
import sys
from typing import Dict, Iterable, Optional


# Known separators that may appear in FIX logs
SOH_CHARS: Iterable[str] = ['\x01', '\u0001', '|']


def split_fix_message(line: str) -> Dict[str, str]:
	"""Parse a single FIX message line into a dictionary of tag-value pairs.
	
	FIX messages use tag=value pairs separated by SOH (Start of Header) characters
	or whitespace. This function detects the separator and extracts all tag-value
	pairs from the message.
	
	Args:
		line: A single line from a FIX log file
		
	Returns:
		Dictionary mapping FIX tag numbers (as strings) to their values
	"""
	separator = None
	for soh_char in SOH_CHARS:
		if soh_char in line:
			separator = soh_char
			break

	if separator is None:
		# No SOH-like character detected, assume whitespace-separated pairs
		parts = line.strip().split()
	else:
		parts = line.strip().split(separator)

	fields: Dict[str, str] = {}
	for part in parts:
		if not part:
			continue
		if '=' not in part:
			# Not a tag=value token, skip it
			continue
		tag, value = part.split('=', 1)
		fields[tag] = value
	
	return fields


def process_fix_file(input_path: str, output_path: str) -> None:
	"""Process FIX file and write matched fills to CSV file.
	
	This function:
	1. Parses NewOrderSingle messages (MsgType='D') to store order information
	2. Matches ExecutionReport messages (MsgType='8') with full fills
	3. Outputs CSV rows for each matched fill with order and execution details
	
	Args:
		input_path: Path to input FIX file
		output_path: Path to output CSV file
	"""
	# Store required order fields per ClOrdID
	orders: Dict[str, Dict[str, str]] = {}

	csv_header = [
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

	with open(input_path, 'r', encoding='utf-8', errors='replace') as input_file, \
		 open(output_path, 'w', newline='', encoding='utf-8') as output_file:
		writer = csv.writer(output_file)
		writer.writerow(csv_header)

		for line_number, raw_line in enumerate(input_file, start=1):
			line = raw_line.rstrip('\n')
			if not line:
				continue
			
			message = split_fix_message(line)
			# MsgType (35): 'D' = NewOrderSingle, '8' = ExecutionReport
			msg_type = message.get('35')

			if msg_type == 'D':
				# NewOrderSingle: record fields needed when order fills
				cl_ord_id = message.get('11')
				if not cl_ord_id:
					continue

				# Store relevant fields for later use when processing fills
				orders[cl_ord_id] = {
					'11': cl_ord_id,
					'60': message.get('60', ''),  # TransactTime
					'55': message.get('55', ''),  # Symbol
					'54': message.get('54', ''),  # Side
					'38': message.get('38', ''),  # OrderQty
					'44': message.get('44', ''),  # LimitPrice
				}

			elif msg_type == '8':
				# ExecutionReport: only consider full fills of limit orders
				# ExecType (150) = FILL (2), OrderStatus (39) = FILLED (2), OrdType (40) = LIMIT (2)
				if (message.get('150') != '2' or 
					message.get('39') != '2' or 
					message.get('40') != '2'):
					continue

				cl_ord_id = message.get('11')
				if not cl_ord_id:
					continue

				order = orders.get(cl_ord_id)
				if not order:
					# Only output fills where we have the original NewOrderSingle
					continue

				# Build CSV row using order values first, falling back to execution fields
				order_id = cl_ord_id
				order_transact_time = order.get('60', '')
				execution_transact_time = message.get('60', '')
				symbol = order.get('55', '') or message.get('55', '')
				side = order.get('54', '') or message.get('54', '')
				order_qty = order.get('38', '') or message.get('38', '')
				limit_price = order.get('44', '') or message.get('44', '')
				avg_px = message.get('6', '')  # AvgPx
				last_mkt = message.get('30', '')  # LastMkt

				writer.writerow([
					order_id,
					order_transact_time,
					execution_transact_time,
					symbol,
					side,
					order_qty,
					limit_price,
					avg_px,
					last_mkt,
				])


def main(argv: Optional[list] = None) -> int:
	"""Main function to handle command-line arguments and initiate processing.
	
	Args:
		argv: Optional command-line arguments (for testing). If None, uses sys.argv
		
	Returns:
		Exit code: 0 on success, 2 on file not found
	"""
	parser = argparse.ArgumentParser(
		description='Convert FIX (NewOrderSingle + ExecutionReport fills) to CSV'
	)
	parser.add_argument(
		'--input_fix_file',
		required=True,
		help='Path to input FIX file'
	)
	parser.add_argument(
		'--output_csv_file',
		required=True,
		help='Path to output CSV file'
	)
	args = parser.parse_args(argv)

	if not os.path.isfile(args.input_fix_file):
		print(
			f'Input file not found: {args.input_fix_file}',
			file=sys.stderr
		)
		return 2

	# Warnings are used for missing/unmatched records; the user can increase
	# verbosity if they want more diagnostic output
	logging.basicConfig(
		level=logging.WARNING,
		format='%(levelname)s: %(message)s'
	)

	process_fix_file(args.input_fix_file, args.output_csv_file)
	return 0


if __name__ == '__main__':
	raise SystemExit(main())


