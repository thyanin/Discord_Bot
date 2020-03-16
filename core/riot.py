"""Module that interacts with the Riot API
and transforms the received data in
a user readable way.
"""
import shelve

from discord.ext import commands

from . import (
    image_transformation,
    timers,
    consts,
    exceptions,
    riot_utility as utility
)

SEASON_2020_START_EPOCH = timers.convert_human_to_epoch_time(consts.RIOT_SEASON_2020_START)


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
        _, rank = player.get_soloq_data()
        ranks.append(player.get_soloq_rank_weight(rank))
        best_bans_for_player.append(get_best_ban(player))
    median_rank = utility.get_median_rank(ranks)
    for i in range(0, len(team)):
        if ranks[i] <= median_rank:
            ban_list.append(get_best_bans_for_team[0])
        elif ranks[i] >= median_rank + 3:
            ban_list.append(get_best_bans_for_team[0])
            ban_list.append(get_best_bans_for_team[1])
            ban_list.append(get_best_bans_for_team[2])
        elif ranks[i] > median_rank:
            ban_list.append(get_best_bans_for_team[0])
            ban_list.append(get_best_bans_for_team[1])
    return ban_list


# === INTERFACE === #


def get_player_stats(ctx, summoner_name=None) -> str:
    summoner = utility.get_or_create_summoner(ctx, summoner_name)
    return f'Rank: {summoner.get_soloq_tier()}-{summoner.get_soloq_rank()} {summoner.get_soloq_lp()}LP, Winrate {summoner.get_soloq_winrate()}%.'


def get_smurf(ctx, summoner_name=None) -> str:
    summoner = utility.get_or_create_summoner(summoner_name)
    is_smurf_word = 'kein'
    if summoner.is_smurf():
        is_smurf_word = 'ein'
    return f'Der Spieler **{utility.format_summoner_name(summoner.name)}** ist sehr wahrscheinlich **{is_smurf_word}** Smurf.'


def calculate_bans_for_team(*names) -> str:
    utility.update_champion_json()
    if len(names) != 5:
        raise commands.CheckFailure()
    team = utility.create_summoners(list(names))
    output = get_best_bans_for_team(team)
    image_transformation.create_new_image(output)
    op_url = f'https://euw.op.gg/multi/query={team[0].name}%2C{team[1].name}%2C{team[2].name}%2C{team[3].name}%2C{team[4].name}'
    return f'Team OP.GG: {op_url}\nBest Bans for Team:\n{utility.pretty_print_list(output)}'


def link_account(discord_user_name, summoner_name):
    if utility.is_command_on_cooldown():
        raise exceptions.DataBaseException('Command on cooldown')
    summoner = utility.create_summoner(summoner_name)
    with shelve.open(f'{consts.DATABASE_DIRECTORY}/{consts.DATABASE_NAME}', 'rc') as database:
        for key in database.keys():
            if key == str(discord_user_name):
                raise exceptions.DataBaseException('Your discord account already has a lol account linked to it')
            if database[key] is not None:
                if database[key].name == summoner.name:
                    raise exceptions.DataBaseException('This lol account already has a discord account that is linked to it')
        database[str(discord_user_name)] = summoner


def update_linked_account_data(discord_user_name):
    summoner = utility.read_account(discord_user_name)
    summoner = utility.create_summoner(summoner.name)
    link_account(discord_user_name, summoner.name)


def get_or_create_summoner(ctx, summoner_name):
    if summoner_name is None:
        summoner = utility.create_summoner(utility.read_account(ctx.message.author.name))
        if utility.is_in_need_of_update(summoner):
            update_linked_account_data(ctx.message.author.name)
        return summoner
    return utility.create_summoner(summoner_name)


def unlink_account(ctx):
    with shelve.open(f'{consts.DATABASE_DIRECTORY}/{consts.DATABASE_NAME}', 'rc') as database:
        for key in database.keys():
            if key == str(ctx.message.author.id):
                del database[key]


# FIXME this is super trash


# def create_embed(ctx):
#     _embed = discord.Embed(
#         title='Kraut9 Leaderboard', colour=discord.Color.from_rgb(62, 221, 22))
#     summoners = list(read_all_accounts())
#     users = ''
#     with shelve.open(f'{consts.DATABASE_DIRECTORY}/{consts.DATABASE_NAME}', 'rc') as database:
#         for key in database.keys():
#             users += f'{key}\n'

#     summoner_names = ''
#     for summoner in summoners:
#         summoner_names += f'{summoner.name}\n'

#     rank_tier_winrate = ''
#     for i in range(0,len(summoners)):
#         summoner_manager.populate_player(summoner)
#         winrate, rank =  get_soloq_data(i)
#         rank_tier_winrate += str(rank) + '      ' + str(winrate) + '\n'
#     _embed.add_field(name='User', value=users)
#     _embed.add_field(name='Summoner', value=summoner_names)
#     _embed.add_field(name='Rank               Winrate', value=rank_tier_winrate)
#     return _embed


# === INTERFACE END === #
