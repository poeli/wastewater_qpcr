# Wastewater qPCR Data Visualization Dashboard

## Project Overview

This project is a wastewater-based epidemiology dashboard that visualizes qPCR data for various pathogens detected in wastewater samples. The application uses Dash (a Python framework built on Flask, Plotly.js, and React.js) to create interactive web visualizations of pathogen concentration data over time.

## Architecture & Components

### Core Components:
- **Dash Application (`app.py`)**: Entry point that initializes the Dash app with styling and server configuration
- **Main Dashboard (`pages/wastewater_qpcr_app.py`)**: Contains the primary visualization logic, data loading, and UI components
- **Data Files (`assets/data/`)**: Contains TSV files with pathogen concentration data and standard deviations
- **Configuration (`assets/data/layout.json`)**: Controls visualization layout, titles, descriptions, and data source mappings

### Data Flow:
1. TSV files in `assets/data/` contain date-indexed qPCR values
2. Dashboard reads `layout.json` to determine which pathogens to display
3. For each pathogen, data files are loaded with the `process_data` function
4. Visualizations are created using Plotly with interactive time selectors
5. Trend analysis displayed in sidebar with color-coded status badges

## Development Workflow

### Setup Development Environment:
```bash
# Using conda
cd wastewater_qpcr_app/
conda env create -f environment.yml
conda activate ww-env

# For Python < 3.14:
python app.py

# For Python 3.14+ (avoids pkgutil.find_loader error):
python run.py

# Using Docker
docker run \
    --rm \
    -p 8765:8765 \
    -v "/path/to/data:/app/assets/data" \
    poeli/wastewater_qpcr_app:latest
```

### Adding New Pathogen Data:
1. Add TSV data files to `assets/data/` with format:
   - Column names are dates
   - Row names are fraction types (e.g., F1, F3)
   - Tab-separated values
2. Update `layout.json` with new entry containing:
   - Title, description and source file paths
   - Axis labels and pathogen type
   - Optional trend analysis details

### Visualization Pattern:
The application follows a consistent pattern for all pathogen data:
- Date-based line charts with error bars from standard deviation values
- Time range selector (1M, 6M, YTD, 1Y, ALL)
- Filtering by pathogen type through dropdown menu
- Trend analysis cards in sidebar with status indicators

## Key Conventions

### Data Formatting:
- Main data files must have `.tsv` extension with tab-separated values
- Standard deviation files should be named with `_std.tsv` suffix
- Date format in TSV files: column headers must be parseable by pandas

### UI Patterns:
- Sidebar contains trend cards for quick status assessment
- Each visualization follows same layout style defined in `PLOT_STYLE`
- Color-coding: red=increasing, green=decreasing, yellow=stable

### Error Handling:
- The app logs detailed information using Python's logging module
- Failed data processing is logged but doesn't crash the application
- Data validation happens during the `process_data` function

## Debugging Tips

1. Check logs for error messages - the app uses standard Python logging
2. For data loading issues, verify TSV format matches expected structure
3. The app runs on port 8765 by default - ensure this port is free
4. For Docker deployment, ensure proper volume mounting to access data files
5. If you encounter `pkgutil.find_loader` errors with Python 3.14+:
   - Use the provided `run.py` script instead of `app.py`
   - Alternatively, use `app.py.patched` which includes a compatibility fix

## Extending the Application

To add new visualization types:
1. Modify the `update_figure` function in `wastewater_qpcr_app.py`
2. Add new entry types to `layout.json` schema
3. Update callbacks to handle new visualization types

The dashboard is designed to be configured through `layout.json` without code changes for most common updates.