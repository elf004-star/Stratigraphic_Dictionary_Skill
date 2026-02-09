# Configuration Reference

This document describes the configuration file format for the drilling data classifier.

## Configuration File Structure

The configuration file (default: `fmse.config.json`) contains the following main sections:

### 1. Basic Input/Output

```json
{
  "input_file": "CCQ_Classification_with_factors.csv",
  "output_file": "processed_CCQ_data.csv"
}
```

- `input_file`: Path to the intermediate CSV file with calculated factors (used with --default mode)
- `output_file`: Path to the final processed CSV file

### 2. Column Mapping

```json
{
  "column_mapping": {
    "机械钻速": "机械钻速（m/h）",
    "进尺": "进尺（m）",
    "MSE": "ESM",
    "井号": "备注"
  }
}
```

Maps original column names to new column names in the output. Special handling:
- `MSE` → `ESM`: Automatically calculates ESM = 6000 / MSE
- Other columns: Simple renaming with numeric formatting

### 3. Columns to Extract

```json
{
  "columns_to_extract": [
    "序号",
    "类别",
    "置信度",
    "进尺命中率",
    "钻头型号",
    "钻头尺寸mm",
    "生产厂家",
    "钻头类别",
    "钻进方式",
    "入井次数",
    "主因子",
    "钻压A",
    "钻压B",
    "转速A",
    "转速B",
    "排量A",
    "排量B",
    "泵压A",
    "泵压B"
  ]
}
```

List of columns to include in the output file. Columns not in this list or mapping will be excluded.

### 4. Output Column Order

```json
{
  "output_column_order": [
    "序号", 
    "类别", 
    "置信度",
    "进尺命中率",
    "钻头型号", 
    "生产厂家", 
    "钻头类别", 
    "钻头尺寸mm", 
    "钻进方式", 
    "入井次数", 
    "机械钻速（m/h）", 
    "进尺（m）", 
    "主因子", 
    "ESM", 
    "备注",
    "钻压A",
    "钻压B",
    "转速A",
    "转速B",
    "排量A",
    "排量B",
    "泵压A",
    "泵压B"
  ]
}
```

Defines the exact order of columns in the output CSV file. Must include all columns from mapping and extraction lists.

### 5. Classification Configuration

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

Controls how data is organized into folders:

- `classification_fields`: Array defining the classification hierarchy
  - `name`: Primary classification field name (e.g., "钻头尺寸mm")
  - `priority`: Classification priority (1 = highest)
  - `sub_classification`: Secondary classification
    - `name`: Sub-classification field name (e.g., "类别")
    - `priority`: Sub-classification priority

- `output_directory`: Base directory for organized output files
- `filename_prefix`: If true, filenames include primary classification prefix (e.g., "311.2_沙溪庙.csv")

## Input Data Requirements

### Required Columns for Processing

The input CSV must contain these columns for factor calculations:

- `进尺` (Progress/footage)
- `机械钻速` (Mechanical drilling rate)
- `钻头尺寸mm` (Bit size in mm)
- `钻压` (Drilling pressure) OR `钻压A` and `钻压B` (A/B pressure values)
- `转速` (Rotation speed) OR `转速A` and `转速B` (A/B speed values)

### Optional A/B Columns

When A/B columns are present, the system calculates adjusted values using k-functions:

- `钻压A`, `钻压B`: Calculate adjusted drilling pressure
- `转速A`, `转速B`: Calculate adjusted rotation speed
- `排量A`, `排量B`: Flow rate A/B values (passed through)
- `泵压A`, `泵压B`: Pump pressure A/B values (passed through)

### Classification Columns

For data organization, the input should contain:

- Primary classification field (e.g., `钻头尺寸mm`)
- Secondary classification field (e.g., `类别`)

## Calculations

### Main Factors

1. **Dynamic Specific Energy**: `钻压 * 转速 / 钻头尺寸 / 机械钻速`
2. **F1**: `0.58*进尺 + 0.53*机械钻速 + 0.5/动比能 - 0.31/钻压 - 0.18/转速`
3. **F2**: `-0.17*进尺 + 0.06*机械钻速 + 0.04/动比能 - 0.61/钻压 - 0.77/转速`
4. **Main Factor**: `0.68 * F1 + 0.32 * F2`

### MSE Calculation

**MSE**: `钻压/(π*钻头尺寸^2/4) + (480*转速*钻压)/(钻头尺寸*机械钻速)`

### ESM Conversion

**ESM**: `6000 / MSE` (when MSE column is mapped to ESM)

## Output Structure

### Intermediate File

Contains all original columns plus:
- `主因子`: Calculated main factor (formatted to 2 decimal places)
- `MSE`: Calculated MSE (formatted to 2 decimal places)

### Final Processed File

Contains columns according to `output_column_order` with:
- Renamed columns per `column_mapping`
- ESM conversion if MSE → ESM mapping exists
- Numeric formatting (2 decimal places or 4 significant digits)

### Organized Files

Files organized in `output_directory` structure:
```
output/
├── 311.2/
│   ├── 311.2_沙溪庙.csv
│   ├── 311.2_自流井.csv
│   └── 311.2_须家河.csv
├── 444.5/
│   └── 444.5_沙溪庙.csv
```

## Configuration File Locations

The system searches for configuration files in this order:
1. Current directory: `./fmse.config.json`
2. User config directory: `~/.CCQ.config/fmse.config.json`

## Error Handling

- Missing required configuration keys: Validation error
- Invalid JSON format: Parse error
- Missing input file: File not found error
- Invalid numeric data: Default to 0 or NaN
- Division by zero: Return infinity or appropriate default
