import os
import json
from datetime import date, timedelta
import tweepy
import praw
from newsapi import NewsApiClient

def twitter():
    tweets = []
    auth = tweepy.OAuthHandler(os.environ.get("CONSUMER_KEY"), os.environ.get("CONSUMER_SECRET"))
    auth.set_access_token(os.environ.get("ACCESS_TOKEN"), os.environ.get("ACCESS_TOKEN_SECRET"))
    api = tweepy.API(auth)
    results = api.search('psmag -filter:retweets -from:pacificstand', rpp=100)
    for i in results:
        obj = json.loads(json.dumps(i._json))
        if obj['retweet_count'] + obj['favorite_count'] > 0:
            tweets.append('https://twitter.com/statuses/' + obj['id_str'], obj['user']['name'], [obj['retweet_count'], obj['favorite_count']])
    return tweets

def reddits():
    posts = []
    reddit = praw.Reddit(client_id=os.environ.get('R_CLIENT_ID'),
                         client_secret=os.environ.get('R_CLIENT_SECRET'),
                         password=os.environ.get('R_PASSWORD'),
                         user_agent='uses search API to track keyword mentions',
                         username=os.environ.get('R_USER'))
    for submission in reddit.subreddit('all').search('psmag.com', sort='new'):
        if 'bot' not in submission.url:
            posts.append([submission.shortlink, submission.score, submission.subreddit.display_name])
    return posts

def web():
    today = date.today().strftime('%Y-%m-%d')
    yesterday = (date.today() - timedelta(1)).strftime('%Y-%m-%d')
    newsapi = NewsApiClient(api_key=os.environ.get("API_KEY"))
    mentions = []
    all_articles = newsapi.get_everything(q='"Pacific Standard" -Time',
                                          from_param=yesterday,
                                          to=today,
                                          language='en',
                                          sort_by='relevancy',
                                          page_size=100)
    for i in all_articles['articles']:
        if i['source']['name'] != 'Psmag.com':
            mentions.append([i['url'], i['source']['name']])
    return mentions

def main():
    results = {}
    results['twitter'] = twitter()
    results['reddit'] = reddits()
    results['web'] = web()
    print(results)

main()
