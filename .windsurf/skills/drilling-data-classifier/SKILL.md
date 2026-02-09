---
name: drilling-data-classifier
description: Comprehensive drilling data processing and classification tool that calculates main factors (F1, F2), MSE (Mechanical Specific Energy), and organizes drilling classification data into structured folders. Use when processing drilling classification CSV files that require: (1) Calculation of drilling performance metrics, (2) A/B column adjustments for pressure and speed, (3) Data classification and folder organization, (4) MSE to ESM conversion, or (5) Configurable column mapping and output formatting.
---

# Drilling Data Classifier

Process drilling classification data with automated factor calculations and intelligent folder organization.

## Quick Start

### Basic Processing

```bash
# Process a drilling data file with default configuration
python scripts/process_drilling_data.py your_data.csv

# Process with custom configuration
python scripts/process_drilling_data.py your_data.csv custom_config.json

# Use files specified in configuration
python scripts/process_drilling_data.py --default
```

### Required Input Columns

Ensure your CSV contains these columns for factor calculations:

- `进尺` (Progress/footage)
- `机械钻速` (Mechanical drilling rate) 
- `钻头尺寸mm` (Bit size in mm)
- `钻压` (Drilling pressure) OR `钻压A`/`钻压B` (A/B pressure values)
- `转速` (Rotation speed) OR `转速A`/`转速B` (A/B speed values)

## Processing Workflow

### 1. Factor Calculation

The script automatically calculates:

- **Dynamic Specific Energy**: `钻压 * 转速 / 钻头尺寸 / 机械钻速`
- **F1**: `0.58*进尺 + 0.53*机械钻速 + 0.5/动比能 - 0.31/钻压 - 0.18/转速`
- **F2**: `-0.17*进尺 + 0.06*机械钻速 + 0.04/动比能 - 0.61/钻压 - 0.77/转速`
- **Main Factor**: `0.68 * F1 + 0.32 * F2`
- **MSE**: `钻压/(π*钻头尺寸^2/4) + (480*转速*钻压)/(钻头尺寸*机械钻速)`

### 2. A/B Column Adjustments

When A/B columns are present, adjusted values are calculated using k-functions:

- **Drilling Pressure**: Uses `get_k_drilling_pressure()` based on pressure difference
- **Rotation Speed**: Uses `get_k_rotation_speed()` based on speed difference

K-function values:
- Difference ≤ 50: k = 0.5
- Difference ≤ 100: k = 0.66  
- Difference ≤ 200: k = 0.8
- Difference > 200: k = 0.86

### 3. Data Organization

Data is automatically organized into folders based on configuration:

```
output/
├── 311.2/
│   ├── 311.2_沙溪庙.csv
│   ├── 311.2_自流井.csv
│   └── 311.2_须家河.csv
├── 444.5/
│   └── 444.5_沙溪庙.csv
```

## Configuration

### Configuration File Location

The system searches for configuration files in order:
1. Current directory: `./fmse.config.json`
2. User config directory: `~/.CCQ.config/fmse.config.json`

### Key Configuration Sections

**Column Mapping**: Rename columns and apply special transformations
```json
{
  "column_mapping": {
    "机械钻速": "机械钻速（m/h）",
    "进尺": "进尺（m）", 
    "MSE": "ESM"
  }
}
```

**Classification**: Define folder organization structure
```json
{
  "classification_config": {
    "classification_fields": [
      {
        "name": "钻头尺寸mm",
        "priority": 1,
        "sub_classification": {
          "name": "类别",
          "priority": 2
        }
      }
    ],
    "output_directory": "output",
    "filename_prefix": true
  }
}
```

For complete configuration reference, see [references/configuration.md](references/configuration.md).

## Output Files

### Intermediate File
- Contains all original columns plus calculated `主因子` and `MSE`
- Saved as `CCQ_Classification_with_factors.csv`

### Final Processed File  
- Columns renamed per configuration mapping
- MSE converted to ESM when mapped
- Numeric formatting applied (2 decimal places or 4 significant digits)
- Saved as `processed_CCQ_data.csv`

### Organized Files
- Data grouped by primary and secondary classification
- Stored in configured output directory
- Filenames include prefix when enabled

## Data Formatting

### Numeric Formatting
- Values ≥ 0.01: Formatted to 2 decimal places
- Values < 0.01: Formatted to 4 significant digits
- Serial numbers (`序号`, `入井次数`): Preserved as integers when possible

### Special Conversions
- **MSE → ESM**: `ESM = 6000 / MSE` (when MSE column is mapped to ESM)
- **A/B Adjustments**: Applied automatically when A/B columns present

## Error Handling

- **Missing Configuration**: Searches default locations, provides clear error messages
- **Invalid Data**: Uses default values (0 or NaN) for invalid numeric data
- **Division by Zero**: Returns infinity or appropriate defaults
- **Missing Columns**: Clear error messages indicating required columns

## Examples

### Example 1: Basic Processing
```bash
python scripts/process_drilling_data.py CCQ_classification.csv
```

### Example 2: Custom Configuration
```bash
python scripts/process_drilling_data.py drilling_data.json my_config.json
```

### Example 3: Default Mode
```bash
python scripts/process_drilling_data.py --default
```

## Dependencies

- Python 3.7+
- pandas
- numpy
- chardet

Install dependencies:
```bash
pip install pandas numpy chardet
```

## Troubleshooting

### Common Issues

1. **Missing Columns**: Ensure CSV contains required columns (`进尺`, `机械钻速`, `钻头尺寸mm`)
2. **Encoding Issues**: Script auto-detects encoding using chardet
3. **Configuration Errors**: Validate JSON syntax and required keys
4. **Permission Errors**: Ensure write access to output directory

### Validation

The script includes comprehensive validation:
- Configuration file format validation
- Required key presence checking  
- Data type validation
- File existence verification

For detailed configuration options and data requirements, refer to [references/configuration.md](references/configuration.md).
