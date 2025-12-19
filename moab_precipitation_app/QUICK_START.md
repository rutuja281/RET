# Quick Start Guide

## Local Development

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Initialize database**:
   ```bash
   python database.py
   ```

3. **Run the application**:
   ```bash
   python app.py
   ```

4. **Open browser**: http://localhost:5000

## Supported File Formats

### MeteoBlue History+ Format
- Has metadata header rows (first 9 rows)
- Timestamp format: `20050101T0000`
- Precipitation in mm
- Snowfall in cm (converted to mm)

### SynopticX Format
- Has metadata at top (STATION info)
- Timestamp column: `Date_Time` (format: `2020-09-30T02:40:00-0600`)
- Precipitation: `precip_accum_ten_minute_set_1` (in mm)
- Snowfall: `estimated_snowfall_rate_set_1` (in mm)

## Features

- ✅ Automatic file format detection
- ✅ Files stored in database (no re-upload needed)
- ✅ Separate rain and snow plots
- ✅ Filter by months/seasons
- ✅ Generate all plots option
- ✅ Ready for free hosting deployment

## Free Hosting Options

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed instructions on:
- Render (recommended)
- Railway
- PythonAnywhere
- Fly.io

