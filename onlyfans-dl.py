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

# maximum number of posts to index
# DONT CHANGE THAT
POST_LIMIT = "100"

# api info
URL = "https://onlyfans.com"
API_URL = "/api2/v2"

#\TODO dynamically get app token
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
    "Accept": "application/json, text/plain, */*",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36",
    "Accept-Encoding": "gzip, deflate"
}

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

                    # Re-add again the updated beforePublishTime/postedAtPrecise params
                    beforePublishTime = list_extend[posts_num-1]['postedAtPrecise']
                    getparams['beforePublishTime'] = beforePublishTime
                    # Merge with previous posts
                    list_base.extend(list_extend)

                    if posts_num < 100:
                        break
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

# download a media item and save it to the relevant directory
new_files=0
def download_media(media):
    id = str(media["id"])
    source = media["source"]["source"]

    if (media["type"] != "photo" and media["type"] != "video") or not media['canView']::
        return

    # find extension
    ext = re.findall('\.\w+\?', source)
    if len(ext) == 0:
        return
    ext = ext[0][:-1]

    path = "/" + media["type"] + "s/" + id + ext
    if not os.path.isfile("profiles/" + PROFILE + path):
        print(path)
        global new_files
        new_files += 1
        r = requests.get(source, stream=True)
        with open("profiles/" + PROFILE + path, 'wb') as f:
            r.raw.decode_content = True
            shutil.copyfileobj(r.raw, f)

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
    API_HEADER["access-token"] = sys.argv[2]
    print("Getting user auth info... ")

    USER_INFO = get_user_info("customer")
    API_HEADER["user-id"] = str(USER_INFO["id"])

    print("Getting target profile info...")
    PROFILE = sys.argv[1]
    PROFILE_INFO = get_user_info(PROFILE)
    PROFILE_ID = str(PROFILE_INFO["id"])

    print("\nonlyfans-dl is downloading content to profiles/" + PROFILE + "!\n")

    if not os.path.isdir("profiles"):
        os.mkdir("profiles")

    if os.path.isdir("profiles/" + PROFILE):
        print("\nProfiles/" + PROFILE + " exists.")
        print("Media already present will not be re-downloaded.")
    else:
        os.mkdir("profiles/" + PROFILE)
        os.mkdir("profiles/" + PROFILE + "/photos")
        os.mkdir("profiles/" + PROFILE + "/videos")

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

    # get all paid posts
    print("Finding paid posts...")

    posts = api_request("/posts/paid", getdata={"limit": 10}) # idk they limit it to 10 whatever...
    if len(posts) == 0:
        print("No paid posts found, give this girl some money :D")
    else:
        print("Found " + str(len(posts)) + " paid posts. Downloading media...")
        # note that we dont need to check for viewable media here
        for post in posts:
            for media in post["media"]:
                if 'source' in media:
            	    download_media(media)

    # get all user posts
    print("Finding posts...")
    posts = api_request("/users/" + PROFILE_ID + "/posts", getdata={"limit": POST_LIMIT})
    if len(posts) == 0:
        print("ERROR: 0 posts found.")
        exit()

    print("Found " + str(len(posts)) + " posts. Downloading media...")

    # iterate over posts, downloading all media
    for post in posts:
        if not post["canViewMedia"]:
            continue

        for media in post["media"]:
            if 'source' in media:
            	download_media(media)
    print("Downloaded " + str(new_files) + " new files.")
