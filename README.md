# Twitch Chat TTS

Small Python script that connects to a Twitch channel, reads every chat message, sends the message text to ElevenLabs, and plays the generated speech on your default audio device.

## Setup

Edit these constants in `twitch_chat_tts.py`:

```python
TWITCH_LOGIN_USERNAME = "your_twitch_login_username"
TWITCH_OAUTH_TOKEN = "oauth:your_twitch_oauth_token"
TWITCH_CHANNEL = "your_twitch_channel"

ELEVENLABS_API_KEY = "your_elevenlabs_api_key"
ELEVENLABS_VOICE_ID = "MEJe6hPrI48Kt2lFuVe3"
```

`TWITCH_LOGIN_USERNAME` is the Twitch account used to connect to chat.

`TWITCH_CHANNEL` is the channel to listen to, without `#`.

`ELEVENLABS_VOICE_ID` is not a secret. Your `ELEVENLABS_API_KEY` and Twitch OAuth token are secrets.

## Twitch OAuth Token

Get a Twitch chat OAuth token from:

https://twitchapps.com/tmi/

The token should look like:

```text
oauth:xxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

Use a token from the same Twitch account as `TWITCH_LOGIN_USERNAME`.

## Install Dependencies

From the project folder:

```powershell
.\.venv\Scripts\python.exe -m pip install httpx sounddevice soundfile
```

## Run

```powershell
.\.venv\Scripts\python.exe twitch_chat_tts.py
```

When it connects, send a message in Twitch chat. The script should print the message and speak it.

## Notes

The script plays audio on the system default output device. Change your Windows default audio device if you want the TTS to go somewhere else.

Do not publish real API keys or OAuth tokens to GitHub. Use placeholders before committing.
