import os
import gzip
import re
import matplotlib.pyplot as plt
import pandas as pd
import calmap
from datetime import datetime, timedelta
from collections import defaultdict


LOG_DIR = os.path.expanduser("~/AppData/Roaming/.minecraft/logs")
CUTOFF_DATE = datetime.strptime("2000-01-01", "%Y-%m-%d") # --- CHANGE THIS TO E.G. ONLY SHOW LAST YEAR ---

START_PATTERN = re.compile(r"\[(\d{2}:\d{2}:\d{2})\]")
END_PATTERN = re.compile(r"\[(\d{2}:\d{2}:\d{2})\]")

def extract_date_from_filename(filename):
    match = re.match(r"(\d{4}-\d{2}-\d{2})", filename)
    if match:
        return datetime.strptime(match.group(1), "%Y-%m-%d")
    return None

def read_session_times(filepath, is_gz, inferred_date):
    open_func = gzip.open if is_gz else open
    start_time = None
    end_time = None

    with open_func(filepath, 'rt', errors='ignore') as f:
        for line in f:
            if not start_time:
                match = START_PATTERN.search(line)
                if match:
                    start_time = match.group(1)
            match = END_PATTERN.search(line)
            if match:
                end_time = match.group(1)

    if start_time and end_time and inferred_date:
        try:
            start_dt = datetime.strptime(f"{inferred_date.strftime('%Y-%m-%d')} {start_time}", "%Y-%m-%d %H:%M:%S")
            end_dt = datetime.strptime(f"{inferred_date.strftime('%Y-%m-%d')} {end_time}", "%Y-%m-%d %H:%M:%S")
            if end_dt > start_dt:
                return start_dt.date(), end_dt - start_dt
        except Exception:
            pass
    return None, None

playtime_per_day = defaultdict(timedelta)

for filename in sorted(os.listdir(LOG_DIR)):
    if not (filename.endswith(".log") or filename.endswith(".log.gz")):
        continue

    filepath = os.path.join(LOG_DIR, filename)
    is_gz = filename.endswith(".gz")
    file_date = extract_date_from_filename(filename)

    if file_date:
        if file_date < CUTOFF_DATE:
            continue
    else:
        file_date = datetime.today()

    day, duration = read_session_times(filepath, is_gz, file_date)
    if day and duration:
        playtime_per_day[day] += duration

print("=== Playtime (based on start/load and save line) per Day (last 1 year) ===")
for day in sorted(playtime_per_day.keys()):
    total = playtime_per_day[day]
    hours, remainder = divmod(total.total_seconds(), 3600)
    minutes, seconds = divmod(remainder, 60)
    print(f"{day}: {int(hours)}h {int(minutes)}m {int(seconds)}s")

series_data = {
    pd.Timestamp(date): duration.total_seconds() / 3600
    for date, duration in playtime_per_day.items()
}
series = pd.Series(series_data)

plt.figure(figsize=(16, 6))
calmap.calendarplot(
    series,
    how='sum',
    cmap='YlGnBu',
    fillcolor='lightgray',
    linewidth=0.5,
    daylabels='MTWTFSS',
    dayticks=[0, 1, 2, 3, 4, 5, 6],
    monthticks=1,
    yearlabels=True,
    yearlabel_kws={'color': 'black', 'fontsize': 14}
)
plt.suptitle('Minecraft Playtime per Day', fontsize=18)
plt.tight_layout()
plt.show()
