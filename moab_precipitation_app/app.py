from flask import Flask, render_template, request, jsonify
import os
from werkzeug.utils import secure_filename
from datetime import datetime
from models import db, DataFile
from config import Config
from data_processor import DataProcessor
from plot_generator import PlotGenerator

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

plot_gen = PlotGenerator()

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
        file_id = data.get('file_id')
        month_filter = data.get('months', [])
        season_filter = data.get('seasons', [])
        plot_types = data.get('plot_types', [])
        generate_all = data.get('generate_all', False)
        
        if not file_id:
            return jsonify({'error': 'No file selected'}), 400
        
        # Get file from database
        data_file = DataFile.query.get_or_404(file_id)
        
        if not os.path.exists(data_file.file_path):
            return jsonify({'error': 'File not found on server'}), 404
        
        # Process data
        processor = DataProcessor(data_file.file_path)
        df, _ = processor.process()
        
        # Convert month strings to integers
        if month_filter:
            month_filter = [int(m) for m in month_filter]
        
        # Generate plots
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
        
        return jsonify({'plots': plots, 'success': True})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

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

