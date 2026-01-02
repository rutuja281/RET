from flask import Flask, render_template, request, jsonify
import os
import sys
import traceback
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

@app.errorhandler(404)
def handle_404(e):
    """Handle 404 errors"""
    try:
        # Check if this is an API endpoint
        if hasattr(request, 'path') and (request.path.startswith('/process') or request.path.startswith('/upload') or request.path.startswith('/delete_file')):
            return jsonify({'error': 'Endpoint not found'}), 404
    except RuntimeError:
        # Request context not available, assume API endpoint
        return jsonify({'error': 'Endpoint not found'}), 404
    # For other routes, use default Flask 404 handling
    from flask import render_template
    return render_template('404.html'), 404 if os.path.exists('templates/404.html') else (str(e), 404)

@app.errorhandler(500)
def handle_500(e):
    """Handle 500 errors"""
    error_msg = str(e) if hasattr(e, '__str__') else 'Internal server error'
    tb_str = traceback.format_exc()
    print(f"Server error: {error_msg}", file=sys.stderr, flush=True)
    print(tb_str, file=sys.stderr, flush=True)
    
    # Return JSON for API endpoints
    try:
        if hasattr(request, 'path') and (request.path.startswith('/process') or request.path.startswith('/upload') or request.path.startswith('/delete_file')):
            return jsonify({'error': f'Server error: {error_msg}'}), 500
    except RuntimeError:
        # Request context not available, assume API endpoint
        pass
    # Always return JSON to be safe
    return jsonify({'error': error_msg}), 500

@app.errorhandler(Exception)
def handle_exception(e):
    """Handle all other exceptions and return JSON error response for API endpoints"""
    error_msg = str(e) if hasattr(e, '__str__') else 'Unknown error'
    tb_str = traceback.format_exc()
    print(f"Unhandled exception: {error_msg}", file=sys.stderr, flush=True)
    print(tb_str, file=sys.stderr, flush=True)
    
    # Return JSON for API endpoints
    try:
        if hasattr(request, 'path') and (request.path.startswith('/process') or request.path.startswith('/upload') or request.path.startswith('/delete_file')):
            return jsonify({'error': error_msg}), 500
    except RuntimeError:
        # Request context not available, assume API endpoint
        pass
    # Always return JSON for exceptions to avoid HTML error pages
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
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not file or not allowed_file(file.filename):
            return jsonify({'error': 'Invalid file type. Please upload a CSV file.'}), 400
        
        # Ensure upload directory exists
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        unique_filename = f"{timestamp}_{filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        
        try:
            file.save(filepath)
        except Exception as e:
            error_msg = f'Error saving file: {str(e)}'
            print(error_msg, file=sys.stderr, flush=True)
            return jsonify({'error': error_msg}), 500
        
        try:
            # Process file to get metadata
            processor = DataProcessor(filepath)
            df, _ = processor.process()
            
            # Validate that we have data
            if len(df) == 0:
                if os.path.exists(filepath):
                    os.remove(filepath)
                return jsonify({'error': 'File processed but contains no valid data rows'}), 400
            
            # Save to database
            # Convert pandas Timestamp to Python datetime for database
            date_start = df['timestamp'].min()
            date_end = df['timestamp'].max()
            
            # Convert to Python datetime if it's a pandas Timestamp
            if hasattr(date_start, 'to_pydatetime'):
                date_start = date_start.to_pydatetime()
            if hasattr(date_end, 'to_pydatetime'):
                date_end = date_end.to_pydatetime()
            
            data_file = DataFile(
                filename=unique_filename,
                original_filename=filename,
                file_path=filepath,
                rows_count=len(df),
                date_range_start=date_start,
                date_range_end=date_end
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
                try:
                    os.remove(filepath)
                except:
                    pass
            error_msg = f'Error processing file: {str(e)}'
            tb_str = traceback.format_exc()
            print(f"Upload error: {error_msg}", file=sys.stderr, flush=True)
            print(tb_str, file=sys.stderr, flush=True)
            return jsonify({'error': error_msg}), 400
    except Exception as e:
        # Catch any other errors in the upload endpoint
        error_msg = f'Error in upload endpoint: {str(e)}'
        tb_str = traceback.format_exc()
        print(error_msg, file=sys.stderr, flush=True)
        print(tb_str, file=sys.stderr, flush=True)
        return jsonify({'error': error_msg}), 500

@app.route('/process', methods=['POST'])
def process_data():
    """Process data and generate plots based on user selections"""
    import gc  # For garbage collection
    
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
        data_file = DataFile.query.get(file_id)
        if not data_file:
            return jsonify({'error': f'File with ID {file_id} not found'}), 404
        
        if not os.path.exists(data_file.file_path):
            return jsonify({'error': 'File not found on server'}), 404
        
        # Process data
        try:
            processor = DataProcessor(data_file.file_path)
            df, _ = processor.process()
            # Force garbage collection after processing to free memory
            gc.collect()
        except Exception as e:
            error_msg = f'Error processing data file: {str(e)}'
            tb_str = traceback.format_exc()
            print(f"Data processing error: {error_msg}", file=sys.stderr, flush=True)
            print(tb_str, file=sys.stderr, flush=True)
            return jsonify({'error': error_msg}), 500
        
        # Convert month strings to integers
        if month_filter:
            try:
                month_filter = [int(m) for m in month_filter]
            except (ValueError, TypeError) as e:
                error_msg = f'Invalid month filter: {str(e)}'
                print(f"Month filter error: {error_msg}", file=sys.stderr, flush=True)
                return jsonify({'error': error_msg}), 400
        
        # Generate regular plots
        plots = {}
        try:
            if generate_all:
                # Limit number of plots for "generate all" to avoid timeout (Render free tier limit)
                # Generate only 2 essential plots to stay within timeout
                plots = {}
                essential_plots = ['annual_totals', 'monthly_climatology']  # Reduced from 3 to 2
                for plot_type in essential_plots:
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
                            elif plot_type == 'monthly_histogram':
                                plots[key] = plot_gen.monthly_histogram(df, precip_type, month_filter)
                            gc.collect()
                        except Exception as e:
                            plots[key] = None
                            tb_str = traceback.format_exc()
                            print(f"Error generating {key}: {str(e)}", file=sys.stderr, flush=True)
                            print(tb_str, file=sys.stderr, flush=True)
            else:
                # Check if any plot types were selected
                if not plot_types or len(plot_types) == 0:
                    return jsonify({
                        'error': 'No plot types selected. Please select at least one plot type.',
                        'suggestion': 'Check at least one plot type checkbox before generating'
                    }), 400
                
                # Limit number of plots per request to avoid timeout (Render free tier has 30s timeout)
                max_plots = 4  # Limit to 4 plots (2 plot types × 2 precip types)
                if len(plot_types) * 2 > max_plots:
                    return jsonify({
                        'error': f'Too many plots requested. Maximum {max_plots} plots at a time (2 plot types). Please select fewer plot types.',
                        'requested': len(plot_types) * 2,
                        'limit': max_plots,
                        'suggestion': 'Try selecting 1-2 plot types at a time'
                    }), 400
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
                            elif plot_type == 'monthly_histogram':
                                plots[key] = plot_gen.monthly_histogram(df, precip_type, month_filter)
                            # Force garbage collection after each plot to free memory
                            gc.collect()
                        except Exception as e:
                            plots[key] = None
                            tb_str = traceback.format_exc()
                            print(f"Error generating {key}: {str(e)}", file=sys.stderr, flush=True)
                            print(tb_str, file=sys.stderr, flush=True)
            # Force garbage collection after plot generation
            gc.collect()
        except Exception as e:
            error_msg = f'Error generating plots: {str(e)}'
            tb_str = traceback.format_exc()
            print(error_msg, file=sys.stderr, flush=True)
            print(tb_str, file=sys.stderr, flush=True)
            return jsonify({'error': error_msg}), 500
        
        # Generate comparison plots if enabled
        comparison_plots = {}
        comparison_stats = {}
        
        if enable_comparison and op_start and op_end and clim_start and clim_end:
            try:
                from scipy import stats
                
                try:
                    op_start_dt = pd.to_datetime(op_start)
                    op_end_dt = pd.to_datetime(op_end)
                    clim_start_dt = pd.to_datetime(clim_start)
                    clim_end_dt = pd.to_datetime(clim_end)
                except Exception as e:
                    error_msg = f'Error parsing date strings: {str(e)}'
                    print(error_msg, file=sys.stderr, flush=True)
                    return jsonify({'error': error_msg}), 400
                
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
                            tb_str = traceback.format_exc()
                            print(f"Error generating comparison plots for {precip_type}: {str(e)}", file=sys.stderr, flush=True)
                            print(tb_str, file=sys.stderr, flush=True)
                else:
                    error_msg = f'No data in selected periods: operating={len(df_operating)}, climatology={len(df_climatology)}'
                    print(error_msg, file=sys.stderr, flush=True)
                    return jsonify({'error': error_msg}), 400
            except Exception as e:
                error_msg = f'Error in comparison analysis: {str(e)}'
                tb_str = traceback.format_exc()
                print(error_msg, file=sys.stderr, flush=True)
                print(tb_str, file=sys.stderr, flush=True)
                return jsonify({'error': error_msg}), 500
        
        # Prepare response - filter out None values and ensure all values are serializable
        try:
            # Clean up plots dictionary - remove None values to reduce response size
            cleaned_plots = {k: v for k, v in plots.items() if v is not None}
            cleaned_comparison_plots = {k: v for k, v in comparison_plots.items() if v is not None}
            
            # Check response size (estimate - base64 strings are roughly 4/3 of original size)
            total_size = sum(len(v) if isinstance(v, str) else 0 for v in list(cleaned_plots.values()) + list(cleaned_comparison_plots.values()))
            
            # If response is too large (> 5MB), return error
            if total_size > 5 * 1024 * 1024:
                return jsonify({
                    'error': 'Response too large. Please generate fewer plots at a time.',
                    'estimated_size_mb': round(total_size / (1024 * 1024), 2)
                }), 413  # 413 Payload Too Large
            
            response_data = {
                'plots': cleaned_plots, 
                'comparison_plots': cleaned_comparison_plots,
                'comparison_stats': comparison_stats,
                'success': True
            }
            
            # Force garbage collection before returning response
            gc.collect()
            
            return jsonify(response_data)
        except Exception as e:
            error_msg = f'Error serializing response: {str(e)}'
            tb_str = traceback.format_exc()
            print(error_msg, file=sys.stderr, flush=True)
            print(tb_str, file=sys.stderr, flush=True)
            return jsonify({'error': error_msg}), 500
    
    except Exception as e:
        error_msg = str(e)
        tb_str = traceback.format_exc()
        print(f"Error in process_data: {error_msg}", file=sys.stderr, flush=True)
        print(tb_str, file=sys.stderr, flush=True)
        return jsonify({'error': error_msg}), 500

@app.route('/delete_file/<int:file_id>', methods=['DELETE'])
def delete_file(file_id):
    """Delete a file from database (soft delete)"""
    try:
        data_file = DataFile.query.get(file_id)
        if not data_file:
            return jsonify({'error': f'File with ID {file_id} not found'}), 404
        data_file.is_active = False
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        error_msg = str(e)
        print(f"Error deleting file: {error_msg}", file=sys.stderr, flush=True)
        return jsonify({'error': error_msg}), 500

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

