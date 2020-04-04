import logging

import discord
from discord.ext import commands

from core import (
    consts,
    checks
)

from riot import riot_commands

logger = logging.getLogger(consts.LOG_NAME)


class RiotCog(commands.Cog):
    @commands.command(name='player')
    @checks.is_riot_enabled()
    @checks.is_in_channels([consts.CHANNEL_COMMANDS, consts.CHANNEL_COMMANDS_MEMBER])
    async def player_(self, ctx, *summoner_name):
        if len(list(summoner_name)) == 0:
            arg = None
        else:
            arg = summoner_name[0]
        await ctx.send(riot_commands.get_player_stats(ctx.message.author.name, arg))

    @commands.command(name='smurf')
    @checks.is_riot_enabled()
    @checks.is_in_channels([consts.CHANNEL_COMMANDS, consts.CHANNEL_COMMANDS_MEMBER])
    async def smurf_(self, ctx, *summoner_name):
        if len(list(summoner_name)) == 0:
            arg = None
        else:
            arg = summoner_name[0]
        await ctx.send(riot_commands.get_smurf(ctx.message.author.name, arg))

    @commands.command(name='bans')
    @checks.is_riot_enabled()
    @checks.is_in_channels([consts.CHANNEL_COMMANDS, consts.CHANNEL_COMMANDS_MEMBER])
    async def bans_(self, ctx, *team_names):
        await ctx.send(
            riot_commands.calculate_bans_for_team(team_names), file=discord.File(
                f'./{consts.FOLDER_CHAMP_SPLICED}/image.jpg'))

    @commands.command(name='clash2')
    @checks.is_riot_enabled()
    @checks.is_in_channels([consts.CHANNEL_COMMANDS, consts.CHANNEL_COMMANDS_MEMBER])
    async def clash2_(self, ctx, summoner_name):
        message, name_list = riot_commands.get_clash_team_opgg_by_summoner_name(summoner_name)
        await ctx.send(message)
        await ctx.send(riot_commands.calculate_bans_for_team(
            name_list[0],name_list[1],name_list[2],name_list[3],name_list[4]), file=discord.File(
            f'./{consts.FOLDER_CHAMP_SPLICED}/image.jpg'))
