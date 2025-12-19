# How to Use the Operating Period vs Climatology Comparison Feature

## Quick Start Guide

### Step 1: Access the Feature

1. Open your web application (http://localhost:5000 or your deployed URL)
2. Scroll down to find **Section 4: "Operating Period vs Climatology Comparison (Optional)"**
   - It's a gray card with the header "4. Operating Period vs Climatology Comparison (Optional)"
   - Located between the "Filter by Months/Seasons" section and "Select Plot Types" section

### Step 2: Enable Comparison

1. Check the checkbox labeled **"Enable Period Comparison"**
2. The date input fields will appear below:
   - Operating Period Start
   - Operating Period End  
   - Climatology Period Start
   - Climatology Period End

### Step 3: Set Your Dates

Enter your date ranges:
- **Operating Period**: The period you want to analyze (e.g., 2020-01-01 to 2025-12-31)
- **Climatology Period**: The baseline/control period (e.g., 2005-01-01 to 2019-12-31)

Default values are pre-filled, but you can change them.

### Step 4: Generate Plots

1. Make sure you have:
   - Selected a file from the dropdown
   - (Optional) Selected months/seasons to filter
   - (Optional) Selected plot types OR checked "Generate All Plots"
   - **Checked "Enable Period Comparison"**

2. Click **"Generate Plots"** button

### Step 5: View Results

After generation, you'll see:
1. **Regular plots** (Rain and Snow sections)
2. **Period Comparison Analysis section** (green header) with:
   - Statistics table showing:
     - Mean ± Standard Deviation for both periods
     - p-values for t-test, Mann-Whitney U test, KS-test
     - Cohen's d effect size
     - Significance indicator
   - **Distribution Comparison Histogram** (for both rain and snow)
   - **Anomaly Plot** (for both rain and snow)

## Visual Location

The comparison section looks like this in the UI:

```
┌─────────────────────────────────────────────────────┐
│ 4. Operating Period vs Climatology Comparison      │
├─────────────────────────────────────────────────────┤
│ ☑ Enable Period Comparison                         │
│                                                     │
│ Operating Period Start: [2020-01-01]               │
│ Operating Period End:   [2025-12-31]               │
│ Climatology Period Start: [2005-01-01]             │
│ Climatology Period End:   [2019-12-31]             │
│                                                     │
│ ℹ Compare precipitation during your operating...   │
└─────────────────────────────────────────────────────┘
```

## Troubleshooting

**If you don't see Section 4:**

1. **Pull latest code**:
   ```bash
   cd /Users/rutuja/RET
   git pull origin rutuja
   ```

2. **Restart your Flask server**:
   ```bash
   cd moab_precipitation_app
   python app.py
   ```

3. **Hard refresh your browser**:
   - Windows/Linux: Ctrl + F5
   - Mac: Cmd + Shift + R

4. **Check browser console for errors**:
   - Press F12 → Console tab
   - Look for any red error messages

5. **Verify the template file**:
   The comparison section should be around line 101-138 in `templates/index.html`

## What the Comparison Shows

- **Statistical Tests**: Whether operating period is significantly different from climatology
- **Effect Size**: How large the difference is (Cohen's d)
- **Visual Comparison**: Overlaid histograms showing distribution differences
- **Anomaly Analysis**: Month-by-month departure from climatological norm

This is perfect for comparing operational periods to historical baselines!

