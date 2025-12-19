# Installation Guide

If you're getting `ModuleNotFoundError`, follow these steps:

## Step 1: Make sure you're using the correct Python

```bash
cd /Users/rutuja/RET/moab_precipitation_app
which python3
python3 --version
```

## Step 2: Install all dependencies

```bash
pip3 install -r requirements.txt
```

If that doesn't work, try:

```bash
python3 -m pip install -r requirements.txt --user
```

## Step 3: Verify installation

```bash
python3 check_setup.py
```

This should show all dependencies as installed (✓).

## Step 4: Run the app

```bash
python3 app.py
```

OR use the helper script:

```bash
./run_app.sh
```

## Troubleshooting

### If flask_sqlalchemy is still not found:

1. Check which Python you're using:
   ```bash
   python3 -c "import sys; print(sys.executable)"
   ```

2. Make sure you install to the same Python:
   ```bash
   python3 -m pip install Flask-SQLAlchemy --user
   ```

3. Verify installation:
   ```bash
   python3 -c "import flask_sqlalchemy; print('OK')"
   ```

### Alternative: Use a virtual environment

```bash
cd /Users/rutuja/RET/moab_precipitation_app
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app.py
```

