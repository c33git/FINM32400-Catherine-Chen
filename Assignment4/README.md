# Assignment 4: Smart Order Router

This assignment builds a machine learning system to predict price improvement and route orders to the best exchange.

## Files

- `feature_engineering.py`: Annotates executions with quotes and calculates price improvement
- `train_models.py`: Trains per-exchange regression models
- `somewhat_smart_order_router.py`: Inference script that loads models and routes orders
- `test_somewhat_smart_order_router.py`: Unit tests for the order router

## Quick Start

**For complete step-by-step instructions, see:**
- `QUICK_START.md` - Quick reference commands
- `WORKFLOW_GUIDE.md` - Detailed workflow guide
- `SERVER_GUIDE.md` - Server operations guide

**Windows users can use helper scripts:**
- `server_commands.ps1` - PowerShell script for server operations
- `server_commands.bat` - Batch script for Command Prompt
- `server_commands.sh` - Bash script for Git Bash/WSL

**Important:** Replace `YOUR_USER_NAME` with your actual username in all commands!

## Setup

### 1. First Time Setup

Create directory on server:
```bash
ssh YOUR_USER_NAME@51.222.140.217
mkdir -p ~/assignment4_order_router
chmod 755 ~/assignment4_order_router
exit
```

Or use PowerShell script:
```powershell
cd Assignment4
.\server_commands.ps1 setup
```
(Edit the script first to add your username)

### 2. Upload Your Code

**Option A: Using PowerShell Script (Windows)**
```powershell
cd Assignment4
.\server_commands.ps1 upload-code
```

**Option B: Manual Upload**
```bash
scp *.py YOUR_USER_NAME@51.222.140.217:~/assignment4_order_router/
```

### 3. Run on Server (Recommended)

Work directly on server to save disk space:

```bash
ssh YOUR_USER_NAME@51.222.140.217
cd ~/assignment4_order_router

# Install dependencies
pip install -r requirements.txt

# Run feature engineering
python feature_engineering.py \
    --executions /opt/assignment3/executions.csv \
    --quotes /opt/assignment4/quotes_2025-09-10_small.csv.gz \
    --output annotated_executions.csv \
    --filter_symbols

# Train models
python train_models.py \
    --input annotated_executions.csv \
    --output_dir models/

# Run tests
pytest test_somewhat_smart_order_router.py -v
```

### Alternative: Work Locally

If you prefer working locally, download data first:
```bash
# Download data (WARNING: Large file!)
scp YOUR_USER_NAME@51.222.140.217:/opt/assignment3/executions.csv .
scp YOUR_USER_NAME@51.222.140.217:/opt/assignment4/quotes_2025-09-10_small.csv.gz .

# Or use PowerShell script:
.\server_commands.ps1 download-data
```

Then run locally and upload results back to server.

## Usage

### Using the Order Router

```python
from somewhat_smart_order_router import best_price_improvement

# Example: Buy order
exchange, predicted_improvement = best_price_improvement(
    symbol='AAPL',
    side='B',
    quantity=100,
    limit_price=150.0,
    bid_price=149.5,
    ask_price=150.5,
    bid_size=1000,
    ask_size=1000
)

print(f"Best exchange: {exchange}, Predicted improvement: {predicted_improvement}")
```

## Notes

- The quotes file is very large. Work with it directly on the server or use `--filter_symbols` to reduce memory usage.
- Models are saved using `joblib` and can be loaded with `joblib.load()`.
- The function `best_price_improvement` is typed as required by the assignment.
- All code follows clean code practices and can be checked with `ruff` or `pylint`.

## Development Tips

1. **Start small**: Use `--filter_symbols` during development to work with a subset of data
2. **Test incrementally**: Test feature engineering before training models
3. **Monitor memory**: Delete dataframes when no longer needed
4. **Use market hours only**: Data is automatically filtered to 9:30 AM - 4:00 PM

