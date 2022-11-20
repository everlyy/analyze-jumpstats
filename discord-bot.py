from discord import app_commands
import AnalyzeJumpstats as ajs
import config
import discord
import tempfile

discord_intents = discord.Intents.default()
discord_client = discord.Client(intents=discord_intents)
discord_client.sync_tree = False
command_tree = app_commands.CommandTree(discord_client)

@discord_client.event
async def on_ready():
	if discord_client.sync_tree:
		print(f"Syncing command tree...")
		await command_tree.sync()
		discord_client.sync_tree = False

	print(f"Discord client ready.")

@command_tree.error
async def command_error(interaction, error):
	message = f"An error occurred while executing `{interaction.command.name}`:\n```{error}```"
	await interaction.followup.send(message)

def strstat(stat):
	return f"{round(stat.distance, 2)} units ({stat.strafes} strafes | {stat.sync}% sync | {stat.pre} pre | {stat.max_vel} max)"

@command_tree.command(description="Analyze your jumpstats from a CSV file.")
async def analyze_jumpstats(interaction, stats_file: discord.Attachment):
	await interaction.response.defer()	

	# I don't know if there's a better way to check for CSV files only
	if stats_file.content_type.split(";")[0] != "text/csv":
		await interaction.followup.send(f"Attachment isn't a CSV file.")
		return

	if stats_file.size > config.MAX_FILE_SIZE:
		await interaction.followup.send(f"Attachment is over 10 MiB.")
		return

	tmpfile = tempfile.NamedTemporaryFile()
	with open(tmpfile.name, "wb") as file:
		await stats_file.save(file)
	
	stats = []
	with open(tmpfile.name, "r") as file:
		stats = ajs.read_stats(file)

	jumps_over = ajs.get_jumps_over(stats)
	longest_jump = ajs.get_longest_jump(stats)
	shortest_jump = ajs.get_shortest_jump(stats)
	average_distance = ajs.get_average_distance(stats)
	common_distances = ajs.get_common_distances(stats)
	common_strafes = ajs.get_common_strafes(stats)

	embed = discord.Embed(
		title="Jumpstats",
		description=f"Loaded {len(stats)} stats from `{stats_file.filename}`"
	)

	embed.set_author(name="everlyy/analyze-jumpstats", url="https://github.com/everlyy/analyze-jumpstats")

	jumps_over_msg = "```"
	for jump_over in jumps_over:
		percent = round((jumps_over[jump_over] / len(stats)) * 100, 2)
		jumps_over_msg += f"{jump_over:>8}: {jumps_over[jump_over]:<4} | {percent}%\n"
	jumps_over_msg += "```"
	embed.add_field(name="Jumps Over", value=jumps_over_msg, inline=False)

	embed.add_field(name="Longest Jump", value=f"`{strstat(longest_jump)}`", inline=False)
	embed.add_field(name="Shortest Jump", value=f"`{strstat(shortest_jump)}`", inline=False)
	embed.add_field(name="Average Distance", value=f"`{round(average_distance, 3)} units`", inline=False)


	common_distances_msg = "```"
	for dist in common_distances[0:5]:
		common_distances_msg += f"{dist[0]:>8}: {dist[1]}\n"
	common_distances_msg += "```"
	embed.add_field(name="Common Distances", value=common_distances_msg, inline=False)
	
	common_strafes_msg = "```"
	for strafes in common_strafes[0:5]:
		common_strafes_msg += f"{strafes[0]:>8}: {strafes[1]}\n"
	common_strafes_msg += "```"
	embed.add_field(name="Common Number of Strafes", value=common_strafes_msg, inline=False)

	await interaction.followup.send(embed=embed)

discord_client.run(config.DISCORD_TOKEN)