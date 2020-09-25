#!/usr/bin/env python
# tweepy-bots/bots/autoreply.py

import tweepy
import logging
import time
from dotenv import load_dotenv
load_dotenv()
import pandas
import os
import re
import pickle

year_re = re.compile(r"[1-2][0-9][0-9][0-9]")

ppm = pandas.read_csv("data/global-co-concentration-ppm.csv")
emissions_raw = pandas.read_csv("data/owid-co2-data.csv")
world = emissions_raw.loc[emissions_raw["country"] == "World"]
world["percent_after"]=100-world["cumulative_co2"]/world["co2"].sum()*100

#pandas.set_option("display.max_rows", None, "display.max_columns", None)
#print(ppm)
#print(world)
#exit()



def create_api():
  consumer_key = os.getenv("CONSUMER_KEY")
  consumer_secret = os.getenv("CONSUMER_SECRET")
  access_token = os.getenv("ACCESS_TOKEN")
  access_token_secret = os.getenv("ACCESS_TOKEN_SECRET")

  auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
  auth.set_access_token(access_token, access_token_secret)
  api = tweepy.API(auth, wait_on_rate_limit=True, wait_on_rate_limit_notify=True)
  try:
    api.verify_credentials()
  except Exception as e:
    logger.error("Error creating API", exc_info=True)
    raise e
  logger.info("API created")
  return api

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

def check_mentions(api, since_id):
  logger.info("Retrieving mentions")
  new_since_id = since_id
  for tweet in tweepy.Cursor(api.mentions_timeline,since_id=since_id).items():
    new_since_id = max(tweet.id, new_since_id)
    if tweet.in_reply_to_status_id is not None:
      continue
    search_object=year_re.search(tweet.text)
    if search_object is not None:
      year = int(search_object.group(0))

      logger.info(f"Answering to {tweet.user.name} for year {year}")

      if year > 2018 or year < 1751:
        api.update_status(
          status="Sorry, data only goes from 1751 up to 2018",
          in_reply_to_status_id=tweet.id,
          auto_populate_reply_metadata=True
        )
      else:
        api.update_status(
          status="Global % of human CO2 emitted since " + str(year) + " = "+str(round(world.loc[world['year']==year]['percent_after'].values[0],2))+"%\n" + \
          "CO2 concentration that year = "+ str(ppm.loc[ppm['year']==1979]['ppm'].values[0]) +"ppm",
          in_reply_to_status_id=tweet.id,
          auto_populate_reply_metadata=True
        )
  return new_since_id

def main():
  api = create_api()

  #since_id=1
  with open('since_id', 'rb') as f:
    since_id = int(pickle.load(f))
    f.close()

  while True:
    since_id = check_mentions(api, since_id)
    with open('since_id', 'wb') as f:
      pickle.dump(since_id,f)
      f.close()
    logger.info("Waiting...")
    time.sleep(30)

if __name__ == "__main__":
  main()
