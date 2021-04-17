#!/usr/bin/python3

import os
import sys
import json
import shutil
import pathlib
import requests
from datetime import datetime, timedelta

######################
# CONFIGURATIONS     #
######################

# content types to download
VIDEOS = True
PHOTOS = True
ALBUMS = True # Separate photos into subdirectories by post/album (uses post date and ID for folder name) (Single photo posts are not put into subdirectories)
POSTS = True
ARCHIVED = True
STORIES = True
MESSAGES = True
PURCHASED = True
#HIGHLIGHTS not supported
USE_SUB_FOLDERS = True # use content type subfolders (messgaes/archived/stories/purchased), or download everything to /profile/photos and /profile/videos
API_HEADER = { # User-Agent must be updated and exact
	"Accept": "application/json, text/plain, */*",
	"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:87.0) Gecko/20100101 Firefox/87.0",
	"Accept-Encoding": "gzip, deflate"
}
######################
# END CONFIGURATIONS #
######################

API_URL = "https://onlyfans.com/api2/v2"
APP_TOKEN = "33d57ade8c02dbc5a333db99ff9ae26a"
USER_INFO = {}
PROFILE = ""
PROFILE_INFO = {}
PROFILE_ID = ""
MAX_AGE = ""
new_files = 0


def api_request(endpoint, getuserinfo = False):
	posts_limit = 100 # API limit for single query, can not incrase
	getparams = { "app-token": APP_TOKEN, "limit": posts_limit }
	if(MAX_AGE):
		getparams['afterPublishTime'] = MAX_AGE + ".000000"
	if getuserinfo:
		return requests.get(API_URL + endpoint, headers=API_HEADER, params=getparams)
	list_base = requests.get(API_URL + endpoint, headers=API_HEADER, params=getparams).json()

	# Fixed the issue with the maximum limit of 100 posts by creating a kind of "pagination"
	if len(list_base) >= posts_limit:
		getparams['beforePublishTime'] = list_base[len(list_base)-1]['postedAtPrecise']

		while len(list_base) >= posts_limit:
			list_extend = requests.get(API_URL + endpoint, headers=API_HEADER, params=getparams).json()
			getparams['beforePublishTime'] = list_extend[len(list_extend)-1]['postedAtPrecise']
			list_base.extend(list_extend) # Merge with previous posts
			if len(list_extend) < posts_limit:
				break
	return list_base


def get_user_info(profile):
	# <profile> = "me" -> info about yourself
	info = api_request("/users/" + profile, True).json()
	if "error" in info:
		print("\nERROR: " + info["error"]["message"])
		exit()
	return info


def download_media(media, subtype, album = False):
	filename = str(media["createdAt"][:10]) + "_" + str(media["id"])
	source = media["source"]["source"]

	if (media["type"] != "photo" and media["type"] != "video") or not media['canView']:
		return
	if (media["type"] == "photo" and not PHOTOS) or (media["type"] == "video" and not VIDEOS):
		return

	extension = source.split('?')[0].split('.')
	ext = '.' + extension[len(extension)-1]
	if len(ext) < 2:
		return

	if ALBUMS and album and media["type"] == "photo":
		path = "/photos/" + album + "/" + filename + ext
	else:
		path = "/" + media["type"] + "s/" + filename + ext
	if USE_SUB_FOLDERS and subtype != "posts":
		path = "/" + subtype + path

	if not os.path.isdir(PROFILE + os.path.dirname(path)):
		pathlib.Path(PROFILE + os.path.dirname(path)).mkdir(parents=True, exist_ok=True)
	if not os.path.isfile(PROFILE + path):
		#print(PROFILE + path)
		global new_files
		new_files += 1
		r = requests.get(source, stream=True)
		with open(PROFILE + path, 'wb') as f:
			r.raw.decode_content = True
			shutil.copyfileobj(r.raw, f)


def get_content(MEDIATYPE, API_LOCATION):
	posts = api_request(API_LOCATION)
	if len(posts) > 0:
		print("Found " + str(len(posts)) + " " + MEDIATYPE)
		for post in posts:
			if "canViewMedia" not in post or not post["canViewMedia"]:
				continue
			if MEDIATYPE == "purchased" and post["fromUser"]["username"] != PROFILE:
				continue # Only get paid posts from PROFILE
			if len(post["media"]) > 1: # Don't put single photo posts in a subfolder
				album = str(post["postedAt"][:10]) + "_" + str(post["id"])
			else:
				album = False
			for media in post["media"]:
				if "source" in media:
					download_media(media, MEDIATYPE, album)
		global new_files
		print("Downloaded " + str(new_files) + " new " + MEDIATYPE)
		new_files = 0
 

if __name__ == "__main__":
	if len(sys.argv) < 3:
		print("Usage: ./onlyfans-dl <profile> <sess cookie> [optional: only get last n days of posts (integer)]")
		print("Get OF 'sess' Cookie from dev console")
		print("Update User Agent: https://ipchicken.com/")		  
		exit()

	API_HEADER["Cookie"] = "sess=" + sys.argv[2]
	USER_INFO = get_user_info("me")
	API_HEADER["user-id"] = str(USER_INFO["id"])
	PROFILE = sys.argv[1]
	PROFILE_INFO = get_user_info(PROFILE)
	PROFILE_ID = str(PROFILE_INFO["id"])

	if os.path.isdir(PROFILE):
		print("\n" + PROFILE + " exists.\nDownloading new media, skipping pre-existing.")
	else:
		print("\nDownloading content to " + PROFILE)
	if(len(sys.argv) >= 4 and sys.argv[3].isnumeric()):
		MAX_AGE = (datetime.today() - timedelta(int(sys.argv[3]))).strftime("%s")
		print("\nGetting posts newer than " + str(datetime.utcfromtimestamp(int(MAX_AGE))) + " UTC\n")

	if POSTS:
		get_content("posts", "/users/" + PROFILE_ID + "/posts")
	if ARCHIVED:
		get_content("archived", "/users/" + PROFILE_ID + "/posts/archived")
	if STORIES:
		get_content("stories", "/users/" + PROFILE_ID + "/stories")
	if MESSAGES:
		get_content("messages", "/chats/" + PROFILE_ID + "/messages")
	if PURCHASED:
		get_content("purchased", "/posts/paid")

