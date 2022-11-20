import csv
import os
from datetime import datetime

COL_RESET = "\033[0m"
COL_BLUE = "\033[34m"
COL_GREEN = "\033[32m"
COL_RED = "\033[31m"
COL_GOLD = "\033[33m"
COL_BOLD = "\033[1m"

class Longjump:
	def __init__(self, time, distance, strafes, pre, max_vel, height, sync, crouch, min_forward):
		self.time = time
		self.distance = distance
		self.strafes = strafes
		self.pre = pre
		self.max_vel = max_vel
		self.height = height
		self.sync = sync
		self.crouch = crouch
		self.min_forward = min_forward

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
	return f"{get_distance_color(stat.distance)}{round(stat.distance, 2)} units ({stat.strafes} strafes | {stat.sync}% sync | {stat.pre} pre | {stat.max_vel} max){COL_RESET}"

def get_longest_jump(stats):
	longest = Longjump(0, 0, 0, 0, 0, 0, 0, False, False)
	for stat in stats:
		if stat.distance > longest.distance:
			longest = stat
	return longest

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
		if stat.time > end_time:
			end_time = stat.time
		if stat.time < start_time:
			start_time = stat.time
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

def format_timestamp(timestamp):
	return datetime.fromtimestamp(timestamp).strftime("%d/%m/%Y %H:%M:%S")

if __name__ == "__main__":
	print(f"Collecting stats...")
	stat_files = get_stat_files("stats/")
	all_stats = []
	for stat_file in stat_files:
		with open(stat_file, "r") as file:
			stats = read_stats(file)
			for stat in stats:
				all_stats.append(stat)
	print(f"Got {len(all_stats)} stat(s) from {len(stat_files)} file(s)")

	start_time, end_time = get_timespan(all_stats)
	jumps_over = get_jumps_over(all_stats)
	longest_jump = get_longest_jump(all_stats)
	shortest_jump = get_shortest_jump(all_stats)
	average_distance = get_average_distance(all_stats)
	common_distances = get_common_distances(all_stats)
	common_strafes = get_common_strafes(all_stats)

	print(f"Jumpstats from {COL_BOLD}{format_timestamp(start_time)}{COL_RESET} to {COL_BOLD}{format_timestamp(end_time)}{COL_RESET}")
	print()

	print(f"jumps over:")
	for jump_over in jumps_over:
		percent = round((jumps_over[jump_over] / len(all_stats)) * 100, 2)
		print(f"{get_distance_color(int(jump_over))}{jump_over:>8}{COL_RESET}: {jumps_over[jump_over]:<4} | {percent}%")

	print()
	print(f"longest jump: {strstat(longest_jump)}")
	print(f"shortest jump: {strstat(shortest_jump)}")
	print(f"average distance: {get_distance_color(average_distance)}{round(average_distance, 3)} units{COL_RESET}")
	print()

	print(f"most common distances jumped:")
	for dist in common_distances[0:5]:
		print(f"{get_distance_color(dist[0])}{dist[0]:>8}{COL_RESET}: {dist[1]}")
	
	print()
	print(f"most common number of strafes:")
	for strafes in common_strafes[0:5]:
		print(f"{strafes[0]:>8}: {strafes[1]}")