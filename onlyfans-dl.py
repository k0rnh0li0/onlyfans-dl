#!/usr/bin/python3
#
# OnlyFans Profile Downloader/Archiver
# KORNHOLIO 2020
# XoursCode 2022
# - refactored api_request (thx to @freakmaxi)
# - added GIF support (treated as videos by OF, where ignored but saved separatly now)
# - added deletion of empty folders after scraping
# - added MEDIA_TYPES for easily disable or enable a specific content type
# - implemented SAVING_DIRS dict
# - implemented SAVE_DIR for determining save location
# - removed exit() on scraping all profiles when one profile had been deactivated
# - using dynamically fetched app_token
# - refined input prompt (hint for comma-separated list added)
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
import hashlib

# maximum number of posts to index
# DONT CHANGE THAT
POST_LIMIT = 10

# api info
URL = "https://onlyfans.com"
API_URL = "/api2/v2"

# user info from /users/customer
USER_INFO = {}

# target profile
PROFILE = ""
# profile data from /users/<profile>
PROFILE_INFO = {}
PROFILE_ID = ""

# local target location (save directory, trailing slash is mandatory)
SAVE_DIR = "../"

# do not change this dict, except you know what you're doing
SAVING_DIRS = {
    "root": "",
    "avatar": "/avatar",
    "header": "/header",
    "archived": "/archived"
    }

# add or remove media types here to be more specific on downloads
MEDIA_TYPES = ['photo', 'video', 'gif']
SAVING_DIRS |= { mt : "/" + mt + "s" for mt in MEDIA_TYPES }
SAVING_DIRS |= { "archived-" + mt : "/archived/" + mt + "s" for mt in MEDIA_TYPES }
# uncomment following lines to save gif into video folder (gif's are saved as mp4 by OF anyway)
#SAVING_DIRS['gif'] = SAVING_DIRS['video']
#SAVING_DIRS['archived-gif'] = SAVING_DIRS['archived-video']

# helper function to make sure a dir is present
def assure_dir(path):
    if not os.path.isdir(path):
        os.mkdir(path)

# helper for deleting empty folders after download
def delete_empty_folders(root):
    deleted = []
    for current_dir, subdirs, files in os.walk(root, topdown=False):
        still_has_subdirs = False
        for subdir in subdirs:
            if os.path.join(current_dir, subdir) not in deleted:
                still_has_subdirs = True
    
        if not any(files) and not still_has_subdirs:
            print(current_dir + " deleted.", end='\r', flush=True)
            os.rmdir(current_dir)
            deleted.append(current_dir)
    
    if len(deleted) > 0:
        if len(deleted) == 1:
            output = str (len(deleted)) + " empty folder deleted."
        else:
            output = str (len(deleted)) + " empty folders deleted."

        max_str = max (deleted, key=len) + " deleted."
        while len (output) < len (max_str):
            output += " "
    else:
        output = "Nothing to do."

    print(output)
    return deleted

# Create Auth with Json
def create_auth(app_token):
    with open("auth.json") as f:
        ljson = json.load(f)
    return {
        "Accept": "application/json, text/plain, */*",
        "User-Agent": ljson["user-agent"],
        "Accept-Encoding": "gzip, deflate",
        "user-id": ljson["user-id"],
        "x-bc": ljson["x-bc"],
        "Cookie": "sess=" + ljson["sess"],
        "app-token": app_token
    }


# Every API request must be signed
def create_signed_headers(link, queryParams):
    global API_HEADER
    path = API_URL + link
    if (queryParams):
        query = '&'.join('='.join((key, val)) for (key, val) in queryParams.items())
        path = f"{path}?{query}"
    unixtime = str(int(dt.datetime.now().timestamp()))
    msg = "\n".join([dynamic_rules["static_param"], unixtime, path, API_HEADER["user-id"]])
    message = msg.encode("utf-8")
    hash_object = hashlib.sha1(message)
    sha_1_sign = hash_object.hexdigest()
    sha_1_b = sha_1_sign.encode("ascii")
    checksum = sum([sha_1_b[number] for number in dynamic_rules["checksum_indexes"]]) + dynamic_rules["checksum_constant"]
    API_HEADER["sign"] = dynamic_rules["format"].format(sha_1_sign, abs(checksum))
    API_HEADER["time"] = unixtime
    return


# API request convenience function
# getdata and postdata should both be JSON
def api_request(endpoint, getdata=None, postdata=None, getparams=None):
    if getparams == None:
        getparams = {
            "order": "publish_date_desc"
        }
    if getdata is not None:
        for i in getdata:
            getparams[i] = getdata[i]

    if postdata is None:
        if getdata is not None:
            # Fixed the issue with the maximum limit of 10 posts by creating a kind of "pagination"

            create_signed_headers(endpoint, getparams)
            list_base = requests.get(URL + API_URL + endpoint,
                                     headers=API_HEADER,
                                     params=getparams).json()
            posts_num = len(list_base)
            
            while posts_num > 0:
                beforePublishTime = list_base[len(list_base) - 1]['postedAtPrecise']
                getparams['beforePublishTime'] = beforePublishTime

                # Extract posts
                create_signed_headers(endpoint, getparams)
                list_extend = requests.get(URL + API_URL + endpoint,
                                           headers=API_HEADER,
                                           params=getparams).json()
                posts_num = len(list_extend)
                if posts_num > 0:
                    list_base.extend(list_extend)
                
            return list_base
        else:
            create_signed_headers(endpoint, getparams)
            print('x')
            return requests.get(URL + API_URL + endpoint,
                                headers=API_HEADER,
                                params=getparams)
    else:
        create_signed_headers(endpoint, getparams)
        return requests.post(URL + API_URL + endpoint,
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

# to get subscribesCount for displaying all subs
# info about yourself
def user_me():
    me = api_request("/users/me").json()
    if "error" in me:
        print("\nERROR: " + me["error"]["message"])
        # bail, we need info for both profiles to be correct
        exit()
    return me

# get all subscriptions in json
def get_subs():
    SUB_LIMIT = str(user_me()["subscribesCount"])
    params = {
        "type": "active",
        "sort": "desc",
        "field": "expire_date",
        "limit": SUB_LIMIT
    }
    return api_request("/subscriptions/subscribes", getparams=params).json()


# download public files like avatar and header
new_files = 0

def select_sub():
    # Get Subscriptions
    SUBS = get_subs()
    sub_dict.update({"0": "*** Download All Models ***"})
    ALL_LIST = []

    for i in range(1, len(SUBS)+1):
        ALL_LIST.append(i)

    for i in range(0, len(SUBS)):
        sub_dict.update({i+1: SUBS[i]["username"]})

    if len(sub_dict) == 1:
        print('No models subbed')
        exit()

    # Select Model
    if ARG1 == "all":
        return ALL_LIST
    
    MODELS = str((input('\n'.join('{} | {}'.format(key, value) for key, value in sub_dict.items()) + "\nEnter number to download model (comma-separated list is allowed)\n")))
    if MODELS == "0":
        return ALL_LIST
    else:
        return [x.strip() for x in MODELS.split(',')]

def download_public_files():
    public_files = ["avatar", "header"]
    for public_file in public_files:
        source = PROFILE_INFO[public_file]
        if source is None:
            continue
        id = get_id_from_path(source)
        file_type = re.findall("\.\w+", source)[-1]
        path = SAVING_DIRS[public_file] + "/" + id + file_type
        if not os.path.isfile(SAVE_DIR + PROFILE + path):
            print("Downloading " + public_file + "...")
            download_file(PROFILE_INFO[public_file], path)
            global new_files
            new_files += 1


# download a media item and save it to the relevant directory
def download_media(media, is_archived):
    id = str(media["id"])
    source = media["source"]["source"]

    if media["type"] not in MEDIA_TYPES or not media['canView']:
        return

    # find extension
    ext = re.findall('\.\w+\?', source)
    if len(ext) == 0:
        return
    ext = ext[0][:-1]
            
    path = SAVING_DIRS["archived-" + media["type"]] if is_archived else SAVING_DIRS[media["type"]]
    path += "/" + id + ext
    
    if not os.path.isfile(SAVE_DIR + PROFILE + path):
        # print(path)
        global new_files
        new_files += 1
        download_file(source, path)


# helper to generally download files
def download_file(source, path):
    r = requests.get(source, stream=True)
    with open(SAVE_DIR + PROFILE + path, 'wb') as f:
        r.raw.decode_content = True
        shutil.copyfileobj(r.raw, f)


def get_id_from_path(path):
    last_index = path.rfind("/")
    second_last_index = path.rfind("/", 0, last_index - 1)
    id = path[second_last_index + 1:last_index]
    return id


def calc_process_time(starttime, arraykey, arraylength):
    timeelapsed = time.time() - starttime
    timeest = (timeelapsed / arraykey) * (arraylength)
    finishtime = starttime + timeest
    finishtime = dt.datetime.fromtimestamp(finishtime).strftime("%H:%M:%S")  # in time
    lefttime = dt.timedelta(seconds=(int(timeest - timeelapsed)))  # get a nicer looking timestamp this way
    timeelapseddelta = dt.timedelta(seconds=(int(timeelapsed)))  # same here
    return (timeelapseddelta, lefttime, finishtime)


# iterate over posts, downloading all media
# returns the new count of downloaded posts
def download_posts(cur_count, posts, is_archived):
    for k, post in enumerate(posts, start=1):
        if "media" not in post or ("canViewMedia" in post and not post["canViewMedia"]):
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


def get_all_videos(videos):
    len_vids = len(videos)
    has_more_videos = False
    if len_vids == 50:
        has_more_videos = True

    while has_more_videos:
        has_more_videos = False
        len_vids = len(videos)
        extra_video_posts = api_request("/users/" + PROFILE_ID + "/posts/videos",
                                        getdata={"limit": str(POST_LIMIT), "order": "publish_date_desc",
                                                 "beforePublishTime": videos[len_vids - 1]["postedAtPrecise"]}
                                        )
        videos.extend(extra_video_posts)
        if len(extra_video_posts) == 50:
            has_more_videos = True

    return videos

def get_all_photos(images):
    len_imgs = len(images)
    has_more_images = False
    if len_imgs == 50:
        has_more_images = True

    while has_more_images:
        has_more_images = False
        len_imgs = len(images)
        extra_img_posts = api_request("/users/" + PROFILE_ID + "/posts/photos",
                                        getdata={"limit": str(POST_LIMIT), "order": "publish_date_desc",
                                                 "beforePublishTime": images[len_imgs - 1]["postedAtPrecise"]}
                                        )
        images.extend(extra_img_posts)
        if len(extra_img_posts) == 50:
            has_more_images = True

    return images

if __name__ == "__main__":

    # Gather inputs
    if len(sys.argv) != 2:
        ARG1 = ""
    else:
        ARG1 = sys.argv[1]

    # Get the rules for the signed headers dynamically, as they may be fluid
    dynamic_rules = requests.get(
        'https://raw.githubusercontent.com/DATAHOARDERS/dynamic-rules/main/onlyfans.json').json()
    # Create Header
    API_HEADER = create_auth(dynamic_rules['app_token'])

    # Select sub
    sub_dict = {}
    SELECTED_MODELS = select_sub()

    # start process
    for M in SELECTED_MODELS:
        PROFILE = sub_dict[int(M)]
        PROFILE_INFO = get_user_info(PROFILE)
        PROFILE_ID = str(PROFILE_INFO["id"])

        print("\nonlyfans-dl is downloading content to " + SAVE_DIR + PROFILE + "!\n")

        if os.path.isdir(SAVE_DIR + PROFILE):
            print("\nThe folder " + SAVE_DIR + PROFILE + " exists.")
            print("Media already present will not be re-downloaded.")

        assure_dir(SAVE_DIR[:-1])
        for value in SAVING_DIRS.values():
            assure_dir(SAVE_DIR + PROFILE + value)

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

        with open(SAVE_DIR + PROFILE + "/info.json", 'w') as infojson:
            json.dump(sinf, infojson)
        
        download_public_files()
        
        # get all user posts
        print("Finding photos...", end=' ', flush=True)
        photos = api_request("/users/" + PROFILE_ID + "/posts/photos", getdata={"limit": str(POST_LIMIT)})
        photo_posts = get_all_photos(photos)
        print("Found " + str(len(photo_posts)) + " photos.")
        print("Finding videos...", end=' ', flush=True)
        videos = api_request("/users/" + PROFILE_ID + "/posts/videos", getdata={"limit": str(POST_LIMIT)})
        video_posts = get_all_videos(videos)
        print("Found " + str(len(video_posts)) + " videos.")
        print("Finding archived content...", end=' ', flush=True)
        archived_posts = api_request("/users/" + PROFILE_ID + "/posts/archived", getdata={"limit": str(POST_LIMIT)})
        print("Found " + str(len(archived_posts)) + " archived posts.")
        postcount = len(photo_posts) + len(video_posts)
        archived_postcount = len(archived_posts)
        if postcount + archived_postcount == 0:
            print("ERROR: 0 posts found.")
            continue

        total_count = postcount + archived_postcount

        print("Found " + str(total_count) + " posts. Downloading media...")

        # get start time for estimation purposes
        starttime = time.time()

        cur_count = download_posts(1, photo_posts, False)
        cur_count = download_posts(cur_count, video_posts, False)
        download_posts(cur_count, archived_posts, True)

        print("Downloaded " + str(new_files) + " new files.")

        # remove non-filled directories to keep profile folders clean
        print("\nCleaning up...")
        delete_empty_folders (SAVE_DIR)
