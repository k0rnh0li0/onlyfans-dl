#!/usr/local/bin/python3
#
# OnlyFans Profile Downloader/Archiver
# KORNHOLIO 2020
#
# See README for help/info.
#
# This program is Free Software, licensed under the
# terms of GPLv3. See LICENSE.txt for details.
import copy
import re
import os
import sys
import json
import shutil
import requests
import time
import datetime as dt
from urllib.parse import urlencode, urlparse
import hashlib
from requests import sessions


# BEGIN USER CONFIG
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:88.0) Gecko/20100101 Firefox/88.0"  # Get from browser
AUTH_ID = 12345678                              # Get 'auth_id' from browser cookies
AUTH_HASH = 'd3bfec9ef74682966e864d371e997ad4'  # Get 'auth_hash' from browser cookies
# END USER CONFIG


# maximum number of posts to index
# DON'T CHANGE THIS
POST_LIMIT = "100"

# api info
URL = "https://onlyfans.com"
API_URL = "/api2/v2"

# TODO dynamically get app token
# Note: this is not an auth token
APP_TOKEN = "33d57ade8c02dbc5a333db99ff9ae26a"

# user info from /users/customer
USER_INFO = {}

# target profile
PROFILE = ""
# profile data from /users/<profile>
PROFILE_INFO = {}
PROFILE_ID = ""

API_HEADER = {
    "user-id": f"{AUTH_ID}",
    "Accept": "application/json, text/plain, */*",
    "User-Agent": USER_AGENT,
    "Accept-Encoding": "gzip, deflate"
}


def create_signed_headers(link: str):
    # Users: 300000 | Creators: 301000
    auth_id = API_HEADER['user-id']
    time2 = str(int(round(time.time())))
    # time2 = str(1620203709)
    path = urlparse(link).path
    query = urlparse(link).query
    path = path if not query else f"{path}?{query}"
    static_param = "rhtNVxJh2LD3Jul5MhHcAAnFMysnLlct"
    a = [static_param, time2, path, auth_id]
    msg = "\n".join(a)
    # print(f'CREATING SIGNED HEADER: msg={msg}')
    message = msg.encode("utf-8")
    hash_object = hashlib.sha1(message)
    sha_1_sign = hash_object.hexdigest()
    sha_1_b = sha_1_sign.encode("ascii")
    checksum = sum([sha_1_b[31], sha_1_b[13], sha_1_b[8], sha_1_b[3], sha_1_b[25], sha_1_b[8], sha_1_b[33], sha_1_b[25], sha_1_b[1], sha_1_b[23], sha_1_b[37], sha_1_b[11], sha_1_b[2], sha_1_b[29], sha_1_b[9], sha_1_b[7],
                    sha_1_b[29], sha_1_b[30], sha_1_b[18], sha_1_b[25], sha_1_b[18], sha_1_b[21], sha_1_b[10], sha_1_b[37],
                    sha_1_b[28], sha_1_b[35], sha_1_b[31], sha_1_b[5],
                    sha_1_b[13], sha_1_b[31], sha_1_b[2], sha_1_b[9]]) + 1110
    headers = copy.copy(API_HEADER)
    headers["sign"] = "6:{}:{:x}:609184ae".format(
        sha_1_sign, abs(checksum))
    headers["time"] = time2
    headers['referer'] = link
    return headers


# helper function to make sure a dir is present
def assure_dir(path):
    if not os.path.isdir(path):
        os.mkdir(path)


def build_url(endpoint, getparams):
    link = URL + API_URL + endpoint
    if getparams:
        link += f'?{urlencode(getparams)}'
    return link


def do_request(method, link, session, postdata=None):
    request_header = create_signed_headers(link)
    # print(f'LINK={link}, headers={request_header}, cookies={session.cookies} postdata={postdata}')

    return session.request(method=method,
                           url=link,
                           # stream=False,
                           # timeout=20,
                           headers=request_header,
                           data=postdata)


# API request convenience function
# getdata and postdata should both be JSON
def api_request(endpoint, session, getdata = None, postdata = None):
    getparams = {
        "app-token": APP_TOKEN
    }
    if getdata is not None:
        for i in getdata:
            getparams[i] = getdata[i]

    link = build_url(endpoint, getparams)

    if postdata is None:
        if getdata is not None:
            # Fixed the issue with the maximum limit of 100 posts by creating a kind of "pagination"

            list_base = do_request('GET', link, session).json()
            posts_num = len(list_base)

            if posts_num >= 100:
                beforePublishTime = list_base[99]['postedAtPrecise']
                getparams['beforePublishTime'] = beforePublishTime
                link = build_url(endpoint, getparams)

                while posts_num == 100:
                    # Extract posts
                    list_extend = do_request('GET', link, session).json()
                    posts_num = len(list_extend)
                    
                    if posts_num < 100:
                        break

                    # Re-add again the updated beforePublishTime/postedAtPrecise params
                    beforePublishTime = list_extend[posts_num-1]['postedAtPrecise']
                    getparams['beforePublishTime'] = beforePublishTime
                    link = build_url(endpoint, getparams)
                    # Merge with previous posts
                    list_base.extend(list_extend)

            return list_base
        else:
            return do_request('GET', link, session)
    else:
        return do_request('POST', link, session, postdata=postdata)


# /users/<profile>
# get information about <profile>
# <profile> = "customer" -> info about yourself
def get_user_info(profile, session):
    info = api_request("/users/" + profile, session).json()
    # print(f'RESPONSE: {info}')
    if "error" in info:
        print("\nERROR: " + info["error"]["message"])
        # bail, we need info for both profiles to be correct
        exit()
    return info


# download public files like avatar and header
new_files=0
def download_public_files():
    public_files = ["avatar", "header"]
    for public_file in public_files:
        source = PROFILE_INFO[public_file]
        if source is None:
            continue
        id = get_id_from_path(source)
        file_type = re.findall("\.\w+", source)[-1]
        path = "/" + public_file + "/" + id + file_type
        if not os.path.isfile("profiles/" + PROFILE + path):
            print("Downloading " + public_file + "...")
            download_file(PROFILE_INFO[public_file], path)
            global new_files
            new_files += 1


# download a media item and save it to the relevant directory
def download_media(media, is_archived):
    id = str(media["id"])
    source = media["source"]["source"]

    if (media["type"] != "photo" and media["type"] != "video") or not media['canView']:
        return

    # find extension
    ext = re.findall('\.\w+\?', source)
    if len(ext) == 0:
        return
    ext = ext[0][:-1]

    if is_archived:
        path = "/archived/" + media["type"] + "s/" + id + ext
    else:
        path = "/" + media["type"] + "s/" + id + ext
    if not os.path.isfile("profiles/" + PROFILE + path):
        # print(path)
        global new_files
        new_files += 1
        download_file(source, path)


# helper to generally download files
def download_file(source, path):
    r = requests.get(source, stream=True)
    with open("profiles/" + PROFILE + path, 'wb') as f:
        r.raw.decode_content = True
        shutil.copyfileobj(r.raw, f)


def get_id_from_path(path):
    last_index = path.rfind("/")
    second_last_index = path.rfind("/", 0, last_index - 1)
    id = path[second_last_index+1:last_index]
    return id


def calc_process_time(starttime, arraykey, arraylength):
    timeelapsed = time.time() - starttime
    timeest = (timeelapsed/arraykey)*(arraylength)
    finishtime = starttime + timeest
    finishtime = dt.datetime.fromtimestamp(finishtime).strftime("%H:%M:%S")  # in time
    lefttime = dt.timedelta(seconds=(int(timeest-timeelapsed)))  # get a nicer looking timestamp this way
    timeelapseddelta = dt.timedelta(seconds=(int(timeelapsed))) # same here
    return (timeelapseddelta, lefttime, finishtime)


# iterate over posts, downloading all media
# returns the new count of downloaded posts
def download_posts(cur_count, posts, is_archived):
    for k, post in enumerate(posts, start=1):
        if not post["canViewMedia"]:
            continue

        for media in post["media"]:
            if 'source' in media:
                download_media(media, is_archived)

        # adding some nice info in here for download stats
        timestats = calc_process_time(starttime, k, total_count)
        dwnld_stats = f"{cur_count}/{total_count} {round(((cur_count / total_count) * 100))}% " + \
                      "Time elapsed: %s, Estimated Time left: %s, Estimated finish time: %s" % timestats
        end = '\n' if cur_count == total_count else '\r'
        print(dwnld_stats, end=end)
        
        cur_count = cur_count + 1

    return cur_count


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: ./onlyfans-dl <profile> <accessToken>")
        print("See README for instructions.")
        exit()

    print("\n~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
    print("~ I AM THE GREAT KORNHOLIO ~")
    print("~  ARE U THREATENING ME??  ~")
    print("~                          ~")
    print("~    COOMERS GUNNA COOM    ~")
    print("~    HACKERS GUNNA HACK    ~")
    print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~\n")

    # check the access token, pull user info
    API_HEADER["app-token"] = APP_TOKEN
    API_HEADER["x-bc"] = ''

    auth_id = API_HEADER['user-id']

    cookies = [
        {'name': 'auth_id', 'value': auth_id},
        {'name': 'sess', 'value': sys.argv[2]},
        {'name': 'auth_hash', 'value': AUTH_HASH},
        {'name': f'auth_uniq_{auth_id}', 'value': ''},
        {'name': f'auth_uid_{auth_id}', 'value': None},
    ]

    print("Getting user auth info... ")

    session = sessions.Session()
    for cookie in cookies:
        session.cookies.set(**cookie)

    USER_INFO = get_user_info("me", session)

    API_HEADER["user-id"] = str(USER_INFO["id"])
    API_HEADER["x-bc"] = ''

    print("Getting target profile info...")
    PROFILE = sys.argv[1]
    PROFILE_INFO = get_user_info(PROFILE, session)
    PROFILE_ID = str(PROFILE_INFO["id"])

    print("\nonlyfans-dl is downloading content to profiles/" + PROFILE + "!\n")

    if os.path.isdir("profiles/" + PROFILE):
        print("\nThe folder profiles/" + PROFILE + " exists.")
        print("Media already present will not be re-downloaded.")

    assure_dir("profiles")
    assure_dir("profiles/" + PROFILE)
    assure_dir("profiles/" + PROFILE + "/avatar")
    assure_dir("profiles/" + PROFILE + "/header")
    assure_dir("profiles/" + PROFILE + "/photos")
    assure_dir("profiles/" + PROFILE + "/videos")
    assure_dir("profiles/" + PROFILE + "/archived")
    assure_dir("profiles/" + PROFILE + "/archived/photos")
    assure_dir("profiles/" + PROFILE + "/archived/videos")

    # first save profile info
    print("Saving profile info...")

    sinf = {
        "id": PROFILE_INFO["id"],
        "name": PROFILE_INFO["name"],
        "username": PROFILE_INFO["username"],
        "about": PROFILE_INFO["rawAbout"],
        "joinDate": PROFILE_INFO["joinDate"],
        "website": PROFILE_INFO["website"],
        "wishlist": PROFILE_INFO["wishlist"],
        "location": PROFILE_INFO["location"],
        "lastSeen": PROFILE_INFO["lastSeen"]
    }

    with open("profiles/" + PROFILE + "/info.json", 'w') as infojson:
        json.dump(sinf, infojson)

    download_public_files()

    # get all user posts
    print("Finding photos...", end=' ', flush=True)
    photo_posts = api_request("/users/" + PROFILE_ID + "/posts/photos", session, getdata={"limit": POST_LIMIT})
    # print(f'RESPONSE: {photo_posts}')
    print("Found " + str(len(photo_posts)) + " photos.")
    print("Finding videos...", end=' ', flush=True)
    video_posts = api_request("/users/" + PROFILE_ID + "/posts/videos", session, getdata={"limit": POST_LIMIT})
    # print(f'RESPONSE: {video_posts}')
    print("Found " + str(len(video_posts)) + " videos.")
    print("Finding archived content...", end=' ', flush=True)
    archived_posts = api_request("/users/" + PROFILE_ID + "/posts/archived", session, getdata={"limit": POST_LIMIT})
    # print(f'RESPONSE: {archived_posts}')
    print("Found " + str(len(archived_posts)) + " archived posts.")
    postcount = len(photo_posts) + len(video_posts)
    archived_postcount = len(archived_posts)
    if postcount + archived_postcount == 0:
        print("ERROR: 0 posts found.")
        exit()

    total_count = postcount + archived_postcount

    print("Found " + str(total_count) + " posts. Downloading media...")

    # get start time for estimation purposes
    starttime = time.time()

    cur_count = download_posts(1, photo_posts, False)
    cur_count = download_posts(cur_count, video_posts, False)
    download_posts(cur_count, archived_posts, True)

    print("Downloaded " + str(new_files) + " new files.")
