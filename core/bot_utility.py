import random
import time
import re
import json

from core import consts, timers
from core.state import global_state as gstate


def read_config_file(filename):
    return json.load(open(f'./config/{filename}.json', 'r'))


def create_team(players):
    num_players = len(players)
    team1 = random.sample(players, int(num_players / 2))
    team2 = players

    for player in team1:
        team2.remove(player)

    teams_message = consts.MESSAGE_TEAM_HEADER
    teams_message += consts.MESSAGE_TEAM_1
    for player in team1:
        teams_message += player + "\n"

    teams_message += consts.MESSAGE_TEAM_2
    for player in team2:
        teams_message += player + "\n"

    return teams_message


def is_purgeable_message(message, cmds, channel, excepted_users):
    """
    Checks if message should be purged based on if it starts with
    a specified command cmd and is send in a specfied channel name
    channel and is from a user excepted user that should not be purged.
    """
    if contains_command(message, tuple(cmds)) and is_in_channel(message, channel):
        if message.author.name in excepted_users:
            return False
        return True
    return False


def create_internal_play_request_message(message, play_request):
    """
    Creates an internal play_request message.
    """
    play_request_time = re.findall('\d\d:\d\d', message.content)
    intern_message = consts.MESSAGE_CREATE_INTERN_PLAY_REQUEST.format(
        play_request.message_author.name, 10 - len(play_requests[message.id]), play_request_time)
    for player_tuple in play_requests[message.id]:
        intern_message += player_tuple[0].name + '\n'
    return intern_message


# TODO: implement this
def switch_to_internal_play_request(message, play_request):
    return create_internal_play_request_message(message, play_request)




def has_any_pattern(message):
    for pattern in consts.PATTERN_LIST_AUTO_REACT:
        if message.content.find(pattern) > -1:
            return True
    return False


def has_pattern(message, pattern):
    if message.content.find(pattern) > -1:
        return True
    return False


def generator_get_auto_role_list(member):
    if len(member.roles) >= 2:
        return

    for role in member.guild.roles:
        if role.id == consts.ROLE_EVERYONE_ID or role.id == consts.ROLE_SETZLING_ID:
            yield role


def get_auto_role_list(member):
    return list(generator_get_auto_role_list(member))


def contains_command(message, command):
    if message.content.startswith(command):
        return True
    return False


def contains_any_command(message, commands):
    for command in commands:
        if message.content.startswith(command):
            return True
    return False


def is_in_channels(message, channels):
    for channel in channels:
        if message.channel.name == channel:
            return True
    return False


def is_in_channel(message, channel):
    return message.channel.name == channel


def get_voice_channel(message, name):
    voice_channel = None
    for voice_channel_iterator in message.guild.voice_channels:
        if voice_channel_iterator.name == name:
            voice_channel = voice_channel_iterator
    return voice_channel if voice_channel is not None else None


def generator_get_players_in_channel(channel):
    for member in channel.members:
        yield member.name


def get_players_in_channel(channel):
    return list(generator_get_players_in_channel(channel))


def get_play_request_creator(message):
    return ''


def add_subscriber_to_play_request(user, play_request):
    is_player = False
    for player in play_request.generate_all_players():
        if user == player:
            is_player = True

    if not is_player:
        play_request.add_subscriber(user)


def is_auto_dm_subscriber(message, client, user, play_requests):
    if user.name in (client.user.name, "Secret Kraut9 Leader") or \
     not is_in_channels(
         message, [consts.CHANNEL_INTERN_PLANING, consts.CHANNEL_PLAY_REQUESTS, consts.CHANNEL_BOT]):
        return False

    message_id = message.id
    if message_id not in play_requests:
        return False

    play_request_author = play_requests[message_id].author
    if user == play_request_author:
        return False
    return True


def update_message_cache(message, message_cache,  time=18):
    message_cache.append((message, timers.start_timer(hrs=18)))


def get_purgeable_messages_list(message, message_cache):
    if not gstate.CONFIG["TOGGLE_AUTO_DELETE"]:
        return
    return [msg[0] for msg in message_cache if timers.is_timer_done(msg[1])]


def is_no_play_request_command(message, bot):
    if not contains_any_command(message, consts.COMMAND_LIST_PLAY_REQUEST) \
    and message.author != bot.user:
        return True
    return False


def clear_message_cache(message, message_cache):
    for message_tuple in message_cache:
        if message in message_tuple:
            message_cache.remove(message_tuple)


def clear_play_requests(message, play_requests):
    if has_any_pattern(message):
        del play_requests[message.id]