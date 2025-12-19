import pandas as pd
import numpy as np
from datetime import datetime
import os

class DataProcessor:
    """Handle data cleaning and processing for multiple file formats"""
    
    def __init__(self, filepath, header_row=None):
        self.filepath = filepath
        self.header_row = header_row
        self.file_format = None  # 'meteoblue' or 'synopticx'
        self.df = None
        
    def detect_file_format(self):
        """Detect if file is MeteoBlue or SynopticX format"""
        with open(self.filepath, 'r', encoding='utf-8-sig', errors='ignore') as f:
            first_lines = [f.readline().strip() for _ in range(15)]
        
        # Check for SynopticX indicators
        if any('STATION:' in line or 'SYNOPTIC' in line.upper() or 'Synoptic' in line 
               for line in first_lines[:10]):
            # Also check for Date_Time column (SynopticX uses this)
            for i, line in enumerate(first_lines):
                if 'Date_Time' in line:
                    self.file_format = 'synopticx'
                    self.header_row = i
                    return
        
        # Check for MeteoBlue indicators
        for i, line in enumerate(first_lines):
            if line.lower().startswith('timestamp') and 'moab' in ' '.join(first_lines[:i]).lower():
                self.file_format = 'meteoblue'
                self.header_row = i if self.header_row is None else self.header_row
                return
        
        # Default to MeteoBlue with header_row=9
        self.file_format = 'meteoblue'
        if self.header_row is None:
            self.header_row = 9
    
    def load_data(self):
        """Load CSV file (MeteoBlue or SynopticX format)"""
        # Detect file format first
        self.detect_file_format()
        
        if self.file_format == 'synopticx':
            return self._load_synopticx()
        else:
            return self._load_meteoblue()
    
    def _load_meteoblue(self):
        """Load MeteoBlue CSV format"""
        df = pd.read_csv(self.filepath, skiprows=self.header_row)
        df['timestamp'] = pd.to_datetime(df['timestamp'], format='%Y%m%dT%H%M')
        self.df = self._clean_column_names(df)
        return self.df
    
    def _load_synopticx(self):
        """Load SynopticX CSV format"""
        # Header is on line with Date_Time (typically index 10)
        # Units row is right after header (skip it)
        # Data starts after units row
        
        # Read with header at detected row, but skip the units row right after
        df = pd.read_csv(self.filepath, skiprows=list(range(self.header_row)) + [self.header_row + 1])
        
        # Parse timestamp - SynopticX uses Date_Time column with format like "2020-09-30T02:40:00-0600"
        if 'Date_Time' in df.columns:
            df['timestamp'] = pd.to_datetime(df['Date_Time'], errors='coerce', utc=True)
            # Remove timezone for consistency
            if df['timestamp'].dt.tz is not None:
                df['timestamp'] = df['timestamp'].dt.tz_localize(None)
            df = df.dropna(subset=['timestamp'])
        else:
            raise ValueError(f"Date_Time column not found in SynopticX file. Columns: {list(df.columns)}")
        
        # Standardize column names for SynopticX
        df = self._standardize_synopticx_columns(df)
        self.df = df
        return self.df
    
    def _standardize_synopticx_columns(self, df):
        """Standardize SynopticX column names to match expected format"""
        rename_map = {}
        
        # Map SynopticX columns to standard names
        column_mapping = {
            'air_temp_set_1': 'Temperature_2m',
            'relative_humidity_set_1': 'Relative_Humidity_2m',
            'wind_speed_set_1': 'Wind_Speed_10m',
            'wind_direction_set_1': 'Wind_Direction_10m',
            'wind_gust_set_1': 'Wind_Gust',
            'snow_depth_set_1': 'Snow_Depth',
            'precip_accum_ten_minute_set_1': 'Precipitation_Total',
            'estimated_snowfall_rate_set_1': 'Snowfall_Amount'
        }
        
        for old_col, new_col in column_mapping.items():
            if old_col in df.columns:
                rename_map[old_col] = new_col
        
        # Rename columns
        df = df.rename(columns=rename_map)
        
        # For SynopticX, precipitation is already in mm, but snowfall rate might need conversion
        # Snowfall rate is in mm/hour, we may need to convert to accumulated snow
        # For now, we'll treat estimated_snowfall_rate as snowfall amount (if available)
        # If Snowfall_Amount exists, keep it; otherwise set to 0
        if 'Snowfall_Amount' not in df.columns or df['Snowfall_Amount'].isna().all():
            df['Snowfall_Amount'] = 0
        
        return df
    
    def _clean_column_names(self, df):
        """Simplify column names"""
        rename_map = {}
        for col in df.columns:
            new_name = col
            if col.startswith('Moab '):
                new_name = col.replace('Moab ', '')
            
            # Simplify bracketed qualifiers
            if '[2 m elevation corrected]' in new_name:
                new_name = new_name.replace(' [2 m elevation corrected]', '_2m')
            elif '[850 mb]' in new_name:
                new_name = new_name.replace(' [850 mb]', '_850mb')
            elif '[700 mb]' in new_name:
                new_name = new_name.replace(' [700 mb]', '_700mb')
            elif '[10 m]' in new_name:
                new_name = new_name.replace(' [10 m]', '_10m')
            elif '[2 m]' in new_name:
                new_name = new_name.replace(' [2 m]', '_2m')
            elif '[sfc]' in new_name:
                new_name = new_name.replace(' [sfc]', '')
            elif '[MSL]' in new_name:
                new_name = new_name.replace(' [MSL]', '')
            
            # Remove any remaining brackets
            if '[' in new_name:
                new_name = new_name.split('[')[0].strip()
            
            # Replace spaces with underscores
            new_name = new_name.replace(' ', '_')
            rename_map[col] = new_name
        
        return df.rename(columns=rename_map)
    
    def handle_missing_values(self, df):
        """Handle missing values by variable type"""
        # Define variable categories
        ACCUMULATION_VARS = ['Precipitation_Total', 'Snowfall_Amount', 'Snow_Depth']
        TEMPERATURE_VARS = ['Temperature_2m', 'Temperature_850mb', 'Temperature_700mb']
        WIND_SPEED_VARS = ['Wind_Speed_10m', 'Wind_Speed_850mb', 'Wind_Speed_700mb', 'Wind_Gust']
        WIND_DIR_VARS = ['Wind_Direction_10m', 'Wind_Direction_850mb', 'Wind_Direction_700mb']
        HUMIDITY_VARS = ['Relative_Humidity_2m']
        PRESSURE_HEIGHT_VARS = ['Mean_Sea_Level_Pressure', 'Geopotential_Height_850mb', 
                                'Geopotential_Height_700mb', 'PBL_Height']
        CLOUD_VARS = ['Cloud_Cover_Total', 'Cloud_Cover_High', 'Cloud_Cover_Medium', 'Cloud_Cover_Low']
        RADIATION_VARS = ['Shortwave_Radiation', 'CAPE']
        
        # 1. Accumulation variables - Fill with 0
        for col in ACCUMULATION_VARS:
            if col in df.columns and df[col].isnull().sum() > 0:
                df[col] = df[col].fillna(0)
        
        # 2. Temperature variables - Linear interpolation
        for col in TEMPERATURE_VARS:
            if col in df.columns and df[col].isnull().sum() > 0:
                df[col] = pd.to_numeric(df[col], errors='coerce').interpolate(method='linear', limit=6, limit_direction='both')
                df[col] = df[col].ffill().bfill()
        
        # 3. Wind speed variables - Linear interpolation
        for col in WIND_SPEED_VARS:
            if col in df.columns and df[col].isnull().sum() > 0:
                df[col] = df[col].interpolate(method='linear', limit=6, limit_direction='both')
                df[col] = df[col].ffill().bfill()
        
        # 4. Wind direction variables - Forward fill
        for col in WIND_DIR_VARS:
            if col in df.columns and df[col].isnull().sum() > 0:
                df[col] = pd.to_numeric(df[col], errors='coerce').ffill(limit=6).bfill()
        
        # 5. Humidity variables - Linear interpolation
        for col in HUMIDITY_VARS:
            if col in df.columns and df[col].isnull().sum() > 0:
                df[col] = df[col].interpolate(method='linear', limit=6, limit_direction='both')
                df[col] = df[col].ffill().bfill()
        
        # 6. Pressure and geopotential height - Linear interpolation
        for col in PRESSURE_HEIGHT_VARS:
            if col in df.columns and df[col].isnull().sum() > 0:
                df[col] = df[col].interpolate(method='linear', limit=6, limit_direction='both')
                df[col] = df[col].ffill().bfill()
        
        # 7. Cloud cover - Forward fill
        for col in CLOUD_VARS:
            if col in df.columns and df[col].isnull().sum() > 0:
                df[col] = pd.to_numeric(df[col], errors='coerce').ffill(limit=6).bfill()
        
        # 8. Radiation and CAPE - Fill with 0
        for col in RADIATION_VARS:
            if col in df.columns and df[col].isnull().sum() > 0:
                df[col] = df[col].fillna(0)
        
        # Handle any remaining columns
        remaining_cols = [col for col in df.columns if col != 'timestamp' and df[col].isnull().sum() > 0]
        for col in remaining_cols:
            df[col] = df[col].interpolate(method='linear', limit=6, limit_direction='both')
            df[col] = df[col].ffill().bfill()
        
        return df
    
    def create_time_columns(self, df):
        """Create derived time columns"""
        df['Year'] = df['timestamp'].dt.year
        df['Month'] = df['timestamp'].dt.month
        df['Day'] = df['timestamp'].dt.day
        
        def get_season(month):
            if month in [12, 1, 2]:
                return 'DJF'
            elif month in [3, 4, 5]:
                return 'MAM'
            elif month in [6, 7, 8]:
                return 'JJA'
            else:
                return 'SON'
        
        df['Season'] = df['Month'].apply(get_season)
        df['WarmCold'] = df['Month'].apply(
            lambda m: 'Warm' if m in [4,5,6,7,8,9,10] else 'Cold'
        )
        
        return df
    
    def separate_precipitation(self, df):
        """Separate rain from snow"""
        # Find columns
        precip_col = None
        snow_col = None
        
        for c in df.columns:
            if 'Precipitation' in c and 'Total' in c:
                precip_col = c
            if 'Snowfall' in c:
                snow_col = c
        
        if not precip_col:
            raise ValueError("Precipitation column not found")
        
        # Calculate rain = total precipitation - snowfall
        if snow_col and snow_col in df.columns:
            # Check if snowfall is in cm (MeteoBlue) or mm (SynopticX)
            # MeteoBlue typically has snowfall in cm, SynopticX uses mm
            if self.file_format == 'synopticx':
                # SynopticX: snowfall rate might be in mm/hour, but we'll use as-is
                # For SynopticX, if we have estimated_snowfall_rate, use it directly (already in mm)
                df['Snow_mm'] = pd.to_numeric(df[snow_col], errors='coerce').fillna(0)
            else:
                # MeteoBlue: snowfall is typically in cm, convert to mm
                df['Snow_mm'] = pd.to_numeric(df[snow_col], errors='coerce').fillna(0) * 10
            
            # Calculate rain
            precip_values = pd.to_numeric(df[precip_col], errors='coerce').fillna(0)
            df['Rain_mm'] = (precip_values - df['Snow_mm']).clip(lower=0)
        else:
            # If no snow column, assume all precipitation is rain
            df['Rain_mm'] = pd.to_numeric(df[precip_col], errors='coerce').fillna(0)
            df['Snow_mm'] = 0
        
        return df, precip_col
    
    def process(self):
        """Full processing pipeline"""
        df = self.load_data()
        df = self.handle_missing_values(df)
        df = self.create_time_columns(df)
        df, precip_col = self.separate_precipitation(df)
        return df, precip_col

