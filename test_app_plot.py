import tkinter as tk
import unittest

from matplotlib.backends.backend_tkagg import NavigationToolbar2Tk

from app import JobsiteWeatherPlanner


class AppPlotTests(unittest.TestCase):
    def test_embedded_plot_and_toolbar(self):
        root = tk.Tk()
        root.withdraw()
        app = JobsiteWeatherPlanner(root)

        data = {
            "timezone": "America/Denver",
            "hourly": {
                "time": [
                    "2026-11-18T14:00",
                    "2026-11-18T15:00",
                    "2026-11-18T16:00",
                ],
                "temperature_2m": [47.2, 48.1, 47.7],
                "wind_speed_10m": [2.8, 2.1, 2.9],
                "wind_gusts_10m": [6.3, 5.4, 5.6],
                "precipitation_probability": [0.0, 0.0, 0.0],
            },
        }
        app._apply_forecast(data)
        root.update()

        self.assertIsInstance(app.plot_toolbar, NavigationToolbar2Tk)
        self.assertEqual(len(app.forecast_axis.lines), 3)
        self.assertEqual(len(app.forecast_dates), 1)

        root.destroy()


if __name__ == "__main__":
    unittest.main()
