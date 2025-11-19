"""Feature engineering: Annotate executions with quotes and calculate price improvement.

This script loads executions and quotes data, merges them using merge_asof,
and calculates price improvement for each execution.
"""
import pandas as pd
import numpy as np
from datetime import datetime
from tqdm import tqdm


def parse_timestamp(timestamp_str: str) -> pd.Timestamp:
    """Parse timestamp from string format.
    
    Args:
        timestamp_str: Timestamp string in format "YYYYMMDD-HH:MM:SS.microseconds"
                       or nanoseconds since epoch
        
    Returns:
        pd.Timestamp object
    """
    if isinstance(timestamp_str, (int, float)):
        # Handle nanosecond timestamp
        return pd.Timestamp(timestamp_str, unit='ns')
    
    try:
        # Handle string format "YYYYMMDD-HH:MM:SS.microseconds"
        return pd.Timestamp(datetime.strptime(timestamp_str, "%Y%m%d-%H:%M:%S.%f"))
    except (ValueError, TypeError):
        return pd.NaT


def calculate_price_improvement(
    limit_price: float,
    execution_price: float,
    side: str
) -> float:
    """Calculate price improvement based on order side.
    
    For buy orders (Side='1'): improvement = LimitPrice - ExecutionPrice
    For sell orders (Side!='1'): improvement = ExecutionPrice - LimitPrice
    
    Args:
        limit_price: The limit price of the order
        execution_price: The execution price
        side: Order side ('1' for buy, anything else for sell)
        
    Returns:
        Price improvement value (can be negative)
    """
    limit_price = float(limit_price)
    execution_price = float(execution_price)
    
    if side == '1':  # Buy order
        improvement = limit_price - execution_price
    else:  # Sell order
        improvement = execution_price - limit_price
    
    return improvement


def filter_market_hours(df: pd.DataFrame, time_col: str) -> pd.DataFrame:
    """Filter dataframe to market hours (9:30 AM to 4:00 PM).
    
    Args:
        df: DataFrame with timestamp column
        time_col: Name of the timestamp column
        
    Returns:
        Filtered DataFrame
    """
    df = df.copy()
    df['hour'] = df[time_col].dt.hour
    df['minute'] = df[time_col].dt.minute
    
    # Market hours: 9:30 AM to 4:00 PM
    market_mask = (
        ((df['hour'] == 9) & (df['minute'] >= 30)) |
        ((df['hour'] >= 10) & (df['hour'] < 16)) |
        ((df['hour'] == 16) & (df['minute'] == 0))
    )
    
    df_filtered = df[market_mask].copy()
    df_filtered = df_filtered.drop(columns=['hour', 'minute'])
    
    return df_filtered


def load_and_prepare_executions(executions_path: str) -> pd.DataFrame:
    """Load and prepare executions data.
    
    Args:
        executions_path: Path to executions CSV file
        
    Returns:
        Prepared DataFrame with executions
    """
    print("Loading executions data...")
    executions = pd.read_csv(executions_path)
    
    # Rename columns to match expected format
    # Based on sample: order_id,order_time,execution_time,symbol,side,order_qty,limit_price,execution_price,exchange
    # But actual file has: OrderID,OrderTransactTime,ExecutionTransactTime,Symbol,Side,OrderQty,LimitPrice,AvgPx,LastMkt
    column_mapping = {
        'OrderID': 'order_id',
        'OrderTransactTime': 'order_time',
        'ExecutionTransactTime': 'execution_time',
        'Symbol': 'symbol',
        'Side': 'side',
        'OrderQty': 'order_qty',
        'LimitPrice': 'limit_price',
        'AvgPx': 'execution_price',
        'LastMkt': 'exchange'
    }
    
    # Only rename columns that exist
    existing_mapping = {k: v for k, v in column_mapping.items() if k in executions.columns}
    executions = executions.rename(columns=existing_mapping)
    
    # Parse timestamps
    executions['order_time'] = executions['order_time'].apply(parse_timestamp)
    executions['execution_time'] = executions['execution_time'].apply(parse_timestamp)
    
    # Filter to market hours
    executions = filter_market_hours(executions, 'order_time')
    
    # Convert symbol to category to save memory
    executions['symbol'] = executions['symbol'].astype('category')
    
    # Sort by timestamp and symbol (required for merge_asof)
    executions = executions.sort_values(['order_time', 'symbol']).reset_index(drop=True)
    
    # Drop rows with missing timestamps
    executions = executions.dropna(subset=['order_time', 'execution_time'])
    
    print(f"Loaded {len(executions)} executions after filtering")
    
    return executions


def load_and_prepare_quotes(quotes_path: str, symbols: pd.Series = None) -> pd.DataFrame:
    """Load and prepare quotes data.
    
    Args:
        quotes_path: Path to quotes CSV file (can be gzipped)
        symbols: Optional Series of symbols to filter to (to save memory)
        
    Returns:
        Prepared DataFrame with quotes
    """
    print("Loading quotes data...")
    quotes = pd.read_csv(quotes_path, compression='gzip' if quotes_path.endswith('.gz') else None)
    
    # Rename columns if needed
    # Sample format: ticker,ask_price,bid_price,sip_timestamp
    column_mapping = {
        'ticker': 'symbol',
        'ask_price': 'ask_price',
        'bid_price': 'bid_price',
        'sip_timestamp': 'timestamp'
    }
    
    existing_mapping = {k: v for k, v in column_mapping.items() if k in quotes.columns}
    quotes = quotes.rename(columns=existing_mapping)
    
    # Filter to specific symbols if provided (to save memory during development)
    if symbols is not None:
        unique_symbols = symbols.unique()
        quotes = quotes[quotes['symbol'].isin(unique_symbols)]
        print(f"Filtered quotes to {len(unique_symbols)} symbols")
    
    # Parse timestamp (nanoseconds since epoch)
    quotes['timestamp'] = pd.to_datetime(quotes['timestamp'], unit='ns')
    
    # Filter to market hours
    quotes = filter_market_hours(quotes, 'timestamp')
    
    # Convert symbol to category to save memory
    quotes['symbol'] = quotes['symbol'].astype('category')
    
    # Sort by timestamp and symbol (required for merge_asof)
    quotes = quotes.sort_values(['timestamp', 'symbol']).reset_index(drop=True)
    
    # Drop rows with missing data
    quotes = quotes.dropna(subset=['timestamp', 'bid_price', 'ask_price'])
    
    print(f"Loaded {len(quotes)} quotes after filtering")
    
    return quotes


def merge_executions_with_quotes(
    executions: pd.DataFrame,
    quotes: pd.DataFrame
) -> pd.DataFrame:
    """Merge executions with quotes using merge_asof.
    
    For each execution, finds the most recent quote at or before the order time.
    
    Args:
        executions: DataFrame with executions
        quotes: DataFrame with quotes
        
    Returns:
        Merged DataFrame with quotes added to executions
    """
    print("Merging executions with quotes...")
    
    # Use merge_asof to find most recent quote at or before order time
    # This requires both dataframes to be sorted by timestamp and symbol
    merged = pd.merge_asof(
        executions,
        quotes[['symbol', 'timestamp', 'bid_price', 'ask_price']],
        left_on='order_time',
        right_on='timestamp',
        by='symbol',
        direction='backward'  # Find most recent quote at or before order time
    )
    
    # Add bid_size and ask_size if available in quotes
    if 'bid_size' in quotes.columns and 'ask_size' in quotes.columns:
        quotes_size = quotes[['symbol', 'timestamp', 'bid_size', 'ask_size']]
        merged = pd.merge_asof(
            merged,
            quotes_size,
            left_on='order_time',
            right_on='timestamp',
            by='symbol',
            direction='backward'
        )
    else:
        # If not available, set to NaN
        merged['bid_size'] = np.nan
        merged['ask_size'] = np.nan
    
    # Drop the timestamp column from quotes (we already have order_time)
    if 'timestamp' in merged.columns:
        merged = merged.drop(columns=['timestamp'])
    
    # Drop rows where we couldn't find a matching quote
    merged = merged.dropna(subset=['bid_price', 'ask_price'])
    
    print(f"Merged {len(merged)} executions with quotes")
    
    return merged


def calculate_price_improvement_feature(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate price improvement for each execution.
    
    Args:
        df: DataFrame with executions and quotes
        
    Returns:
        DataFrame with price_improvement column added
    """
    print("Calculating price improvement...")
    
    df = df.copy()
    df['price_improvement'] = df.apply(
        lambda row: calculate_price_improvement(
            row['limit_price'],
            row['execution_price'],
            row['side']
        ),
        axis=1
    )
    
    return df


def main():
    """Main function to perform feature engineering."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Annotate executions with quotes and calculate price improvement'
    )
    parser.add_argument(
        '--executions',
        required=True,
        help='Path to executions CSV file'
    )
    parser.add_argument(
        '--quotes',
        required=True,
        help='Path to quotes CSV file (can be gzipped)'
    )
    parser.add_argument(
        '--output',
        required=True,
        help='Path to output CSV file'
    )
    parser.add_argument(
        '--filter_symbols',
        action='store_true',
        help='Filter to symbols present in executions (to save memory)'
    )
    
    args = parser.parse_args()
    
    # Load executions
    executions = load_and_prepare_executions(args.executions)
    
    # Load quotes (optionally filtered to symbols in executions)
    symbols_to_filter = executions['symbol'] if args.filter_symbols else None
    quotes = load_and_prepare_quotes(args.quotes, symbols_to_filter)
    
    # Merge executions with quotes
    merged = merge_executions_with_quotes(executions, quotes)
    
    # Calculate price improvement
    final_df = calculate_price_improvement_feature(merged)
    
    # Select and order columns for output
    output_columns = [
        'order_id', 'order_time', 'execution_time', 'symbol', 'side',
        'order_qty', 'limit_price', 'execution_price', 'exchange',
        'bid_price', 'ask_price', 'bid_size', 'ask_size', 'price_improvement'
    ]
    
    # Only include columns that exist
    output_columns = [col for col in output_columns if col in final_df.columns]
    final_df = final_df[output_columns]
    
    # Save to CSV
    print(f"Saving to {args.output}...")
    final_df.to_csv(args.output, index=False)
    print(f"Saved {len(final_df)} rows to {args.output}")
    
    # Print summary statistics
    print("\nSummary Statistics:")
    print(f"Total executions: {len(final_df)}")
    print(f"Exchanges: {final_df['exchange'].nunique()}")
    print(f"Symbols: {final_df['symbol'].nunique()}")
    print(f"\nPrice improvement by exchange:")
    print(final_df.groupby('exchange')['price_improvement'].agg(['mean', 'std', 'count']))


if __name__ == '__main__':
    main()

