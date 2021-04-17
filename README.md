# OnlyFans Profile Downloader / Archiver v2
This tool downloads all photos/videos from an OnlyFans profile, creating a local archive.\
You must be subscribed to the profile to download their content.

A fork of [onlyfans-dl](https://github.com/k0rnh0li0/onlyfans-dl) with more features and options!

onlyfans-dl will create a directory named after the profile in the current working directory.\
A subdirectory structure will be built depending on the options set.\
Any existing media will be skipped, not redownloaded.\
Content will be named as DATE_ID e.g. 2021-04-17_123456.jpg

###Requires
Requires Python3 and 'requests': `python -m pip install requests`

## Features
* Choose what type of content to download (photos, videos, posts, stories, messages, purchases, archived)
* Choose to create subfolders for each of the above, or combine them all into one folder
* Choose to sort posts with more than one photo into "albums" (subfolders)
* Download everything, or only the last **n** days of content

## Usage
First make sure to set your user-agent in the script and configure your options.

`./onlyfans-dl.py <profile> <sess cookie> [optional: max age (integer)]`
* `<profile>` - the username of the profile to download
* `<sess cookie>` - your session's auth token (see below for how to find this)
* `[max age]` - Optional: Only get posts from the last **n** days (integer)

## Access Token
OnlyFans has captchas, so I can't automate login.\
You need your browser's user-agent, and onlyfans session cookie. Here's how to get them

- Get your user-agent [here](https://whatismybrowser.com/detect/what-is-my-user-agent) or my fav [ipchicken](https://ipchicken.com/)
  - copy it into the `User-Agent` key of `API_HEADER` in `onlyfans-dl.py`
- Login to OnlyFans as normal
- Open the dev console Storage Inspector (`SHIFT+F9` on FireFox). or the "Application" tab of Chrome DevTools
- Click Cookies -> https://onlyfans.com
- Copy the value of the `sess` cookie, that's your access token.

Once you have your access token, don't logout or otherwise end your session until you have finished downloading content with onlyfans-dl.

## Contributing
PRs are welcome; be sure to take some time to familiarize yourself with OnlyFans' API if you would like to extend/modify the functionality of this script.
