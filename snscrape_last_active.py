import argparse
import urllib.request

import snscrape.modules.twitter as sntwitter

class LastActive:
  def mostRecentMention(username):
    search = sntwitter.TwitterSearchScraper(f'to:{username}')
    for i,tweet in enumerate(search.get_items()):
      if tweet.user.username.casefold() == username:
        return tweet

      if tweet.inReplyToUser is None:
        continue

      if tweet.inReplyToUser.username.casefold() == username:
        return tweet

    return None

if __name__ == "__main__":
  argparser = argparse.ArgumentParser()
  argparser.add_argument('username')

  args = argparser.parse_args()

  username = args.username.casefold().strip('@')


  tweet = LastActive.mostRecentMention(username.casefold())

  if tweet is not None:
    print(tweet)
    print(tweet.date)
  else:
    print("UNKNOWN")

