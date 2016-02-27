# -*- coding: utf-8 -*-

import tweepy
import json


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
            print "Just gave ", u.name, "(", u.name, ") follow"

            #tweepy_api.destroy_friendship(u.screen_name)
            #print "On second taught better unfollow"
            exit()

    print 'Saving followers on '+screen_name+'.json'
    with open(screen_name+'.json', 'w+') as outfile:
        json.dump(users_list, outfile, ensure_ascii=False)


if __name__ == '__main__':
    screen_name_to_stalk = "Cintli"
    get_follws_and_befriend_them(screen_name_to_stalk)
