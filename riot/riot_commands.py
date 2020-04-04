"""Module that interacts with the Riot API
and transforms the received data in
a user readable way.
"""
import shelve
import numpy as np
import matplotlib.pyplot as plt
import logging

from discord.ext import commands
import discord

import pandas as pd
from core import (
    timers,
    consts,
    exceptions
)

from . import (
    image_transformation,
    riot_utility as utility
)


logger = logging.getLogger(consts.LOG_NAME)
SEASON_2020_START_EPOCH = timers.convert_human_to_epoch_time(consts.RIOT_SEASON_2020_START)

_timers = []

# FIXME: this is trash
# === BAN CALCULATION === #


def get_best_ban(summoner):
    ban_list = []
    most_played_champs = list(summoner.get_most_played_champs(10))
    for champ in most_played_champs:
        if summoner.has_played_champ_by_name_in_last_n_days(champ, 30):
            ban_list.append(champ)
        if len(ban_list) == 5:
            return ban_list
    return ban_list


def get_best_bans_for_team(team) -> list:
    ban_list = []
    ranks = []
    best_bans_for_player = []
    for player in team:
        ranks.append(player.rank_value)
        best_bans_for_player.append(get_best_ban(player))
    average_rank = utility.get_average_rank(ranks)
    for i in range(0, len(team)):
        if ranks[i] <= average_rank - 500:
            continue
        elif ranks[i] > average_rank - 500 and ranks[i] <= average_rank + 800:
            ban_list.append(best_bans_for_player[i][0])
        elif team[i].is_smurf() or ranks[i] > average_rank + 800:
            ban_list.append(best_bans_for_player[i][0])
            ban_list.append(best_bans_for_player[i][1])
            ban_list.append(best_bans_for_player[i][2])
        while len(ban_list) > 5:
            del ban_list[-1]
    return ban_list


# === INTERFACE === #


def get_player_stats(discord_user_name, summoner_name) -> str:
    summoner = get_or_create_summoner(discord_user_name, summoner_name)
    return f'Rank: {summoner.get_soloq_tier()}-{summoner.get_soloq_rank()} {summoner.get_soloq_lp()}LP, Winrate {summoner.get_soloq_winrate()}%.'


def get_smurf(discord_user_name, summoner_name) -> str:
    summoner = get_or_create_summoner(discord_user_name, summoner_name)
    is_smurf_word = 'kein'
    if summoner.is_smurf():
        is_smurf_word = 'ein'
    return f'Der Spieler **{utility.format_summoner_name(summoner.name)}** ist sehr wahrscheinlich **{is_smurf_word}** Smurf.'


def calculate_bans_for_team(*names) -> str:
    utility.update_champion_json()
    if len(names[0]) != 5:
        logger.exception('Check Failure')
        raise commands.CheckFailure()
    team = list(utility.create_summoners(list(names[0])))
    output = get_best_bans_for_team(team)
    image_transformation.create_new_image(output)
    op_url = f'https://euw.op.gg/multi/query={team[0].name}%2C{team[1].name}%2C{team[2].name}%2C{team[3].name}%2C{team[4].name}'
    return f'Team OP.GG: {op_url}\nBest Bans for Team:\n{utility.pretty_print_list(output)}'


def link_account(discord_user_name, summoner_name):
    if utility.is_command_on_cooldown(_timers):
        logger.exception('DataBaseException')
        raise exceptions.DataBaseException('Command on cooldown')
    summoner = utility.create_summoner(summoner_name)
    summoner.discord_user_name = discord_user_name
    with shelve.open(f'{consts.DATABASE_DIRECTORY}/{consts.DATABASE_NAME}', 'rc') as database:
        for key in database.keys():
            if key == str(discord_user_name):
                logger.exception('DataBaseException')
                raise exceptions.DataBaseException('Your discord account already has a lol account linked to it')
            if database[key] is not None:
                if database[key].name == summoner.name:
                    logger.exception('DataBaseException')
                    raise exceptions.DataBaseException('This lol account already has a discord account that is linked to it')
        database[str(discord_user_name)] = summoner


def update_linked_account_data(discord_user_name):
    summoner = utility.read_account(discord_user_name)
    summoner = utility.create_summoner(summoner.name)
    link_account(discord_user_name, summoner.name)


def get_or_create_summoner(discord_user_name, summoner_name):
    if summoner_name is None:
        summoner = utility.create_summoner(utility.read_account(discord_user_name).name)
        if utility.is_in_need_of_update(summoner):
            update_linked_account_data(discord_user_name)
        return summoner
    return utility.create_summoner(summoner_name)


def unlink_account(discord_user_name):
    with shelve.open(f'{consts.DATABASE_DIRECTORY}/{consts.DATABASE_NAME}', 'rc') as database:
        for key in database.keys():
            if key == str(discord_user_name):
                del database[key]

# FIXME im still not happy with this
def create_embed(ctx):
    summoners = list(utility.read_all_accounts())
    [summoner.get_rank_value() for summoner in summoners]
    summoners.sort(key=lambda x: x.rank_value, reverse=True)
    op_url = 'https://euw.op.gg/multi/query='
    for summoner in summoners:
        op_url = op_url + f'{summoner.name}%2C'
    _embed = discord.Embed(
        title='Kraut9 Leaderboard',
        colour=discord.Color.from_rgb(62, 221, 22),
        url=op_url[:-3])

    rank_strings = []
    white_space_pattern = '\u200b \u200b'
    for summoner in summoners:
        rank_string = summoner.get_soloq_rank_string()
        length = len(rank_string)
        rank_string = rank_string + f' %!{summoner.get_soloq_winrate()}%'
        rank_string = rank_string.replace('%!', f'{white_space_pattern * (25 - length)}')
        rank_strings.append(rank_string)

    _embed.add_field(name='User', value='\n'.join([summoner.discord_user_name for summoner in summoners]))
    _embed.add_field(name='Summoner', value='\n'.join([summoner.name for summoner in summoners]))
    _embed.add_field(name='Rank \t\t\t\t\t\t\t\t Winrate', value='\n'.join(rank_strings))
    return _embed


def test_matplotlib():
    summoners = list(utility.read_all_accounts())
    [summoner.get_rank_value() for summoner in summoners]
    summoners.sort(key=lambda x: x.rank_value, reverse=True)

    rank_strings = []
    for summoner in summoners:
        rank_string = f'{summoner.get_soloq_tier()}-{summoner.get_soloq_rank()} {summoner.get_soloq_lp()}LP'
        rank_strings.append(rank_string)
    winrates = [f'{summoner.get_soloq_winrate()}%' for summoner in summoners]
    discord_users = [summoner.discord_user_name for summoner in summoners]
    summoner_names = [summoner.name for summoner in summoners]
    
    data = [[summoner.name, summoner.discord_user_name, f'{summoner.get_soloq_tier()}-{summoner.get_soloq_rank()} {summoner.get_soloq_lp()}LP', f'{summoner.get_soloq_winrate()}%'] for summoner in summoners]
    fig, ax = plt.subplots()

    # hide axes
    fig.patch.set_visible(False)
    ax.axis('off')
    ax.axis('tight')

    df = pd.DataFrame(data, columns=['Discord User', 'Summoner', 'Rank', 'Winrate'])

    ax.table(cellText=df.values, colLabels=df.columns, loc='center')

    fig.tight_layout()

    plt.savefig(f'./{consts.FOLDER_CHAMP_SPLICED}/leaderboard.png')

"""
Get clash team op.gg and bans by just entering one name
Process:
1. Get summoner by Summoner Name
2. Get Clash team_id by Summoner Id
3. Get Clash players by teamID
4. Get Summoner Names by Players SummonerId
5. Create op.gg Link for summoner names

=> 7 API calls per team => ok

"""

def load_json(file_name, folder='config'):
    with open(f'./{folder}/{file_name}.json', encoding="utf8") as all_data:
        return json.load(all_data)

def get_riot_watcher():
    tokens = load_json("bot")
    return RiotWatcher(str(tokens["riot_token"]))


def get_clash_by_summoner_id(summoner_id):
    return get_riot_watcher().clash.by_summoner_id(consts.RIOT_REGION, summoner_id)


def get_clash_by_team_id(team_id):
    return get_riot_watcher().clash.by_team_id(consts.RIOT_REGION, team_id)


def get_summoner_ids_by_player_list(player_list):
    summoner_id_list = []
    for player in player_list:
        summoner_id_list.append(player.summonerId)
    return summoner_id_list


def get_summoner_name_by_summoner_id(summoner_id):
    summoner_data = get_riot_watcher().summoner.by_id(consts.RIOT_REGION, summoner_id)
    return summoner_data['name']


def get_clash_team_opgg_by_summoner_name(summoner_name):
    summoner = utility.create_summoner(summoner_name, summoner_data_only=True)
    team_id = get_clash_by_summoner_id(summoner.data_summoner['id'])['teamId']
    player_list = get_clash_by_team_id(team_id)['players']
    summoner_id_list = get_summoner_ids_by_player_list(player_list)
    op_url = 'https://euw.op.gg/multi/query='
    return_text = ''
    name_list = []
    for i in range(0, len(summoner_id_list)):
        name = get_summoner_name_by_summoner_id(summoner_id_list[i])
        name_list.append(name)
        op_url += f'{name}%2C' 
        return_text += f'Summoner: {name}, Position: {player_list[i].position}\n'
    return_text += f'\n{op_url[:-3]}'
    return return_text, name_list



# === INTERFACE END === #
