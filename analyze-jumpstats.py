from datetime import datetime, timedelta
import argparse
import csv
import os
import sys
import time

COL_RESET = "\033[0m"
COL_BLUE = "\033[34m"
COL_GREEN = "\033[32m"
COL_RED = "\033[31m"
COL_GOLD = "\033[93m"
COL_BOLD = "\033[1m"

class Longjump:
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

	def init_empty():
		return Longjump(0, 0, 0, 0, 0, 0, 0, False, False)

def get_distance_color(distance):
	color = COL_RESET
	if distance >= 265:
		color = COL_BLUE
	if distance >= 270:
		color = COL_GREEN
	if distance >= 275:
		color = COL_RED
	if distance >= 285:
		color = COL_GOLD
	return color

def get_stat_files(directory):
	stat_files = []
	for root, dirs, files in os.walk(directory):
		for file in files:
			if file.endswith(".csv"):
				stat_files.append(os.path.join(root, file))

	return stat_files

def read_stats(fp):
	stats = []
	reader = csv.reader(fp)
	next(reader)
	for row in reader:
		time, distance, strafes, pre, max_vel, height, sync, crouch, min_forward = row
		stats.append(Longjump(int(time), float(distance), int(strafes), float(pre), int(max_vel), float(height), int(sync), crouch == "yes", min_forward == "yes"))
	return stats

def strstat(stat):
	return f"{get_distance_color(stat.distance)}{round(stat.distance, 3)} units ({stat.strafes} strafes | {stat.sync}% sync | {stat.pre} pre | {stat.max_vel} max){COL_RESET}"

def get_longest_jumps(stats):
	longest_jumps = { "all": Longjump.init_empty(), "month": Longjump.init_empty(), "week": Longjump.init_empty() }
	time_month_ago = datetime.now() - timedelta(days=30)
	time_week_ago = datetime.now() - timedelta(days=7)

	for stat in stats:
		if stat.distance > longest_jumps["all"].distance:
			longest_jumps["all"] = stat

		if datetime.fromtimestamp(stat.timestamp) > time_month_ago and stat.distance > longest_jumps["month"].distance:
			longest_jumps["month"] = stat

		if datetime.fromtimestamp(stat.timestamp) > time_week_ago and stat.distance > longest_jumps["week"].distance:
			longest_jumps["week"] = stat

	return longest_jumps

def get_shortest_jump(stats):
	shortest = Longjump(1000, 1000.0, 1000, 1000.0, 1000, 1000.0, 1000, False, False)
	for stat in stats:
		if stat.distance < shortest.distance:
			shortest = stat
	return shortest

def get_average_distance(stats):
	total_distance = 0.00
	for stat in stats:
		total_distance += stat.distance
	return total_distance / len(stats)

def get_common_distances(stats):
	distances = {}
	for stat in stats:
		key = int(stat.distance)
		if key in distances:
			distances[key] += 1
		else:
			distances[key] = 1
	return list(reversed(sorted(distances.items(), key=lambda x:x[1])))

def get_common_strafes(stats):
	strafes = {}
	for stat in stats:
		key = int(stat.strafes)
		if key in strafes:
			strafes[key] += 1
		else:
			strafes[key] = 1
	return list(reversed(sorted(strafes.items(), key=lambda x:x[1])))

def get_timespan(stats):
	start_time = 2147483648
	end_time = 0
	for stat in stats:
		if stat.timestamp > end_time:
			end_time = stat.timestamp
		if stat.timestamp < start_time:
			start_time = stat.timestamp
	return start_time, end_time

def get_jumps_over(stats):
	jumps_over = {"265": 0, "270": 0, "275": 0, "285": 0}
	for stat in stats:
		if stat.distance > 285:
			jumps_over["285"] += 1
		if stat.distance > 275:
			jumps_over["275"] += 1
		if stat.distance > 270:
			jumps_over["270"] += 1
		if stat.distance > 265:
			jumps_over["265"] += 1
	return jumps_over

def get_active_hours(stats):
	active_hours = {}
	for stat in stats:
		#                                                     I blame windows for this shit
		#                                                                  V
		hour = datetime.fromtimestamp(stat.timestamp).strftime("%I %p").lstrip("0")
		if hour in active_hours:
			active_hours[hour] += 1
		else:
			active_hours[hour] = 1
	return list(reversed(sorted(active_hours.items(), key=lambda x:x[1])))

def get_active_days(stats):
	active_days = {}
	for stat in stats:
		day = datetime.fromtimestamp(stat.timestamp).strftime("%a").lower()
		if day in active_days:
			active_days[day] += 1
		else:
			active_days[day] = 1
	return list(reversed(sorted(active_days.items(), key=lambda x:x[1])))

def format_timestamp(timestamp):
	return datetime.fromtimestamp(timestamp).strftime("%d/%m/%Y %H:%M:%S")

def merge_stat_files(stat_files):
	fields = ["time", "distance", "strafes", "pre", "max", "height", "sync", "crouchjump", "-forward"]
	new_rows = []
	for stat_file in stat_files:
		with open(stat_file, "r") as file:
			reader = csv.reader(file)
			next(reader)
			for row in reader:
				new_rows.append(row)

	print(f"Read {len(new_rows)} rows from {len(stat_files)} files.")
	print(f"Merging all into one file...")

	with open("merged.csv", "w", newline='', encoding='utf-8') as file:
		writer = csv.writer(file)
		writer.writerow(fields)
		for row in new_rows:
			writer.writerow(row)

if __name__ == "__main__":
	parser = argparse.ArgumentParser()
	parser.add_argument("-d", "--stats-directory", help="Choose different stats directory", dest="stats_directory")
	parser.add_argument("-m", "--merge", help="Merge all stat files into one", action="store_true", dest="merge")
	args = parser.parse_args()

	stats_directory = "stats/"
	if args.stats_directory is not None:
		stats_directory = args.stats_directory

	print(f"Collecting stats...")
	stat_files = get_stat_files(stats_directory)

	if args.merge:
		merge_start = time.time()
		print(f"Merging {len(stat_files)} files...")
		merge_stat_files(stat_files)
		merge_time = time.time() - merge_start
		print(f"Completed merge in {round(merge_time * 1000, 2)}ms")
		sys.exit(0)

	all_stats = []
	for stat_file in stat_files:
		with open(stat_file, "r") as file:
			stats = read_stats(file)
			for stat in stats:
				all_stats.append(stat)
	print(f"Got {len(all_stats)} stat(s) from {len(stat_files)} file(s)")

	if len(all_stats) < 1:
		print(f"No stats to analyze. Quitting.")
		sys.exit(0)

	start_time, end_time = get_timespan(all_stats)
	active_hours = get_active_hours(all_stats)
	active_days = get_active_days(all_stats)
	jumps_over = get_jumps_over(all_stats)
	longest_jumps = get_longest_jumps(all_stats)
	shortest_jump = get_shortest_jump(all_stats)
	average_distance = get_average_distance(all_stats)
	common_distances = get_common_distances(all_stats)
	common_strafes = get_common_strafes(all_stats)

	print(f"Jumpstats from {COL_BOLD}{format_timestamp(start_time)}{COL_RESET} to {COL_BOLD}{format_timestamp(end_time)}{COL_RESET}")
	print()

	print(f"{COL_BOLD}active hours{COL_RESET}:")
	for active_hour in active_hours[0:5]:
		print(f"{active_hour[0]:>8}: {active_hour[1]} jumps")
	print()

	print(f"{COL_BOLD}active days{COL_RESET}:")
	for active_day in active_days[0:5]:
		print(f"{active_day[0]:>8}: {active_day[1]} jumps")
	print()

	print(f"{COL_BOLD}jumps over{COL_RESET}:")
	for jump_over in jumps_over:
		percent = round((jumps_over[jump_over] / len(all_stats)) * 100, 2)
		print(f"{get_distance_color(int(jump_over))}{jump_over:>8}{COL_RESET}: {jumps_over[jump_over]:<4} | {percent}%")
	print()

	print(f"{COL_BOLD}longest jumps{COL_RESET}:")
	for longest_jump in longest_jumps:
		# Time will default to zero if there's no matches, so if you haven't 
		# hit a jump in a week we'll just not show a result
		if longest_jumps[longest_jump].timestamp == 0:
			continue
		print(f"{longest_jump:>8}: {strstat(longest_jumps[longest_jump])} ({format_timestamp(longest_jumps[longest_jump].timestamp)})")
	print()

	print(f"{COL_BOLD}shortest jump{COL_RESET}:    {strstat(shortest_jump)} ({format_timestamp(shortest_jump.timestamp)}){COL_RESET}")
	print(f"{COL_BOLD}average distance{COL_RESET}: {get_distance_color(average_distance)}{round(average_distance, 3)} units{COL_RESET}")
	print()

	print(f"{COL_BOLD}most common distances jumped{COL_RESET}:")
	for dist in common_distances[0:5]:
		print(f"{get_distance_color(dist[0])}{dist[0]:>8}{COL_RESET}: {dist[1]}")
	
	print()
	print(f"{COL_BOLD}most common number of strafes{COL_RESET}:")
	for strafes in common_strafes[0:5]:
		print(f"{strafes[0]:>8}: {strafes[1]}")