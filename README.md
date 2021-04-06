THE GREAT KORNHOLIO PRESENTS

# OnlyFans Profile Downloader/Archiver
This tool downloads all photos/videos from an OnlyFans profile, creating a local archive.
You must be subscribed to the profile to download their content.

onlyfans-dl will create a directory called `profiles` in the repo directory. 
Each profile you download will be stored as a subdirectory of `profiles`.
Inside each profile directory, some information will be saved in `info.json`,
and all media will be downloaded to `photos/` and `videos/`.

DON'T OPEN AN ISSUE ABOUT THE REQUESTS LIBRARY. ( 
[#8](https://github.com/k0rnh0li0/onlyfans-dl/issues/8)
[#25](https://github.com/k0rnh0li0/onlyfans-dl/issues/25)
[#28](https://github.com/k0rnh0li0/onlyfans-dl/issues/28)
[#29](https://github.com/k0rnh0li0/onlyfans-dl/issues/29)
[#33](https://github.com/k0rnh0li0/onlyfans-dl/issues/33)
[#44](https://github.com/k0rnh0li0/onlyfans-dl/issues/44)
[#45](https://github.com/k0rnh0li0/onlyfans-dl/issues/45)
)

LOOK: `python -m pip install requests`

## Usage
`./onlyfans-dl.py <profile> <accessToken>`
* `<profile>` - the username of the profile to download
* `<accessToken>` - your session's auth token (see below for how to find this)

## Access Token
OnlyFans does a bunch of captcha schit in the login, so I wasn't able to automate the login
process. It's very easy to get your auth token though, here's how:

- Open your browser.
- After checking the value of your User-Agent (you can do this [here](https://whatismybrowser.com/detect/what-is-my-user-agent)),
copy it, and put it in the value of the `User-Agent` key of `API_HEADER` in `onlyfans-dl.py`.
- Login to OnlyFans as normal.
- Once you have logged in, open the Storage Inspector (`SHIFT+F9` on FireFox). This will be under
the "Application" tab of Chrome DevTools.
- Click Cookies -> https://onlyfans.com
- Copy the value of the `sess` cookie, that's your access token.

Once you have your access token, don't logout or otherwise end your session until you have
finished downloading content with onlyfans-dl.

## Contributing

PRs are welcome; be sure to take some time to familiarize yourself with OnlyFans' API if
you would like to extend/modify the functionality of this script.
