# Jobsite Weather Planner

A Python Tkinter desktop app that retrieves a seven-day Open-Meteo hourly
forecast and provides Go, Caution, and No-Go planning ratings for crane lifts,
concrete pours, and roofing work.

## Features

- Place-name search or manual latitude/longitude entry
- Seven-day hourly weather forecast
- Crane, concrete, and roofing ratings with visible reasons
- Work interval entry for each forecast date
- Crane and concrete criteria with source fields
- Embedded Matplotlib temperature/wind plot
- Matplotlib navigation toolbar for pan, zoom, reset, and save-as-image
- Live hourly slider that redraws the selected-hour marker and weather summary
- JSON input save/open and CSV rating export

Planning indicators are not safety approvals. Enter crane limits and concrete
minimums from applicable manufacturer or project sources.

## Requirements

- Windows
- Python 3.10 or newer
- Internet access for Open-Meteo

## Install

Open PowerShell in this folder and run:

```powershell
cd "C:\Users\omiya\OneDrive\Documents\CCE270\HW Desktop App"
py -m pip install matplotlib
```

NumPy is also used by the calculation environment. If it is not already
installed, run:

```powershell
py -m pip install numpy
```

## Run

From this folder:

```powershell
python app.py
```

## Using the App

1. Search for a place, or enter latitude and longitude directly.
2. Select **Fetch 7-Day Forecast**.
3. Enter work start and end times using 24-hour `HH:MM` format.
4. Enter the crane limit and manufacturer source.
5. Enter the concrete minimum and project specification/source.
6. Select **Calculate Ratings**.
7. Use the Matplotlib toolbar to pan, zoom, reset, or save the plot.
8. Drag the selected-hour slider to update the hourly summary and plot marker.

Use **Save Inputs** to save the current fields and **Open Inputs** to restore
them. Use **Export CSV** to save the displayed daily ratings.

## Validation

Run the calculation and Tkinter plot tests with:

```powershell
python -m unittest -v test_weather_calculations.py test_app_plot.py
```

Expected-versus-actual validation results are recorded in `spec.md`.

## Weather Data

Forecast and place-search data are provided by Open-Meteo:

- https://open-meteo.com/en/docs
- https://geocoding-api.open-meteo.com/
