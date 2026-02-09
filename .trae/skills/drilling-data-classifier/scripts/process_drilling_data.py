#!/usr/bin/env python3
"""
Drilling Data Processing Script

This script processes drilling classification data by:
1. Calculating main factors (F1, F2) and MSE
2. Handling A/B column adjustments for drilling pressure and rotation speed
3. Organizing data into classified folders based on configuration
4. Performing data transformations and formatting

Usage:
    python process_drilling_data.py <input_csv> [config_file]
    python process_drilling_data.py --default [config_file]
"""

import argparse
import csv
import json
import os
import sys
import pandas as pd
import numpy as np
import math
from decimal import Decimal, ROUND_HALF_UP
from collections import defaultdict
from pathlib import Path
import chardet

# Version information
VERSION = "1.0.0"


def get_version():
    """Return the version of the program."""
    return f"Drilling Data Processor v{VERSION}"


def find_config_file(config_filename="fmse.config.json"):
    """Find configuration file in current directory or user's .CCQ.config folder."""
    # First, look in current directory
    current_dir_config = Path(config_filename)
    if current_dir_config.exists():
        return current_dir_config
    
    # Then, look in user's .CCQ.config folder
    user_home = Path.home()
    user_config_dir = user_home / ".CCQ.config"
    user_config_file = user_config_dir / config_filename
    
    if user_config_file.exists():
        return user_config_file
    
    return None


def validate_config(config):
    """Validate the configuration file format."""
    required_keys = ['classification_config', 'column_mapping', 'columns_to_extract', 'output_column_order']
    
    for key in required_keys:
        if key not in config:
            raise ValueError(f"Missing required key '{key}' in configuration file")
    
    # Validate classification_config
    if not isinstance(config['classification_config'], dict):
        raise ValueError("classification_config must be a dictionary")
    
    # Validate column_mapping
    if not isinstance(config['column_mapping'], dict):
        raise ValueError("column_mapping must be a dictionary")
    
    # Validate columns_to_extract
    if not isinstance(config['columns_to_extract'], list):
        raise ValueError("columns_to_extract must be a list")
    
    # Validate output_column_order
    if not isinstance(config['output_column_order'], list):
        raise ValueError("output_column_order must be a list")


def calculate_adjusted_value(val_a, val_b, k_func):
    """
    Calculate adjusted value based on A/B values and corresponding k function
    val_a: A value
    val_b: B value
    k_func: Function to calculate k value based on difference
    """
    min_val = min(val_a, val_b)
    diff = abs(val_a - val_b)
    k = k_func(diff)
    return min_val + k * diff


def get_k_drilling_pressure(diff):
    """Get k1 value based on drilling pressure difference"""
    if diff <= 50:
        return 0.5
    elif diff <= 100:
        return 0.66
    elif diff <= 200:
        return 0.8
    else:
        return 0.86


def get_k_rotation_speed(diff):
    """Get k2 value based on rotation speed difference"""
    if diff <= 50:
        return 0.5
    elif diff <= 100:
        return 0.66
    elif diff <= 200:
        return 0.8
    else:
        return 0.86


def calculate_dynamic_specific_energy(drilling_pressure, rotation_speed, bit_size, mechanical_rate):
    """
    Calculate dynamic specific energy
    Dynamic specific energy = drilling_pressure * rotation_speed / bit_size / mechanical_rate
    """
    # Avoid division by zero
    if bit_size == 0 or mechanical_rate == 0:
        return float('inf') if mechanical_rate == 0 else 0
    
    return drilling_pressure * rotation_speed / bit_size / mechanical_rate


def calculate_f1(progress, mechanical_rate, dynamic_specific_energy, drilling_pressure, rotation_speed):
    """
    Calculate F1
    F1 = 0.58*progress + 0.53*mechanical_rate + 0.5/dynamic_specific_energy - 0.31/drilling_pressure - 0.18/rotation_speed
    """
    # Avoid division by zero
    dse_reciprocal = 0 if dynamic_specific_energy == 0 else 1 / dynamic_specific_energy
    dp_reciprocal = 0 if drilling_pressure == 0 else 1 / drilling_pressure
    rs_reciprocal = 0 if rotation_speed == 0 else 1 / rotation_speed
    
    f1 = (0.58 * progress + 
          0.53 * mechanical_rate + 
          0.5 * dse_reciprocal - 
          0.31 * dp_reciprocal - 
          0.18 * rs_reciprocal)
          
    return f1


def calculate_f2(progress, mechanical_rate, dynamic_specific_energy, drilling_pressure, rotation_speed):
    """
    Calculate F2
    F2 = -0.17*progress + 0.06*mechanical_rate + 0.04/dynamic_specific_energy - 0.61/drilling_pressure - 0.77/rotation_speed
    """
    # Avoid division by zero
    dse_reciprocal = 0 if dynamic_specific_energy == 0 else 1 / dynamic_specific_energy
    dp_reciprocal = 0 if drilling_pressure == 0 else 1 / drilling_pressure
    rs_reciprocal = 0 if rotation_speed == 0 else 1 / rotation_speed
    
    f2 = (-0.17 * progress + 
          0.06 * mechanical_rate + 
          0.04 * dse_reciprocal - 
          0.61 * dp_reciprocal - 
          0.77 * rs_reciprocal)
          
    return f2


def calculate_mse(drilling_pressure, bit_size, rotation_speed, mechanical_rate):
    """
    Calculate MSE
    MSE = drilling_pressure/(π*bit_size^2/4) + (480*rotation_speed*drilling_pressure)/(bit_size*mechanical_rate)
    """
    # Avoid division by zero
    if bit_size == 0 or mechanical_rate == 0:
        return float('inf')
    
    term1 = drilling_pressure / (math.pi * (bit_size/2)**2)
    term2 = (480 * rotation_speed * drilling_pressure) / (bit_size * mechanical_rate)
    
    return term1 + term2


def format_number(value):
    """
    Format number to 2 decimal places or 4 significant digits (automatically selected based on value size)
    """
    if pd.isna(value):
        return value
    
    original_value = float(value)
    
    # For zero or near-zero values
    if original_value == 0:
        return 0.00
    
    # Decide format based on value size
    abs_val = abs(original_value)
    
    if abs_val >= 0.01:
        # For values >= 0.01, keep 2 decimal places
        formatted = round(original_value, 2)
        # Ensure returned value displays with 2 decimal places
        return float(f"{formatted:.2f}")
    else:
        # For values < 0.01, use 4 significant digits
        return float(f"{original_value:.4g}")


def format_number_util(num):
    """Format number to either 2 decimal places or 4 significant digits."""
    if isinstance(num, str):
        try:
            num = float(num)
        except ValueError:
            return num
    
    # Format to 4 significant digits, but with max 2 decimal places
    if num == 0:
        return 0
    
    # Format to 4 significant digits using g format, but ensure max 2 decimal places for practical purposes
    formatted = float(f'{num:.4g}')
    
    # If it's a whole number, return as int
    if formatted.is_integer():
        return int(formatted)
    
    # Limit to 2 decimal places max for readability
    return round(formatted, 2)


def process_drilling_data(csv_file_path):
    """
    Process drilling data, add main factors and MSE columns
    """
    # Use smarter way to detect and read CSV file encoding
    with open(csv_file_path, 'rb') as f:
        raw_data = f.read()
        encoding = chardet.detect(raw_data)['encoding']
    
    df = pd.read_csv(csv_file_path, encoding=encoding)
    
    # Initialize result arrays
    main_factors = []
    mses = []
    
    # Iterate through each row of data
    for index, row in df.iterrows():
        try:
            # Get data
            progress = row['进尺']
            mechanical_rate = row['机械钻速']
            bit_size = row['钻头尺寸mm']
            
            # Check if A/B column data exists
            if '钻压A' in df.columns and '钻压B' in df.columns:
                drilling_pressure_a = row['钻压A']
                drilling_pressure_b = row['钻压B']
                
                # Calculate adjusted drilling pressure
                adjusted_drilling_pressure = calculate_adjusted_value(
                    drilling_pressure_a, 
                    drilling_pressure_b, 
                    get_k_drilling_pressure
                )
            else:
                # If no A/B columns, use drilling pressure field directly
                adjusted_drilling_pressure = row['钻压']
            
            if '转速A' in df.columns and '转速B' in df.columns:
                rotation_speed_a = row['转速A']
                rotation_speed_b = row['转速B']
                
                # Calculate adjusted rotation speed
                adjusted_rotation_speed = calculate_adjusted_value(
                    rotation_speed_a, 
                    rotation_speed_b, 
                    get_k_rotation_speed
                )
            else:
                # If no A/B columns, use rotation speed field directly
                adjusted_rotation_speed = row['转速']
            
            # Calculate dynamic specific energy
            dynamic_specific_energy = calculate_dynamic_specific_energy(
                adjusted_drilling_pressure, 
                adjusted_rotation_speed, 
                bit_size, 
                mechanical_rate
            )
            
            # Calculate F1 and F2
            f1 = calculate_f1(progress, mechanical_rate, dynamic_specific_energy, adjusted_drilling_pressure, adjusted_rotation_speed)
            f2 = calculate_f2(progress, mechanical_rate, dynamic_specific_energy, adjusted_drilling_pressure, adjusted_rotation_speed)
            
            # Calculate main factor
            main_factor = 0.68 * f1 + 0.32 * f2
            
            # Calculate MSE
            mse = calculate_mse(adjusted_drilling_pressure, bit_size, adjusted_rotation_speed, mechanical_rate)
            
            # Format values
            formatted_main_factor = format_number(main_factor)
            formatted_mse = format_number(mse)
            
            main_factors.append(formatted_main_factor)
            mses.append(formatted_mse)
            
        except Exception as e:
            print(f"Error processing row {index+1}: {e}")
            # Add default values
            main_factors.append(np.nan)
            mses.append(np.nan)
    
    # Add new columns to DataFrame
    df['主因子'] = main_factors
    df['MSE'] = mses
    
    # Ensure main factor and MSE column formatting
    df['主因子'] = df['主因子'].apply(lambda x: f"{x:.2f}" if not pd.isna(x) else x)
    df['MSE'] = df['MSE'].apply(lambda x: f"{x:.2f}" if not pd.isna(x) else x)
    
    return df


def load_config(config_file):
    """Load the configuration file."""
    with open(config_file, 'r', encoding='utf-8') as f:
        config = json.load(f)
    return config


def create_output_structure(data, config):
    """Organize the data according to the configuration."""
    classification_config = config['classification_config']
    classification_field = classification_config['classification_fields'][0]['name']
    sub_classification_field = classification_config['classification_fields'][0]['sub_classification']['name']
    
    # Group data by the primary classification field
    primary_groups = defaultdict(lambda: defaultdict(list))
    
    for row in data:
        primary_value = str(row[classification_field])
        sub_value = str(row[sub_classification_field])
        primary_groups[primary_value][sub_value].append(row)
    
    return primary_groups


def write_output_files(primary_groups, config):
    """Write the organized data to output files."""
    classification_config = config['classification_config']
    output_dir = classification_config['output_directory']
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    for primary_key, sub_groups in primary_groups.items():
        # Create a subdirectory for the primary classification
        primary_dir = os.path.join(output_dir, primary_key)
        os.makedirs(primary_dir, exist_ok=True)
        
        for sub_key, rows in sub_groups.items():
            # Create filename with prefix if configured
            if classification_config.get('filename_prefix', False):
                filename = f"{primary_key}_{sub_key}.csv"
            else:
                filename = f"{sub_key}.csv"
            
            filepath = os.path.join(primary_dir, filename)
            
            # Write the CSV file
            if rows:
                with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
                    fieldnames = rows[0].keys()
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    
                    # Write header
                    writer.writeheader()
                    
                    # Write rows
                    for row in rows:
                        writer.writerow(row)


def process_csv(input_file, output_file, config):
    """Process the CSV file according to the configuration."""
    # Load configuration
    column_mapping = config.get('column_mapping', {})
    columns_to_extract = config.get('columns_to_extract', [])
    
    # Read the input CSV file
    with open(input_file, 'r', encoding='utf-8-sig') as infile:  # utf-8-sig handles BOM
        reader = csv.DictReader(infile)
        rows = list(reader)
    
    # Process the data
    processed_rows = []
    for row in rows:
        processed_row = {}
        
        # Handle all original columns, applying transformations where needed
        for key, value in row.items():
            # Normalize the key by removing BOM if present
            normalized_key = key.replace('\ufeff', '')
            
            # Check if this column needs to be renamed
            if normalized_key in column_mapping:
                new_col_name = column_mapping[normalized_key]
                
                # Special handling for MSE -> ESM calculation
                if normalized_key == 'MSE':
                    try:
                        mse_value = float(value) if value != '' else 0
                        if mse_value != 0:
                            esm_value = 6000 / mse_value
                            # Format to either 2 decimal places or 4 significant digits
                            processed_row[new_col_name] = format_number_util(esm_value)
                        else:
                            processed_row[new_col_name] = 0  # or some other default value
                    except ValueError:
                        processed_row[new_col_name] = 0  # handle non-numeric values
                else:
                    # Apply formatting to numeric values in renamed columns if needed
                    try:
                        # Try to convert to float to check if it's numeric
                        float_val = float(value)
                        # Only format if it's not a simple integer-like serial number
                        if normalized_key == '入井次数' or normalized_key == '序号':
                            # For serial numbers and entry count, preserve original form if possible
                            if float_val.is_integer():
                                processed_row[new_col_name] = int(float_val)
                            else:
                                processed_row[new_col_name] = format_number_util(float_val)
                        else:
                            processed_row[new_col_name] = format_number_util(float_val)
                    except ValueError:
                        # Not a numeric value, keep as is
                        processed_row[new_col_name] = value
            # Check if this column is in the extract list (and wasn't renamed)
            elif normalized_key in columns_to_extract:
                # Apply formatting to numeric values in extracted columns if needed
                try:
                    float_val = float(value)
                    if normalized_key == '入井次数' or normalized_key == '序号':
                        # For serial numbers and entry count, preserve original form if possible
                        if float_val.is_integer():
                            processed_row[normalized_key] = int(float_val)
                        else:
                            processed_row[normalized_key] = format_number_util(float_val)
                    else:
                        processed_row[normalized_key] = format_number_util(float_val)
                except ValueError:
                    # Not a numeric value, keep as is
                    processed_row[normalized_key] = value
            # Also include the serial number column which might not be in either list
            elif normalized_key == '序号':
                # Apply formatting to numeric values
                try:
                    float_val = float(value)
                    if float_val.is_integer():
                        processed_row['序号'] = int(float_val)
                    else:
                        processed_row['序号'] = format_number_util(float_val)
                except ValueError:
                    # Not a numeric value, keep as is
                    processed_row['序号'] = value
            # For other columns not in mapping or extraction list, we skip them
        
        processed_rows.append(processed_row)
    
    # Get the desired column order from the config
    final_headers = config['output_column_order']
    
    # Write the output CSV file
    with open(output_file, 'w', newline='', encoding='utf-8-sig') as outfile:
        writer = csv.DictWriter(outfile, fieldnames=final_headers)
        writer.writeheader()
        writer.writerows(processed_rows)


def main():
    """Main function that orchestrates the complete workflow."""
    parser = argparse.ArgumentParser(description='Process drilling classification data')
    parser.add_argument('csv_file', nargs='?', help='Input CSV file to process')
    parser.add_argument('config_file', nargs='?', default='fmse.config.json', help='Configuration file (default: fmse.config.json)')
    parser.add_argument('--default', '-d', action='store_true', help='Use input/output files specified in the configuration file')
    parser.add_argument('--version', '-v', action='store_true', help='Show version information')
    
    args = parser.parse_args()
    
    # Handle version flag
    if args.version:
        print(get_version())
        return
    
    # Find and load configuration file first (needed for default mode)
    config_path = find_config_file(args.config_file)
    if config_path is None:
        print(f"Error: Configuration file '{args.config_file}' not found in current directory or in ~/.CCQ.config/")
        return
    
    # Handle default flag - if --default is specified, use files from config
    if args.default:
        try:
            print(f"Loading configuration from {config_path}")
            config = load_config(str(config_path))
            
            # Validate configuration
            validate_config(config)
            
            # Extract input and output files from config
            if 'input_file' not in config or 'output_file' not in config:
                print(f"Error: Configuration file '{config_path}' must contain 'input_file' and 'output_file' keys for --default mode.")
                return
                
            input_file = config['input_file']
            processed_file = config['output_file']
            intermediate_file = "CCQ_Classification_with_factors.csv"  # Still needed as intermediate step
            
            print("Configuration loaded and validated successfully")
            print(f"Using input file: {input_file}")
            print(f"Using output file: {processed_file}")
        except json.JSONDecodeError as e:
            print(f"Error: Invalid JSON format in configuration file '{config_path}': {e}")
            return
        except ValueError as e:
            print(f"Error: Invalid configuration format in '{config_path}': {e}")
            return
        except Exception as e:
            print(f"Error: Failed to load configuration from '{config_path}': {e}")
            return
    else:
        # Check if CSV file is provided
        if not args.csv_file:
            print("Error: CSV file is required (unless --default option is used).")
            parser.print_help()
            return
        input_file = args.csv_file
        
        # Load config after determining if we're in default mode
        try:
            print(f"Loading configuration from {config_path}")
            config = load_config(str(config_path))
            
            # Validate configuration
            validate_config(config)
            
            print("Configuration loaded and validated successfully")
        except json.JSONDecodeError as e:
            print(f"Error: Invalid JSON format in configuration file '{config_path}': {e}")
            return
        except ValueError as e:
            print(f"Error: Invalid configuration format in '{config_path}': {e}")
            return
        except Exception as e:
            print(f"Error: Failed to load configuration from '{config_path}': {e}")
            return
        
        # Set default output files for non-default mode
        intermediate_file = "CCQ_Classification_with_factors.csv"
        processed_file = "processed_CCQ_data.csv"
    
    # Check if input file exists
    if not os.path.exists(input_file):
        print(f"Error: Input file '{input_file}' does not exist.")
        return
    
    # Step 1: Process drilling data to add main factors and MSE
    print(f"Processing drilling data from {input_file}")
    try:
        result_df = process_drilling_data(input_file)
    except FileNotFoundError:
        print(f"Error: Input file '{input_file}' not found.")
        return
    except Exception as e:
        print(f"Error: Failed to process drilling data from '{input_file}': {e}")
        return
    
    # Save the intermediate result with factors
    try:
        result_df.to_csv(intermediate_file, index=False, encoding='utf_8_sig')
        print(f"Drilling data processing completed! Results saved to {intermediate_file}")
    except Exception as e:
        print(f"Error: Failed to save intermediate results to '{intermediate_file}': {e}")
        return
    
    # Step 2: Process the CSV according to configuration
    try:
        process_csv(intermediate_file, processed_file, config)
        print(f"CSV processing completed! Results saved to {processed_file}")
    except Exception as e:
        print(f"Error: Failed to process CSV file: {e}")
        return
    
    # Step 3: Organize the data according to configuration
    print(f"Reading processed file {processed_file}")
    # Read the input CSV file
    data = []
    try:
        with open(processed_file, 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                data.append(row)
        print(f"Loaded {len(data)} rows from {processed_file}")
    except FileNotFoundError:
        print(f"Error: Processed file '{processed_file}' not found.")
        return
    except Exception as e:
        print(f"Error: Failed to read processed file '{processed_file}': {e}")
        return
    
    # Organize the data according to configuration
    print("Creating output structure...")
    try:
        primary_groups = create_output_structure(data, config)
        print("Output structure created")
    except Exception as e:
        print(f"Error: Failed to create output structure: {e}")
        return
    
    # Write the output files
    print("Writing output files...")
    try:
        write_output_files(primary_groups, config)
        print("Data organization completed successfully!")
    except Exception as e:
        print(f"Error: Failed to write output files: {e}")
        return


if __name__ == "__main__":
    main()
