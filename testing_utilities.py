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


def open_json(file_name):
    filee = open(file_name)
    jsonn = filee.read()
    filee.close()
    json_list = json.loads(jsonn)
    return json_list


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


def give_follow(usr):
    if usr['followed_by'] or usr['following']:
        return False
    elif usr['omit']:
        return False
    else:
        return True


def give_unfollow(usr, days_to_wait):
    if usr['following']:
        if not usr['followed_by']:
            date_format = "%Y-%m-%d"
            try:
                s = usr['date_followed']
                d = datetime.datetime.strptime(s, date_format) + datetime.timedelta(days=days_to_wait)
            except ValueError:
                s = usr['date_retrieved']
                d = datetime.datetime.strptime(s, date_format) + datetime.timedelta(days=days_to_wait)
            if d.date() < datetime.date.today():
                return True
    elif usr['omit']:
        return False
    else:
        return False


def get_account_followers_and_initialize_data(scrname_to_stalk):
    tokens_list = open_json('Tokens.json')
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
    print "He/She has " + str(user_to_stalk.followers_count) + " followers."
    # print user.friends_count

    followers_list = []
    for page in tweepy.Cursor(tweepy_api.followers,
                              screen_name=scrname_to_stalk).pages():
        usr = {}
        for u in page:
            usr['screen_name'] = u.screen_name
            usr['name'] = u.name
            usr['date_retrieved'] = str(datetime.date.today())
            usr['date_followed'] = ''

            friendship = tweepy_api.show_friendship(
                source_screen_name=me.screen_name,
                target_screen_name=u.screen_name)
            usr['followed_by'] = friendship[0].followed_by
            usr['following'] = friendship[0].following
            usr['omit'] = False

            followers_list.append(usr.copy())

    directory = 'Data_'+scrname_to_stalk
    file_name = directory+'/'+scrname_to_stalk+'_followers.json'
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

    print 'Saving followers on ' + file_name
    with open(file_name, 'w+') as outfile:
        json.dump(followers_list, outfile, ensure_ascii=False)


def follow_users(scrname_to_stalk, follows_limit):
    tokens_list = open_json('Tokens.json')
    tweepy_api = create_tweepy_object(tokens_list[0])
    try:
        me = tweepy_api.verify_credentials()
    except False:
        print "Wrong credentials"
        exit()
    print "I'm ", me.name, "(", me.screen_name, ")"

    print "I'll follow ", scrname_to_stalk, " followers."

    directory = 'Data_'+scrname_to_stalk
    file_name = directory+'/'+scrname_to_stalk+'_followers.json'
    try:
        users_list = open_json(file_name)
    except IOError:
        print 'File ' + file_name + ' not found.'
        print 'You have to run with --init argument first.'
        exit()
    follow_count = 0
    for usr in users_list:
        if give_follow(usr):
            try:
                tweepy_api.create_friendship(usr['screen_name'])
                print "Just gave ", usr['screen_name'], "(", usr['name'], ") follow."
                follow_count += 1
                usr['following'] = True
                usr['date_followed'] = str(datetime.date.today())
            except tweepy.error.TweepError as e:
                print e
                usr['omit'] = True
        if follow_count == follows_limit:
            break
    print "Updating the followers file."
    with open(file_name, 'w+') as outfile:
        json.dump(users_list, outfile, ensure_ascii=False)


def unfollow_users(scrname_to_stalk, days_to_wait):
    tokens_list = open_json('Tokens.json')
    tweepy_api = create_tweepy_object(tokens_list[0])
    try:
        me = tweepy_api.verify_credentials()
    except False:
        print "Wrong credentials"
        exit()
    print "I'm ", me.name, "(", me.screen_name, ")"

    print "I'll unfollow ", scrname_to_stalk, " followers that haven't follow me back =(."

    directory = 'Data_'+scrname_to_stalk
    file_name = directory+'/'+scrname_to_stalk+'_followers.json'
    try:
        users_list = open_json(file_name)
    except IOError:
        print 'File ' + file_name + ' not found.'
        print 'You have to run with --init argument first.'
        exit()

    for usr in users_list:
        if give_unfollow(usr, days_to_wait):
            try:
                tweepy_api.destroy_friendship(usr['screen_name'])
                print "Just gave ", usr['screen_name'], "(", usr['name'], ") unfollow."

            except tweepy.error.TweepError as e:
                print e

            usr['following'] = False
            usr['omit'] = True

    print "Updating the followers file."
    with open(file_name, 'w+') as outfile:
        json.dump(users_list, outfile, ensure_ascii=False)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
    description = """A twitter follower and unfollower app.
                It's meant to run three distinct routines:
                --init, --follow and -- unfollow.""")

    parser.add_argument('-s', '--screen_name',
                        help='User screen name',
                        # action='store_true',
                        # default=False,
                        required=True)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--init',
                        help='Initial run to get an accounts follwers.',
                        action='store_true',
                        default=False,
                        required=False)
    group.add_argument('--follow',
                        help='Run the following routine.',
                        action='store_true',
                        default=False,
                        required=False)
    parser.add_argument('-l', '--follows_limit',
                        help='How many follows to give in one run.',
                        # action='store_true',
                        default=500)
    group.add_argument('--unfollow',
                        help='Run the unfollowing routine.',
                        action='store_true',
                        default=False,
                        required=False)
    parser.add_argument('-d', '--days_to_wait',
                        help='Days to wait before unfollowing someone who did not follow back.',
                        # action='store_true',
                        default=10)
    args = parser.parse_args()
    screen_name_to_stalk = args.screen_name
    follows_limit = int(args.follows_limit)
    days_to_wait = int(args.days_to_wait)

    if args.init:
        get_account_followers_and_initialize_data(screen_name_to_stalk)

    if args.follow:
        follow_users(screen_name_to_stalk, follows_limit)

    if args.unfollow:
        unfollow_users(screen_name_to_stalk, days_to_wait)
