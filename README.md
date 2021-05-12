# OnlyFans Profile Downloader / Archiver v2
This tool downloads all photos/videos from an OnlyFans profile, creating a local archive.\
You must be subscribed to the profile to download their content.

A fork of [onlyfans-dl](https://github.com/k0rnh0li0/onlyfans-dl) with more features and options!

onlyfans-dl will create a directory named after the profile in the current working directory.\
A subdirectory structure will be built depending on the options set.\
Any existing media will be skipped, not redownloaded.\
Content will be named as DATE_ID (e.g. 2021-04-17_123456.jpg)

### Requires
Requires Python3 and 'requests': `python -m pip install requests`

## Features
* Choose what type of content to download (photos, videos, posts, stories, messages, purchases, archived)
* Choose to create subfolders for each of the above, or combine them all into one folder
* Choose to sort posts with more than one photo into "albums" (subfolders)
* Download everything, or only the last <integer> days of content

### ToDo
Add "all" profile to dynamically get list of subscribed profiles, and download recent updates from them all.\
Add python library requirements file

## Usage
First make sure to set your session variables in the script and configure your options.

`./onlyfans-dl.py <profile> [optional: max age (integer)]`
* `<profile>` - the username of the profile to download
* `<sess cookie>` - your session's auth token (see below for how to find this)
* `[max age]` - Optional: Only get posts from the last <integer> days

## Session Variables
Requests to the API now need to be signed. This is an obfuscation technique from the developers to discourage scraping. Thanks for the most recent patch goes to [DIGITALCRIMINAL](https://github.com/DIGITALCRIMINAL/OnlyFans).

You need your browser's __user-agent__, onlyfans __sess__ion cookie, __x-bc__ HTTP header, and __user-id__. Here's how to get them

- Get your user-agent here [ipchicken](https://ipchicken.com/)
- Session Cookie
  - Login to OnlyFans as normal
  - Open the dev console Storage Inspector (`SHIFT+F9` on FireFox). or the "Application" tab of Chrome DevTools
  - Click Cookies -> https://onlyfans.com
  - Copy the value of the `sess` cookie
- x-bc and user-id
  - Login to OnlyFans, goto home page
  - Open dev console `F12` -> Network tab (`Ctrl+Shift+E` in FireFox)
  - Click __Headers__ sub-tab (default)
  - Click on one of the JSON elements and look under __request headers__ on the right

There are variables for each of these values at the top of the script. Make sure to update them every time you login or your browser updates.

## Contributing
PRs are welcome; be sure to take some time to familiarize yourself with OnlyFans' API if you would like to extend/modify the functionality of this script.
