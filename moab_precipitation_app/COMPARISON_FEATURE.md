# Operating Period vs Climatology Comparison Feature

## Location in UI

The comparison feature is located as **Section 4** in the web interface, between the "Filter by Months/Seasons" section and "Select Plot Types" section.

## How to Use

1. **Enable the Feature**: 
   - Look for the card titled "4. Operating Period vs Climatology Comparison (Optional)"
   - Check the checkbox labeled "Enable Period Comparison"
   - The date input fields will appear below

2. **Set Your Periods**:
   - **Operating Period Start**: e.g., 2020-01-01
   - **Operating Period End**: e.g., 2025-12-31
   - **Climatology Period Start**: e.g., 2005-01-01
   - **Climatology Period End**: e.g., 2019-12-31

3. **Generate Plots**:
   - Select your file, filters, and plot types as usual
   - Click "Generate Plots"
   - The comparison plots and statistics will appear in a separate "Period Comparison Analysis" section

## What You'll Get

### Comparison Plots (for both Rain and Snow):
- **Distribution Comparison Histogram**: Overlay showing operating period vs climatology distributions
- **Anomaly Plot**: Monthly departure from climatological mean (color-coded)

### Statistical Tests:
- **t-test**: Tests for significant difference in means
- **Mann-Whitney U test**: Non-parametric test
- **Kolmogorov-Smirnov test**: Tests for distribution differences
- **Cohen's d**: Effect size measure

### Statistics Table:
Shows mean ± standard deviation for both periods, p-values, effect size, and significance indicators.

## Troubleshooting

If you don't see the comparison section:

1. **Check if you're running the latest code**: 
   ```bash
   git pull origin rutuja
   ```

2. **Restart the Flask server**:
   ```bash
   python app.py
   ```

3. **Clear browser cache**: Press Ctrl+F5 (or Cmd+Shift+R on Mac) to hard refresh

4. **Check browser console** for JavaScript errors (F12 → Console tab)

## Code Files Modified

- `templates/index.html`: Added comparison UI section (lines ~101-138)
- `static/js/main.js`: Added comparison toggle handler and display functions
- `app.py`: Added comparison logic in `/process` route
- `plot_generator.py`: Added `operating_vs_climatology_histogram()` and `precipitation_anomaly()` methods

