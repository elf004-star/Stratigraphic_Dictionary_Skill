---
name: drilling-data-processor
description: Process drilling data files (CSV, XLS, XLSX, XML format) with configurable header handling, column extraction, data filtering, and transformation. Use when working with well drilling data tables that have dual headers, need column selection, data cleaning, splitting columns by delimiter, numeric range filtering, and sorting. Supports石油钻井数据 like bit records, drilling parameters, and formation data.
---

# Drilling Data Processor

Process drilling industry data files with flexible configuration-driven transformations.

## Quick Start

```python
from scripts.processor import CSVProcessor

# Initialize with config file
processor = CSVProcessor('processor.config.json')

# Process file
df = processor.load_and_process_csv('data.xls')

# Save result
df.to_csv('output.csv', index=False, encoding='utf-8-sig')
```

Or use command line:

```bash
python scripts/processor.py data.xls -c processor.config.json -o output.csv
```

## Configuration

Create a JSON config file to define processing rules. See [references/config-example.json](references/config-example.json) for a complete example.

### Key Config Sections

**header_definition**: Specify how to identify column headers
- `method`: "row" (by row number) or "letter" (by column letters)
- `value`: Row number or letter string (e.g., "A,B,C")

**data_start_row**: Row number where actual data begins (1-based)

**columns_to_extract**: Select and rename specific columns
- `method`: "letter", "name", or "auto"
- `columns`: List of columns to extract (use $A$ format for letter mode in auto)
- `new_headers`: New names for extracted columns (empty string = keep original)

**processing_options**:
- `remove_empty_rows`: Remove rows with empty values in specified columns
- `remove_invalid_number_rows`: Remove rows with non-numeric values
- `numeric_range_filter`: Filter numeric values by min/max ranges
- `column_splitting`: Split columns by delimiter into new columns
- `sorting`: Sort by multiple columns with ascending/descending order

## Column Extraction Modes

**Auto mode** (recommended): Mix column names and $letters$
```json
"columns": ["井号", "型号", "$D$", "生产厂家"]
```

**Letter mode**: Use Excel column letters
```json
"method": "letter",
"columns": ["A", "B", "C"]
```

**Name mode**: Use column header names
```json
"method": "name",
"columns": ["WellName", "BitModel"]
```

## File Format Support

- CSV files (with proper quoting support)
- Excel .xlsx files (using openpyxl)
- Excel .xls files (using xlrd)
- Excel 2003 XML format .xls files

## Config File Location

Processor searches for config in this order:
1. Current working directory
2. User home/.CCQ.config/

## Dependencies

```
pandas
numpy
openpyxl
xlrd
```

