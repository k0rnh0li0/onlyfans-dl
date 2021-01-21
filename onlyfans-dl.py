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

###########################
# THING YOU CAN CONFIGURE #
###########################

# choose which content types you want to download
DOWNLOAD_POSTS = True
DOWNLOAD_ARCHIVED_POSTS = True
DOWNLOAD_STORIES = True
DOWNLOAD_HIGHLIGHTS = True
DOWNLOAD_MESSAGES = True
DOWNLOAD_PURCHASED = True

# use sub-folders depending on content type, or download everything to /profile/photos and /profile/videos
USE_SUB_FOLDERS = True

# User-Agent can be retrieved from https://www.whatismybrowser.com/detect/what-is-my-user-agent
API_HEADER = {
    "Accept": "application/json, text/plain, */*",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.141 Safari/537.36",
    "Accept-Encoding": "gzip, deflate"
}

########################
# END OF CONFIGURATION #
########################

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

# maximum number of posts to index
# DONT CHANGE THAT
POST_LIMIT = "100"
ARCHIVED_POST_LIMIT = "100"
STORY_LIMIT = "100"
HIGHLIGHT_LIMIT = "100"
MESSAGE_LIMIT = "10"
PURCHASE_LIMIT = "100"

# API request convenience function
# getdata and postdata should both be JSON
def api_request(endpoint, getdata = None, postdata = None):
    getparams = {
        "app-token": APP_TOKEN
    }
    if getdata is not None:
        posts_limit = int(getdata["limit"])
        for i in getdata:
            getparams[i] = getdata[i]

    if postdata is None:
        if getdata is not None:
            # Fixed the issue with the maximum limit of 100 posts by creating a kind of "pagination"

            list_base = requests.get(URL + API_URL + endpoint,
                        headers=API_HEADER,
                        params=getparams).json()
            posts_num = len(list_base)

            if posts_num >= posts_limit:
                beforePublishTime = list_base[posts_limit - 1]['postedAtPrecise']
                getparams['beforePublishTime'] = beforePublishTime

                while posts_num == posts_limit:
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

                    if posts_num < posts_limit:
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

# make sure all folders are already present
def build_folder_structure():
    profile_path = "profiles/" + PROFILE
    if not os.path.isdir(profile_path):
        os.mkdir(profile_path)
        os.mkdir(profile_path + "/photos")
        os.mkdir(profile_path + "/videos")
    if USE_SUB_FOLDERS
        if not os.path.isdir(profile_path + "/archived") and DOWNLOAD_ARCHIVED_POSTS:
            os.mkdir(profile_path + "/archived")
            os.mkdir(profile_path + "/archived" + "/photos")
            os.mkdir(profile_path + "/archived" + "/videos")
        if not os.path.isdir(profile_path + "/stories") and DOWNLOAD_STORIES:
            os.mkdir(profile_path + "/stories")
            os.mkdir(profile_path + "/stories" + "/photos")
            os.mkdir(profile_path + "/stories" + "/videos")
        if not os.path.isdir(profile_path + "/highlights") and DOWNLOAD_HIGHLIGHTS:
            os.mkdir(profile_path + "/highlights")
            os.mkdir(profile_path + "/highlights" + "/photos")
            os.mkdir(profile_path + "/highlights" + "/videos")
        if not os.path.isdir(profile_path + "/messages") and DOWNLOAD_MESSAGES:
            os.mkdir(profile_path + "/messages")
            os.mkdir(profile_path + "/messages" + "/photos")
            os.mkdir(profile_path + "/messages" + "/videos")
        if not os.path.isdir(profile_path + "/purchased") and DOWNLOAD_PURCHASED:
            os.mkdir(profile_path + "/purchased")
            os.mkdir(profile_path + "/purchased" + "/photos")
            os.mkdir(profile_path + "/purchased" + "/videos")


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
def download_media(media, *args):
    id = str(media["id"])
    source = media["source"]["source"]

    if (media["type"] != "photo" and media["type"] != "video") or not media['canView']:
        return

    # find extension
    ext = re.findall('\.\w+\?', source)
    if len(ext) == 0:
        return
    ext = ext[0][:-1]

    path = "/" + media["type"] + "s/" + id + ext
    if len(args) > 0 and USE_SUB_FOLDERS:
        path = "/" + args[0] + path
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

    # check the access token, pull user info
    API_HEADER["access-token"] = sys.argv[2]
    print("Getting user auth info... ")

    USER_INFO = get_user_info("customer")
    API_HEADER["user-id"] = str(USER_INFO["id"])

    print("Getting target profile info...")
    PROFILE = sys.argv[1]
    PROFILE_INFO = get_user_info(PROFILE)
    PROFILE_ID = str(PROFILE_INFO["id"])

    print("\nonlyfans-dl is downloading content to profiles/" + PROFILE + "!")

    if not os.path.isdir("profiles"):
        os.mkdir("profiles")

    if os.path.isdir("profiles/" + PROFILE):
        print("\nProfiles/" + PROFILE + " exists.")
        print("Media already present will not be re-downloaded.")
    else:
        build_folder_structure()

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

    # check folders in-case anything changed    
    build_folder_structure()

    # TODO: Simplify structure. Most of these code blocks are repeated,
    #       with small changes between each function. There should be a way
    #       to create a shell function where we can pass in the parameters
    #       that change for each content type.

    # get all user posts
    if DOWNLOAD_POSTS:
        print("\nFinding posts...")
        posts = api_request("/users/" + PROFILE_ID + "/posts", getdata={"limit": POST_LIMIT})
        if len(posts) == 0:
            print("No posts found.")
        else:
            print("Found " + str(len(posts)) + " posts. Downloading media...")
            # iterate over posts, downloading all media
            for post in posts:
                if not post["canViewMedia"]:
                    continue

                for media in post["media"]:
                    if 'source' in media:
                        download_media(media)
            print("Downloaded " + str(new_files) + " new files.")

    # reset file counter
    post_files = new_files
    new_files = 0

    # get all user archived posts
    if DOWNLOAD_ARCHIVED_POSTS:
        print("\nFinding archived posts...")
        posts = api_request("/users/" + PROFILE_ID + "/posts/archived", getdata={"limit": ARCHIVED_POST_LIMIT})
        if len(posts) == 0:
            print("No archived posts found.")
        else:
            print("Found " + str(len(posts)) + " archived posts. Downloading media...")
            # iterate over posts, downloading all media
            for post in posts:
                if not post["canViewMedia"]:
                    continue

                for media in post["media"]:
                    if 'source' in media:
                        download_media(media, "archived")
            print("Downloaded " + str(new_files) + " new files.")

    # reset file counter
    archived_post_files = new_files
    new_files = 0

    # get all user stories
    if DOWNLOAD_STORIES:
        print("\nFinding stories...")
        posts = api_request("/users/" + PROFILE_ID + "/stories", getdata={"limit": STORY_LIMIT})
        if len(posts) == 0:
            print("No stories found.")
        elif len(posts) == 1 and "error" in posts:
            print("You do not have access to this user's stories.")
        else:
            print("Found " + str(len(posts)) + " stories. Downloading media...")
            # iterate over stories, downloading all media
            for post in posts:
                for media in post["media"]:
                    if 'source' in media:
                        download_media(media, "stories")
            print("Downloaded " + str(new_files) + " new files.")

    # reset file counter
    story_files = new_files
    new_files = 0

    # get all user highlights
    if DOWNLOAD_HIGHLIGHTS:
        # if you're curious, highlights are really dumb. you first need to hit one URL to findout if the user has any highlights,
        # then from there you need to get the IDs of each highlight, and ping a different URL location with those IDs to actually
        # download the content. 
        print("\nFinding highlights...")
        stories = api_request("/users/" + PROFILE_ID + "/stories/highlights", getdata={"limit": HIGHLIGHT_LIMIT})
        if len(stories) == 0:
            print("No highlights found.")
        elif len(stories) == 1 and "error" in stories:
            print("You do not have access to this user's highlights.")
        else:
            print("Found " + str(len(stories)) + " highlights. Downloading media...")
            for story in stories:
                posts = api_request("/stories/highlights/{}".format(story["id"]), getdata={"limit": HIGHLIGHT_LIMIT})
                posts = posts["stories"]
                # iterate over highlights, downloading all media
                for post in posts:
                    for media in post["media"]:
                        if 'source' in media:
                            download_media(media, "highlights")
                print("Downloaded " + str(new_files) + " new files.")

    # reset file counter
    highlight_files = new_files
    new_files = 0

    # TODO: Purchased posts will often contain posts purhcased from messages.
    #       A more complex system should be implemented to avoid downloading
    #       purchased messages to avoid having these posts show up in the
    #       messages folder as well as the purchased folder.
    #
    #       Looking through the response from messages, I can't see any easy
    #       way to determine whether or not a message was originally paywalled
    #       and then purchased, as purchased posts just show up as "free" with
    #       thier ability to be purchased set to false.

    # get all user messages
    if DOWNLOAD_MESSAGES:
        print("\nFinding messages...")
        posts = api_request("/chats/" + PROFILE_ID + "/messages", getdata={"limit": MESSAGE_LIMIT})
        posts = posts["list"]
        if len(posts) == 0:
            print("No messages found.")
        else:
            print("Found " + str(len(posts)) + " messages. Downloading media...")
            # iterate over messages, downloading all media
            for post in posts:
                for media in post["media"]:
                    if 'source' in media:
                        download_media(media, "messages")
            print("Downloaded " + str(new_files) + " new files.")

    # reset file counter
    message_files = new_files
    new_files = 0

    # get all user purchases
    if DOWNLOAD_PURCHASED:
        print("\nFinding purchased posts...")
        posts = api_request("/posts/paid", getdata={"limit": PURCHASE_LIMIT})
        if len(posts) == 0:
            print("No purchased posts found.")
        else:
            print("Found " + str(len(posts)) + " purchased posts. Downloading media...")
            # iterate over purchased posts, downloading all media
            for post in posts:
                user = post["fromUser"]
                username = user["username"]
                if username != PROFILE:
                    continue
                for media in post["media"]:
                    if 'source' in media:
                        download_media(media, "purchased")
            print("Downloaded " + str(new_files) + " new files.")

    purchased_files = new_files

    print("\nTotal files downloaded:" +
        "\nPosts: {}".format(post_files) +
        "\nArchived Posts: {}".format(archived_post_files) +
        "\nStories: {}".format(story_files) +
        "\nHighlights: {}".format(highlight_files) +
        "\nMessages: {}".format(message_files) +
        "\nPurchased: {}".format(purchased_files))