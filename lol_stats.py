import sys
import pandas as pd
import time
from collections import Counter

from riotwatcher import LolWatcher, ApiError

from champions_dict import *


# global
API_KEY = 'get_an_api_key_from_riots_website'


def get_matchlist(watcher, account_id, region='na1'):
	''' retrieves all matches for the given account id and returns as a dataframe '''
	matches = []
	i = 0

	while True:
		try:
			match = watcher.match.matchlist_by_account(region, account_id, begin_index=100*i, end_index=100*(i+1)) # could potentially limit to desired game modes here~~
			if match['matches']:
				matches.append(match)
				i += 1
				time.sleep(.1)
				print(i*100, '/ ?')
			else:
				break
		except:
			pass

	all_matches = [m for match in matches for m in match['matches']]
	return pd.DataFrame(all_matches)


def get_all_matches(watcher, matchlist, region='na1'):
	''' retrieves all matches in the given matchlist and returns as a dataframe '''
	matches = []
	failed = []

	for i, match in enumerate(matchlist):
		try:
			matches.append(watcher.match.by_id(region, match))
		except:
			failed.append(match)
		if not i%10:
			print(i, '/', len(matchlist))
		time.sleep(1.5)
	print(len(matchlist), '/', len(matchlist))

	print('Number failed:', len(failed))
	
	if failed:
		print('Retrying...')
		ffailed = []

		for match in failed:
			try:
				matches.append(watcher.match.by_id(region, match))
			except:
				ffailed.append(match)
			time.sleep(1.5)

		if ffailed:
			print('Doubly failed match ids:')
			print(ffailed)
		else:
			print('Success')

	return pd.DataFrame(matches)


def match_details(matches, account_id, queue='sr'):
	'''
	returns dataframe consisting of important details for all matches played in the desired queue

	MOST RELEVANT 5V5 QUEUE TYPES FROM RIOT API:
	400: summoners rift, normal draft
	420: summoners rift, ranked solo
	430: summoners rift, normal blind pick
	440: summoners rift, ranked flex
	450: aram
	700: summoners rift, clash

	valid queues: sr, ranked, soloq, clash, aram
	with included queue types below
	'''

	# theres a better way to do this but this is easy and quick
	# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
	valid_queue_ids = {
		'sr': [400, 420, 430, 440, 700],
		'ranked': [420, 440],
		'soloq': 420,
		'clash': 700,
		'aram': 450,
		'sr_and_aram': [400, 420, 430, 440, 450, 700],
	}
	if type(valid_queue_ids[queue]) is int:
		filtered_matches = matches[matches.queueId == valid_queue_ids[queue]]
	else:
		queue_mask = matches.queueId.apply(lambda x: x in valid_queue_ids[queue])
		filtered_matches = matches[queue_mask]
	# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

	match_details = []
	for i in range(len(filtered_matches)):
		match_details.append(extract_details_from_match(filtered_matches.iloc[i,:], account_id))

	return pd.DataFrame(match_details)


def extract_details_from_match(match, account_id):
	''' returns dictionary containing stats about the match from the perspective of account_name '''
	for p in match.participantIdentities:
		if p['player']['accountId'] == account_id:
			player_participant_id = p['participantId']
			break

	for p in match['participants']:
		if p['participantId'] == player_participant_id:
			win = p['stats']['win']
			blue_side = (p['teamId'] == 100) # 100 is blue side, 200 is red
			player_champion = p['championId']

	game_detail = {
		'game_id': match['gameId'],
		'win': win,
		'blue_side': blue_side,
		'player_champion': player_champion,
		'ally_champions': [],
		'enemy_champions': [],
	}

	for p in match['participants']:
		if p['stats']['win'] != win:
			game_detail['enemy_champions'].append(p['championId'])
		elif p['participantId'] != player_participant_id:
			game_detail['ally_champions'].append(p['championId'])

	return game_detail


def wr_by_player_champ(games):
	''' returns a dataframe containing games, wins, losses and wr for champions played by account_name '''
	pc_group = games.groupby('player_champion')

	wr = pd.concat([pc_group.win.count(), pc_group.win.sum().astype(int)], axis=1).fillna(0)
	wr.columns = ['games', 'wins']
	wr.index = wr.index.map(id_to_champ)

	wr['losses'] = wr.games - wr.wins
	wr['winrate'] = wr.wins / wr.games

	return wr.sort_values(by='winrate', ascending=False)


def wr_by_team_champs(games, team):
	'''
	returns a dataframe containing games, wins, losses and wr for champions on the given team
	from perspective of account_name
	team = enemy: stats AGAINST champs on enemy team
	team = ally: stats WITH champs on team

	'''
	team_champions = team + '_champions'
	win = []
	lose = []

	for champs in games[games.win][team_champions]:
		win.extend(champs)
	for champs in games[~games.win][team_champions]:
		lose.extend(champs)

	win = Counter(win)
	lose = Counter(lose)

	wr = pd.DataFrame([win, lose]).T.sort_index().fillna(0)
	wr.columns = ['wins', 'losses']
	wr.index = wr.index.map(id_to_champ)
	wr['games'] = wr.wins + wr.losses
	wr['winrate'] = wr.wins / wr.games
	wr = wr[['games', 'wins', 'losses', 'winrate']]

	return wr.sort_values(by='winrate', ascending=False)


def oldest_recorded_match(matches):
	''' returns the timestamp of the oldest recorded match '''
	if type(matches.iloc[-1].timestamp) == int:
		return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(matches.iloc[-1].timestamp))
	else:
		return matches.iloc[-1].timestamp


def unplayed_champions(games):
	'''	returns list of champions that have never been played in the previously determined queue type '''
	return sorted(list(set(champ_to_id_dict.keys() - set(games.player_champion.map(id_to_champ).unique()))))


def their_yasuo_vs_your_yasuo(ally, enemy):
	'''
	combines tables of ally and enemy champions games and winrates
	adds delta_winrate column that descibes how much more a given champion wins when on
		the other team (FROM THEIR PERSPECTIVE) than when on your team (FROM YOURS)
	a high negative value indicates that that champ performs  better when against you
	a high positive value indicates that that champ performs better when on your team
	'''
	wr = pd.DataFrame([ally.games, ally.winrate, enemy.games, enemy.winrate]).T
	wr.columns = ['games_with', 'winrate_with', 'games_against', 'winrate_against']
	wr['delta_winrate'] = wr.winrate_with - (1 - wr.winrate_against)

	return wr.sort_values(by='delta_winrate')



def main():
	# global that could be args
	region = 'na1'

	if len(sys.argv) > 1:
		account_name = sys.argv[1]
	else:
		account_name = 'vayneofcastamere'

	print('Account name:', account_name)

	watcher = LolWatcher(API_KEY)
	account = watcher.summoner.by_name(region, account_name)
	account_id = account['accountId']
	print('Account id:', account_id)

	print('Collecting matchlist')
	df_ml = get_matchlist(watcher, account_id, region)
	df_ml.to_json(account_name + '_matchlist.json')
	# df_ml = pd.read_json('voc_matchlist.json')

	print('Collecting matches')
	df = get_all_matches(watcher, df_ml.gameId.values, region)
	df.to_json(account_name + '_allmatches.json')
	# df = pd.read_json('voc_allmatches.json')

	print('\n')
	print('Oldest match on record:', oldest_recorded_match(df_ml), '\n')

	games = match_details(df, account_id, queue='sr')

	print('You have never played the following champions in the given mode:')
	print(unplayed_champions(games), '\n')

	wr_player = wr_by_player_champ(games)
	wr_ally = wr_by_team_champs(games, 'ally')
	wr_enemy = wr_by_team_champs(games, 'enemy')
	yas = their_yasuo_vs_your_yasuo(wr_ally, wr_enemy)

	print('Winrates by player champion:')
	print(wr_player, '\n')
	print('Winrates with allied champion:')
	print(wr_ally, '\n')
	print('Winrates against enemy champion:')
	print(wr_enemy, '\n')

	print('Winrate differential by champion based on team')
	print('a negative value indicates that a given champion performs better when on enemy team')
	print('a positive value indicates that a given champion performs better when on your team')
	print(yas, '\n')

	print('Is enemy team yasuo actually better than your team Yasuo?')
	print(yas.loc['Yasuo'])


if __name__ == '__main__':
	main()
