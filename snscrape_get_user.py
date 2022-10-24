import os
import sys

import json
import re

import snscrape.modules.twitter as sntwitter

def get_userinfo(screen_name):
  search = sntwitter.TwitterUserScraper(screen_name)
  entity = search._get_entity()

  if entity is None:
    print("No user info found")
    return None

  keys = ["id", "created", "username",
          "followersCount", "statusesCount", "displayname", "location", "link",
          "rawDescription", "profileImageUrl"]

  for key in keys:
    value = entity.__dict__[key]
    if type(value) == str:
      value = re.sub("\s", " ", value)
    print(key+": "+str(value))

  return entity


if __name__ == '__main__':
  username = str(sys.argv[1])
  get_userinfo(username)

