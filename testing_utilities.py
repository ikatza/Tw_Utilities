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


# def get_tokens():
#     tokens_file = open('Tokens.json')
#     tokens_json = tokens_file.read()
#     tokens_file.close()
#     tokens_list = json.loads(tokens_json)
#     return tokens_list


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


def roll_tokens(tokens_f, resource):
    tokens_list = open_json(tokens_f)
    for tokens in tokens_list:
        tweepy_api = create_tweepy_object(tokens)
        limits = twitter_remaining_calls(tweepy_api)
        remaining_lookup = limits[resource]['remaining']
        if remaining_lookup > 0:
            break
    return tweepy_api

def give_follow(usr):
    if not usr['date_retrieved']:
        return False
    if usr['followed_by'] or usr['following']:
        return False
    elif usr['omit']:
        return False
    else:
        return True


def give_unfollow(usr, days_to_wait):
    if not usr['date_retrieved']:
        return False
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


def twitter_remaining_calls(twitter):
    limits = twitter.rate_limit_status(resources='friendships,followers')
    # limits = twitter.rate_limit_status()

    response = {
        'Followers': limits['resources']['followers']['/followers/ids'],
        'Friendships_show': limits['resources']['friendships']['/friendships/show'],
        'Friendships_lookup': limits['resources']['friendships']['/friendships/lookup']
        }

    return response


def get_user(usr_identifier):
    # usr_identifier is ID or screen_name
    tokens_list = open_json('Tokens_auth.json')
    tweepy_api = create_tweepy_object(tokens_list[0])
    isint = False
    try:
        isint = usr_identifier.isdigit()
    except AttributeError:
        isint = (int == type(usr_identifier))
    if isint:
        usr = tweepy_api.get_user(user_id=int(usr_identifier))
    else:
        usr = tweepy_api.get_user(screen_name=usr_identifier)
    return usr


def get_account_followers(scrname_to_stalk):
    tokens_list = open_json('Tokens_auth.json')
    tweepy_api = create_tweepy_object(tokens_list[0])

    # tokens_list_app = open_json('Tokens_app.json')
    # tweepy_api_app = create_tweepy_object(tokens_list_app[0])

    try:
        me = tweepy_api.verify_credentials()
    except False:
        print "Wrong credentials"
        exit()
    print "I'm ", me.name, "(", me.screen_name, ")"

    # print tweepy_api.me()

    print "I'll get ", scrname_to_stalk, " followers list."
    user_to_stalk = tweepy_api.get_user(screen_name=scrname_to_stalk)
    print "He/She has " + str(user_to_stalk.followers_count) + " followers.\n"
    # print user.friends_count

    directory = 'Data_'+scrname_to_stalk
    file_name = directory+'/'+scrname_to_stalk+'_followers.json'
    try:
        os.makedirs(directory)
    except OSError:
        if not os.path.isdir(directory):
            raise

    followers_list = []
    # for page in tweepy.Cursor(tweepy_api.followers,
    #                           screen_name=scrname_to_stalk).pages():
    for page in tweepy.Cursor(tweepy_api.followers_ids,
                              screen_name=scrname_to_stalk).pages():

        usr = {}
        for u in page:
            # usr['screen_name'] = u.screen_name
            # usr['name'] = u.name

            # usr['id'] = u
            # usr['date_retrieved'] = str(datetime.date.today())
            # usr['date_followed'] = ''
            # friendship = tweepy_api.show_friendship(
            #     # source_screen_name=me.screen_name,
            #     # target_screen_name=u.screen_name)
            #     source_id=me.id,
            #     target_id=usr['id'])
            # usr['followed_by'] = friendship[0].followed_by
            # usr['following'] = friendship[0].following
            # usr['omit'] = False

            usr['id'] = u
            usr['date_retrieved'] = ''
            usr['date_followed'] = ''
            usr['followed_by'] = ''
            usr['following'] = ''
            usr['omit'] = False

            followers_list.append(usr.copy())

        print 'Saving followers on ' + file_name
        with open(file_name, 'w+') as outfile:
            json.dump(followers_list, outfile, ensure_ascii=False)

    if len(followers_list) != user_to_stalk.followers_count:
        print "Warning! \n",
        "The number of reported and retrieved followers don't match."
        print "Reported followers: ", str(user_to_stalk.followers_count)
        print "Retrieved followers: ", str(len(followers_list))


def get_friendship_status(scrname_to_stalk, pickup=False):
    # tokens_list = open_json('Tokens_auth.json')
    # for tokens in tokens_list:
    #     tweepy_api = create_tweepy_object(tokens)
    #     limits = twitter_remaining_calls(tweepy_api)
    #     remaining_lookup = limits['Friendships_lookup']['remaining']
    tokens_f = 'Tokens_auth.json'
    resource = 'Friendships_lookup'

    print "Now I'll get the friendship status that ", scrname_to_stalk, " followers have with me.\n"

    directory = 'Data_'+scrname_to_stalk
    file_name = directory+'/'+scrname_to_stalk+'_followers.json'
    try:
        users_list = open_json(file_name)
    except IOError:
        print 'File ' + file_name + ' not found.'
        # print 'You have to run with --init argument first.'
        exit()

    lookup_limit = 100
    warningg = False
    start = 0
    if pickup:
        for idx, usr in enumerate(users_list):
            if not usr['date_retrieved']:
                start = idx
                break
        print "Picking up at index, ", idx, "of the followers list.\n"
    # chunks=[users_list[x:x+lookup_limit] for x in xrange(0, len(users_list), lookup_limit)]
    for i in range(start, len(users_list), lookup_limit):
        chunk = users_list[i:i + lookup_limit]
        ids_in_chunk = [chunk[j]['id'] for j in xrange(0, len(chunk))]
        tweepy_api = roll_tokens(tokens_f, resource)
        relationships = tweepy_api.lookup_friendships(user_ids=ids_in_chunk)
        for idx, relationship in enumerate(relationships):
            ### ###  debugging stuff, will remove in a later commit
            # print "i ", i
            # print "idx ", idx
            # print "i+idx ", i+idx
            if users_list[i+idx]['id'] == relationship.id:
                users_list[i+idx]['followed_by'] = relationship.is_followed_by
                users_list[i+idx]['following'] = relationship.is_following
                users_list[i+idx]['date_retrieved'] = str(datetime.date.today())
            else:
                warningg = True
        print "Updating the followers file."
        with open(file_name, 'w+') as outfile:
            json.dump(users_list, outfile, ensure_ascii=False)

    if warningg:
        print "Warning!.\n"
        print "Something odd happened in the get_friendship_status routine."
        exit()

    ### ### NO LONGER USING THIS CALL, MAYBE SOME DAY WITH THREADING?
    # friendship = tweepy_api.show_friendship(
    #     # source_screen_name=me.screen_name,
    #     # target_screen_name=u.screen_name)
    #     source_id=me.id,
    #     target_id=usr['id'])


def follow_users(scrname_to_stalk, follows_limit, verbose=False):
    tokens_list = open_json('Tokens_auth.json')
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
                # tweepy_api.create_friendship(usr['screen_name'])
                # print "Just gave ", usr['screen_name'], "(", usr['name'], ") follow."
                tweepy_api.create_friendship(usr['id'])
                if verbose:
                    u = get_user(usr['id'])
                    print "Just gave ", u.screen_name, "(", u.name, ") follow."
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


def unfollow_users(scrname_to_stalk, days_to_wait, verbose=False):
    tokens_list = open_json('Tokens_auth.json')
    tweepy_api = create_tweepy_object(tokens_list[0])
    try:
        me = tweepy_api.verify_credentials()
    except False:
        print "Wrong credentials"
        exit()
    print "I'm ", me.name, "(", me.screen_name, ")"

    print "I'll unfollow ", scrname_to_stalk, " followers that haven't follow me back =(."
    print "They had ", days_to_wait, " days to follow me."

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
                # tweepy_api.destroy_friendship(usr['screen_name'])
                # print "Just gave ", usr['screen_name'], "(", usr['name'], ") unfollow."
                tweepy_api.destroy_friendship(usr['id'])
                if verbose:
                    u = get_user(usr['id'])
                    print "Just gave ", u.screen_name, "(", u.name, ") unfollow."

            except tweepy.error.TweepError as e:
                print e

            usr['following'] = False
            usr['omit'] = True

    print "Updating the followers file."
    with open(file_name, 'w+') as outfile:
        json.dump(users_list, outfile, ensure_ascii=False)


if __name__ == '__main__':

    # tokens_list = open_json('Tokens_auth.json')
    # tweepy_api = create_tweepy_object(tokens_list[0])
    # resource = 'friendship'
    # limits = twitter_remaining_calls(tweepy_api)
    # print limits
    # print limits['Friendships_lookup']['remaining']

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
    group.add_argument('--friendship',
                        help='Pick up where friendship status left..',
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
    group.add_argument('--user',
                        help='Get user info.',
                        action='store_true',
                        default=False,
                        required=False)
    parser.add_argument('-u', '--user_id',
                        help='An user ID.',
                        # action='store_true',
                        default=10)
    parser.add_argument('-v', '--verbose',
                        help='Be verbose with the output',
                        action='store_true',
                        default=False,
                        required=False)
    args = parser.parse_args()
    screen_name_to_stalk = args.screen_name
    follows_limit = int(args.follows_limit)
    days_to_wait = int(args.days_to_wait)
    usr_id = args.user_id
    verbose = args.verbose

    if args.init:
        get_account_followers(screen_name_to_stalk)
        get_friendship_status(screen_name_to_stalk)
    if args.friendship:
        get_friendship_status(screen_name_to_stalk, pickup=True)
    if args.follow:
        if verbose:
            print "Asking to be verbose."
            print "Keep in mind it requires more calls to the API and might increase the waiting time.\n"
        follow_users(screen_name_to_stalk, follows_limit, verbose)

    if args.unfollow:
        if verbose:
            print "Asking to be verbose."
            print "Keep in mind it requires more calls to the API and might increase the waiting time.\n"
        unfollow_users(screen_name_to_stalk, days_to_wait, verbose)

    if args.user:
        usr = get_user(usr_id)
        if verbose:
            print usr
        else:
            print "User ID: ", usr.id
            print "User screen_name: ", usr.screen_name
            print "User name: ", usr.name
