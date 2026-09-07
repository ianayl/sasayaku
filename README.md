# Sasayaku <img src="https://raw.githubusercontent.com/ianayl/sasayaku/main/extension/public/icon/icon128.png" width="20" height="20" style="border-radius: 16px" alt="Sasayaku" />

> [!NOTE]
> Heavily work in progress -- This project is not ready for use yet.

Sasayaku generates improved Youtube subtitles for asbplayer using Whisper.

[Asbplayer](https://github.com/asbplayer/asbplayer) + [Yomitan](https://github.com/yomidevs/yomitan) is a classic Chrome extension combination for language learning through videos. I've been trying to learn a bit of Japanese for an upcoming Japan trip, but Youtube's own subtitle generation for Japanese are sometimes... really wrong... and that's really confusing for a beginner in Japanese to navigate.

Thus, Sasayaku is a Chrome extension + local webserver combination that:
- Lets me generate higher-quality subtitles for asbplayer using Whisper (it doesn't have to be Japanese!)
- ... and subsequently upload them to asbplayer using the asbplayer websocket server.
