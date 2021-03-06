import asyncio
from importlib import reload
import logging


from discord.ext import commands

from core import (
    consts,
    checks
)

from core.state import global_state as gstate

logger = logging.getLogger('cog_debug')


class DebugCog(commands.Cog, command_attrs=dict(hidden=True)):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='version')
    @checks.is_in_channels([])
    @commands.has_role(consts.ROLE_ADMIN_ID)
    async def version_(self, ctx):
        logger.debug('!version called')
        await ctx.send(gstate.VERSION)
    
    @commands.command(name='reload-ext')
    @checks.is_in_channels([])
    @commands.has_role(consts.ROLE_ADMIN_ID)
    async def reload_ext_(self, ctx, ext):
        logger.info('!reload-ext called')
        try:
            self.bot.reload_extension(ext)
            log_str = "Extension " + ext + " is reloaded"
            logger.info(log_str)
        except commands.ExtensionNotLoaded:
            log_str = "Extension " + ext + " was not loaded!"
            logger.error(log_str)
        except commands.ExtensionNotFound:
            log_str = "Extension " + ext + " was not found!"
            logger.error(log_str)
        except Exception as error:
            log_str = "Unknown error reloading extension " + ext
            logger.error(log_str)
            await ctx.send(log_str)
            raise error

        await ctx.send(log_str)

    @commands.command(name='status')
    @checks.is_in_channels([])
    @commands.has_role(consts.ROLE_ADMIN_ID)
    async def status_(self, ctx):
        logger.debug('!status called')
        await ctx.send("Bot is alive.")

    @commands.command(name='reload-config')
    @checks.is_in_channels([])
    @commands.has_role(consts.ROLE_ADMIN_ID)
    async def reload_config(self, ctx):
        global consts
        logger.info('Try to reload the configuration.')
        await ctx.send("Reload configuration.json:")
        gstate.read_config()
        consts = reload(consts)
        gstate.get_version()
        await ctx.send("Done.")
        logger.info('configuration reloaded.')

    @commands.command(name='enable-debug')
    @checks.is_in_channels([])
    @checks.is_debug_config_enabled()
    @commands.has_role(consts.ROLE_ADMIN_ID)
    async def enable_debug(self, ctx):
        gstate.debug = True
        str_debug_activated="Debugging is activated for one hour."
        await ctx.send(str_debug_activated)
        logger.info(str_debug_activated)
        await asyncio.sleep(3600)
        gstate.debug = False
        gstate.CONFIG["TOGGLE_DEBUG"] = False
        gstate.write_and_reload_config(gstate.CONFIG)
        str_debug_deactivated="Debugging is deactivated."
        await ctx.send(str_debug_deactivated)
        logger.info(str_debug_deactivated)

    @commands.command(name='print')
    @checks.is_in_channels([])
    @checks.is_debug_enabled()
    @commands.has_role(consts.ROLE_ADMIN_ID)
    async def print_(self, ctx, arg):
        logger.debug('!print %s called', arg)
        # return_string = ast.literal_eval(arg)
        # less safe but more powerful
        return_string = eval(arg)
        await ctx.send(return_string)
        print(return_string)

    @commands.command(name='end')
    @checks.is_in_channels([])
    @commands.has_role(consts.ROLE_ADMIN_ID)
    @commands.is_owner()
    async def end_(self, ctx, *arg):
        if len(list(arg)) == 0:
            await ctx.send('Use "restart" or "abort".')
            return
        exit_status = 2
        if str(arg[0]) == "restart":
            exit_status=0
            await ctx.send('Bot will be restarted if systemd is configured to restart on success.')
        elif str(arg[0]) == "abort":
            exit_status=3
            await ctx.send('Bot will be aborted.')
        else:
            await ctx.send('Use "restart" or "abort".')
            return

        
        logger.info("Try to abort bot with exit status %s", exit_status)
        await self.bot.logout(exit_status)


def setup(bot: commands.Bot):
    bot.add_cog(DebugCog(bot))
    logger.info('Debug cogs loaded')