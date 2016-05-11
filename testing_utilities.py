# -*- coding: utf-8 -*-

import os
import sys
reload(sys)
sys.setdefaultencoding("utf-8")
import tweepy
import json
import argparse
import datetime
import unidecode
import unicodedata

def get_tokens():
    tokens_file = open('Tokens.json')
    tokens_json = tokens_file.read()
    tokens_file.close()
    tokens_list = json.loads(tokens_json)
    return tokens_list


def create_tweepy_object(tokens):
    try:
        auth = tweepy.OAuthHandler(tokens['Key'], tokens['Secret'])
        auth.set_access_token(tokens['Token'], tokens['TokenSecret'])
        tweepy_api = tweepy.API(auth, wait_on_rate_limit=True,
                                wait_on_rate_limit_notify=True)
    except KeyError:
        auth = tweepy.AppAuthHandler(tokens['Key'], tokens['Secret'])
        tweepy_api = tweepy.API(auth, wait_on_rate_limit=True,
                                wait_on_rate_limit_notify=True)
    return tweepy_api


# def twitter_remaining_calls(twitter):
#     limits = twitter.rate_limit_status(resources='friends,followers')

#     response = {
#         # 'Followers': limits['resources']['followers']['/followers/ids'],
#         # 'Friends': limits['resources']['friends']['/friends/ids']}
#         'Followers': limits['resources']['followers']['/followers/list'],
#         'Friends': limits['resources']['friends']['/friends/list']}

#     return response


def get_account_followers(scrname_to_stalk):
    tokens_list = get_tokens()
    tweepy_api = create_tweepy_object(tokens_list[0])
    # user = tweepy_api.get_user(screen_name=screen_name)
    try:
        me = tweepy_api.verify_credentials()
    except False:
        print "Wrong credentials"
        exit()
    print "I'm ", me.name, "(", me.screen_name, ")"
    # print tweepy_api.me()

    print "I'll get ", scrname_to_stalk, " followers list."
    user_to_stalk = tweepy_api.get_user(screen_name=scrname_to_stalk)
    print "He/She has "+str(user_to_stalk.followers_count)+ " followers."
    # print user.friends_count

    followers_list = []
    for page in tweepy.Cursor(tweepy_api.followers,
                              screen_name=scrname_to_stalk).pages():
        usr = {}
        for u in page:
            usr['screen_name'] = u.screen_name
            usr['name'] = u.name
            usr['data_retrieved'] = str(datetime.date.today())

            ### After to compare:
            # format = "%Y-%m-%d"
            # s = data_retrieved
            # d = datetime.datetime.strptime(s, format) + datetime.timedelta(days=10)
            # if d.date() < datetime.date.today():
            #     unfollow()



            friendship = tweepy_api.show_friendship(source_screen_name=me.screen_name, target_screen_name=u.screen_name)
            usr['followed_by'] = friendship[0].followed_by
            usr['following'] = friendship[0].following

            followers_list.append(usr.copy())

    directory = 'Data_'+scrname_to_stalk
    try:
        os.makedirs(directory)
    except OSError:
        if not os.path.isdir(directory):
            raise
    if len(followers_list) != user_to_stalk.followers_count:
        print "Warning! \n",
        "The number of reported and retrieved followers don't match."
        print "Reported followers: ", str(user_to_stalk.followers_count)
        print "Retrieved followers: ", str(len(followers_list))

    print 'Saving followers on '+directory+'/'+scrname_to_stalk+'_followers.json'
    with open(directory+'/'+scrname_to_stalk+'_followers.json', 'w+') as outfile:
        json.dump(followers_list, outfile, ensure_ascii=False)


def get_follws_and_befriend_them(screen_name):
    tokens_list = get_tokens()
    tweepy_api = create_tweepy_object(tokens_list[0])
    # user = tweepy_api.get_user(screen_name=screen_name)
    try:
        user = tweepy_api.verify_credentials()
    except False:
        print "Wrong credentials"
        exit()
    print "I'm ", user.name, "(", user.screen_name, ")"
    # print tweepy_api.me()
    print "I'll follow ", screen_name, " followers"


    users_list = []
    for page in tweepy.Cursor(tweepy_api.followers,
                              screen_name=screen_name).pages():
        usr = {}
        for u in page:
            usr['screen_name'] = u.screen_name
            usr['name'] = u.name
            # usr['location'] = u.location
            # usr['description'] = u.description
            # usr['image_url'] = u.profile_image_url
            # users_list.append(us.copy())

            tweepy_api.create_friendship(u.screen_name)
            print "Just gave ", u.screen_name, "(", u.name, ") follow"

            #tweepy_api.destroy_friendship(u.screen_name)
            #print "On second taught better unfollow"
            exit()

    print 'Saving followers on '+screen_name+'.json'
    with open(screen_name+'.json', 'w+') as outfile:
        json.dump(users_list, outfile, ensure_ascii=False)


if __name__ == '__main__':

    # screen_name_to_stalk = "Cintli"
    # get_follws_and_befriend_them(screen_name_to_stalk)

    tokens_list = get_tokens()
    tweepy_api = create_tweepy_object(tokens_list[0])
    # screen_name = 'babrielpalacios'
    # screen_name = 'gabyinthewild'
    # try:
    #     tweepy_api.create_friendship(screen_name)
    #     print "Just gave ", screen_name, "(", screen_name, ") follow"
    # except tweepy.error.TweepError as e:
    #     print e

    # print "Out and ok"

    screen_name_to_stalk = "DiegoCorro1"
    get_account_followers(screen_name_to_stalk)
