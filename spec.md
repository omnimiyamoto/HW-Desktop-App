# Jobsite Weather Planner Desktop App

## 1. App overview

The Jobsite Weather Planner is a Python Tkinter desktop application that helps a superintendent review a seven-day local-time weather forecast and decide whether crane lifts, concrete pours, and roofing work should proceed as Go, Caution, or No-Go. The app uses a selected jobsite location, scheduled work intervals, and source-cited project limits.

## 2. Purpose

Help a superintendent:

- Select a jobsite in the United States or another supported Open-Meteo location.
- Review an hourly seven-day forecast.
- Schedule work intervals, including overnight intervals.
- Enter crane and concrete limits with their sources.
- View daily ratings and the weather conditions that caused each rating.

The ratings are planning indicators, not safety approvals or guarantees.

## Platform

- Python Tkinter desktop app
- Starts with `python app.py`
- NumPy for calculations
- Matplotlib for embedded plots
- Matplotlib NavigationToolbar2Tk for pan, zoom, reset, and save-as-image
- Open-Meteo Forecast and Geocoding APIs
- Internet connection required for location search and forecast retrieval

## 3. Users

Primary users are civil engineering students and construction superintendents. The app is also useful for engineers or project managers who need a quick forecast-based planning view.

## 4. Inputs

- **Jobsite:** place-name search or latitude/longitude entry.
- **Forecast location:** a valid latitude from -90 to 90 degrees and longitude from -180 to 180 degrees.
- **Work intervals:** start and end times for each of seven forecast dates. Times use AM/PM controls and minute-level precision.
- **Shift presets:** optional 7:00 AM–3:30 PM Day Shift and 7:00 PM–7:00 AM Night Shift presets.
- **Crane limit:** positive finite wind limit, mph or km/h, plus a required manufacturer manual/source text.
- **Concrete limit:** finite minimum temperature, °F or °C, plus a required project specification/source text.
- **Display unit preference:** U.S. customary for U.S. locations and metric for other locations, with a manual unit selector for entered criteria.
- Invalid values, missing criteria, missing forecast fields, overlaps, and failed API requests must produce visible error or unavailable states.

## 5. Calculations

The app retrieves Open-Meteo hourly `temperature_2m`, `wind_speed_10m`, `wind_gusts_10m`, and `precipitation_probability`.

### Crane lifts

Let `V_limit` be the crane limit in mph or km/h and `V_max` be the maximum of sustained wind and gust values during scheduled hours:

- No-Go: `V_max >= V_limit`
- Caution: `0.8 * V_limit <= V_max < V_limit`
- Go: `V_max < 0.8 * V_limit`

The crane limit must come from the applicable manufacturer manual. The 80% caution buffer is an app planning rule, not an OSHA or manufacturer limit.

### Concrete pours

Let `T_project` be the entered project minimum and `T_min` be the minimum scheduled-hour temperature:

- No-Go: `T_min < T_project`
- Caution: `T_project <= T_min < 40°F`
- Go: `T_min >= T_project` and `T_min >= 40°F`

If the project limit or source is missing, the concrete rating is Not Configured.

### Roofing

Let `P_max` be the maximum precipitation probability during scheduled hours:

- Go: `P_max < 30%`
- Caution: `30% <= P_max < 60%`
- No-Go: `P_max >= 60%`

These bands are app heuristics, not roofing safety standards.

### Unit conversions

- °F = °C × 9/5 + 32
- mph = km/h / 1.60934
- km/h = mph × 1.60934

All conversions must preserve finite values and are checked for rating consistency.

## 6. Outputs

- A clear jobsite and forecast status panel.
- Seven daily rating cards or rows for Crane, Concrete, and Roofing.
- A reason and measured extreme for each available rating.
- An embedded Matplotlib plot of temperature, wind, gust, or precipitation over the forecast.
- Matplotlib pan, zoom, reset, and save tools.
- A live slider that selects an hour and redraws the plot and hourly summary.
- Visible Loading, Not Scheduled, Not Configured, Unavailable, and Forecast Error states.
- A status disclaimer that ratings are planning indicators only.
- Export of hourly forecast and rating results to CSV.

## 7. Look and feel

- Resizable desktop window with a left input panel and right results/plot area.
- Clear labels with units on every numeric input and output.
- Professional light theme and readable status colors:
  - Go: green
  - Caution: amber
  - No-Go: red
- Inputs and plot remain usable at a minimum window size of approximately 1000 × 700 pixels.

## Validation

The validation location is Provo, Utah, approximately 40.2301° N, 111.6557° W.

The recorded 2026-11-18 local forecast fixture uses 2:00 PM–5:00 PM, with hours 14:00, 15:00, and 16:00:

| Local hour | Temperature | Sustained wind | Gust | Precipitation |
|---|---:|---:|---:|---:|
| 14:00 | 47.2°F | 2.8 mph | 6.3 mph | 0% |
| 15:00 | 48.1°F | 2.1 mph | 5.4 mph | 0% |
| 16:00 | 47.7°F | 2.9 mph | 5.6 mph | 0% |

Test-only limits:

- Crane limit: 15 mph, 80% caution threshold 12 mph.
- Concrete minimum: 35°F.
- These limits are fixtures only and are not operational recommendations.

Hand calculations:

1. `V_max = 6.3 mph < 12 mph`, producing Crane **Go**.
2. `T_min = 47.2°F >= 35°F` and `>= 40°F`, producing Concrete **Go**.
3. `P_max = 0% < 30%`, producing Roofing **Go**.

Additional validation sources:

- The weather API value source is Open-Meteo: https://open-meteo.com/en/docs
- The example NWS provider comparison is https://api.weather.gov/gridpoints/SLC/105,150/forecast/hourly
- Unit formulas are standard conversions stated in this spec.

## Validation results

| Case | Source / derivation | Expected | Actual | Result |
|---|---|---|---|---|
| Provo recorded forecast | Hand calculation using 14:00–16:00 fixture | Crane Go; Concrete Go; Roofing Go | — | To be filled by agent validation |
| Crane threshold boundaries | Hand calculation: Caution at 12 mph, No-Go at 15 mph | 11.99 mph Caution; 12 mph Caution; 15 mph No-Go | — | To be filled by agent validation |
| Temperature/wind conversion property | `°C -> °F -> °C` and `km/h -> mph -> km/h` round trips | Original values restored within 1e-6 | — | To be filled by agent validation |

The app developer will confirm at least one passing validation case interactively in the desktop app before submission.

## Out of scope

- Safety approval or guarantee
- Crane operator or manufacturer approval
- Complete ACI or OSHA compliance
- Concrete curing and protection after pour hours
- Site-specific microclimate or obstruction analysis
- Locations unsupported by Open-Meteo
- Continuous-beam or structural-engineering analysis

## Added features

1. **Embedded Matplotlib forecast plot:** line plots for temperature and wind/gust or precipitation, plus pan, zoom, reset, and save-image controls.
2. **Live forecast-hour slider:** selecting an hour redraws the plot and updates the hourly condition summary immediately.
3. **Design-state save/open and CSV export:** save the user inputs to JSON and export forecast/rating results to CSV.

## Build stages

1. Create the specification and project prompt instructions.
2. Build the resizable Tkinter mockup and verified calculation module.
3. Add place search and seven-day forecast retrieval.
4. Add work intervals and activity ratings.
5. Run all hand and property validations and commit the validated must-have app.
6. Add the embedded Matplotlib plot and navigation toolbar.
7. Add the live-hour slider and test redraw behavior.
8. Add JSON save/open and CSV export.
9. Add final README, polish, and rerun all tests.
