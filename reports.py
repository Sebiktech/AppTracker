from datetime import datetime, timedelta
from collections import defaultdict

def generate_daily_report(self):
    date_str = self.daily_date.get() or datetime.now().strftime("%Y-%m-%d")
    try:
        target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        return

    daily_stats = self.daily_data.get(target_date.isoformat(), {})
    category_stats = self.category_data.get(target_date.isoformat(), {})

    report = f"Daily Report - {target_date}\n\n"
    report += "Applications:\n"
    for app, time in sorted(daily_stats.items(), key=lambda x: x[1], reverse=True):
        report += f"  {app.ljust(30)} {self.format_time(time)}\n"

    report += "\nCategories:\n"
    for cat, time in sorted(category_stats.items(), key=lambda x: x[1], reverse=True):
        report += f"  {cat.ljust(30)} {self.format_time(time)}\n"

    self.daily_text.configure(state="normal")
    self.daily_text.delete("1.0", "end")
    self.daily_text.insert("end", report)
    self.daily_text.configure(state="disabled")


def generate_weekly_report(self):
    date_str = self.weekly_date.get() or datetime.now().strftime("%Y-%m-%d")
    try:
        start_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        start_date -= timedelta(days=start_date.weekday())  # Monday start
    except ValueError:
        return

    end_date = start_date + timedelta(days=6)
    week_dates = [start_date + timedelta(days=i) for i in range(7)]

    weekly_apps = defaultdict(float)
    weekly_cats = defaultdict(float)

    for date in week_dates:
        date_str = date.isoformat()
        for app, time in self.daily_data.get(date_str, {}).items():
            weekly_apps[app] += time
        for cat, time in self.category_data.get(date_str, {}).items():
            weekly_cats[cat] += time

    report = f"Weekly Report - {start_date} to {end_date}\n\n"
    report += "Applications:\n"
    for app, time in sorted(weekly_apps.items(), key=lambda x: x[1], reverse=True):
        report += f"  {app.ljust(30)} {self.format_time(time)}\n"

    report += "\nCategories:\n"
    for cat, time in sorted(weekly_cats.items(), key=lambda x: x[1], reverse=True):
        report += f"  {cat.ljust(30)} {self.format_time(time)}\n"

    self.weekly_text.configure(state="normal")
    self.weekly_text.delete("1.0", "end")
    self.weekly_text.insert("end", report)
    self.weekly_text.configure(state="disabled")


def export_daily_csv(self):
    file_path = filedialog.asksaveasfilename(defaultextension=".csv",
                                             filetypes=[("CSV Files", "*.csv")])
    if not file_path:
        return

    date_str = self.daily_date.get() or datetime.now().strftime("%Y-%m-%d")
    daily_stats = self.daily_data.get(date_str, {})

    with open(file_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["Application", "Time Spent", "Category"])
        for app, time in daily_stats.items():
            category = self.get_app_category(app)
            writer.writerow([app, time, category])


def export_weekly_csv(self):
    file_path = filedialog.asksaveasfilename(defaultextension=".csv",
                                             filetypes=[("CSV Files", "*.csv")])
    if not file_path:
        return

    # ... Similar to daily export but aggregate weekly data ...
