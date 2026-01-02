# Precipitation Data Analysis Web Application

A web-based application for analyzing precipitation data with separate visualizations for rain and snow. Supports both MeteoBlue History+ and SynopticX CSV file formats.

## Features

- **File Upload & Database Storage**: Upload MeteoBlue CSV files that are stored in a database
- **Separate Rain/Snow Analysis**: Automatically separates precipitation into rain and snow components
- **Interactive UI**: Select months, seasons, and plot types through an intuitive web interface
- **Multiple Plot Types**:
  - Monthly Heatmap
  - Monthly Climatology
  - Monthly Distribution Boxplots
  - Seasonal Boxplots
  - Annual Totals
- **Generate All Plots**: One-click option to generate all plots for both rain and snow
- **Flexible Filtering**: Filter by specific months or seasons

## Installation

1. Install Python dependencies:
```bash
pip install -r requirements.txt
```

2. Initialize the database:
```bash
python database.py
```

3. Run the application:
```bash
python app.py
```

4. Open your browser and navigate to:
```
http://localhost:5000
```

## Usage

1. **Upload a CSV file**: Click "Choose File" and select your MeteoBlue CSV file, then click "Upload File"
2. **Select a file**: Choose a file from the dropdown (files are stored in the database)
3. **Optional Filters**: Select specific months or seasons (leave empty for all data)
4. **Choose Plot Types**: Select individual plots or check "Generate All Plots"
5. **Generate**: Click "Generate Plots" to create visualizations

## File Structure

```
moab_precipitation_app/
├── app.py                 # Main Flask application
├── config.py              # Configuration settings
├── models.py              # Database models
├── database.py            # Database initialization
├── data_processor.py      # Data cleaning and processing
├── plot_generator.py      # Plot generation functions
├── requirements.txt       # Python dependencies
├── templates/
│   └── index.html        # Main UI template
├── static/
│   ├── css/
│   │   └── style.css
│   └── js/
│       └── main.js
└── uploads/               # Uploaded CSV files storage
```

## Data Processing

The application:
- Handles missing values based on variable type (precipitation → 0, temperature → interpolate, etc.)
- Separates rain from snow (rain = total precipitation - snowfall)
- Creates time-based columns (Year, Month, Season, etc.)
- Generates separate plots for rain and snow data

## Deployment

For production deployment:

1. Change the `SECRET_KEY` in `config.py`
2. Use a production database (PostgreSQL recommended):
   ```python
   SQLALCHEMY_DATABASE_URI = 'postgresql://user:pass@localhost/dbname'
   ```
3. Use a production WSGI server (e.g., gunicorn):
   ```bash
   pip install gunicorn
   gunicorn -w 4 -b 0.0.0.0:5000 app:app
   ```

## Notes

- CSV files should be in MeteoBlue History+ format or SynopticX format
- Files are stored in the `uploads/` directory
- The database file (`precipitation_data.db`) is created automatically in the app directory

## Render Free Tier Limitations

When deploying to Render's free tier, please note:
- **30-second request timeout**: Generating multiple plots may timeout
- **Memory limits**: Large datasets can cause memory issues
- **Recommendation**: Generate plots one at a time (1-2 plot types maximum)
- The application automatically limits to 4 plots per request to prevent timeouts
- If you experience 502 errors, try generating fewer plots or upgrade to a paid Render plan

