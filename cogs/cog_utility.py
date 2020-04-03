import logging

import discord
from discord.ext import commands

from core import (
    consts,
    bot_utility as utility,
    checks,
    exceptions,
    timers
)

from riot import riot_commands

from core.state import global_state as gstate

logger = logging.getLogger(consts.LOG_NAME)


class UtilityCog(commands.Cog):
    @commands.command(name='create-team')
    @checks.is_in_channels([consts.CHANNEL_INTERN_PLANING, consts.CHANNEL_COMMANDS])
    async def create_team(self, ctx: commands.Context, *player_names):
        voice_channel = discord.utils.find(lambda x: len(x.members) >= 6, ctx.message.guild.voice_channels)
        voice_channel = voice_channel if voice_channel is not None else utility.get_voice_channel(ctx.message, consts.CHANNEL_CREATE_TEAM_VOICE_ID)
        players_list = utility.get_players_in_channel(voice_channel)
        if len(list(player_names)) != 0:
            for player_name in player_names:
                if player_name == 'mv':
                    continue
                players_list.append(player_name)
        message, team1, team2 = utility.create_team(players_list)
        await ctx.send(message)

        role = discord.utils.find(lambda x: x.name == 'Wurzel', ctx.message.guild.roles)
        if len(list(player_names)) == 0:
            return

        if player_names[0] == 'mv' and role in ctx.message.author.roles:
            channel_team1 = discord.utils.find(lambda x: x.name == 'Team 1', ctx.message.guild.voice_channels)
            channel_team2 = discord.utils.find(lambda x: x.name == 'Team 2', ctx.message.guild.voice_channels)
            for member in voice_channel.members:
                if member.name in team1:
                    await member.move_to(channel_team1)
                elif member.name in team2:
                    await member.move_to(channel_team2)

    @commands.command(name='link')
    @checks.is_riot_enabled()
    @checks.is_in_channels([consts.CHANNEL_COMMANDS, consts.CHANNEL_COMMANDS_MEMBER])
    async def link_(self, ctx, summoner_name):
        try:
            riot_commands.link_account(ctx.message.author.name, summoner_name)
        except commands.CommandInvokeError:
            pass
        else:
            await ctx.message.author.send(
                f'Dein Lol-Account wurde erfolgreich mit deinem Discord Account verbunden!\nFalls du deinen Account wieder entfernen möchtest benutze das {ctx.bot.command_prefix}unlink Command.')

    @commands.command(name='unlink')
    @checks.is_in_channels([consts.CHANNEL_COMMANDS, consts.CHANNEL_COMMANDS_MEMBER])
    async def unlink_(self, ctx, *summoner_names):
        try:
            if len(list(summoner_names)) != 0:
                raise commands.CommandInvokeError
            riot_commands.unlink_account(ctx.message.author.name)
        except commands.CommandInvokeError:
            pass
        else:
            await ctx.message.author.send(
                'Dein Lol-Account wurde erfolgreich von deinem Discord Account getrennt!')

    @commands.command(name='purge')
    @commands.has_role(consts.ROLE_ADMIN_ID)
    async def purge_(self, ctx, count: int):
        last_count_messages = await ctx.message.channel.history(limit=count + 1).flatten()
        [await message_.delete() for message_ in last_count_messages if not message_.pinned]

    @commands.command(name='leaderboard')
    @commands.has_role(consts.ROLE_ADMIN_ID)
    async def test_embed(self, ctx):
        await ctx.send(embed=riot_commands.create_embed(ctx))

    @commands.command(name='test-plt')
    @commands.has_role(consts.ROLE_ADMIN_ID)
    async def test_plt(self, ctx):
        riot_commands.test_matplotlib()
        await ctx.send(file=discord.File(f'./{consts.FOLDER_CHAMP_SPLICED}/leaderboard.png'))

    # dont use this
    @commands.command(name='game-selector')
    @commands.has_role(consts.ROLE_ADMIN_ID)
    async def game_selector(self, ctx):
        message = await ctx.send(consts.MESSAGE_GAME_SELECTOR)
        for emoji in ctx.bot.emojis:
            if emoji.name == 'rl' or emoji.name == 'lol' or emoji.name == 'csgo' or emoji.name == 'apex' or emoji.name == 'val':
                await message.add_reaction(emoji)
        gstate.game_selector_id = message.id

    @commands.command(name='create-channel')
    @checks.is_in_channels([consts.CHANNEL_COMMANDS_MEMBER])
    async def create_channel(self, ctx, channel_name):
        for tmp_channels in gstate.tmp_text_channels:
            if tmp_channels[2] == ctx.message.author:
                raise exceptions.LimitReachedException('Der Autor hat schon einen temprorären Channel erstellt.')
        tmp_channel_category = discord.utils.find(lambda x: x.name == consts.CHANNEL_CATEGORY_TEMPORARY, ctx.message.guild.channels)
        tmp_channel = await ctx.message.guild.create_text_channel(channel_name, category=tmp_channel_category)
        gstate.tmp_text_channels.append((tmp_channel, timers.start_timer(hrs=12), ctx.message.author))

    @create_team.error
    async def error_handler(self, ctx, error):
        logger.exception('Error handler got called.')
        if isinstance(error, commands.CheckFailure):
            if str(ctx.command) == 'enable-debug':
                await ctx.send(
                    'Der Debug Toggle in der Konfiguration ist nicht eingeschaltet.')
            elif str(ctx.command) == 'purge':
                await ctx.send(
                    'Du hast nicht die benötigten Rechte um dieses Command auszuführen.')
            elif str(ctx.command) == 'print':
                await ctx.send(
                    f'Der Debug Modus ist zur Zeit nicht aktiviert. Versuche es mit {ctx.bot.command_prefix}enable-debug zu aktivieren.')
            else:
                await ctx.send(
                    'Das hat nicht funktioniert. (Überprüfe, ob du im richtigen Channel bist.)')
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(
                'Es fehlt ein Parameter. (z.B. der Zeitparameter bei ?play-lol)')
        else: 
            await ctx.send(error)
