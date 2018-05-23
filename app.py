import json
import requests
import tweepy
from newsapi import NewsApiClient

def twitter():
    tweets = []
    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_token_secret)
    api = tweepy.API(auth)
    results = api.search('psmag -filter:retweets -from:pacificstand', rpp=100)
    for i in results:
    obj = json.loads(json.dumps(i._json))
    if obj['retweet_count'] + obj['favorite_count'] > 0:
        tweets.append([obj['retweet_count'], obj['favorite_count'], 'https://twitter.com/statuses/' + obj['id_str'], obj['user']['name']])
    return tweets

def reddit():
    posts = []
    f = requests.get("https://www.reddit.com/search.json?q=psmag.com&sort=new")
    resp = f.text
    j = json.loads(resp)
    entries = j['data']['children']
    for i in entries:
        if 'bot' not in i['data']['url']:
            posts.append([i['data']['url'], i['data']['score'], i['data']['subreddit']])
    return posts

def web():
    mentions = []
    all_articles = newsapi.get_everything(q='"Pacific Standard" -Time',
                                          from_param='2018-05-01',
                                          to='2018-05-22',
                                          language='en',
                                          sort_by='relevancy',
                                          page_size=100)
    for i in all_articles['articles']:
        if i['source']['name'] != 'Psmag.com':
            mentions.append([i['source']['name'], i['url']])
    return mentions

def main():
    results = {}
    results['twitter'] = twitter()
    results['reddit'] = reddit()
    results['web'] = web()
    print(results)
