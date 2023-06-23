# pylint: disable=global-statement
'''eInk Media Control Display'''

import asyncio
import os
import subprocess
import serial
import shutil

from winsdk.windows.media.control import \
    GlobalSystemMediaTransportControlsSessionManager as MediaManager, \
    GlobalSystemMediaTransportControlsSession
from winsdk.windows.storage.streams import Buffer, DataReader, InputStreamOptions

OLD_SESSION = None
TOKEN = None
OLD_INFO = {"title": "", "artist": "", "album": ""}
THINGS_LEFT = 0


async def update_media(session: GlobalSystemMediaTransportControlsSession, things):
    '''gets media information whenever media property changes, gets thumbnail
    and calls ImageMagick command to compress it'''
    global OLD_INFO
    now_playing = await session.try_get_media_properties_async()
    if (now_playing.title == OLD_INFO["title"] and now_playing.artist == OLD_INFO["artist"]):
        return
    OLD_INFO = {"title": now_playing.title,
                "artist": now_playing.artist, "album": now_playing.album_title}
    print(OLD_INFO)
    # handle collecting the thumbnail
    if now_playing.thumbnail:
        thumb_stream_ref = now_playing.thumbnail
        thumb_read_buffer = Buffer(5000000)
        readable_stream = await thumb_stream_ref.open_read_async()
        await readable_stream.read_async(
            thumb_read_buffer, thumb_read_buffer.capacity, InputStreamOptions.READ_AHEAD)
        buffer_reader = DataReader.from_buffer(thumb_read_buffer)
        byte_buffer = bytearray(thumb_read_buffer.length)
        buffer_reader.read_bytes(byte_buffer)
        if os.path.exists("media_thumb.jpg"):
            os.remove("media_thumb.jpg")
        with open('media_thumb.jpg', 'wb+') as fobj:
            fobj.write(bytearray(byte_buffer))
        # compress and Floyd-Steinberg dither the image for display
        subprocess.run(
            ["magick", "media_thumb.jpg",
             "-resize", "x128", "-crop", "128x128+0+0",
             "-dither", "FloydSteinberg", "-define", "dither:diffusion-amount=72%",
             "-remap", "pattern:gray50", "out/mono.jpg"
             ], check=False, shell=True)
    else:
        shutil.copyfile("default.jpg", "out/mono.jpg")
    # write song description into file for sending
    print("sending...")
    with open("out/desc.txt", "wb+") as file:
        file.write(bytes(OLD_INFO["title"] + "\n" + OLD_INFO["artist"] +
                         "\n" + OLD_INFO["album"] + "\n", 'utf-8'))
    # if process thinks it is most recent then send over the thumbnail and desc
    if THINGS_LEFT == things:
        subprocess.run(["ampy", "-p", "COM5",
                        "put", "out", "/"], check=True, shell=True)
    # send command to refresh the screen
    ser = serial.Serial("COM5", 112500)
    ser.write(bytes("from main import refresh\rrefresh()\r", 'utf-8'))
    ser.close()
    print("done!")


# pylint: disable-next=unused-argument
def handle_media_changed(session, args):
    '''get the information when something changes'''
    global THINGS_LEFT
    THINGS_LEFT += 1
    asyncio.run(update_media(session, THINGS_LEFT))


async def update_session(manager: MediaManager):
    '''updates the session to whatever media app is focused.'''
    session = manager.get_current_session()
    if session:
        global TOKEN
        global THINGS_LEFT
        THINGS_LEFT += 1
        media_changed_token = session.add_media_properties_changed(
            handle_media_changed)
        TOKEN = media_changed_token
        await update_media(session, THINGS_LEFT)


# pylint: disable-next=unused-argument
def handle_sessions_changed(manager: MediaManager, args):
    '''handler for updating the session info'''
    global OLD_SESSION
    if OLD_SESSION:
        OLD_SESSION.remove_media_properties_changed(TOKEN)
    OLD_SESSION = manager.get_current_session()
    asyncio.run(update_session(manager))


async def main():
    '''Set up the async things'''
    os.makedirs("out", exist_ok=True)
    manager = await MediaManager.request_async()
    sessions_changed_token = manager.add_current_session_changed(
        handle_sessions_changed)
    try:
        asyncio.create_task(update_session(manager))
        event = asyncio.Event()
        await event.wait()
    finally:
        manager.remove_current_session_changed(sessions_changed_token)

if __name__ == '__main__':
    asyncio.run(main())
