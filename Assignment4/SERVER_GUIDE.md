# Server Operations Guide

This guide explains how to work with data on the SSH server and push your code.

## Prerequisites

You need:
- SSH access to the server: `51.222.140.217`
- Your username (replace `YOUR_USER_NAME` in all commands)
- SSH key or password authentication set up

## Option 1: Work Directly on Server (Recommended)

This saves disk space since you don't need to download the large quotes file.

### Step 1: SSH into the server

```bash
ssh YOUR_USER_NAME@51.222.140.217
```

### Step 2: Create your assignment directory

```bash
mkdir -p ~/assignment4_order_router
cd ~/assignment4_order_router
```

### Step 3: Upload your code files

From your **local machine** (in a new terminal, while still connected via SSH in another terminal):

```bash
# Navigate to your project directory
cd "C:\Users\cat33\OneDrive\ドキュメント\Uchicago\2025 Fall\FINM 32400\Homework\FINM-32400-Catherine-Chen\Assignment4"

# Upload all Python files
scp *.py YOUR_USER_NAME@51.222.140.217:~/assignment4_order_router/
```

### Step 4: Run your scripts on the server

Back in your SSH session:

```bash
cd ~/assignment4_order_router

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

## Option 2: Download Data to Local Machine

If you prefer to work locally, you can download the data:

### Download data files

```bash
# From your local machine
scp YOUR_USER_NAME@51.222.140.217:/opt/assignment3/executions.csv .
scp YOUR_USER_NAME@51.222.140.217:/opt/assignment4/quotes_2025-09-10_small.csv.gz .
```

**Warning**: The quotes file is very large (even compressed). This may take a long time and use significant disk space.

### Run locally

```bash
python feature_engineering.py \
    --executions executions.csv \
    --quotes quotes_2025-09-10_small.csv.gz \
    --output annotated_executions.csv \
    --filter_symbols

python train_models.py \
    --input annotated_executions.csv \
    --output_dir models/
```

### Upload results back to server

```bash
scp -r models/ YOUR_USER_NAME@51.222.140.217:~/assignment4_order_router/
scp *.py YOUR_USER_NAME@51.222.140.217:~/assignment4_order_router/
```

## Final Submission Checklist

Make sure these files are on the server at `~/assignment4_order_router/`:

- [ ] `somewhat_smart_order_router.py`
- [ ] `test_somewhat_smart_order_router.py`
- [ ] `models/models.joblib` (or `models.joblib` in the directory)
- [ ] Any other supporting files you created

## Troubleshooting

### Permission denied errors

Make sure your directory exists and you have write permissions:
```bash
ssh YOUR_USER_NAME@51.222.140.217
mkdir -p ~/assignment4_order_router
chmod 755 ~/assignment4_order_router
```

### Can't find models.joblib

The `somewhat_smart_order_router.py` looks for models in:
1. Current directory: `models.joblib`
2. `assignment4_order_router/models.joblib`
3. Same directory as the script: `models.joblib`

Make sure your models are saved in one of these locations.

### Memory issues

- Use `--filter_symbols` flag in feature engineering
- Work with a subset of symbols during development
- Delete large dataframes when done: `del df`

### Connection issues

If you have trouble connecting:
```bash
# Test connection
ssh -v YOUR_USER_NAME@51.222.140.217

# If using password instead of key
ssh YOUR_USER_NAME@51.222.140.217
# (will prompt for password)
```

## Quick Reference Commands

```bash
# SSH into server
ssh YOUR_USER_NAME@51.222.140.217

# Upload single file
scp file.py YOUR_USER_NAME@51.222.140.217:~/assignment4_order_router/

# Upload directory
scp -r models/ YOUR_USER_NAME@51.222.140.217:~/assignment4_order_router/

# Download file
scp YOUR_USER_NAME@51.222.140.217:/path/to/file .

# View file on server (without downloading)
ssh YOUR_USER_NAME@51.222.140.217 "head -n 20 /opt/assignment4/quotes_2025-09-10_small.csv.gz | zcat"
```

