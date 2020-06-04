
import re
import logging
import asyncio

import discord
from discord.ext import commands

from core import (
    checks,
    exceptions,
    timers,
    help_text,
    DiscordBot
)

from core.play_requests import PlayRequest, PlayRequestCategory

logger = logging.getLogger(__name__)



class PlayRequestsCog(commands.Cog, name='Play-Request Commands'):
    def __init__(self, bot: DiscordBot.KrautBot):
        self.bot = bot

    @commands.command(name='play', help = help_text.play_HelpText.text, brief = help_text.play_HelpText.brief, usage = help_text.play_HelpText.usage)
    @checks.is_in_channels("play_request")
    async def play_(self, ctx: commands.Context, game_name, _time, *args):
        guild_config = self.bot.config.get_guild_config(ctx.guild.id)
        
        is_not_now = True
        logger.info('Create a play request')
        game_name = game_name.upper()
        message = 'Something went wrong.'
        if game_name == 'CLASH':
            await self.create_clash(ctx, _time)
            return
        game = guild_config.get_game(game_name)
        if _time == 'now':
            arg = None if len(list(args)) == 0 else args[0]
            if arg != None:
                if int(arg[1:]) > guild_config.unsorted_config.play_now_time_add_limit or int(arg[1:]) <= 0:
                    raise exceptions.LimitReachedException()
                play_request_time = timers.add_to_current_time(int(arg[1:]))
                message = guild_config.messages.play_at.format(
                    role_mention=ctx.guild.get_role(game.role_id).mention,
                    player=ctx.message.author.mention,
                    game=game.name_long,
                    time=play_request_time
                )
            else:
                is_not_now = False
                message = guild_config.messages.play_now.format(
                    role_mention=ctx.guild.get_role(game.role_id).mention,
                    player=ctx.message.author.mention,
                    game=game.name_long
                )
        else:
            if len(re.findall('([0-2])?[0-9]:[0-5][0-9]', _time)) == 0:
                exception_str = exceptions.BadArgumentFormat()
                logger.error(exception_str)
                raise exception_str
            message = guild_config.messages.play_at.format(
                role_mention=ctx.guild.get_role(game.role_id).mention,
                player=ctx.message.author.mention,
                game=game.name_long,
                time=_time
            )
        
        play_request_message = await ctx.send(message)
        _category = self.get_category(game_name)
        play_request = PlayRequest(play_request_message.id, ctx.message.author.id, category=_category)
        await self.add_play_request_to_state(ctx.guild.id, play_request)
        await self.add_auto_reaction(ctx, play_request_message)

        await ctx.message.delete()

        if is_not_now:
            await self.auto_reminder(play_request_message)

    async def add_auto_reaction(self, ctx: commands.Context, play_request_message: discord.Message):
        guild_config = self.bot.config.get_guild_config(ctx.guild.id)

        await play_request_message.add_reaction(guild_config.unsorted_config.emoji_join)
        await play_request_message.add_reaction(guild_config.unsorted_config.emoji_pass)


    async def add_play_request_to_state(self, guild_id: int, play_request):
        logger.debug("Add the message id %s to the global state", play_request.message_id)
        self.bot.state.get_guild_state(guild_id).play_requests[play_request.message_id] = play_request
    
    def get_category(self, game_name):
        _category = None
        if game_name == 'LOL':
            _category = PlayRequestCategory.LOL
        elif game_name == 'APEX':
            _category = PlayRequestCategory.APEX
        elif game_name == 'CSGO':
            _category = PlayRequestCategory.CSGO
        elif game_name == 'RL':
            _category = PlayRequestCategory.RL
        elif game_name == 'VAL':
            _category = PlayRequestCategory.VAL
        elif game_name == 'CLASH':
            _category = PlayRequestCategory.CLASH
        return _category


    async def auto_reminder(self, message):
        guild_config = self.bot.config.get_guild_config(message.guild.id)
        logger.debug("Create an auto reminder for play request with id %s", message.id)
        time_difference = timers.get_time_difference(message.content)
        if time_difference > 0:
            await asyncio.sleep(time_difference)
            for player_id in self.bot.state.get_guild_state(message.guild.id).play_requests[message.id].generate_all_players():
                player = self.bot.get_user(player_id)
                await player.send(guild_config.messages.play_request_reminder)

    async def create_clash(self, ctx, date):
        guild_config = self.bot.config.get_guild_config(ctx.guild.id)
        logger.debug('Create a clash request')
        # TODO I don't like this. With this you can only have one clash request
        self.bot.state.get_guild_state(ctx.guild.id).clash_date = date
        play_request_message = await ctx.send(guild_config.messages.clash_create.format(
            role_mention=ctx.guild.get_role(guild_config.get_game("clash").role_id).mention,
            player=ctx.message.author.mention,
            date=date
            )
        )
        _category = self.get_category("CLASH")
        play_request = PlayRequest(play_request_message.id, ctx.message.author.id, category=_category)
        await self.add_play_request_to_state(ctx.guild.id, play_request)
        await self.add_auto_reaction(ctx, play_request_message)
        

        

def setup(bot: DiscordBot.KrautBot):
    bot.add_cog(PlayRequestsCog(bot))
    logger.info('Play request cogs loaded')
