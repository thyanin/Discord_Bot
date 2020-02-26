import sys, os
sys.path.append(os.path.join(sys.path[0],'modules'))
import discord
import json
import time
from importlib import reload
from modules import consts, riot, timers, bot_utility as utility, reminder, ocr
import asyncio

# === init functions === #
def setVersion():
    global consts
    version_file = open("./.git/refs/heads/master", "r")
    consts.VERSION = version_file.read()[:7]

def read_json(filename):
    return json.load(open(f'./config/{filename}.json', 'r'))

# === init === #
client = discord.Client()
bot =  read_json('bot')
config = read_json('configuration')
play_requests = {}
tmp_message_author = None
setVersion()
message_cache = []
debug_bool = False

# === classes === #
class player_in_play_request:
    discord_user = discord.user
    players_known = {}

    def __init__(self, user):
        self.discord_user = user

# === events === #
@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))

@client.event
async def on_member_join(member):
    # auto role
    await member.edit(roles=utility.get_auto_role_list(member))
        
@client.event
async def on_message(message):
    global config
    global consts
    global play_requests
    global tmp_message_author
    global message_cache
    global debug_bool


    if type(message.channel) is discord.DMChannel:
        return

    # auto react - reacts to all patterns in consts.PATTERN_LIST_AUTO_REACT
    # and creates a new play_request
    # only reacts with EMOJI_ID_LIST[5] == :fill:
    if config["TOGGLE_AUTO_REACT"] and utility.has_any_pattern(message):
        await message.add_reaction(client.get_emoji(consts.EMOJI_ID_LIST[5]))
        await message.add_reaction(consts.EMOJI_PASS)

        play_requests[message.id] = [[tmp_message_author, time.time()]]
        if config["TOGGLE_AUTO_DELETE"]:
            
            message_cache = utility.update_message_cache(message, message_cache)
            message_cache, deleteable_messages = utility.get_purgeable_messages(message_cache)
            for message in deleteable_messages:
                await message.delete()
        #WIP
        if utility.has_pattern(message, consts.PATTERN_PLAY_REQUEST):
            reminder.set_reminder(message)

    # make all messages in play_requests channel auto_deleteable
    elif config["TOGGLE_AUTO_DELETE"] and utility.is_in_channel(message, consts.CHANNEL_PLAY_REQUESTS):
        message_cache = utility.update_message_cache(message, message_cache)

        if not utility.contains_any_command(message, consts.COMMAND_LIST_PLAY_REQUEST) and message.author != client.user:
            await message.delete()

    # create team command
    if utility.contains_command(message, consts.COMMAND_CREATE_TEAM) and utility.is_in_channels(message, [consts.CHANNEL_INTERN_PLANING, consts.CHANNEL_BOT]):
        voice_channel = utility.get_voice_channel(message, consts.CHANNEL_CREATE_TEAM_VOICE)
        players_list = utility.get_players_in_channel(voice_channel)
        await message.channel.send(utility.create_team(players_list))

    #play-now command
    if utility.contains_command(message, consts.COMMAND_PLAY_NOW) and utility.is_in_channels(message, [consts.CHANNEL_PLAY_REQUESTS, consts.CHANNEL_BOT]):
        tmp_message_author = message.author
        await message.channel.send((consts.MESSAGE_PLAY_NOW).format(message.author.mention))
       
    #play-lol command
    if utility.contains_command(message, consts.COMMAND_PLAY_LOL) and utility.is_in_channels(message, [consts.CHANNEL_PLAY_REQUESTS, consts.CHANNEL_BOT]):
        if len(message.content.split(' ')) == 2:
            tmp_message_author = message.author
            await message.channel.send((consts.MESSAGE_PLAY_LOL).format(message.author.mention, message.content.split(' ')[1]))
        else:
            await message.channel.send(f'Wrong format: {message.cotent}')


    # clash ocr command test
    if utility.contains_command(message, '!ocr') and len(message.attachments) == 1 and utility.is_in_channels(message, [consts.CHANNEL_BOT, consts.CHANNEL_MEMBER_ONLY]):
        attached_image = message.attachments[0]
        attached_image_file_name = attached_image.filename
        await attached_image.save(attached_image_file_name)
        ocr.set_image_file_name(attached_image_file_name)
        await message.channel.send(ocr.run_ocr())
        ocr.clean_up_image(attached_image_file_name)

    # riot commands
    if config["TOOGLE_RIOT_API"] == False:
        await message.channel.send('Sorry, der Befehl ist aktuell nicht verfügbar.')
    else:
        if message.content.startswith('?player'):
            await message.channel.send(riot.riot_command(message))
        elif message.content.startswith('?bans'):
            await message.channel.send(riot.riot_command(message), file=discord.File(f'./{consts.FOLDER_CHAMP_SPLICED}/image.jpg'))

    # debug commands
    if message.channel.name == "bot":
        if message.content.startswith("?testmsg"):
            await message.channel.send("test")
            await message.add_reaction(consts.EMOJI_PASS)
        elif message.content.startswith("?version"):
            await message.channel.send(consts.VERSION)
        elif message.content.startswith("?reload_config"):
            await message.channel.send("Reload configuration.json:")
            config = read_json('configuration')
            #consts = reload(modules.consts)
            await message.channel.send("Done.")
            if config["TOOGLE_DEBUG"]:
                debug_bool = True
                await message.channel.send("Debugging is activated for one hour.")
                await asyncio.sleep(3600)
                debug_bool = False
                await message.channel.send("Debugging is deactivated.")
            elif debug_bool:
                    debug_bool = False
                    await message.channel.send("Debugging is deactivated.")
        # killswitch
        elif message.content.startswith('!end'):
            await message.channel.send('Bot is shut down!')
            await client.logout()
        # exploit the pi through this - glhf!
        elif message.content.startswith('?print'):
            if debug_bool:
                return_string = eval(message.content.split(' ')[1])
                await message.channel.send(return_string)
                print(return_string)
            else:
                await message.channel.send("Debugging is not activated.")

     # deletes all messages that are not commands (consts.COMMAND_LIST_ALL)  except bot responses in all cmd channels (consts.CHANNEL_LIST_COMMANDS)
    # if config["TOGGLE_AUTO_DELETE"]:
    #     if utility.is_purgeable_message(message, consts.COMMAND_LIST_PLAY_REQUEST, consts.CHANNEL_PLAY_REQUESTS, [consts.BOT_DYNO_NAME]):
    #         await message.delete()
    #     elif utility.is_purgeable_message(message, consts.COMMAND_LIST_INTERN_PLANING, consts.CHANNEL_INTERN_PLANING, [consts.BOT_DYNO_NAME, client.user.name]):
    #         await message.delete()
    
    if config["TOGGLE_COMMAND_ONLY"]:
        if utility.contains_any_command(message, consts.COMMAND_LIST_PLAY_REQUEST):
            await message.delete()


@client.event
async def on_message_delete(message):
    global consts
    global play_requests
    # delete play_request if old play-request gets deleted
    if utility.has_any_pattern(message):
        del play_requests[message.id]
    for message_tuple in message_cache:
        if message in message_tuple:
            message_cache.remove(message_tuple)



@client.event
async def on_reaction_add(reaction, user):
    # auto dm
    global config
    global play_requests
    if not config["TOGGLE_AUTO_DM"]:
        return
  
    if not utility.is_auto_dm_subscriber(reaction.message, client, user, play_requests):
        return

    
    message_id = reaction.message.id
    play_request_author = play_requests[message_id][0][0]
    utility.add_subscriber_to_play_request(message_id, user, play_requests)
    # if reaction is 'EMOJI_PASS' delete player from play_request and return
    if str(reaction.emoji) == consts.EMOJI_PASS:
        for player in play_requests[message_id]:
            if user == player[0]:
                play_requests[message_id].remove(player)
        return
    
  
    #send auto dms to subscribers and author
    for player in play_requests[message_id]:
        if player[0] == play_request_author and player[0] != user:
            await play_request_author.send(consts.MESSAGE_AUTO_DM_CREATOR.format(user.name, str(reaction.emoji)))
        elif player[0] != user:
            await player[0].send(consts.MESSAGE_AUTO_DM_SUBSCRIBER.format(user.name, play_request_author.name, str(reaction.emoji)))
  
    #switch to internal play request if more than 6 players(author + 5 players_known) are subscribed
    if len(play_requests[message_id]) == 6:
        await reaction.channel.send(utility.switch_to_internal_play_request(play_requests))
    
# run
print("Start Client")
client.run(str(bot["token"]))
print("End")