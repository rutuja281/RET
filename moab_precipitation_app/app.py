from flask import Flask, render_template, request, jsonify
import os
from werkzeug.utils import secure_filename
from datetime import datetime
import pandas as pd
import numpy as np
from models import db, DataFile
from config import Config
from data_processor import DataProcessor
from plot_generator import PlotGenerator

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

plot_gen = PlotGenerator()

@app.errorhandler(Exception)
def handle_exception(e):
    """Handle all exceptions and return JSON error response"""
    error_msg = str(e)
    print(f"Unhandled exception: {error_msg}")
    print(traceback.format_exc())
    return jsonify({'error': error_msg}), 500

# Create upload directory
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS

@app.route('/')
def index():
    """Main page with file selection and options"""
    files = DataFile.query.filter_by(is_active=True).order_by(DataFile.uploaded_at.desc()).all()
    return render_template('index.html', files=files)

@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle file upload"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        unique_filename = f"{timestamp}_{filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(filepath)
        
        try:
            # Process file to get metadata
            processor = DataProcessor(filepath)
            df, _ = processor.process()
            
            # Save to database
            data_file = DataFile(
                filename=unique_filename,
                original_filename=filename,
                file_path=filepath,
                rows_count=len(df),
                date_range_start=df['timestamp'].min(),
                date_range_end=df['timestamp'].max()
            )
            db.session.add(data_file)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'file_id': data_file.id,
                'filename': filename,
                'rows_count': len(df),
                'date_range': f"{df['timestamp'].min().strftime('%Y-%m-%d')} to {df['timestamp'].max().strftime('%Y-%m-%d')}"
            })
        except Exception as e:
            # Clean up file if processing fails
            if os.path.exists(filepath):
                os.remove(filepath)
            return jsonify({'error': f'Error processing file: {str(e)}'}), 400
    
    return jsonify({'error': 'Invalid file type. Please upload a CSV file.'}), 400

@app.route('/process', methods=['POST'])
def process_data():
    """Process data and generate plots based on user selections"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data received'}), 400
        
        file_id = data.get('file_id')
        month_filter = data.get('months', [])
        season_filter = data.get('seasons', [])
        plot_types = data.get('plot_types', [])
        generate_all = data.get('generate_all', False)
        
        # Comparison period settings
        enable_comparison = data.get('enable_comparison', False)
        op_start = data.get('op_start')
        op_end = data.get('op_end')
        clim_start = data.get('clim_start')
        clim_end = data.get('clim_end')
        
        if not file_id:
            return jsonify({'error': 'No file selected'}), 400
        
        # Get file from database
        data_file = DataFile.query.get_or_404(file_id)
        
        if not os.path.exists(data_file.file_path):
            return jsonify({'error': 'File not found on server'}), 404
        
        # Process data
        try:
            processor = DataProcessor(data_file.file_path)
            df, _ = processor.process()
        except Exception as e:
            import traceback
            error_msg = f'Error processing data file: {str(e)}'
            print(f"Data processing error: {error_msg}")
            print(traceback.format_exc())
            return jsonify({'error': error_msg}), 500
        
        # Convert month strings to integers
        if month_filter:
            month_filter = [int(m) for m in month_filter]
        
        # Generate regular plots
        if generate_all:
            plots = plot_gen.generate_all_plots(df, month_filter, season_filter)
        else:
            plots = {}
            for plot_type in plot_types:
                for precip_type in ['rain', 'snow']:
                    key = f'{precip_type}_{plot_type}'
                    try:
                        if plot_type == 'monthly_heatmap':
                            plots[key] = plot_gen.monthly_totals_heatmap(df, precip_type, month_filter)
                        elif plot_type == 'monthly_climatology':
                            plots[key] = plot_gen.monthly_climatology(df, precip_type, month_filter)
                        elif plot_type == 'seasonal_boxplot':
                            plots[key] = plot_gen.seasonal_boxplot(df, precip_type, season_filter)
                        elif plot_type == 'annual_totals':
                            plots[key] = plot_gen.annual_totals(df, precip_type)
                        elif plot_type == 'monthly_distribution':
                            plots[key] = plot_gen.monthly_distribution_boxplot(df, precip_type, month_filter)
                    except Exception as e:
                        plots[key] = None
                        print(f"Error generating {key}: {str(e)}")
        
        # Generate comparison plots if enabled
        comparison_plots = {}
        comparison_stats = {}
        
        if enable_comparison and op_start and op_end and clim_start and clim_end:
            try:
                from scipy import stats
                
                op_start_dt = pd.to_datetime(op_start)
                op_end_dt = pd.to_datetime(op_end)
                clim_start_dt = pd.to_datetime(clim_start)
                clim_end_dt = pd.to_datetime(clim_end)
                
                # Filter data by periods
                df_operating = df[(df['timestamp'] >= op_start_dt) & (df['timestamp'] <= op_end_dt)]
                df_climatology = df[(df['timestamp'] >= clim_start_dt) & (df['timestamp'] <= clim_end_dt)]
                
                if len(df_operating) > 0 and len(df_climatology) > 0:
                    # Generate comparison plots for both rain and snow
                    for precip_type in ['rain', 'snow']:
                        try:
                            comparison_plots[f'{precip_type}_comparison_histogram'] = plot_gen.operating_vs_climatology_histogram(
                                df_operating, df_climatology, precip_type
                            )
                            comparison_plots[f'{precip_type}_anomaly'] = plot_gen.precipitation_anomaly(
                                df_operating, df_climatology, precip_type
                            )
                            
                            # Calculate statistics
                            col_name = 'Rain_mm' if precip_type == 'rain' else 'Snow_mm'
                            monthly_op = df_operating.groupby(['Year', 'Month'])[col_name].sum().values
                            monthly_clim = df_climatology.groupby(['Year', 'Month'])[col_name].sum().values
                            
                            # Statistical tests
                            t_stat, t_pval = stats.ttest_ind(monthly_op, monthly_clim)
                            u_stat, u_pval = stats.mannwhitneyu(monthly_op, monthly_clim, alternative='two-sided')
                            ks_stat, ks_pval = stats.ks_2samp(monthly_op, monthly_clim)
                            
                            # Effect size (Cohen's d)
                            pooled_std = np.sqrt((monthly_op.std()**2 + monthly_clim.std()**2) / 2)
                            cohens_d = (monthly_op.mean() - monthly_clim.mean()) / pooled_std if pooled_std > 0 else 0
                            
                            comparison_stats[precip_type] = {
                                'operating_mean': float(monthly_op.mean()),
                                'operating_std': float(monthly_op.std()),
                                'climatology_mean': float(monthly_clim.mean()),
                                'climatology_std': float(monthly_clim.std()),
                                't_test_pvalue': float(t_pval),
                                'mannwhitney_pvalue': float(u_pval),
                                'ks_test_pvalue': float(ks_pval),
                                'cohens_d': float(cohens_d)
                            }
                        except Exception as e:
                            print(f"Error generating comparison plots for {precip_type}: {str(e)}")
            except Exception as e:
                print(f"Error in comparison analysis: {str(e)}")
        
        return jsonify({
            'plots': plots, 
            'comparison_plots': comparison_plots,
            'comparison_stats': comparison_stats,
            'success': True
        })
    
    except Exception as e:
        import traceback
        error_msg = str(e)
        print(f"Error in process_data: {error_msg}")
        print(traceback.format_exc())
        return jsonify({'error': error_msg}), 500

@app.route('/delete_file/<int:file_id>', methods=['DELETE'])
def delete_file(file_id):
    """Delete a file from database (soft delete)"""
    try:
        data_file = DataFile.query.get_or_404(file_id)
        data_file.is_active = False
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    print("=" * 60)
    print("Precipitation Data Analysis Web Application")
    print("=" * 60)
    print("\n✓ Database initialized")
    print("✓ Server starting...")
    print("\nOpen your browser and navigate to:")
    print("  http://localhost:5000")
    print("\nPress Ctrl+C to stop the server")
    print("=" * 60)
    print()
    
    # For production hosting, use environment variable for port
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)

