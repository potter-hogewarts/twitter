import sys
# tweepyをインストールしたディレクトリ相対パスを指定する
sys.path.append('python_package')
# coding: UTF-8
import json
import tweepy
import discord
from requests_oauthlib import OAuth1Session
import urllib.request
from datetime import datetime, timedelta, timezone
#from pytz import timezone
from discord.ext import tasks
import random
from discord.ui import View
import os
import requests

#本番用
TOKEN = os.getenv('TOKEN')
intents=discord.Intents.all()
client = discord.Client(intents=intents)
tree = discord.app_commands.CommandTree(client)

msg = ""
tweet_msg = ""
txt = ""
url = ""
media_id = None

#reply用
channel = None

# 設定ファイル読み込み
config = json.load(open('config.json', 'r'))


# Twitter API credentials
consumer_key = config['twitter']['consumerKey']
consumer_secret = config['twitter']['consumerSecret']
access_token = config['twitter']['accessToken']
access_token_secret = config['twitter']['accessTokenSecret']
bearer_token = config['twitter']['bearerToken']

# Authenticate Twitter API
auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_token_secret)

# Create API object
api = tweepy.API(auth)
twitter = tweepy.Client(
    bearer_token = bearer_token,
    consumer_key=consumer_key,
    consumer_secret=consumer_secret,
    access_token=access_token,
    access_token_secret=access_token_secret,
    wait_on_rate_limit=True)


#このリストを用いて、フォーローする人を決定する
except_unfollow_users = ["@XXXXX","@YYYYY"]

@client.event
async def on_ready():
    global channel
    await client.change_presence(activity=discord.Game(name="X"))
    await tree.sync()
    #Tweetチャンネル(本番用Hogewarts)
    channel = client.get_channel("ZZZZZ")


    try:
        auto_tweet.start()
    except Exception as e:
        print(e)
        pass
    print("起動")


@tree.command(
    name="log",#コマンド名
    description="管理者権限"#コマンドの説明
)
@discord.app_commands.default_permissions(
    administrator=True
)
async def log(interaction: discord.Interaction):
    await interaction.response.send_message(file=discord.File('./twitter.log'),ephemeral=True)

def upload(url,filename):
    request = requests.get(url, stream=True)
    print(f"statuscode:{request.status_code}")

    if request.status_code == 200:
        with open(filename, 'wb') as image:
            for chunk in request:
                image.write(chunk)
            
            
        media = api.media_upload(filename=filename)
        os.remove(filename)
        return(media.media_id)
    else:
        return None
    

#tweet_function
def lambda_handler(msg,media_id):
     # ツイート画像付きツイートかそうでないかの判定
    if media_id == None:
        #print("None")
        twitter.create_tweet(text=msg)

    elif media_id != None:
        twitter.create_tweet(text=msg, media_ids =[media_id])

def tweet_check(account):
    #print("てすとお")
    tweets_id = []
    try:
        tweets = tweepy.Cursor(api.user_timeline, id = account).items(50)
        for tw in tweets:
            #print("tweet:",tw)
            #print()
            if ((tw.text.startswith('RT')) or (tw.text.startswith('@'))) and ("@AAAAA" not in tw.text):
                pass
            else:
                tweets_id.append(tw.id)
    except:
        pass

    return tweets_id



@tasks.loop(seconds=18000)
async def accounts():
    accounts = {"@AAAA":000000000000000,"@BBBB":000000000000001}
    for account,chnl_id in accounts.items():
        print(account,":")
        try:
            await detect_tweets(account,chnl_id)
        except Exception as e:
            print(e)
            pass


@client.event
async def detect_tweets(account,chnl_id):
    channel = client.get_channel(chnl_id)

    time_now = datetime.now()
    #print("time_now:",time_now)
    tweets=api.user_timeline(screen_name=account)
    #tweets = twitter.get_users_tweets(account)
    
    print(f'tweets:{tweets}')

    #JapanTime_now
    time_now = time_now.astimezone(timezone(timedelta(hours=+9)))
    
    uxtime_now = int(time_now.timestamp())
    
    for tweet in tweets:
        #TweetTime_UnixTime
        uxjst_tweet = int(tweet.created_at.astimezone(timezone(timedelta(hours=+9))).timestamp())
        
        #日本時刻に変換した上でUNIXTIME
        #uxjst_tweet = int((tweet.created_at + timedelta(hours=+9)).timestamp())

        #print(tweet._json)
        print(tweet)

        if (uxtime_now - uxjst_tweet) <= 18005:
            print("distance_time:",uxtime_now - uxjst_tweet)
            await channel.send(tweet._json['entities']['urls'][0]['expanded_url'])

@tasks.loop(seconds=86400)
async def auto_tweet():
    print("auto")
    global tweet_msg
    #time_now = datetime.now()
    #print("ツイート時間:")
    #print(time_now.astimezone(timezone('Asia/Tokyo')))
    f = open('tweet.txt',encoding="utf-8")
    msg = f.read().split('\n')
    f.close()
    while True:
        txt = random.choice(msg)
        #print("txt:",txt)
        
        print("tweet_msg:",tweet_msg)
        print("txt:",txt)

        if tweet_msg != txt:
            tweet_msg = txt
            break
        print("Loop")

    print("実行")

    print("tweetmsg:",tweet_msg)

    try:
        twitter.create_tweet(text=tweet_msg)
    except Exception as e:
        print(e)
    
    print("実行")

class HugaButton(discord.ui.Button): #HugaButtonはButtonのサブクラス
    def __init__(self,txt:str):
        super().__init__(label=txt,style=discord.ButtonStyle.blurple)

    async def on_error(self, interaction: discord.Interaction):
        await interaction.response.send_message("もう一度",ephemeral=True)


    async def callback(self, interaction: discord.Interaction):
        global msg
        global media_id
        
        if self.label == "ツイートする":
            #try:
            lambda_handler(msg,media_id)
            await interaction.response.send_message("https://twitter.com/AAAAA でツイート",ephemeral=True)
            #except Exception as e:
                #print(e)
                #await interaction.response.send_message("文字数オーバーよ")
            return

        if self.label == "ツイートしない":
            msg = ""
            await interaction.response.send_message("内容を破棄",ephemeral=True)
            return

#$chatでツイート
@tree.command(
    name="tweets",#コマンド名
    description="ツイート"#コマンドの説明
)
@discord.app_commands.default_permissions(
    kick_members = True
)
async def tweets(interaction: discord.Interaction):
    #本番用(Hogewarts)
    tweet_Room = client.get_channel(1111111111111111)
    
    #テスト用(Slythepin)
    #tweet_Room = bot.get_channel(849937728920879145)

    if interaction.channel == tweet_Room:
        await interaction.response.send_message(interaction.user.name + "ツイートするものを5分以内に入力",ephemeral=True)
        channel = interaction.channel
        global url
        url = ""

        def check(m):
            global url
            global msg
            global media_id
            try:
                url = m.attachments[0].url
                filename = m.attachments[0].filename
                media_id = upload(url,filename)

            except Exception as e:
                print(e)
                pass
            msg = m.content
            return m.channel == channel

        try:
            await client.wait_for('message', timeout=300 ,check=check)
        except:
            #5分以内に入力または、エラーが起きた場合
            await interaction.followup.send("もう一度",ephemeral=True)
            return

        #ツイート内容の確認
        embed = discord.Embed(title="下の内容でツイート",description=msg)

        if url != "":
            embed.set_image(url=url)
        else:
            pass

        view = View(timeout=300)

        button = HugaButton("ツイートする")
        view.add_item(button)
        button = HugaButton("ツイートしない")
        view.add_item(button)

        await interaction.followup.send(embed=embed,view=view,ephemeral=True)

    else:
        pass

client.run(TOKEN) #ボットのトークン
