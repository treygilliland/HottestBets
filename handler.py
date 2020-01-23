import json, config, requests, random
from twython import Twython, TwythonError

""" Example method
def retweet(event, context):
    twitter = Twython(config.APP_KEY, config.APP_SECRET, config.OAUTH_TOKEN, config.OAUTH_TOKEN_SECRET)

    search_results = twitter.search(q='serverless', result_type='mixed', lang='en')
    message = ""

    for tweet in search_results['statuses']:
        try:
            twitter.retweet(id=tweet['id'])
            message = f"Retweeted \"{tweet['text']}\" by {tweet['user']['name']}"
            twitter.create_friendship(id=tweet['user']['id'])
            break
        except TwythonError:
            pass

    body = {
        "message": message,
        "input": event
    }

    response = {
        "statusCode": 200,
        "body": json.dumps(body)
    }

    return response
"""

def get_random_key():
    #sport_keys = {"NBA": "basketball_nba", "MMA": "mma_mixed_martial_arts", "NCAAB": "basketball_ncaab", "NHL": "icehockey_nhl"}
    sport_keys = ["basketball_nba", "basketball_ncaab", "icehockey_nhl", "americanfootball_nfl"]

    sports_response = requests.get('https://api.the-odds-api.com/v3/sports', params={'api_key': config.API_KEY})

    sports_json = json.loads(sports_response.text)

    if not sports_json['success']:
        print(
            'There was a problem with the sports request:',
            sports_json['msg']
        )

    else:
        print()
        print(
            'Successfully got {} sports'.format(len(sports_json['data'])),
            'Here\'s all the sports:'
        )

        
        inseason_keys = []

        for item in sports_json["data"]:
            if item in sport_keys:
                inseason_keys.append(item)

    return random.choice(sport_keys)


# This requests current odds data and calls get_best_odds to generate tweets
def update_odds_json(sport_key):
    region = "us"
    mkt = "h2h"

    # request odds for the key
    odds_response = requests.get('https://api.the-odds-api.com/v3/odds', params={
        'api_key': config.API_KEY,
        'sport': sport_key,
        'region': region, # uk | us | eu | au
        'mkt': mkt # h2h | spreads | totals
    })

    odds_json = json.loads(odds_response.text)
    if not odds_json['success']:
        print('There was a problem with the odds request:' + odds_json['msg'])
    else:
        # Write todays odds to file
        # with open('data/NBAodds.txt', 'w') as outfile:
        #     json.dump(odds_json, outfile)

        # odds_json['data'] contains a list of live and 
        #   upcoming events and odds for different bookmakers.
        # Events are ordered by start time (live events are first)
        print('\nSuccessfully got {} events. Here\'s the first event:'.format( len(odds_json['data']) ) )
        print(odds_json['data'][0])

        # Log odd api usage
        print('\nRemaining requests', odds_response.headers['x-requests-remaining'])
        print('Used requests', odds_response.headers['x-requests-used'])

        return odds_json

# This determines the best odds and generates the tweet
def get_best_odds(odds_json):
    # with open('data/NBAodds.txt') as odds:
    #     odds_json = json.load(odds)

    tweets = []

    for i, game in enumerate(odds_json["data"]):
        game = odds_json["data"][i]

        sites = game["sites"]

        team1 = {"team": game["teams"][0], "odds": 0, "site": ""}
        team2 = {"team": game["teams"][1], "odds": 0, "site": ""}
        for site in sites:
            key = site["site_key"]
            team1_odds = site["odds"]["h2h"][0]
            team2_odds = site["odds"]["h2h"][1]
            if team1_odds > team1["odds"]:
                team1["odds"] = team1_odds
                team1["site"] = site["site_nice"]

            if team2_odds > team2["odds"]:
                team2["odds"] = team2_odds
                team2["site"] = site["site_nice"]

        if team1["odds"] < team2["odds"]:
            favorite = team1
            underdog = team2
        else:
            favorite = team2
            underdog = team1

        tweets.append("{} ({}) vs. {} ({})\n\nFavorite odds from {}.\nUnderdog odds from {}.".format(favorite["team"], favorite["odds"], underdog["team"], underdog["odds"], favorite["site"], underdog["site"]))

    return tweets

def generate_tweets():
    tweets = []

    #if no tweets generated, try another key
    while len(tweets) == 0:
        #key = get_random_key()
        key = "basketball_nba"
        odds_json = update_odds_json(key)
        tweets = get_best_odds(odds_json)

    return tweets

# this generates and tweets the bet
def tweet_bet(event, context):
    twitter = Twython(config.APP_KEY, config.APP_SECRET, config.OAUTH_TOKEN, config.OAUTH_TOKEN_SECRET)
    tweets = generate_tweets()

    error = ["(0)", "Favorite odds from .", "underdog odds from ."]
    bet = ""
    while len(bet) == 0:
        bet = random.choice(tweets)
        for item in error:
            if item in bet:
                bet = ""


    try:
        twitter.update_status(status=bet)
        message = "Tweeted bet: " + bet
    except:
        message = "ERROR TWEETING BET"
        pass


    body = {
        "message": message,
        "input": event
    }

    response = {
        "statusCode": 200,
        "body": json.dumps(body)
    }

    return response