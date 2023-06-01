# pylint: disable=global-statement
'''eInk Media Control Display'''

import asyncio
import os
import subprocess

from winsdk.windows.media.control import \
    GlobalSystemMediaTransportControlsSessionManager as MediaManager, \
    GlobalSystemMediaTransportControlsSession
from winsdk.windows.storage.streams import Buffer, DataReader, InputStreamOptions

OLD_SESSION = None
TOKEN = None
OLD_INFO = {"title": "", "artist": "", "album": ""}


async def update_media(session: GlobalSystemMediaTransportControlsSession):
    '''gets media information whenever media property changes, gets thumbnail 
    and calls ImageMagick command to compress it'''
    global OLD_INFO
    now_playing = await session.try_get_media_properties_async()
    if (now_playing.title == OLD_INFO["title"] and now_playing.artist == OLD_INFO["artist"]):
        return
    OLD_INFO = {"title": now_playing.title,
                "artist": now_playing.artist, "album": now_playing.album_title}
    if now_playing.thumbnail:
        thumb_stream_ref = now_playing.thumbnail
        thumb_read_buffer = Buffer(5000000)
        readable_stream = await thumb_stream_ref.open_read_async()
        await readable_stream.read_async(
            thumb_read_buffer, thumb_read_buffer.capacity, InputStreamOptions.READ_AHEAD)
        buffer_reader = DataReader.from_buffer(thumb_read_buffer)
        byte_buffer = bytearray(thumb_read_buffer.length)
        buffer_reader.read_bytes(byte_buffer)
        if os.path.exists("media_thumb.png"):
            os.remove("media_thumb.png")
        with open('media_thumb.png', 'wb+') as fobj:
            fobj.write(bytearray(byte_buffer))
        subprocess.run(
            ["C:/Program Files/ImageMagick-7.1.1-Q16-HDRI/convert.exe", "media_thumb.png",
             "-resize", "x128", "-crop", "128x128+0+0",
             "-dither", "FloydSteinberg", "-define", "dither:diffusion-amount=72%",
             "-remap", "pattern:gray50", "mono.png"
             ], check=False)
    print(OLD_INFO)


# pylint: disable-next=unused-argument
def handle_media_changed(session, args):
    '''get the information when something changes'''
    asyncio.run(update_media(session))


async def update_session(manager: MediaManager):
    '''updates the session to whatever media app is focused.'''
    session = manager.get_current_session()
    if session:
        global TOKEN
        media_changed_token = session.add_media_properties_changed(
            handle_media_changed)
        TOKEN = media_changed_token
        await update_media(session)


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
