from __future__ import annotations

import csv
import json
import math
import threading
import tkinter as tk
import urllib.parse
import urllib.request
from datetime import datetime, timedelta
from tkinter import filedialog, messagebox, ttk

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure

import weather_calculations as calculations


GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"


class JobsiteWeatherPlanner:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Jobsite Weather Planner")
        self.root.geometry("1180x760")
        self.root.minsize(1000, 700)

        self.forecast: dict | None = None
        self.forecast_dates: list[str] = []
        self.location_name = "No jobsite selected"
        self.latitude: float | None = None
        self.longitude: float | None = None
        self.timezone = ""

        self._configure_styles()
        self._build_layout()
        self._set_initial_state()

    def _configure_styles(self) -> None:
        style = ttk.Style(self.root)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("App.TFrame", background="#edf2f7")
        style.configure("Card.TFrame", background="#ffffff")
        style.configure("Title.TLabel", background="#edf2f7", foreground="#17324d", font=("Segoe UI", 20, "bold"))
        style.configure("Subtitle.TLabel", background="#edf2f7", foreground="#5d6b7a", font=("Segoe UI", 10))
        style.configure("CardTitle.TLabel", background="#ffffff", foreground="#17324d", font=("Segoe UI", 11, "bold"))
        style.configure("Muted.TLabel", background="#ffffff", foreground="#637282", font=("Segoe UI", 9))
        style.configure("Status.TLabel", background="#ffffff", foreground="#17324d", font=("Segoe UI", 10))
        style.configure("Go.Treeview", background="#f2f8f4")
        style.configure("Caution.Treeview", background="#fff8e8")
        style.configure("No-Go.Treeview", background="#fff2f1")

    def _build_layout(self) -> None:
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        main = ttk.Frame(self.root, style="App.TFrame", padding=12)
        main.grid(row=0, column=0, sticky="nsew")
        main.columnconfigure(1, weight=1)
        main.rowconfigure(1, weight=1)

        header = ttk.Frame(main, style="App.TFrame")
        header.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 10))
        ttk.Label(header, text="Jobsite Weather Planner", style="Title.TLabel").pack(side="left")
        ttk.Button(header, text="Save Inputs", command=self._save_inputs).pack(side="right", padx=(6, 0))
        ttk.Button(header, text="Open Inputs", command=self._open_inputs).pack(side="right")

        left = ttk.Frame(main, style="App.TFrame")
        left.grid(row=1, column=0, sticky="ns", padx=(0, 10))
        left.columnconfigure(0, weight=1)

        location_card = ttk.LabelFrame(left, text="1. Jobsite", padding=10)
        location_card.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        ttk.Label(location_card, text="Place name").grid(row=0, column=0, sticky="w")
        self.place_var = tk.StringVar()
        place_entry = ttk.Entry(location_card, textvariable=self.place_var, width=34)
        place_entry.grid(row=1, column=0, sticky="ew", pady=(2, 6))
        ttk.Button(location_card, text="Search", command=self._search_place).grid(row=1, column=1, padx=(6, 0))
        self.search_list = tk.Listbox(location_card, height=4, width=40)
        self.search_list.grid(row=2, column=0, columnspan=2, sticky="ew")
        self.search_list.bind("<<ListboxSelect>>", self._select_search_result)
        self.place_results: list[dict] = []

        coord_card = ttk.LabelFrame(left, text="Selected coordinates", padding=10)
        coord_card.grid(row=1, column=0, sticky="ew", pady=(0, 8))
        ttk.Label(coord_card, text="Latitude (°)").grid(row=0, column=0, sticky="w")
        ttk.Label(coord_card, text="Longitude (°)").grid(row=0, column=1, sticky="w")
        self.latitude_var = tk.StringVar(value="")
        self.longitude_var = tk.StringVar(value="")
        ttk.Entry(coord_card, textvariable=self.latitude_var, width=14).grid(row=1, column=0, padx=(0, 6))
        ttk.Entry(coord_card, textvariable=self.longitude_var, width=14).grid(row=1, column=1)
        ttk.Button(coord_card, text="Fetch 7-Day Forecast", command=self._fetch_forecast).grid(
            row=2, column=0, columnspan=2, sticky="ew", pady=(8, 0)
        )

        criteria_card = ttk.LabelFrame(left, text="2. Project criteria", padding=10)
        criteria_card.grid(row=2, column=0, sticky="ew", pady=(0, 8))
        ttk.Label(criteria_card, text="Crane limit").grid(row=0, column=0, sticky="w")
        self.crane_var = tk.StringVar()
        ttk.Entry(criteria_card, textvariable=self.crane_var, width=12).grid(row=1, column=0, sticky="w")
        self.crane_unit = tk.StringVar(value="mph")
        ttk.Combobox(criteria_card, textvariable=self.crane_unit, values=("mph", "km/h"), width=8, state="readonly").grid(
            row=1, column=1, padx=(6, 0)
        )
        ttk.Label(criteria_card, text="Manufacturer source").grid(row=2, column=0, sticky="w", pady=(6, 0))
        self.crane_source_var = tk.StringVar()
        ttk.Entry(criteria_card, textvariable=self.crane_source_var, width=30).grid(row=3, column=0, columnspan=2, sticky="ew")

        ttk.Label(criteria_card, text="Concrete minimum").grid(row=4, column=0, sticky="w", pady=(8, 0))
        self.concrete_var = tk.StringVar()
        ttk.Entry(criteria_card, textvariable=self.concrete_var, width=12).grid(row=5, column=0, sticky="w")
        self.concrete_unit = tk.StringVar(value="F")
        ttk.Combobox(criteria_card, textvariable=self.concrete_unit, values=("F", "C"), width=8, state="readonly").grid(
            row=5, column=1, padx=(6, 0)
        )
        ttk.Label(criteria_card, text="Project specification/source").grid(row=6, column=0, sticky="w", pady=(6, 0))
        self.concrete_source_var = tk.StringVar()
        ttk.Entry(criteria_card, textvariable=self.concrete_source_var, width=30).grid(row=7, column=0, columnspan=2, sticky="ew")

        schedule_card = ttk.LabelFrame(left, text="3. Work intervals", padding=10)
        schedule_card.grid(row=3, column=0, sticky="ew")
        ttk.Label(
            schedule_card,
            text="Each date: start–end in 24-hour HH:MM",
            style="Muted.TLabel",
        ).grid(row=0, column=0, columnspan=3, sticky="w")
        self.schedule_rows: list[tuple[str, tk.StringVar, tk.StringVar]] = []

        right = ttk.Frame(main, style="App.TFrame")
        right.grid(row=1, column=1, sticky="nsew")
        right.rowconfigure(2, weight=1)
        right.columnconfigure(0, weight=1)

        summary_card = ttk.LabelFrame(right, text="Forecast and ratings", padding=10)
        summary_card.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        summary_card.columnconfigure(0, weight=1)
        self.location_status = tk.StringVar(value="Select a jobsite")
        ttk.Label(summary_card, textvariable=self.location_status, style="Status.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(
            summary_card,
            text="Planning indicators only. Always follow manufacturer manuals and project safety procedures.",
            style="Muted.TLabel",
        ).grid(row=1, column=0, sticky="w", pady=(4, 0))

        plot_card = ttk.LabelFrame(right, text="Hourly forecast plot", padding=6)
        plot_card.grid(row=1, column=0, sticky="ew", pady=(0, 8))
        plot_card.columnconfigure(0, weight=1)

        self.forecast_figure = Figure(figsize=(7.2, 2.4), dpi=100, constrained_layout=True)
        self.forecast_axis = self.forecast_figure.add_subplot(111)
        self.forecast_axis.set_title("Hourly weather")
        self.forecast_axis.set_ylabel("Temperature (°F) / Wind (mph)")
        self.forecast_axis.grid(True, alpha=0.25)

        plot_host = ttk.Frame(plot_card, style="Card.TFrame")
        plot_host.grid(row=0, column=0, sticky="ew")

        self.plot_canvas = FigureCanvasTkAgg(self.forecast_figure, master=plot_host)
        self.plot_canvas.draw()
        self.plot_canvas.get_tk_widget().pack(side="top", fill="both", expand=True)
        self.plot_toolbar = NavigationToolbar2Tk(self.plot_canvas, plot_host)
        self.plot_toolbar.update()

        slider_row = ttk.Frame(plot_card, style="Card.TFrame")
        slider_row.grid(row=1, column=0, sticky="ew", pady=(6, 0))
        slider_row.columnconfigure(1, weight=1)
        ttk.Label(slider_row, text="Selected hour", style="Muted.TLabel").grid(row=0, column=0, sticky="w")
        self.hour_slider = ttk.Scale(slider_row, from_=0, to=0, orient="horizontal", command=self._on_hour_slider)
        self.hour_slider.grid(row=0, column=1, sticky="ew", padx=(8, 8))
        self.hour_summary_var = tk.StringVar(value="Load a forecast to inspect an hour.")
        ttk.Label(slider_row, textvariable=self.hour_summary_var, style="Status.TLabel").grid(
            row=1, column=0, columnspan=2, sticky="w", pady=(4, 0)
        )
        self.hour_slider_index = 0

        table_card = ttk.Frame(right, style="Card.TFrame", padding=8)
        table_card.grid(row=2, column=0, sticky="nsew")
        table_card.rowconfigure(0, weight=1)
        table_card.columnconfigure(0, weight=1)

        columns = ("date", "crane", "concrete", "roofing")
        self.ratings_table = ttk.Treeview(table_card, columns=columns, show="headings", height=14)
        self.ratings_table.heading("date", text="Date")
        self.ratings_table.heading("crane", text="Crane")
        self.ratings_table.heading("concrete", text="Concrete")
        self.ratings_table.heading("roofing", text="Roofing")
        self.ratings_table.column("date", width=140, anchor="w")
        self.ratings_table.column("crane", width=170, anchor="w")
        self.ratings_table.column("concrete", width=170, anchor="w")
        self.ratings_table.column("roofing", width=170, anchor="w")
        self.ratings_table.grid(row=0, column=0, sticky="nsew")

        scrollbar = ttk.Scrollbar(table_card, orient="vertical", command=self.ratings_table.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.ratings_table.configure(yscrollcommand=scrollbar.set)
        self.ratings_table.bind("<<TreeviewSelect>>", self._show_rating_detail)

        detail_card = ttk.LabelFrame(right, text="Rating detail", padding=10)
        detail_card.grid(row=3, column=0, sticky="ew", pady=(8, 0))
        self.detail_var = tk.StringVar(value="Select a forecast date after entering criteria and work intervals.")
        ttk.Label(detail_card, textvariable=self.detail_var, wraplength=650, justify="left").pack(anchor="w")

        button_row = ttk.Frame(right, style="App.TFrame")
        button_row.grid(row=4, column=0, sticky="ew", pady=(8, 0))
        ttk.Button(button_row, text="Calculate Ratings", command=self._calculate_ratings).pack(side="left")
        ttk.Button(button_row, text="Export CSV", command=self._export_csv).pack(side="left", padx=(6, 0))

    def _set_initial_state(self) -> None:
        self.detail_var.set("Select a jobsite and fetch a forecast.")

    def _fetch_json(self, url: str) -> dict:
        request = urllib.request.Request(url, headers={"User-Agent": "CCE270-Desktop-Weather-Planner/1.0"})
        with urllib.request.urlopen(request, timeout=20) as response:
            return json.loads(response.read().decode("utf-8"))

    def _search_place(self) -> None:
        place = self.place_var.get().strip()
        if not place:
            messagebox.showerror("Place search", "Enter a place name.")
            return
        self.location_status.set("Searching for place…")
        threading.Thread(target=self._search_place_thread, args=(place,), daemon=True).start()

    def _search_place_thread(self, place: str) -> None:
        try:
            params = urllib.parse.urlencode({"name": place, "count": 8, "language": "en", "format": "json"})
            data = self._fetch_json(f"{GEOCODING_URL}?{params}")
            results = data.get("results", [])
            self.root.after(0, lambda: self._show_place_results(results))
        except Exception as exc:
            self.root.after(0, lambda: messagebox.showerror("Place search", f"Search failed: {exc}"))

    def _show_place_results(self, results: list[dict]) -> None:
        self.place_results = results
        self.search_list.delete(0, tk.END)
        if not results:
            self.location_status.set("No matching places found.")
            return
        for result in results:
            name = result.get("name", "")
            state = result.get("admin1", "")
            country = result.get("country", "")
            parts = [part for part in (name, state, country) if part]
            self.search_list.insert(tk.END, ", ".join(parts))
        self.location_status.set("Choose a matching place.")

    def _select_search_result(self, _event: tk.Event | None = None) -> None:
        selection = self.search_list.curselection()
        if not selection:
            return
        result = self.place_results[selection[0]]
        self.latitude = float(result["latitude"])
        self.longitude = float(result["longitude"])
        self.latitude_var.set(f"{self.latitude:.4f}")
        self.longitude_var.set(f"{self.longitude:.4f}")
        self.location_name = ", ".join(
            part
            for part in (
                result.get("name", ""),
                result.get("admin1", ""),
                result.get("country", ""),
            )
            if part
        )
        country_code = result.get("country_code", "")
        if country_code == "US":
            self.crane_unit.set("mph")
            self.concrete_unit.set("F")
        else:
            self.crane_unit.set("km/h")
            self.concrete_unit.set("C")
        self.location_status.set(f"{self.location_name} — coordinates selected")

    def _fetch_forecast(self) -> None:
        try:
            latitude = float(self.latitude_var.get())
            longitude = float(self.longitude_var.get())
            if not -90 <= latitude <= 90 or not -180 <= longitude <= 180:
                raise ValueError("Latitude or longitude is outside its valid range.")
        except ValueError as exc:
            messagebox.showerror("Forecast", str(exc))
            return

        self.latitude = latitude
        self.longitude = longitude
        self.location_status.set("Loading seven-day forecast…")
        threading.Thread(target=self._fetch_forecast_thread, args=(latitude, longitude), daemon=True).start()

    def _fetch_forecast_thread(self, latitude: float, longitude: float) -> None:
        try:
            params = {
                "latitude": latitude,
                "longitude": longitude,
                "hourly": "temperature_2m,wind_speed_10m,wind_gusts_10m,precipitation_probability",
                "timezone": "auto",
                "forecast_days": 7,
                "temperature_unit": "fahrenheit",
                "wind_speed_unit": "mph",
                "precipitation_unit": "inch",
            }
            data = self._fetch_json(f"{FORECAST_URL}?{urllib.parse.urlencode(params)}")
            self.root.after(0, lambda: self._apply_forecast(data))
        except Exception as exc:
            self.root.after(0, lambda: messagebox.showerror("Forecast", f"Forecast request failed: {exc}"))

    def _apply_forecast(self, data: dict) -> None:
        hourly = data.get("hourly")
        if not hourly or not hourly.get("time"):
            messagebox.showerror("Forecast", "The forecast response contained no hourly values.")
            return
        self.forecast = data
        self.timezone = data.get("timezone", "Unknown timezone")
        times = hourly["time"]
        seen: list[str] = []
        for time_text in times:
            date = time_text[:10]
            if date not in seen:
                seen.append(date)
            if len(seen) == 7:
                break
        self.forecast_dates = seen
        self._build_schedule_rows()
        self._draw_forecast_plot()
        if self.latitude is not None and self.longitude is not None:
            coordinate_text = f"{self.latitude:.4f}°, {self.longitude:.4f}° — "
        else:
            coordinate_text = ""
        self.location_status.set(f"{self.location_name} — {coordinate_text}{self.timezone}")
        self.detail_var.set("Forecast loaded. Enter work intervals and project criteria, then calculate ratings.")

    def _draw_forecast_plot(self) -> None:
        if not self.forecast:
            return
        hourly = self.forecast["hourly"]
        times = [datetime.fromisoformat(value) for value in hourly["time"]]
        temperatures = hourly["temperature_2m"]
        winds = hourly["wind_speed_10m"]
        gusts = hourly["wind_gusts_10m"]

        self.forecast_axis.clear()
        self.forecast_axis.plot(times, temperatures, color="#2878a5", linewidth=1.8, label="Temperature (°F)")
        self.forecast_axis.plot(times, winds, color="#e69f00", linewidth=1.4, label="Wind (mph)")
        self.forecast_axis.plot(times, gusts, color="#c44e52", linewidth=1.4, label="Gust (mph)")
        self.forecast_axis.set_title("Seven-day hourly forecast")
        self.forecast_axis.set_ylabel("Temperature (°F) / Wind (mph)")
        self.forecast_axis.set_xlabel("Local date and hour")
        self.forecast_axis.grid(True, alpha=0.25)
        self.forecast_axis.legend(loc="upper right", fontsize=8, ncols=3)
        self.forecast_figure.autofmt_xdate(rotation=25)
        self.plot_canvas.draw_idle()
        maximum = max(0, len(times) - 1)
        self.hour_slider.configure(from_=0, to=maximum)
        self.hour_slider_index = 0
        self.hour_slider.set(0)
        self._update_selected_hour(0)

    def _on_hour_slider(self, value: str) -> None:
        try:
            index = int(round(float(value)))
        except ValueError:
            return
        self.hour_slider_index = index
        self._update_selected_hour(index)

    def _update_selected_hour(self, index: int) -> None:
        if not self.forecast:
            return
        hourly = self.forecast["hourly"]
        times = [datetime.fromisoformat(value) for value in hourly["time"]]
        temperatures = hourly["temperature_2m"]
        winds = hourly["wind_speed_10m"]
        gusts = hourly["wind_gusts_10m"]
        precipitation = hourly["precipitation_probability"]
        if not times:
            return

        index = max(0, min(index, len(times) - 1))
        selected_time = times[index]
        hour_12 = selected_time.hour % 12 or 12
        period = "AM" if selected_time.hour < 12 else "PM"
        selected_hour = (
            f"{selected_time.strftime('%A, %b %d')} at "
            f"{hour_12}:{selected_time.minute:02d} {period}"
        )
        temperature = temperatures[index]
        wind = winds[index]
        gust = gusts[index]
        pop = precipitation[index]
        self.hour_summary_var.set(
            f"{selected_hour}: {temperature:.1f}°F  |  Wind {wind:.1f} mph  "
            f"|  Gust {gust:.1f} mph  |  Precipitation {pop:.0f}%"
        )

        for marker in getattr(self, "_selected_hour_markers", []):
            marker.remove()
        self._selected_hour_markers = [
            self.forecast_axis.axvline(
                selected_time,
                color="#7a4bc3",
                linestyle="--",
                linewidth=1.5,
                label="_selected_hour",
            )
        ]
        self.plot_canvas.draw_idle()

    def _build_schedule_rows(self) -> None:
        for _, start_var, end_var in self.schedule_rows:
            start_var.set("")
            end_var.set("")
        for widget in tuple(getattr(self, "_schedule_frame", []).values()) if isinstance(getattr(self, "_schedule_frame", None), dict) else ():
            widget.destroy()
        self.schedule_rows = []

        schedule_card = self.root.nametowidget(
            "." + str(next(iter([w for w in self.root.winfo_children() if isinstance(w, ttk.Frame)])))
        ) if False else None

        for frame in self.root.winfo_children():
            pass

        # Locate the work-interval LabelFrame by text.
        schedule_card = None
        for frame in self.root.winfo_children():
            for child in frame.winfo_children():
                if isinstance(child, ttk.LabelFrame) and child.cget("text") == "3. Work intervals":
                    schedule_card = child
                    break
        if schedule_card is None:
            for frame in self.root.winfo_children():
                for child in frame.winfo_children():
                    if isinstance(child, ttk.LabelFrame) and child.cget("text"):
                        for descendant in child.winfo_children():
                            if isinstance(descendant, ttk.LabelFrame) and descendant.cget("text") == "3. Work intervals":
                                schedule_card = descendant

        # Work interval card was stored as a widget by rebuilding a direct search.
        if not hasattr(self, "schedule_card"):
            for widget in self.root.winfo_children():
                for candidate in widget.winfo_children():
                    if isinstance(candidate, ttk.LabelFrame) and candidate.cget("text") == "3. Work intervals":
                        schedule_card = candidate
                        break
        if not hasattr(self, "schedule_card"):
            # The card is the 4th direct child of the left main frame; find it recursively.
            schedule_card = schedule_card

        # Keep this method simple: rebuild widgets from the known grid position by searching descendants.
        found = []
        def walk(parent: tk.Misc) -> None:
            for child in parent.winfo_children():
                if isinstance(child, ttk.LabelFrame) and child.cget("text") == "3. Work intervals":
                    found.append(child)
                walk(child)
        walk(self.root)
        if not found:
            return
        schedule_card = found[0]

        for child in schedule_card.winfo_children():
            if getattr(child, "_name", "") not in (""):
                pass
        # Remove only existing schedule rows; preserve the heading label.
        for child in list(schedule_card.grid_slaves()):
            grid_info = child.grid_info()
            if grid_info and int(grid_info.get("row", 0)) >= 1:
                child.destroy()

        for row, date in enumerate(self.forecast_dates, start=1):
            ttk.Label(schedule_card, text=f"{date}").grid(row=row, column=0, sticky="w")
            start_var = tk.StringVar(value="")
            end_var = tk.StringVar(value="")
            ttk.Entry(schedule_card, textvariable=start_var, width=8).grid(row=row, column=1)
            ttk.Entry(schedule_card, textvariable=end_var, width=8).grid(row=row, column=2, padx=(4, 0))
            self.schedule_rows.append((date, start_var, end_var))

    def _calculate_ratings(self) -> None:
        if not self.forecast:
            messagebox.showerror("Ratings", "Fetch a forecast before calculating ratings.")
            return

        for item in self.ratings_table.get_children():
            self.ratings_table.delete(item)

        try:
            crane_limit = float(self.crane_var.get())
            concrete_minimum = float(self.concrete_var.get())
            if crane_limit <= 0:
                raise ValueError("The crane limit must be positive.")
            if not math.isfinite(crane_limit) or not math.isfinite(concrete_minimum):
                raise ValueError("Criteria must contain finite numbers.")
        except ValueError as exc:
            messagebox.showerror("Criteria", str(exc))
            return
        if not self.crane_source_var.get().strip():
            messagebox.showerror("Criteria", "Enter a crane manufacturer source.")
            return
        if not self.concrete_source_var.get().strip():
            messagebox.showerror("Criteria", "Enter a concrete project specification/source.")
            return

        if self.crane_unit.get() == "km/h":
            crane_limit_mph = calculations.kmh_to_mph(crane_limit)
        else:
            crane_limit_mph = crane_limit
        if self.concrete_unit.get() == "C":
            concrete_minimum_f = calculations.celsius_to_fahrenheit(concrete_minimum)
        else:
            concrete_minimum_f = concrete_minimum

        hourly = self.forecast["hourly"]
        times = hourly["time"]
        temperatures = hourly["temperature_2m"]
        winds = hourly["wind_speed_10m"]
        gusts = hourly["wind_gusts_10m"]
        precipitation = hourly["precipitation_probability"]

        self.rating_details: dict[str, dict[str, calculations.Rating]] = {}
        for date, start_var, end_var in self.schedule_rows:
            start_text = start_var.get().strip()
            end_text = end_var.get().strip()
            if not start_text or not end_text:
                status_text = "Not Scheduled"
                crane_status = concrete_status = roofing_status = status_text
                item = self.ratings_table.insert("", tk.END, values=(date, crane_status, concrete_status, roofing_status))
                self.ratings_table.set(item, "date", date)
                continue

            try:
                start_clock = datetime.strptime(start_text, "%H:%M")
                end_clock = datetime.strptime(end_text, "%H:%M")
            except ValueError:
                messagebox.showerror("Schedule", f"{date}: use 24-hour HH:MM times.")
                return

            start = datetime.strptime(date, "%Y-%m-%d").replace(
                hour=start_clock.hour, minute=start_clock.minute
            )
            end = datetime.strptime(date, "%Y-%m-%d").replace(
                hour=end_clock.hour, minute=end_clock.minute
            )
            if end <= start:
                end += timedelta(days=1)

            indexes = []
            for index, time_text in enumerate(times):
                hour = datetime.strptime(time_text, "%Y-%m-%dT%H:%M")
                hour_end = hour + timedelta(hours=1)
                if hour < end and hour_end > start:
                    indexes.append(index)

            if not indexes:
                status_text = "Unavailable"
                item = self.ratings_table.insert("", tk.END, values=(date, status_text, status_text, status_text))
                continue

            if any(temperatures[index] is None for index in indexes):
                concrete_status = "Unavailable"
            else:
                concrete_rating = calculations.concrete_rating(
                    min(temperatures[index] for index in indexes),
                    concrete_minimum_f,
                )
                concrete_status = concrete_rating.status

            wind_values = [
                value
                for index in indexes
                for value in (winds[index], gusts[index])
                if value is not None
            ]
            if not wind_values:
                crane_status = "Unavailable"
            else:
                crane_rating = calculations.crane_rating(max(wind_values), crane_limit_mph)
                crane_status = crane_rating.status

            pop_values = [precipitation[index] for index in indexes if precipitation[index] is not None]
            if not pop_values:
                roofing_status = "Unavailable"
            else:
                roofing_rating = calculations.roofing_rating(max(pop_values))
                roofing_status = roofing_rating.status

            item = self.ratings_table.insert(
                "",
                tk.END,
                values=(date, crane_status, concrete_status, roofing_status),
            )
            self.rating_details[date] = {
                "Crane": crane_rating if crane_status != "Unavailable" else calculations.Rating("Unavailable", "Missing wind or gust data."),
                "Concrete": concrete_rating if concrete_status != "Unavailable" else calculations.Rating("Unavailable", "Missing temperature data."),
                "Roofing": roofing_rating if roofing_status != "Unavailable" else calculations.Rating("Unavailable", "Missing precipitation data."),
            }

        self.detail_var.set("Select a date and then choose a rating column to inspect the reason.")

    def _show_rating_detail(self, _event: tk.Event | None = None) -> None:
        selection = self.ratings_table.selection()
        if not selection:
            return
        values = self.ratings_table.item(selection[0], "values")
        date = values[0]
        details = getattr(self, "rating_details", {}).get(date)
        if not details:
            self.detail_var.set(f"{date}: {', '.join(values[1:])}")
            return
        parts = [f"{name}: {rating.status} — {rating.reason}" for name, rating in details.items()]
        self.detail_var.set(f"{date}\n" + "\n".join(parts))

    def _export_csv(self) -> None:
        path = filedialog.asksaveasfilename(
            title="Export ratings",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")],
        )
        if not path:
            return
        try:
            with open(path, "w", newline="", encoding="utf-8") as file:
                writer = csv.writer(file)
                writer.writerow(["Date", "Crane", "Concrete", "Roofing"])
                for item in self.ratings_table.get_children():
                    writer.writerow(self.ratings_table.item(item, "values"))
            messagebox.showinfo("Export", f"Ratings exported to {path}")
        except OSError as exc:
            messagebox.showerror("Export", f"Could not export CSV: {exc}")

    def _save_inputs(self) -> None:
        path = filedialog.asksaveasfilename(
            title="Save inputs",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json")],
        )
        if not path:
            return
        payload = {
            "place": self.place_var.get(),
            "latitude": self.latitude_var.get(),
            "longitude": self.longitude_var.get(),
            "crane_limit": self.crane_var.get(),
            "crane_unit": self.crane_unit.get(),
            "crane_source": self.crane_source_var.get(),
            "concrete_limit": self.concrete_var.get(),
            "concrete_unit": self.concrete_unit.get(),
            "concrete_source": self.concrete_source_var.get(),
            "schedules": [
                {"date": date, "start": start.get(), "end": end.get()}
                for date, start, end in self.schedule_rows
            ],
        }
        try:
            with open(path, "w", encoding="utf-8") as file:
                json.dump(payload, file, indent=2)
        except OSError as exc:
            messagebox.showerror("Save", f"Could not save inputs: {exc}")

    def _open_inputs(self) -> None:
        path = filedialog.askopenfilename(
            title="Open inputs",
            filetypes=[("JSON files", "*.json")],
        )
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as file:
                payload = json.load(file)
            self.place_var.set(payload.get("place", ""))
            self.latitude_var.set(payload.get("latitude", ""))
            self.longitude_var.set(payload.get("longitude", ""))
            self.crane_var.set(payload.get("crane_limit", ""))
            self.crane_unit.set(payload.get("crane_unit", "mph"))
            self.crane_source_var.set(payload.get("crane_source", ""))
            self.concrete_var.set(payload.get("concrete_limit", ""))
            self.concrete_unit.set(payload.get("concrete_unit", "F"))
            self.concrete_source_var.set(payload.get("concrete_source", ""))
            schedule_lookup = {row["date"]: row for row in payload.get("schedules", [])}
            for date, start, end in self.schedule_rows:
                row = schedule_lookup.get(date)
                if row:
                    start.set(row.get("start", ""))
                    end.set(row.get("end", ""))
        except (OSError, json.JSONDecodeError) as exc:
            messagebox.showerror("Open", f"Could not open inputs: {exc}")


def main() -> None:
    root = tk.Tk()
    app = JobsiteWeatherPlanner(root)
    root.mainloop()


if __name__ == "__main__":
    main()
