---
name: gold-geometric-optimization
description: 3D scatter plot visualization using golden ratio geometric optimization algorithm with configurable parameters and automatic configuration file lookup. Use when processing CSV data files with 5 columns (index, label, x, y, z values) for geological, drilling, or stratigraphic data analysis that requires identifying optimal points using the golden ratio geometric selection method.
---

# Golden Ratio Geometric Optimization

## Overview

This skill provides 3D scatter plot visualization using the golden ratio geometric optimization algorithm. It processes CSV files with 5 columns (序号, 标签, X, Y, Z values) to identify optimal points using the formula x*y*z >= S_limit, where S_limit is calculated using the golden ratio (default 0.618). The algorithm visualizes data points above and below the threshold surface, with customizable parameters and configuration.

## Quick Start

### Basic Usage
```bash
python scripts/gold.py path/to/data.csv
```

### Batch Processing (Recommended)
To process all eligible CSV files in a directory at once:
```bash
python scripts/gold.py path/to/directory
```
The script will automatically scan the directory for CSV files with the correct 5-column format and process them all in one go.

### With Custom Parameters
```bash
python scripts/gold.py path/to/data.csv --golden-ratio 0.618 --num-points 10 --view-mode
```

### With Custom Configuration
```bash
python scripts/gold.py path/to/data.csv --config-file custom.config.json
```

## Data Format Requirements

The input CSV file must have exactly 5 columns in this order:
1. **序号** (Index) - Sequential numbering
2. **标签** (Label) - Text identifier for each point
3. **X Value** - Numeric value (e.g., mechanical drilling speed)
4. **Y Value** - Numeric value (e.g., footage)
5. **Z Value** - Numeric value (e.g., main factor)

When using batch processing on a directory, the script will automatically identify and process only those files that match this 5-column format requirement.

Example:
```
序号,标签,机械钻速（m/h）,进尺（m）,主因子
1,PointA,8.01,644.4,222.23
2,PointB,7.8,965.05,331.45
```

## Core Capabilities

### 1. Golden Ratio Threshold Calculation
The algorithm calculates S_limit using the golden ratio geometric optimization method:
- For each point: S_i = x_i * y_i * z_i
- Points where S >= S_limit are considered "optimal"
- The threshold S_limit is computed based on golden ratio principles

### 2. 3D Visualization
- Creates interactive 3D scatter plots with configurable viewing parameters
- Optimal points (above threshold) shown in color with labels
- Non-optimal points (below threshold) shown as transparent with thin borders
- Color mapping based on Z-value intensity (purple for low, red for high)

### 3. Configurable Parameters
- Golden ratio value (default 0.618)
- Number of selected points
- Axis range factors
- Surface range factors
- Display options (colormap labels, view mode)

## Configuration System

The system follows this priority order to locate configuration:

1. **CSV Directory**: `gold.config.json` in the same directory as the input CSV file
2. **Current Directory**: `gold.config.json` in the current working directory
3. **User Config**: `~/.CCQ.config/gold.config.json` in user's home directory
4. **Default**: Built-in default values if no config file found

Configuration file format:
```json
{
  "axis_ranges": {
    "x": {"min": "auto", "max": "auto", "min_factor": 0.8, "max_factor": 1.2},
    "y": {"min": "auto", "max": "auto", "min_factor": 0.8, "max_factor": 1.2},
    "z": {"min": "auto", "max": "auto", "min_factor": 0.8, "max_factor": 1.6}
  },
  "surface_ranges": {
    "x": {"min_factor": 0.1, "max_factor": 1.0},
    "y": {"min_factor": 0.1, "max_factor": 1.0},
    "z": {"min_factor": 0.1, "max_factor": 1.0}
  }
}
```

## Command Line Options

| Option | Description | Default |
|--------|-------------|---------|
| `--golden-ratio` | Golden ratio value for threshold calculation | 0.618 |
| `--num-points` | Directly specify number of points to select | Auto-calculate |
| `--view` | Show plot in window instead of saving | False |
| `--colormap-label` | Display color bar with Z-value mapping | False |
| `--config-file` | Path to custom configuration file | gold.config.json |

## Output

The script generates:
- A 3D scatter plot saved as an image file in the same directory as the input CSV
- Console output showing which configuration file was used
- Properly labeled axes using the column headers from the CSV
- Optimized label positioning to avoid overlaps
- A detailed report file (gold_report.md) summarizing the selected and unselected points
- Color-coded visualization where optimal points are colored and labeled, and suboptimal points are transparent

When processing a directory, the script will:
- Automatically scan for all CSV files in the directory and subdirectories (up to 3 levels deep)
- Identify and process only files that match the required 5-column format
- Skip files that don't match the format or have insufficient data
- Generate a comprehensive report (gold_report.md) summarizing results from all processed files

## Error Handling

- Validates CSV has exactly 5 columns with correct headers
- Filters out rows with NaN or empty values
- Provides warnings for insufficient data points
- Gracefully handles missing configuration files using defaults
