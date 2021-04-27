#!/usr/bin/python
#
# OnlyFans Profile Downloader/Archiver
# KORNHOLIO 2020
#
# See README for help/info.
#
# This program is Free Software, licensed under the
# terms of GPLv3. See LICENSE.txt for details.

import re
import os
import sys
import json
import shutil
import requests
import time
import datetime as dt

# Initialize variables (Purely cosmetic to stop linters from throwing errors)
POST_LIMIT = ""
URL = ""
API_URL = ""
APP_TOKEN = ""
USER_INFO = {}
PROFILE = ""
PROFILE_INFO = {}
PROFILE_ID = ""
API_HEADER = {}
ACCESS_TOKEN = ""

# move dynamic data out of the __main__
# config.json template added to git and gitignored.
def parsed_config(filename):
    with open(f"{filename}",'r') as f:
        return json.load(f)

# helper function to make sure a dir is present
def assure_dir(path):
    if not os.path.isdir(path):
        os.mkdir(path)

# API request convenience function
# getdata and postdata should both be JSON
def api_request(endpoint, getdata = None, postdata = None):
    getparams = {
        "app-token": APP_TOKEN
    }
    if getdata is not None:
        for i in getdata:
            getparams[i] = getdata[i]

    if postdata is None:
        if getdata is not None:
            # Fixed the issue with the maximum limit of 100 posts by creating a kind of "pagination"

            list_base = requests.get(URL + API_URL + endpoint,
                        headers=API_HEADER,
                        params=getparams).json()
            posts_num = len(list_base)

            if posts_num >= 100:
                beforePublishTime = list_base[99]['postedAtPrecise']
                getparams['beforePublishTime'] = beforePublishTime

                while posts_num == 100:
                    # Extract posts
                    list_extend = requests.get(URL + API_URL + endpoint,
                                    headers=API_HEADER,
                                    params=getparams).json()
                    posts_num = len(list_extend)
                    
                    if posts_num < 100:
                        break

                    if posts_num < 100:
                        break
                        
                    # Re-add again the updated beforePublishTime/postedAtPrecise params
                    beforePublishTime = list_extend[posts_num-1]['postedAtPrecise']
                    getparams['beforePublishTime'] = beforePublishTime
                    # Merge with previous posts
                    list_base.extend(list_extend)

            return list_base
        else:
            return requests.get(URL + API_URL + endpoint,
                            headers=API_HEADER,
                            params=getparams)
    else:
        return requests.post(URL + API_URL + endpoint + "?app-token=" + APP_TOKEN,
                             headers=API_HEADER,
                             params=getparams,
                             data=postdata)

# /users/<profile>
# get information about <profile>
# <profile> = "customer" -> info about yourself
def get_user_info(profile):
    info = api_request("/users/" + profile).json()
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

    # Parses json to variables
    # Ignore linters that claim variables are undefined
    config = parsed_config("config.json")
    for i in config.keys():
        globals()[i] = config[i]
    
    #print(f"{POST_LIMIT}\n{URL}\n{API_URL}\n{APP_TOKEN}\n{USER_INFO}\n{PROFILE}\n{PROFILE_INFO}\n{PROFILE_ID}\n{API_HEADER}\n{ACCESS_TOKEN}")
    if ACCESS_TOKEN == "put-token-here" or not ACCESS_TOKEN:
        
        print("Make sure you configure config.json")
        print("Usage: ./onlyfans-dl <profile>")
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
    
    API_HEADER["Cookie"] = "sess=" + ACCESS_TOKEN

    print("Getting user auth info... ")

    USER_INFO = get_user_info("me")
    API_HEADER["user-id"] = str(USER_INFO["id"])

    print("Getting target profile info...")
    PROFILE = sys.argv[1]
    PROFILE_INFO = get_user_info(PROFILE)
    PROFILE_ID = str(PROFILE_INFO["id"])

    print("\nonlyfans-dl is downloading content to profiles/" + PROFILE + "!\n")

    if os.path.isdir("profiles/" + PROFILE):
        print(f"\nThe profile {PROFILE} exists.")
        print("Existing files will not be re-downloaded.")

    assure_dir("profiles")
    assure_dir(f"profiles/{PROFILE}")
    assure_dir(f"profiles/{PROFILE}/avatar")
    assure_dir(f"profiles/{PROFILE}/header")
    assure_dir(f"profiles/{PROFILE}/photos")
    assure_dir(f"profiles/{PROFILE}/videos")
    assure_dir(f"profiles/{PROFILE}/archived")
    assure_dir(f"profiles/{PROFILE}/archived/photos")
    assure_dir(f"profiles/{PROFILE}/archived/videos")

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
    photo_posts = api_request("/users/" + PROFILE_ID + "/posts/photos", getdata={"limit": POST_LIMIT})
    print("Found " + str(len(photo_posts)) + " photos.")
    print("Finding videos...", end=' ', flush=True)
    video_posts = api_request("/users/" + PROFILE_ID + "/posts/videos", getdata={"limit": POST_LIMIT})
    print("Found " + str(len(video_posts)) + " videos.")
    print("Finding archived content...", end=' ', flush=True)
    archived_posts = api_request("/users/" + PROFILE_ID + "/posts/archived", getdata={"limit": POST_LIMIT})
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
