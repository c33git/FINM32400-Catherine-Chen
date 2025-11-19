# Quick Start Guide: Assignment 4

## Quick Reference Commands

### 1. First Time Setup

Replace `YOUR_USER_NAME` with your actual username in all commands!

```bash
# SSH into server
ssh YOUR_USER_NAME@51.222.140.217

# Create directory on server
mkdir -p ~/assignment4_order_router
chmod 755 ~/assignment4_order_router
exit
```

Or use PowerShell script (after editing to add your username):
```powershell
cd Assignment4
.\server_commands.ps1 setup
```

### 2. Upload Your Code to Server

**Option A: Using PowerShell Script** (Windows)

```powershell
cd Assignment4
.\server_commands.ps1 upload-code
```

**Option B: Manual SCP Command**

```bash
# From Assignment4 directory
scp *.py YOUR_USER_NAME@51.222.140.217:~/assignment4_order_router/
```

### 3. Run on Server

```bash
# SSH into server
ssh YOUR_USER_NAME@51.222.140.217
cd ~/assignment4_order_router

# Install dependencies (first time only)
pip install pandas numpy scikit-learn joblib tqdm pytest

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

### 4. Verify Submission

```bash
# On server
cd ~/assignment4_order_router
ls -la
pytest test_somewhat_smart_order_router.py -v
```

## Alternative: Work Locally

If you prefer working on your local machine:

```powershell
# Download data (WARNING: Large file!)
cd Assignment4
.\server_commands.ps1 download-data

# Install dependencies
pip install -r requirements.txt

# Run feature engineering locally
python feature_engineering.py --executions executions.csv --quotes quotes_2025-09-10_small.csv.gz --output annotated_executions.csv --filter_symbols

# Train models locally
python train_models.py --input annotated_executions.csv --output_dir models/

# Test locally
pytest test_somewhat_smart_order_router.py -v

# Upload everything to server
.\server_commands.ps1 upload-code
```

## Files to Upload

Make sure these are on the server at `~/assignment4_order_router/`:

- ✅ `somewhat_smart_order_router.py` (required)
- ✅ `test_somewhat_smart_order_router.py` (required)
- ✅ `models/models.joblib` (after training)
- 📄 Other supporting files (optional)

## Need More Details?

See `WORKFLOW_GUIDE.md` for complete step-by-step instructions.

