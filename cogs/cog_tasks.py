import time
import datetime
import shelve
import asyncio
import json
import logging

from discord.ext import tasks, commands
import discord

import matplotlib
import matplotlib.pyplot as plt


from riot import (
    riot_commands,
    riot_utility
)

from core.state import global_state as gstate

from core import (
    consts,
    bot_utility as utility,
    timers
)

logger = logging.getLogger(consts.LOG_NAME)

def update_summoners_data(file_path='./data/summoners_data.json'):
    summoners = list(riot_utility.read_all_accounts())
    time_updated = time.time()
    summoners = list(riot_commands.update_linked_summoners_data(summoners))

    with open(file_path) as json_file:
        summoners_data = json.load(json_file)

    queue_data_empty_dict = {'date_time': [], 'Rang': [], 'Winrate': []}
    for summoner in summoners:
        # print(summoner.discord_user_name, summoner.data_league)
        if summoner.discord_user_name not in summoners_data:
            summoners_data[summoner.discord_user_name] = {'soloq': queue_data_empty_dict, 'flex': queue_data_empty_dict}

        summoner_soloq_rank = summoner.get_rank_value()
        summoner_flex_rank = summoner.get_rank_value('RANKED_FLEX_SR')
        summoner_soloq_winrate = summoner.get_winrate()
        summoner_flex_winrate = summoner.get_winrate('RANKED_FLEX_SR')

        # TODO Bad copy paste!
        if len(summoners_data[summoner.discord_user_name]['soloq']['date_time']) == 0 or summoner_soloq_rank != summoners_data[summoner.discord_user_name]['soloq']['Rang'][-1] or summoner_soloq_winrate != summoners_data[summoner.discord_user_name]['soloq']['Winrate'][-1]:
            summoners_data[summoner.discord_user_name]['soloq']['date_time'].append(time_updated)
            summoners_data[summoner.discord_user_name]['soloq']['Rang'].append(summoner_soloq_rank)
            summoners_data[summoner.discord_user_name]['soloq']['Winrate'].append(summoner_soloq_winrate)
        if len(summoners_data[summoner.discord_user_name]['flex']['date_time']) == 0 or summoner_flex_rank != summoners_data[summoner.discord_user_name]['flex']['Rang'][-1] or summoner_flex_winrate != summoners_data[summoner.discord_user_name]['flex']['Winrate'][-1]:
            summoners_data[summoner.discord_user_name]['flex']['date_time'].append(time_updated)
            summoners_data[summoner.discord_user_name]['flex']['Rang'].append(summoner_flex_rank)
            summoners_data[summoner.discord_user_name]['flex']['Winrate'].append(summoner_flex_winrate)

    with open(file_path, 'w') as json_file:
        json.dump(summoners_data, json_file, indent=4)

    return summoners_data

def plot_summoners_data(summoners_data, queue_type, data, filename):
    fig1, ax1 = plt.subplots()

    ax1.set_xlabel('Zeit')
    ax1.set_ylabel(data)

    ax1.set_title(queue_type)

    if data == "Rang":
        ax1.set_yticks(list(range(0, 2300, 400)))
        ax1.set_yticks(list(range(0, 2300, 100)), minor=True)
        ranks_string = ["Eisen 4", "Bronze 4", "Silber 4", "Gold 4", "Platin 4", "Diamant 4"]
        ax1.set_yticklabels(ranks_string)
        ax1.grid(axis='y')

    for summoner in summoners_data:
        # TODO Timezone is false
        x_data = [matplotlib.dates.epoch2num(time) for time in summoners_data[summoner][queue_type]['date_time']]

        ax1.plot_date(x_data, list(summoners_data[summoner][queue_type][data]), label=summoner, drawstyle='steps-post', ls='-')

    ax1.legend()

    fig1.savefig(filename)




class LoopCog(commands.Cog):
    """A class for background tasks"""

    def __init__(self, bot: commands.bot):
        self.bot = bot

        self.message_cache = gstate.message_cache
        self.print_leaderboard_weekly.start()
        self.check_LoL_patch.start()
        self.auto_delete_purgeable_messages.start()
        self.auto_delete_tmp_channels.start()


    # @tasks.loop(hours = 24 * 7)
    # @tasks.loop(seconds = 5)
    @tasks.loop(hours=24)
    async def print_leaderboard_weekly(self):
        summoners_data = update_summoners_data()

        rank_plot_filename = 'temp/rank_graph.png'
        plot_summoners_data(summoners_data, 'soloq', 'Rang', rank_plot_filename)
        await self.channel.send(file=discord.File(rank_plot_filename))

        winrate_plot_filename = './temp/winrate_graph.png'
        plot_summoners_data(summoners_data, 'soloq', 'Winrate', winrate_plot_filename)
        await self.channel.send(file=discord.File(winrate_plot_filename))

        flex_rank_plot_filename = 'temp/flex_rank_graph.png'
        plot_summoners_data(summoners_data, 'flex', 'Rang', flex_rank_plot_filename)
        await self.channel.send(file=discord.File(flex_rank_plot_filename))

        flex_winrate_plot_filename = './temp/flex_winrate_graph.png'
        plot_summoners_data(summoners_data, 'flex', 'Winrate', flex_winrate_plot_filename)
        await self.channel.send(file=discord.File(flex_winrate_plot_filename))

    @print_leaderboard_weekly.before_loop
    async def before_print_leaderboard_weekly(self):
        datetime_now = datetime.datetime.now()
        offset_day = 0 if datetime_now.hour < 18 else 1
        datetime_18 = datetime.datetime(datetime_now.year, datetime_now.month, datetime_now.day + offset_day, 18)
        time_delta = (datetime_18 - datetime_now).total_seconds()
        print("Sekunden, bis geplottet wird:", time_delta)

        await asyncio.sleep(time_delta)
        await self.bot.wait_until_ready()

        self.channel = self.bot.get_channel(639889605256019980)

    @tasks.loop(hours=24)
    async def check_LoL_patch(self):
        logger.info('New LoL patch notes')
        # The for loop is not needed right now but if the bot will ever run on multiple servers this is needed.
        for guild in self.bot.guilds:
            if riot_utility.update_current_patch():
                annoucement_channel = discord.utils.find(lambda m: m.name == 'announcements', guild.channels)
                await annoucement_channel.send(consts.MESSAGE_PATCH_NOTES_FORMATTED.format(guild.get_role(consts.ROLE_LOL_ID).mention, riot_utility.get_current_patch_url()))
    
    # auto delete all purgeable messages
    @tasks.loop(hours=1)
    async def auto_delete_purgeable_messages(self):
        purgeable_message_list = utility.get_purgeable_messages_list(self.message_cache)
        for purgeable_message_id in purgeable_message_list:
            utility.clear_message_cache(purgeable_message_id, self.message_cache)
            purgeable_message = self.bot.fetch_message(purgeable_message_id)
            await purgeable_message.delete()

    # auto delete all tmp_channels
    @tasks.loop(hours=1)
    async def auto_delete_tmp_channels(self):
        deleted_channels = []
        for temp_channel_id in gstate.tmp_channel_ids:
            if timers.is_timer_done(gstate.tmp_channel_ids[temp_channel_id]["timer"]):
                temp_channel = self.bot.get_channel(temp_channel_id)
                await temp_channel.delete(reason = "Delete temporary channel because time is over")
                deleted_channels.append(temp_channel_id)
        
        for channel in deleted_channels:
            del gstate.tmp_channel_ids[channel]