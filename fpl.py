import json
import random
from operator import itemgetter

# Configuration values for this gameweek

gameweek = 3
transfersavailable = 1

# Player codes of current team
currentplayers = [1718,44346,41135,42786,14664,37915,13017,26793,11735,56979,50089,19159,20480,49323,112139]
currentteam = []
currentteamvalue = 998

# Global Variables
players = []
typecount = []

# Configuration values for game rules
playertypes = ['Goalkeeper','Defender','Midfielder','Forward']
squadcount = [2,5,5,3]
squadsize = 15
playmin = [1,3,0,1]
playmax = [1,5,5,3]
budget = currentteamvalue
maxperteam = 3
gamesperseason = 38.0

# Used to calculate strength of opponent.
# Based on weighted average of last 3 seasons finishing positions
teamstrength = {
'Man City': 1,
'Chelsea' : 2,
'Arsenal' : 2,
'Liverpool' : 3,
'Man Utd' : 3,
'Spurs' : 3,
'Everton' : 3,
'Stoke' : 6,
'Newcastle' : 6,
'Swansea' : 6,
'Southampton' : 7,
'West Ham' : 8,
'West Brom' : 8,
'Sunderland' : 9,
'Crystal Palace' : 9,
'Aston Villa' : 9,
'Hull' : 10,
'QPR' : 11,
'Burnley' : 12,
'Leicester' : 12 }


class fpl():

    # Read station data from file
    @staticmethod
    def getplayerdata():
        output = open('playerkeydata','w')
        f = open('playerdata','r')

        for line in f:
            player = json.loads(line)    
            player['picked'] = False

            # Calculate four week look ahead points for player
            fpl.lookaheadpoints(player, gameweek)

            # Add player to global variable  
            players.append(player)

            # Output key player data
            playerdata = player['second_name'].encode('ascii', errors='ignore')
            playerdata += "," + str(player['total_points'])
            playerdata += "," + str(player['now_cost'])
            playerdata += "," + player['team_name']
            playerdata += "," + player['type_name']
            playerdata += "," + str(player['lookaheadpoints'])

            output.write(playerdata + '\n')

        f.close()
        output.close()
        
        # Create a list of current team players
        currentteam = fpl.createcurrentteam()

    # Generate a four week lookahead score for a player
    @staticmethod
    def lookaheadpoints(player, currentweek):
        # Get points per game for player during last season
        ppg = fpl.pointspergame(player)

        # twp - this weeks points
        # lap - look ahead points
        twp = 0
        lap = 0
        # Week scores are weighted in favor of current week
        weekweight = 1
        for week in range(currentweek, currentweek + 4):
            # Get this weeks fixture
            fixture = "Gameweek " + str(week)
            fixtures = player['fixtures']['all']

            # Check all the gameweeks looking for this week
            # Assumes each week has no more than one game for the player
            gamethisweek = False
            for thisweeksgame in fixtures:
                if thisweeksgame[1] == fixture:
                    gamethisweek = True
                    break

            if gamethisweek == True:

                # Player has game this week
                # Find name of opponent
                split = thisweeksgame[2].find('(')
                otherteam = thisweeksgame[2][0:split-1]
                # Calculate strength of opponent for this week
                sos = fpl.strengthofschedule(player['team_name'],otherteam)

                # Set factor for home game vs away game
                if '(H)' in thisweeksgame[2]:
                    home = 1.0
                else:
                    home = 0.5


                # Points this week is set to
                #     player points per game *
                #     strength of opponent *
                #     home game factor *
                #     week weighting - set to 1.0, 0.75, 0.5, 0.25
                ptw = ( ppg * sos * home ) * weekweight
                # Set this week points for this week
                if week == currentweek:
                    twp = ptw
                # Set lookahead points
                lap += ptw

            weekweight = weekweight - 0.25

        # Boost score for players who play most minutes
        minutes = 0
        games = 38
        # Get last seasons total minutes
        history = player['season_history']
        for season in history:
            if season[0] == "2013/14":
                minutes = season[1]

        # Get minutes and games this season
        # Apply factor to increase relevance of this seasons minutes
        if gameweek != 1:
            minutes += player['minutes'] * 2.0
            games += ((gameweek - 1) * 2.0)
            if player['minutes'] < (gameweek-1) * 60:
                lap = lap / 10.0
                twp = twp / 10.0

        # Calculate minutes per game
        if games == 0 or minutes == 0:
            minutespergame = 0
        else:
            minutespergame = minutes / float(games)

        # Add points boosts for high minute averages
        if minutespergame > 80:
            lap += 3
            twp += 1
        elif minutespergame > 60:
            lap += 1

        # Store values in global player variable
        player['thisweekpoints'] = twp
        player['lookaheadpoints'] = lap

    # Calculate points per game for a player
    @staticmethod
    def pointspergame(player):
        ppg = 0
        history = player['season_history']
        for season in history:
            if season[0] == "2013/14":
                ppg = season[16] / float(gamesperseason)

        if gameweek != 1:
            ppg += ((player['total_points'] / float(gamesperseason) * 2.0))
        
        return ppg

    # Calculate strength of opponent
    @staticmethod
    def strengthofschedule(playerteam, otherteam):
        sos = teamstrength[otherteam] - teamstrength[playerteam]
        sos += 11
        sos = float(sos) / 22
        return sos

    # Get a random player
    @staticmethod
    def getrandomplayer():
        player = players[random.randint(0,len(players)-1)]
        return player


    # Create the current team from a list of player codes
    @staticmethod
    def createcurrentteam():
        for playerid in currentplayers:
            for player in players:
                if player['code'] == playerid:
                    currentteam.append(player)
                    break
        fpl.scoreteam(currentteam,True)
        return currentteam

    # Calculate the value of a team
    @staticmethod
    def teamvalue(team):
        teamvalue = 0
        for player in team:
            teamvalue += player['now_cost']
        return teamvalue

    # Check a team is valid by the rules of the game
    @staticmethod
    def validteam(team):

        # Only transfersavailable changes permitted

        transfers = 0
        for player in team:
            if player not in currentteam:
                transfers += 1

        if transfers > transfersavailable:
            return False

        # no more than 3 players per team
        teamcount = {}
        for player in team:
            if player['team_name'] in teamcount.keys():
                teamcount[player['team_name']] += 1
            else:
                teamcount[player['team_name']] = 1

        for club in teamcount:
            if teamcount[club] > 3:
                return False

        # Each player only once in each team
        for idx1, player in enumerate(team):
            for idx2, otherplayer in enumerate(team):
                if idx1 != idx2:
                    if player['code'] == otherplayer['code']:
                        return False

        # no more than 1000 value
        if fpl.teamvalue(team) > budget:
            print "over budget"
            return False

        # Check for right number of each type of player
        for idx, count in enumerate(squadcount):
            number = 0
            for player in team:
                if player['type_name'] == playertypes[idx]:
                    number += 1
                    if number > count:
                        return False

        # Player must be available
        for player in team:
            if player['status'] != 'a':
                return False

        return True

    # Transfer in a player
    @staticmethod
    def transfer(player):
        # Sort the team by look ahead points - smallest to largest
        sortedteam = sorted(currentteam, key=itemgetter('lookaheadpoints'))

        value = fpl.teamvalue(sortedteam)

        # Check the transferred in player is available
        if player['status'] != 'a':
            return currentteam

        # Look at each player in the current team
        for currentplayer in sortedteam:
            # If the player to transfer in is 
            # - The right type
            # - A better player by lookaheadpoints 
            # - Fits in the budget
            # Then transfer in the player and remove the current player
            if player['type_name'] == currentplayer['type_name']:
                if player['lookaheadpoints'] > currentplayer['lookaheadpoints']:
                    if value + player['now_cost'] - currentplayer['now_cost'] <= currentteamvalue:
                        sortedteam.remove(currentplayer)
                        sortedteam.append(player)
                        return sortedteam
        return currentteam

    # Score a team by look ahead points             
    @staticmethod
    def scoreteam(team,display=False):
        pickedteam = []
        typecount = [0,0,0,0]

        if fpl.validteam(team) == False:
            return 0

        sortedteam = sorted(team, key=itemgetter('lookaheadpoints'), reverse=True)

        for player in team:
            player['picked'] = False

        for idx, count in enumerate(playmin):
            if count != 0:
                picked = 0
                for player in sortedteam:
                    if player['type_name'] == playertypes[idx]:
                        pickedteam.append(player)
                        picked += 1
                        typecount[idx] += 1
                        player['picked'] = True
                    if picked == count:
                        break
    
        playersneeded = 6
        for player in sortedteam:
            if player['picked'] == True:
                continue

            idx = playertypes.index(player['type_name'])
            if typecount[idx] == playmax[idx]:
                continue

            pickedteam.append(player)
            playersneeded -= 1
            typecount[idx] += 1
            player['picked'] = True

            if playersneeded == 0:
                break
    
        points = 0
        for player in pickedteam:
            if player['status'] == 'a':
                points += player['lookaheadpoints']

       # optimize the non-picked players - but not too much
        for player in team:
            if player not in pickedteam:
                if player['status'] == 'a':
                    points += player['lookaheadpoints'] * 0.1

        if display == True:
            fpl.printteam(sortedteam)
            print "Points", points

        return points

    # Print out a team
    @staticmethod
    def printteam(team):
        for player in team:
            playerdata = player['second_name'].encode('ascii', errors='ignore')
            playerdata += "," + str(player['total_points'])
            playerdata += "," + str(player['now_cost'])
            playerdata += "," + player['team_name']
            playerdata += "," + player['type_name']
            playerdata += "," + str(player['code'])
            playerdata += "," + str(player['lookaheadpoints'])
            playerdata += "," + str(player['thisweekpoints'])

            if player['picked'] == True:
                playerdata += ", Picked"

            print playerdata
        
        print "Team value %s" % fpl.teamvalue(team)

# Get the player data from a file
fpl.getplayerdata()

# If any of the current team have become unavailable or not definite
# Set their score to 0
for player in currentteam:
    if player['status'] != 'a':
        player['lookaheadpoints'] = 0

# Store the score of the current team
bestteam = currentteam
bestscore = fpl.scoreteam(currentteam,True)

# Loop through each player looking for a good transfer
for player in players:
    newteam = fpl.transfer(player)
    if fpl.validteam(newteam):
        # Check if the team with the transferred player is better than the best team found so far
        if fpl.scoreteam(newteam,False) > bestscore:
            bestteam = newteam
            bestscore = fpl.scoreteam(bestteam,True)
            print "New Best Score", bestscore

# Print out the best team found
fpl.scoreteam(bestteam,True)


