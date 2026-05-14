import asyncio
import tempfile
import uuid
from pathlib import Path

import httpx
import sounddevice as sd
import soundfile as sf

TWITCH_SERVER = "irc.chat.twitch.tv"
TWITCH_PORT = 6697
TWITCH_LOGIN_USERNAME = "your_twitch_login_username"
TWITCH_OAUTH_TOKEN = "oauth:your_twitch_oauth_token"
TWITCH_CHANNEL = "your_twitch_channel"

ELEVENLABS_API_KEY = "your_elevenlabs_api_key"
ELEVENLABS_VOICE_ID = "MEJe6hPrI48Kt2lFuVe3"
ELEVENLABS_MODEL_ID = "eleven_flash_v2_5"
ELEVENLABS_OUTPUT_FORMAT = "mp3_44100_128"
ELEVENLABS_TIMEOUT_SECONDS = 60.0


async def send_irc(writer: asyncio.StreamWriter, text: str):
    writer.write(f"{text}\r\n".encode("utf-8"))
    await writer.drain()


async def read_irc_line(reader: asyncio.StreamReader) -> str:
    raw_line = await reader.readline()
    if not raw_line:
        raise RuntimeError("Twitch closed the connection.")

    return raw_line.decode("utf-8", errors="replace").strip()


def extract_message(line: str) -> str | None:
    if " PRIVMSG " not in line or " :" not in line:
        return None

    message = line.split(" :", 1)[1].strip()
    return message or None


def normalize_oauth_token(token: str) -> str:
    token = token.strip()
    if token.startswith("oauth:"):
        return token
    return f"oauth:{token}"


def synthesize_speech(text: str, output_path: Path):
    response = httpx.post(
        f"https://api.elevenlabs.io/v1/text-to-speech/{ELEVENLABS_VOICE_ID}",
        params={"output_format": ELEVENLABS_OUTPUT_FORMAT},
        headers={
            "xi-api-key": ELEVENLABS_API_KEY,
            "Content-Type": "application/json",
        },
        json={
            "text": text,
            "model_id": ELEVENLABS_MODEL_ID,
        },
        timeout=ELEVENLABS_TIMEOUT_SECONDS,
    )
    try:
        response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        raise RuntimeError(
            f"ElevenLabs TTS failed: {exc.response.status_code} {exc.response.text}"
        ) from exc

    output_path.write_bytes(response.content)


def play_audio(audio_path: Path):
    audio_data, sample_rate = sf.read(str(audio_path), dtype="float32", always_2d=True)
    sd.play(audio_data, samplerate=sample_rate, blocking=True)
    sd.stop()


async def speak(text: str):
    temp_path = Path(tempfile.gettempdir()) / f"twitch_tts_{uuid.uuid4().hex}.mp3"
    try:
        await asyncio.to_thread(synthesize_speech, text, temp_path)
        await asyncio.to_thread(play_audio, temp_path)
    finally:
        temp_path.unlink(missing_ok=True)


async def connect_to_twitch() -> tuple[asyncio.StreamReader, asyncio.StreamWriter]:
    reader, writer = await asyncio.open_connection(TWITCH_SERVER, TWITCH_PORT, ssl=True)
    channel = TWITCH_CHANNEL.strip().lstrip("#").lower()

    await send_irc(writer, f"PASS {normalize_oauth_token(TWITCH_OAUTH_TOKEN)}")
    await send_irc(writer, f"NICK {TWITCH_LOGIN_USERNAME.strip().lower()}")
    await send_irc(writer, f"JOIN #{channel}")

    while True:
        line = await read_irc_line(reader)
        if line.startswith("PING"):
            await send_irc(writer, "PONG :tmi.twitch.tv")
            continue

        if "Login authentication failed" in line:
            raise RuntimeError("Twitch rejected the OAuth token.")
        if "Improperly formatted auth" in line:
            raise RuntimeError("Twitch rejected the OAuth token format.")
        if f" JOIN #{channel}" in line:
            return reader, writer


async def run():
    reader, writer = await connect_to_twitch()
    channel = TWITCH_CHANNEL.strip().lstrip("#").lower()
    print(f"Reading Twitch messages from #{channel}.")

    try:
        while True:
            line = await read_irc_line(reader)
            if line.startswith("PING"):
                await send_irc(writer, "PONG :tmi.twitch.tv")
                continue

            message = extract_message(line)
            if message is None:
                continue

            print(message)
            await speak(message)
    finally:
        writer.close()
        await writer.wait_closed()


async def main():
    while True:
        try:
            await run()
        except Exception as exc:
            print(f"Twitch TTS stopped: {exc}")
            print("Reconnecting in 5 seconds...")
            await asyncio.sleep(5)


if __name__ == "__main__":
    asyncio.run(main())
