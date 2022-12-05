from datetime import datetime, timedelta
import argparse
import csv
import os
import sys
import time

LJSTAT_ENTRY_COUNT = 9

class LJStat:
	def __init__(self, timestamp, distance, strafes, pre, max_vel, height, sync, crouch, min_forward):
		self.timestamp = timestamp
		self.distance = distance
		self.strafes = strafes
		self.pre = pre
		self.max_vel = max_vel
		self.height = height
		self.sync = sync
		self.crouch = crouch
		self.min_forward = min_forward

	def init_from_csv_row(row):
		if len(row) != LJSTAT_ENTRY_COUNT:
			raise Exception(f"CSV row doesn't have {LJSTAT_ENTRY_COUNT} entries.")

		time, distance, strafes, pre, max_vel, height, sync, crouch, min_forward = row
		return LJStat(
			int(time), 
			float(distance), 
			int(strafes), 
			float(pre), 
			int(max_vel), 
			float(height), 
			int(sync), 
			crouch == "yes", 
			min_forward == "yes"
		)

	def init_empty():
		return LJStat(0, 0.0, 0, 0.0, 0, 0.0, 0, False, False)

	def __str__(self):
		return f"{round(self.distance, 3)} units ({self.strafes} strafes | {self.sync}% sync | {self.pre} pre | {self.max_vel} max)"

class Color:
	RESET = "\033[0m"
	BOLD = "\033[1m"

	BLUE = "\033[34m"
	GREEN = "\033[32m"
	RED = "\033[31m"
	GOLD = "\033[93m"

def color_for_distance(lj_dist):
	color_map = {
		285: Color.GOLD,
		275: Color.RED,
		270: Color.GREEN,
		265: Color.BLUE
	}

	for col_dist in color_map:
		if lj_dist >= col_dist:
			return color_map[col_dist]
	return Color.RESET

def get_files_in_directory(directory, filetype):
	files_in_directory = []
	for root, dirs, files in os.walk(directory):
		for file in files:
			if file.endswith(filetype):
				files_in_directory.append(os.path.join(root, file))
	return files_in_directory

def read_stats_from_file(filename):
	stats = []
	with open(filename, "r") as file:
		reader = csv.reader(file)
		next(reader) # Skip the header
		for row in reader:
			try:
				stat = LJStat.init_from_csv_row(row)
				stats.append(stat)
			except Exception as e:
				print(f"Error while reading {filename}: {e}")
	return stats

class StatAnalytics:
	def __init__(self):
		self.timespan = { "start": 2147483648, "end": 0 }

		self.longest_jumps_per_timediff = {
			"all":   { "jump": LJStat.init_empty(), "timediff": datetime.fromtimestamp(0) },
			"month": { "jump": LJStat.init_empty(), "timediff": datetime.now() - timedelta(days=30) },
			"week":  { "jump": LJStat.init_empty(), "timediff": datetime.now() - timedelta(days=7) },
			"day":   { "jump": LJStat.init_empty(), "timediff": datetime.now() - timedelta(days=1) },
		}

		self.shortest_jump = LJStat.init_empty()
		self.shortest_jump.distance = 10000.0

		self.__total_distance = 0.0
		self.average_distance = 0.0

		self.common_distances = {}

		self.common_strafes = {}

		self.jumps_over = { 265: 0, 270: 0, 275: 0, 285: 0 }

		self.active_hours = {}

		self.active_days = {}

	def __timespan_from_stat(self, stat):
		if stat.timestamp < self.timespan["start"]:
			self.timespan["start"] = stat.timestamp
		if stat.timestamp > self.timespan["end"]:
			self.timespan["end"] = stat.timestamp

	def __longest_jumps_per_timediff_from_stat(self, stat):
		jump_time = datetime.fromtimestamp(stat.timestamp)
		for longest_jump_per_timediff in self.longest_jumps_per_timediff:
			ljtd = self.longest_jumps_per_timediff[longest_jump_per_timediff]

			if jump_time > ljtd["timediff"] and stat.distance > ljtd["jump"].distance:
				ljtd["jump"] = stat

	def __shortest_jump_from_stat(self, stat):
		if stat.distance < self.shortest_jump.distance:
			self.shortest_jump = stat

	def __common_distances_from_stat(self, stat):
		key = int(stat.distance)
		if key in self.common_distances:
			self.common_distances[key] += 1
		else:
			self.common_distances[key] = 1

	def __common_strafes_from_stat(self, stat):
		key = int(stat.strafes)
		if key in self.common_strafes:
			self.common_strafes[key] += 1
		else:
			self.common_strafes[key] = 1

	def __jumps_over_from_stat(self, stat):
		for dist in self.jumps_over:
			if stat.distance > dist:
				self.jumps_over[dist] += 1

	def __active_hours_from_stat(self, stat):
		# Has to be stripped because Windows doesn't support `%-I`
		hour = datetime.fromtimestamp(stat.timestamp).strftime("%I %p").lstrip("0")
		if hour in self.active_hours:
			self.active_hours[hour] += 1
		else:
			self.active_hours[hour] = 1

	def __active_days_from_stat(self, stat):
		day = datetime.fromtimestamp(stat.timestamp).strftime("%a").lower()
		if day in self.active_days:
			self.active_days[day] += 1
		else:
			self.active_days[day] = 1

	def analytics_from_list(self, stats):
		for stat in stats:
			self.__timespan_from_stat(stat)
			self.__longest_jumps_per_timediff_from_stat(stat)
			self.__shortest_jump_from_stat(stat)
			self.__common_distances_from_stat(stat)
			self.__common_strafes_from_stat(stat)
			self.__jumps_over_from_stat(stat)
			self.__active_hours_from_stat(stat)
			self.__active_days_from_stat(stat)

			self.__total_distance += stat.distance

		self.average_distance = self.__total_distance / len(stats);

		# Finalize some values by sorting them
		self.common_distances = list(reversed(sorted(self.common_distances.items(), key=lambda x:x[1])))
		self.common_strafes = list(reversed(sorted(self.common_strafes.items(), key=lambda x:x[1])))
		self.active_days = list(reversed(sorted(self.active_days.items(), key=lambda x:x[1])))
		self.active_hours = list(reversed(sorted(self.active_hours.items(), key=lambda x:x[1])))

def fmttime(timestamp):
	return datetime.fromtimestamp(timestamp).strftime("%d/%m/%Y %H:%M:%S")

def merge_stat_files(stats_directory, merged_file):
	merge_start_time = time.time()

	header = [ "time", "distance", "strafes", "pre", "max", "height", "sync", "crouchjump", "-forward" ]

	print(f"Merging all files in {Color.BOLD}{stats_directory}{Color.RESET} to {Color.BOLD}{merged_file}{Color.RESET}...")
	files = get_files_in_directory(stats_directory, ".csv")

	with open(merged_file, "w", newline="", encoding="utf-8") as outfile:
		writer = csv.writer(outfile)
		writer.writerow(header)

		for file in files:
			with open(file, "r") as infile:
				count = 0
				reader = csv.reader(infile)
				next(reader) # Skip header
				for row in reader:
					count += 1
					if len(row) != LJSTAT_ENTRY_COUNT:
						print(f"WARNING: Not adding line {count + 1} to merged file because it does not have {LJSTAT_ENTRY_COUNT} entries.")
						continue
					writer.writerow(row)

				print(f"Moved {Color.BOLD}{count}{Color.RESET} rows from {Color.BOLD}{file}{Color.RESET} to {Color.BOLD}{merged_file}{Color.RESET}")

	merge_time = time.time() - merge_start_time
	print(f"Merge completed in {Color.BOLD}{round(merge_time * 1000, 2)}ms{Color.RESET}")

if __name__ == "__main__":
	global_start_time = time.time()
	stats_directory = "stats/"

	parser = argparse.ArgumentParser()
	parser.add_argument("-d", "--stats-directory", help="Choose a different stats directory", dest="stats_directory")
	parser.add_argument("-m", "--merge", help="Merge all the files from the stats directory into one", dest="merged_file")
	args = parser.parse_args()

	if args.stats_directory is not None:
		stats_directory = args.stats_directory

	if args.merged_file is not None:
		merge_stat_files(stats_directory, args.merged_file)
		sys.exit(0)

	print(f"Collecting stats...")
	collect_stats_start_time = time.time()
	files = get_files_in_directory(stats_directory, ".csv")
	stats = []
	for file in files:
		stats.extend(read_stats_from_file(file))
	collect_stats_time = time.time() - collect_stats_start_time
	print(f"Collected {Color.BOLD}{len(stats)} stat(s){Color.RESET} from {Color.BOLD}{len(files)} file(s){Color.RESET} in {Color.BOLD}{round(collect_stats_time * 1000, 2)}ms{Color.RESET}")
	print()

	print("Calculating analytics...")
	analytics_start_time = time.time()
	analytics = StatAnalytics()
	analytics.analytics_from_list(stats)
	analytics_time = time.time() - analytics_start_time
	print(f"Calculated analytics in {Color.BOLD}{round(analytics_time * 1000, 2)}ms{Color.RESET}")
	print()

	print(f"Jumpstats from {Color.BOLD}{fmttime(analytics.timespan['start'])}{Color.RESET} to {Color.BOLD}{fmttime(analytics.timespan['end'])}{Color.RESET}")
	print()

	print(f"{Color.BOLD}most active days{Color.RESET}:")
	for active_day in analytics.active_days[0:3]:
		print(f"{active_day[0]:>8}: {active_day[1]} jumps")
	print()

	print(f"{Color.BOLD}most active hours{Color.RESET}:")
	for active_hour in analytics.active_hours[0:3]:
		print(f"{active_hour[0]:>8}: {active_hour[1]} jumps")
	print()

	print(f"{Color.BOLD}longest jumps{Color.RESET}:")
	for timediff in analytics.longest_jumps_per_timediff:
		longest_jump = analytics.longest_jumps_per_timediff[timediff]

		if longest_jump["jump"].timestamp == 0:
			continue

		print(f"{timediff:>8}: {color_for_distance(longest_jump['jump'].distance)}{longest_jump['jump']}{Color.RESET} {fmttime(longest_jump['jump'].timestamp)}")
	print()

	print(f"{Color.BOLD}jumps over{Color.RESET}:")
	for dist in analytics.jumps_over:
		percent = round((analytics.jumps_over[dist] / len(stats)) * 100, 2)
		print(f"{color_for_distance(dist)}{dist:>8}{Color.RESET}: {analytics.jumps_over[dist]:<6} | {percent}%")
	print()

	print(f"{Color.BOLD}shortest jump{Color.RESET}:    {color_for_distance(analytics.shortest_jump.distance)}{analytics.shortest_jump}{Color.RESET}")
	print(f"{Color.BOLD}average distance{Color.RESET}: {color_for_distance(analytics.average_distance)}{round(analytics.average_distance, 3)} units{Color.RESET}")
	print()

	print(f"{Color.BOLD}most common distances jumped{Color.RESET}:")
	for common_distance in analytics.common_distances[0:5]:
		print(f"{color_for_distance(common_distance[0])}{common_distance[0]:>8}{Color.RESET}: {common_distance[1]}")
	print()

	print(f"{Color.BOLD}most common number of strafes{Color.RESET}:")
	for common_strafe in analytics.common_strafes[0:5]:
		print(f"{common_strafe[0]:>8}: {common_strafe[1]}")
	print()

	global_time = time.time() - global_start_time
	print(f"Done in {Color.BOLD}{round(global_time * 1000, 2)}ms{Color.RESET}")