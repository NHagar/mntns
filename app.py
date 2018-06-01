import os
import json
import datetime
import psycopg2
import tweepy
import praw
import requests
from newsapi import NewsApiClient

db_url = os.environ.get("DATABASE_URL")
conn = psycopg2.connect(db_url)
cur = conn.cursor()

def twitter():
    tweets = []
    auth = tweepy.OAuthHandler(os.environ.get("CONSUMER_KEY"), os.environ.get("CONSUMER_SECRET"))
    auth.set_access_token(os.environ.get("ACCESS_TOKEN"), os.environ.get("ACCESS_TOKEN_SECRET"))
    api = tweepy.API(auth)
    results = api.search('psmag -filter:retweets -from:pacificstand', rpp=100)
    for i in results:
        obj = json.loads(json.dumps(i._json))
        if obj['retweet_count'] + obj['favorite_count'] > 0:
            tweets.append(str(('https://twitter.com/statuses/' + obj['id_str'], obj['user']['name'], obj['retweet_count'], obj['favorite_count'])))
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
            posts.append(str((submission.shortlink, submission.score, submission.subreddit.display_name)))
    return posts

def web():
    today = datetime.date.today().strftime('%Y-%m-%d')
    yesterday = (datetime.date.today() - datetime.timedelta(1)).strftime('%Y-%m-%d')
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
            mentions.append(str((i['url'], i['source']['name'])))
    return mentions

def main():
    results = {}
    results['twitter'] = twitter()
    results['reddit'] = reddits()
    results['web'] = web()
    return results

def database():
    data = main()
    for i in data['twitter']:
        try:
            cur.execute("INSERT INTO twitter VALUES " + i)
        except psycopg2.IntegrityError:
            conn.rollback()
        else:
            conn.commit()
    for i in data['reddit']:
        try:
            cur.execute("INSERT INTO reddit VALUES " + i)
        except psycopg2.IntegrityError:
            conn.rollback()
        else:
            conn.commit()
    for i in data['web']:
        try:
            cur.execute("INSERT INTO newsapi VALUES " + i)
        except psycopg2.IntegrityError:
            conn.rollback()
        else:
            conn.commit()

def build():
    message = {'attachments': []}
    cur.execute("SELECT * FROM twitter")
    tweets = cur.fetchall()
    tw = {
        "fallback": "Twitter mentions",
        "title": "Twitter",
        "fields": []
    }
    for i in tweets:
        tw['fields'].append({
            "value": "<%s|%s>" % (i[0], i[1])
        })
    cur.execute("SELECT * FROM reddit")
    rposts = cur.fetchall()
    re = {
        "fallback": "Reddit mentions",
        "title": "Reddit",
        "fields": []
    }
    for i in rposts:
        re['fields'].append({
            "value": "<%s|%s>" % (i[0], i[2])
        })
    cur.execute("SELECT * FROM newsapi")
    mentions = cur.fetchall()
    web = {
        "fallback": "Web mentions",
        "title": "Web",
        "fields": []
    }
    for i in mentions:
        web['fields'].append({
            "value": "<%s|%s>" % (i[0], i[1])
        })
    message['attachments'].extend([tw, re, web])
    return message

def send():
    payload = build()
    webhook_url = os.environ.get("SLACK_URL")
    response = requests.post(
        webhook_url, data=json.dumps(payload),
        headers={'Content-Type': 'application/json'}
    )
    if response.status_code != 200:
        raise ValueError(
            'Request to slack returned an error %s, the response is:\n%s'
            % (response.status_code, response.text)
    )

if datetime.datetime.now().hour == 12:
    database()
    send()
else:
    database()
