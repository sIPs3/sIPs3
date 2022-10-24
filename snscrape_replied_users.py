# Print a list of accounts replied to by a user

import argparse
import csv
import datetime
import logging
import os
import sys
import time

import urllib

import snscrape.modules.twitter as sntwitter

logging.getLogger(sntwitter.__name__).setLevel(logging.DEBUG)

class ScrapeRepliedUsers:
  def __init__(self, datadir):
    url = 'https://raw.githubusercontent.com/travisbrown/twitter-watch/main/data/suspensions.csv'

    fn = os.path.join(datadir, 'suspensions.csv')
    if not os.path.isfile(fn):
      urllib.request.urlretrieve(url, fn)

    self.suspensions = {}  
    with open(fn) as csvfile:
      reader = csv.reader(csvfile)
      for row in reader:
        self.suspensions[int(row[2])] = row

  def _getAccountStatus(self,uid):
    if uid in self.suspensions and self.suspensions[uid][1] == '':
      return 'Suspended'

    search = sntwitter.TwitterUserScraper(int(uid))

    try:
      entity = search._get_entity()
    except KeyError as err:
      return 'EXCEPTION'

    if entity is None:
      return 'Suspended'
    if entity.protected is True:
      return 'Protected'
    return 'Available'

  def getLastActive(self, u):
    replySearch = sntwitter.TwitterSearchScraper(f'to:{u.username}')
    lastactive = datetime.datetime.now(datetime.timezone.utc)
    for i,reply in enumerate(replySearch.get_items()):
      if i > 10:
        lastactive = None
        break

      if reply.user.username.casefold() == u.username.casefold():
        lastactive = reply.date
        break
      if reply.inReplyToUser is None:
        continue
      if reply.inReplyToUser.username.casefold() == u.username.casefold():
        lastactive = reply.date
        break

    return lastactive

  def scrapeRepliedUsers(self, username, until, limit, status, mentions):
    # Sanitize inputs
    username = username.strip('@')

    if until is None:
      now = datetime.datetime.now()
      until = now.strftime("%Y-%m-%d")

    # Set up tweet scraper and execute search
    q = f'from:{username} -to:{username} filter:replies until:{until}'

    if mentions is True:
      # Search mentions of user instead of tweets from user
      q = f'@{username} -to:{username} filter:replies until:{until}'

    search = sntwitter.TwitterSearchScraper(q)
    cache = {}
    writer = csv.writer(sys.stdout)
    writer.writerow(['lastactive','date','status','twitterid','username','displayname'])
    for i,tweet in enumerate(search.get_items()):
      if limit is not None and i > limit:
        break

      if tweet.inReplyToTweetId is None:
        continue

      u = tweet.inReplyToUser

      # Only print each account once
      if u.id in cache:
        continue
      
      # Skip replies to self
      if u.username.casefold() == username.casefold():
        continue

      acctstatus = self._getAccountStatus(tweet.inReplyToUser.id)
      cache[u.id] = True

      # Filter results by status if filter is specified
      if status is not None and status.casefold() != acctstatus.casefold():
        continue

      if u.id in self.suspensions:
        lastactive = datetime.datetime.fromtimestamp(int(self.suspensions[u.id][0]))
      else:
        lastactive = self.getLastActive(u)
        if lastactive is None:
          lastactive = tweet.date

      if datetime.datetime.strptime(until, '%Y-%m-%d').date() < lastactive.date():
        continue

      lastactive = lastactive.strftime("%Y-%m-%d")
      
      date = tweet.date.strftime("%Y-%m-%d")
     
      out = [lastactive,date,f'[{acctstatus}]',u.id,u.username,u.displayname]
      if u.id in self.suspensions:
        out.append(self.suspensions[u.id][7])

      writer.writerow(out)

    return None

if __name__ == "__main__":
  # Set up arguments and parse
  argparser = argparse.ArgumentParser(
    description="Print a list of accounts replied to by a user")
  argparser.add_argument('--limit', '-l', type=int,
    help="The maximum number of replies to search")
  argparser.add_argument('--until', '-u', type=str,
    help="Search for replies up to a given date")
  argparser.add_argument('--status', '-s', type=str,
    help="Only display accounts with a given status")
  argparser.add_argument('--mentions', action='store_true',
    help="Scrape replies that mention user instead of replies from user")
  argparser.add_argument('--datadir', type=str,
    help="Directory containing cached data")
  argparser.set_defaults(mentions=False, datadir='./')

  argparser.add_argument('username')

  args = argparser.parse_args()

  # Execute scrape with provided arguments
  scraper = ScrapeRepliedUsers(args.datadir)

  try:
    scraper.scrapeRepliedUsers(
      args.username, args.until, args.limit, args.status, args.mentions)
  except KeyboardInterrupt:
    print('Keyboard interrupt')
    try:
      sys.exit(0)
    except SystemExit:
      os._exit(0)
