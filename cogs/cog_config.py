import logging

import json

import discord
from discord.ext import commands

from core import (
    checks,
    DiscordBot,
    converters
)

logger = logging.getLogger(__name__)

class ConfigCog(commands.Cog, name='Configuration commands'):
    """ A cog used to configure the bot
    """
    def __init__(self, bot: DiscordBot.KrautBot):
        self.bot = bot
    
    @commands.group(name='config')
    @checks.is_in_channels()
    @checks.has_any_role("admin_id")
    async def config(self, ctx: commands.Context):
        """ Commands to set the config of the bot """
        if ctx.invoked_subcommand is None:
            await ctx.send_help(self.config)
    
    
    @config.command(name='print')
    async def config_print(self, ctx: commands.Context):
        """ Prints the bot config for this server """

        guild_id = ctx.guild.id

        logger.debug("Print the guild config for %i", guild_id)

        file_name = "{dir}/config_{guild_id}.json".format(dir=self.bot.config.general_config.directory_temp_files, guild_id=guild_id)
        with open(file_name, "w") as json_file:
            json.dump(self.bot.config.get_guild_config(guild_id).asdict(), json_file, indent="\t")
        
        await ctx.send(file=discord.File(file_name))
    
    @config.command(name='read')
    # @config.after_invoke(after_config)
    async def config_read(self, ctx: commands.Context):
        """ Set the bot config for this server using an attached json file
        """

        if len(ctx.message.attachments) != 1:
            logger.error("Guild %i: config read called without a file!")
            await ctx.send(f"Please attach a json config file to the command. You can get the current file by calling ``{self.bot.get_command_prefix(ctx.guild.id)}config print``.")
            raise commands.CommandError("Config read called without a file")

        logger.info("Read guild config from file for guild %i", ctx.guild.id)
        json_as_bytes = await ctx.message.attachments[0].read()
        guild_config = self.bot.config.get_guild_config(ctx.guild.id)
        try:
            guild_config.fromdict(json.loads(json_as_bytes), update=False)
            await self.bot.check_channels_id_in_config(ctx.guild.id)
            await ctx.send("Config was set by the given file")
        except json.JSONDecodeError:
            logger.error("Wasn't able to read the json file.")
            await ctx.send("JSON file is invalid")

    @config.command(name='set')
    # @config.after_invoke(after_config)
    async def config_set(self, ctx: commands.Context, category: str, *, configs: converters.ArgsToDict):
        """ Set the bot config for this server

        Keyword arguments:
        category -- The category
        configs -- A string with the format "setting: value". Value can be a list. Then the values have to be surrounded by parentheses and seperated by commatas"
        """

        guild_config = self.bot.config.get_guild_config(ctx.guild.id)
        guild_config.fromdict({category: configs}, update=True)

        await self.bot.check_channels_id_in_config(ctx.guild.id)

        await ctx.send("Config updated")
        logger.info("Update the guild config category %s to %s for guild %i", category, configs, ctx.guild.id)
    

    @commands.check(checks.is_super_user)
    @config.command(name='reload')
    async def config_reload(self, ctx):
        """ Reloads the bot config from the config file.

        Only avaible for super users
        """
        logger.info('Try to reload the configuration.')
        await ctx.send("Reload configuration.json:")
        self.bot.config.update_config_from_file()
        self.bot.state.get_version()
        await ctx.send("Done.")
        logger.info('configuration reloaded.')
    
    @commands.check(checks.is_super_user)
    @config.command(name='write')
    @checks.is_in_channels()
    @checks.has_any_role("admin_id")
    async def config_write(self, ctx):
        """ Writes the bot config to the config file.

        Only avaible for super users
        """
        logger.info('Try to write the configuration.')
        self.bot.config.write_config_to_file()
        await ctx.send("Done.")

def setup(bot: DiscordBot.KrautBot):
    bot.add_cog(ConfigCog(bot))
    logger.info('Config cog loaded')
