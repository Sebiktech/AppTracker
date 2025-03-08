import json

def log_time(self, app_name, start, end):
    current = start
    while current < end:
        next_hour = (current + timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)
        end_time = min(next_hour, end)

        duration = (end_time - current).total_seconds()
        date_str = current.strftime("%Y-%m-%d")
        hour_str = current.strftime("%H")

        self.hourly_data[date_str][hour_str][app_name] += duration

        current = next_hour

def save_data(self):
    # Convert defaultdict to regular dict for JSON serialization
    save_data = {}
    for date, hours in self.hourly_data.items():
        save_data[date] = {}
        for hour, apps in hours.items():
                save_data[date][hour] = dict(apps)

    with open(self.log_file, 'w') as f:
        json.dump(save_data, f, indent=2)


