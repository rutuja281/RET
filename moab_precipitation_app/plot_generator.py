import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import pandas as pd
import base64
import io
# Import scipy.stats only when needed (in comparison functions)
try:
    from scipy import stats
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False
    stats = None

class PlotGenerator:
    """Generate plots as base64 encoded images"""
    
    def __init__(self):
        # Try different matplotlib styles for compatibility
        try:
            plt.style.use('seaborn-v0_8-whitegrid')
        except OSError:
            try:
                plt.style.use('seaborn-whitegrid')
            except OSError:
                pass  # Use default style
        
        sns.set_palette('husl')
        
    def _fig_to_base64(self, fig):
        """Convert matplotlib figure to base64 string"""
        buf = io.BytesIO()
        fig.savefig(buf, format='png', dpi=150, bbox_inches='tight')
        buf.seek(0)
        img_base64 = base64.b64encode(buf.read()).decode('utf-8')
        plt.close(fig)
        return img_base64
    
    def monthly_totals_heatmap(self, df, precip_type='rain', month_filter=None):
        """Monthly totals heatmap for rain OR snow"""
        if month_filter and len(month_filter) > 0:
            df = df[df['Month'].isin(month_filter)]
        
        col_name = 'Rain_mm' if precip_type == 'rain' else 'Snow_mm'
        
        if col_name not in df.columns:
            raise ValueError(f"Column {col_name} not found in dataframe")
        
        monthly_totals = df.groupby(['Year', 'Month'])[col_name].sum().reset_index()
        monthly_pivot = monthly_totals.pivot(index='Year', columns='Month', values=col_name)
        
        fig, ax = plt.subplots(figsize=(14, 10))
        month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                       'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        
        sns.heatmap(monthly_pivot, annot=True, fmt='.1f', cmap='Blues',
                   cbar_kws={'label': f'{precip_type.capitalize()} (mm)'},
                   xticklabels=month_names, ax=ax)
        ax.set_xlabel('Month')
        ax.set_ylabel('Year')
        ax.set_title(f'Monthly Total {precip_type.capitalize()} Heatmap - Moab, Utah')
        
        return self._fig_to_base64(fig)
    
    def monthly_climatology(self, df, precip_type='rain', month_filter=None):
        """Monthly climatology bar chart"""
        if month_filter and len(month_filter) > 0:
            df = df[df['Month'].isin(month_filter)]
        
        col_name = 'Rain_mm' if precip_type == 'rain' else 'Snow_mm'
        
        if col_name not in df.columns:
            raise ValueError(f"Column {col_name} not found in dataframe")
        
        monthly_totals = df.groupby(['Year', 'Month'])[col_name].sum().reset_index()
        monthly_clim = monthly_totals.groupby('Month')[col_name].agg(['mean', 'std'])
        monthly_clim.columns = ['Mean', 'Std']
        
        fig, ax = plt.subplots(figsize=(12, 6))
        month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                       'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        x = np.arange(12)
        
        # Only plot months that exist in data
        available_months = monthly_clim.index.tolist()
        x_vals = [i for i in range(12) if (i+1) in available_months]
        labels = [month_names[i] for i in x_vals]
        means = [monthly_clim.loc[i+1, 'Mean'] for i in x_vals]
        stds = [monthly_clim.loc[i+1, 'Std'] for i in x_vals]
        
        ax.bar(x_vals, means, yerr=stds, capsize=5, 
              color='steelblue', edgecolor='white', alpha=0.8,
              error_kw={'ecolor': 'darkblue', 'elinewidth': 2})
        ax.set_xticks(x_vals)
        ax.set_xticklabels(labels)
        ax.set_xlabel('Month')
        ax.set_ylabel(f'{precip_type.capitalize()} (mm)')
        ax.set_title(f'Monthly {precip_type.capitalize()} Climatology with Standard Deviation - Moab, Utah')
        
        # Add value labels
        for i, (mean, std) in enumerate(zip(means, stds)):
            ax.text(x_vals[i], mean + std + max(means) * 0.02, f'{mean:.1f}', 
                   ha='center', va='bottom', fontsize=9)
        
        return self._fig_to_base64(fig)
    
    def seasonal_boxplot(self, df, precip_type='rain', season_filter=None):
        """Seasonal distribution boxplot"""
        def assign_season_year(row):
            if row['Month'] == 12:
                return row['Year'] + 1
            return row['Year']
        
        df['SeasonYear'] = df.apply(assign_season_year, axis=1)
        col_name = 'Rain_mm' if precip_type == 'rain' else 'Snow_mm'
        
        if col_name not in df.columns:
            raise ValueError(f"Column {col_name} not found in dataframe")
        
        seasonal_totals = df.groupby(['SeasonYear', 'Season'])[col_name].sum().reset_index()
        
        if season_filter and len(season_filter) > 0:
            seasonal_totals = seasonal_totals[seasonal_totals['Season'].isin(season_filter)]
        
        season_order = ['DJF', 'MAM', 'JJA', 'SON']
        season_colors = {'DJF': '#3498db', 'MAM': '#2ecc71', 'JJA': '#e74c3c', 'SON': '#f39c12'}
        
        # Only include seasons that have data
        available_seasons = seasonal_totals['Season'].unique().tolist()
        boxplot_data = []
        labels = []
        colors_list = []
        
        for season in season_order:
            if season in available_seasons:
                data = seasonal_totals[seasonal_totals['Season'] == season][col_name].values
                if len(data) > 0:
                    boxplot_data.append(data)
                    labels.append(season)
                    colors_list.append(season_colors[season])
        
        if len(boxplot_data) == 0:
            raise ValueError("No seasonal data available")
        
        fig, ax = plt.subplots(figsize=(10, 6))
        bp = ax.boxplot(boxplot_data, patch_artist=True, labels=labels)
        
        for patch, color in zip(bp['boxes'], colors_list):
            patch.set_facecolor(color)
            patch.set_alpha(0.7)
        
        ax.set_xlabel('Season')
        ax.set_ylabel(f'{precip_type.capitalize()} (mm)')
        ax.set_title(f'Seasonal {precip_type.capitalize()} Distribution - Moab, Utah\n(DJF=Winter, MAM=Spring, JJA=Summer, SON=Fall)')
        
        return self._fig_to_base64(fig)
    
    def annual_totals(self, df, precip_type='rain'):
        """Annual totals time series"""
        col_name = 'Rain_mm' if precip_type == 'rain' else 'Snow_mm'
        
        if col_name not in df.columns:
            raise ValueError(f"Column {col_name} not found in dataframe")
        
        annual = df.groupby('Year')[col_name].sum()
        
        fig, ax = plt.subplots(figsize=(14, 6))
        ax.bar(annual.index, annual.values, color='steelblue', alpha=0.8, edgecolor='white')
        
        mean_val = annual.mean()
        ax.axhline(mean_val, color='red', linestyle='--', linewidth=2, 
                   label=f'Mean: {mean_val:.1f} mm')
        
        # Add trend line
        z = np.polyfit(annual.index, annual.values, 1)
        p = np.poly1d(z)
        ax.plot(annual.index, p(annual.index), color='orange', linewidth=2, 
               linestyle='-', label='Trend')
        
        ax.set_xlabel('Year')
        ax.set_ylabel(f'{precip_type.capitalize()} (mm)')
        ax.set_title(f'Annual Total {precip_type.capitalize()} - Moab, Utah')
        ax.legend()
        ax.set_xticks(annual.index[::max(1, len(annual)//10)])  # Show every Nth year
        
        return self._fig_to_base64(fig)
    
    def monthly_distribution_boxplot(self, df, precip_type='rain', month_filter=None):
        """Monthly precipitation distribution boxplot"""
        if month_filter and len(month_filter) > 0:
            df = df[df['Month'].isin(month_filter)]
        
        col_name = 'Rain_mm' if precip_type == 'rain' else 'Snow_mm'
        
        if col_name not in df.columns:
            raise ValueError(f"Column {col_name} not found in dataframe")
        
        monthly_totals = df.groupby(['Year', 'Month'])[col_name].sum().reset_index()
        
        fig, ax = plt.subplots(figsize=(14, 6))
        month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                       'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        
        boxplot_data = []
        for m in range(1, 13):
            month_data = monthly_totals[monthly_totals['Month'] == m][col_name].values
            if len(month_data) > 0:
                boxplot_data.append(month_data)
            else:
                boxplot_data.append([])
        
        bp = ax.boxplot(boxplot_data, patch_artist=True, labels=month_names)
        
        # Color the boxes
        colors = plt.cm.Blues(np.linspace(0.3, 0.8, 12))
        for patch, color in zip(bp['boxes'], colors):
            patch.set_facecolor(color)
        
        ax.set_xlabel('Month')
        ax.set_ylabel(f'Monthly Total {precip_type.capitalize()} (mm)')
        ax.set_title(f'Monthly {precip_type.capitalize()} Distribution - Moab, Utah')
        
        return self._fig_to_base64(fig)
    
    def monthly_histogram(self, df, precip_type='rain', month_filter=None):
        """Histogram of precipitation for selected individual months"""
        col_name = 'Rain_mm' if precip_type == 'rain' else 'Snow_mm'
        
        if col_name not in df.columns:
            raise ValueError(f"Column {col_name} not found in dataframe")
        
        # Filter by selected months if provided
        if month_filter and len(month_filter) > 0:
            df = df[df['Month'].isin(month_filter)]
        
        # Calculate monthly totals for each year-month combination
        monthly_totals = df.groupby(['Year', 'Month'])[col_name].sum().reset_index()
        
        # Get months to plot
        months_to_plot = sorted(monthly_totals['Month'].unique()) if month_filter and len(month_filter) > 0 else sorted(monthly_totals['Month'].unique())
        
        month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                       'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        
        # Determine number of subplots needed
        n_months = len(months_to_plot)
        if n_months == 0:
            raise ValueError("No months to plot")
        
        # Create subplots - arrange in a grid
        cols = min(3, n_months)
        rows = (n_months + cols - 1) // cols
        
        fig, axes = plt.subplots(rows, cols, figsize=(5*cols, 4*rows))
        if n_months == 1:
            axes = [axes]
        else:
            axes = axes.flatten()
        
        for idx, month in enumerate(months_to_plot):
            month_data = monthly_totals[monthly_totals['Month'] == month][col_name].values
            
            if len(month_data) == 0:
                continue
            
            ax = axes[idx]
            
            # Create histogram
            n_bins = min(15, max(5, len(month_data) // 3))  # Adaptive number of bins
            ax.hist(month_data, bins=n_bins, color='steelblue', edgecolor='white', alpha=0.7)
            
            # Add mean line
            mean_val = month_data.mean()
            ax.axvline(mean_val, color='red', linestyle='--', linewidth=2, label=f'Mean: {mean_val:.1f} mm')
            
            # Add median line
            median_val = np.median(month_data)
            ax.axvline(median_val, color='orange', linestyle='--', linewidth=2, label=f'Median: {median_val:.1f} mm')
            
            ax.set_xlabel(f'{precip_type.capitalize()} (mm)', fontsize=10)
            ax.set_ylabel('Frequency', fontsize=10)
            ax.set_title(f'{month_names[month-1]} - {precip_type.capitalize()} Distribution', fontsize=11, fontweight='bold')
            ax.legend(fontsize=9)
            ax.grid(True, alpha=0.3)
        
        # Hide unused subplots
        for idx in range(n_months, len(axes)):
            axes[idx].axis('off')
        
        plt.tight_layout()
        return self._fig_to_base64(fig)
    
    def operating_vs_climatology_histogram(self, df_op, df_clim, precip_type='rain'):
        """Overlay histogram comparing operating period vs climatology"""
        try:
            from scipy import stats
        except ImportError:
            stats = None
        col_name = 'Rain_mm' if precip_type == 'rain' else 'Snow_mm'
        
        # Calculate monthly totals
        monthly_op = df_op.groupby(['Year', 'Month'])[col_name].sum().values
        monthly_clim = df_clim.groupby(['Year', 'Month'])[col_name].sum().values
        
        # Determine common bin edges
        all_data = np.concatenate([monthly_op, monthly_clim])
        bins = np.linspace(0, np.percentile(all_data, 98), 25)
        
        fig, ax = plt.subplots(figsize=(12, 6))
        
        ax.hist(monthly_clim, bins=bins, alpha=0.6, label='Climatology',
                color='steelblue', edgecolor='white', density=True)
        ax.hist(monthly_op, bins=bins, alpha=0.6, label='Operating Period',
                color='darkorange', edgecolor='white', density=True)
        
        ax.axvline(monthly_clim.mean(), color='steelblue', linestyle='--', linewidth=2)
        ax.axvline(monthly_op.mean(), color='darkorange', linestyle='--', linewidth=2)
        
        ax.set_xlabel(f'Monthly {precip_type.capitalize()} (mm)', fontsize=12)
        ax.set_ylabel('Density', fontsize=12)
        ax.set_title(f'Monthly {precip_type.capitalize()} Distribution: Operating Period vs Climatology', fontsize=14)
        ax.legend(fontsize=11)
        
        return self._fig_to_base64(fig)
    
    def precipitation_anomaly(self, df_op, df_clim, precip_type='rain'):
        """Anomaly plot showing departure from climatology"""
        col_name = 'Rain_mm' if precip_type == 'rain' else 'Snow_mm'
        
        # Calculate climatological mean for each month
        monthly_clim = df_clim.groupby(['Year', 'Month'])[col_name].sum().reset_index()
        clim_monthly_means = monthly_clim.groupby('Month')[col_name].mean()
        
        # Calculate anomalies for operating period
        monthly_op = df_op.groupby(['Year', 'Month'])[col_name].sum().reset_index()
        monthly_op['Climatology'] = monthly_op['Month'].map(clim_monthly_means)
        monthly_op['Anomaly'] = monthly_op[col_name] - monthly_op['Climatology']
        
        # Create date index for plotting
        monthly_op['Date'] = pd.to_datetime(
            monthly_op['Year'].astype(str) + '-' + 
            monthly_op['Month'].astype(str).str.zfill(2) + '-01'
        )
        
        fig, ax = plt.subplots(figsize=(14, 6))
        
        colors = ['#e74c3c' if x > 0 else '#3498db' for x in monthly_op['Anomaly']]
        ax.bar(monthly_op['Date'], monthly_op['Anomaly'], 
               color=colors, alpha=0.8, width=25)
        
        ax.axhline(0, color='black', linewidth=1)
        ax.set_xlabel('Date', fontsize=12)
        ax.set_ylabel(f'{precip_type.capitalize()} Anomaly (mm)', fontsize=12)
        ax.set_title(f'Monthly {precip_type.capitalize()} Anomaly During Operating Period\n(Departure from Climatological Mean)', fontsize=14)
        
        # Add legend
        from matplotlib.patches import Patch
        legend_elements = [Patch(facecolor='#e74c3c', alpha=0.8, label='Above Normal'),
                           Patch(facecolor='#3498db', alpha=0.8, label='Below Normal')]
        ax.legend(handles=legend_elements, loc='upper right')
        
        return self._fig_to_base64(fig)
    
    def generate_all_plots(self, df, month_filter=None, season_filter=None):
        """Generate all plots for both rain and snow"""
        plots = {}
        
        plot_types = [
            ('monthly_heatmap', self.monthly_totals_heatmap),
            ('monthly_climatology', self.monthly_climatology),
            ('seasonal_boxplot', self.seasonal_boxplot),
            ('annual_totals', self.annual_totals),
            ('monthly_distribution', self.monthly_distribution_boxplot),
            ('monthly_histogram', self.monthly_histogram)
        ]
        
        for precip_type in ['rain', 'snow']:
            for plot_name, plot_func in plot_types:
                key = f'{precip_type}_{plot_name}'
                try:
                    if 'monthly' in plot_name and 'seasonal' not in plot_name:
                        plots[key] = plot_func(df, precip_type, month_filter)
                    elif 'seasonal' in plot_name:
                        plots[key] = plot_func(df, precip_type, season_filter)
                    else:
                        plots[key] = plot_func(df, precip_type)
                except Exception as e:
                    plots[key] = None
                    print(f"Error generating {key}: {e}")
        
        return plots

