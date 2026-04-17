import asyncio
import os
from datetime import datetime, timedelta
from typing import Union

from pyrogram import Client
from pyrogram.types import InlineKeyboardMarkup, Message, InlineKeyboardButton
from pytgcalls import PyTgCalls, StreamType
from pytgcalls.exceptions import (
    AlreadyJoinedError,
    NoActiveGroupCall,
    TelegramServerError,
)
from pytgcalls.types import Update
from pytgcalls.types.input_stream import AudioPiped, AudioVideoPiped
from pytgcalls.types.input_stream.quality import HighQualityAudio, MediumQualityVideo
from pytgcalls.types.stream import StreamAudioEnded

import config
from VenomMusic import LOGGER, YouTube, app
from VenomMusic.misc import db
from VenomMusic.utils.database import (
    add_active_chat,
    add_active_video_chat,
    get_lang,
    get_loop,
    group_assistant,
    is_autoend,
    music_on,
    remove_active_chat,
    remove_active_video_chat,
    set_loop,
)
from VenomMusic.utils.exceptions import AssistantErr
from VenomMusic.utils.formatters import check_duration, seconds_to_min, speed_converter
from VenomMusic.utils.inline.play import stream_markup
from VenomMusic.utils.stream.autoclear import auto_clean
from VenomMusic.utils.thumbnails import gen_thumb
from strings import get_string

autoend = {}
counter = {}

# ✅ SIRF EK MESSAGE STORE KARENGE
last_msg_id = {}


async def _clear_(chat_id):
    db[chat_id] = []
    await remove_active_video_chat(chat_id)
    await remove_active_chat(chat_id)


async def delete_last_message(chat_id: int):
    """Delete previous message - SIMPLE FIX"""
    try:
        if chat_id in last_msg_id and last_msg_id[chat_id]:
            try:
                await app.delete_messages(chat_id, last_msg_id[chat_id])
                LOGGER(__name__).info(f"✅ DELETED: {last_msg_id[chat_id]}")
                last_msg_id[chat_id] = None
                return True
            except Exception as e:
                LOGGER(__name__).error(f"❌ DELETE FAILED: {e}")
        return False
    except:
        return False


async def send_now_playing(chat_id, title, duration, user, videoid, streamtype, original_chat_id):
    """Send ONLY current song message"""
    try:
        language = await get_lang(chat_id)
        _ = get_string(language)
        
        # 🔥 DELETE OLD MESSAGE FIRST
        await delete_last_message(original_chat_id)
        
        img = await gen_thumb(videoid)
        button = stream_markup(_, chat_id)
        
        if streamtype == "video":
            caption = _["stream_1"].format(
                f"https://t.me/{app.username}?start=info_{videoid}",
                title[:23], duration, user,
            )
        else:
            caption = f"🎵 **Now Playing:**\n📌 {title[:50]}\n⏱️ {duration}\n👤 {user}"
        
        run = await app.send_photo(
            chat_id=original_chat_id,
            photo=img,
            caption=caption,
            reply_markup=InlineKeyboardMarkup(button),
        )
        
        # ✅ STORE NEW MESSAGE ID
        last_msg_id[original_chat_id] = run.id
        LOGGER(__name__).info(f"✨ NEW: {run.id}")
        
        if chat_id in db and db[chat_id]:
            db[chat_id][0]["mystic"] = run
        return run
    except Exception as e:
        LOGGER(__name__).error(f"Error: {e}")
        return None


async def send_song_ended(chat_id):
    """Send song ended message"""
    try:
        await delete_last_message(chat_id)
        
        msg = await app.send_message(
            chat_id=chat_id,
            text="🎵 **Song Ended!**\n\nUse `/play` to play new song"
        )
        
        last_msg_id[chat_id] = msg.id
        LOGGER(__name__).info(f"📢 ENDED: {msg.id}")
        
        # Auto delete after 15 seconds
        await asyncio.sleep(15)
        await delete_last_message(chat_id)
        
        return msg
    except Exception as e:
        LOGGER(__name__).error(f"Error: {e}")
        return None


class Call(PyTgCalls):
    def __init__(self):
        self.userbot1 = Client(
            name="VenomAss1",
            api_id=config.API_ID,
            api_hash=config.API_HASH,
            session_string=str(config.STRING1),
        )
        self.one = PyTgCalls(self.userbot1, cache_duration=100)
        
        self.userbot2 = Client(
            name="VenomAss2",
            api_id=config.API_ID,
            api_hash=config.API_HASH,
            session_string=str(config.STRING2),
        )
        self.two = PyTgCalls(self.userbot2, cache_duration=100)
        
        self.userbot3 = Client(
            name="VenomAss3",
            api_id=config.API_ID,
            api_hash=config.API_HASH,
            session_string=str(config.STRING3),
        )
        self.three = PyTgCalls(self.userbot3, cache_duration=100)
        
        self.userbot4 = Client(
            name="VenomAss4",
            api_id=config.API_ID,
            api_hash=config.API_HASH,
            session_string=str(config.STRING4),
        )
        self.four = PyTgCalls(self.userbot4, cache_duration=100)
        
        self.userbot5 = Client(
            name="VenomAss5",
            api_id=config.API_ID,
            api_hash=config.API_HASH,
            session_string=str(config.STRING5),
        )
        self.five = PyTgCalls(self.userbot5, cache_duration=100)

    async def pause_stream(self, chat_id: int):
        assistant = await group_assistant(self, chat_id)
        await assistant.pause_stream(chat_id)

    async def resume_stream(self, chat_id: int):
        assistant = await group_assistant(self, chat_id)
        await assistant.resume_stream(chat_id)

    async def stop_stream(self, chat_id: int):
        assistant = await group_assistant(self, chat_id)
        try:
            await delete_last_message(chat_id)
            await _clear_(chat_id)
            await assistant.leave_group_call(chat_id)
        except:
            pass

    async def stop_stream_force(self, chat_id: int):
        try:
            await delete_last_message(chat_id)
        except:
            pass
        for x in [self.one, self.two, self.three, self.four, self.five]:
            try:
                await x.leave_group_call(chat_id)
            except:
                pass
        try:
            await _clear_(chat_id)
        except:
            pass

    async def speedup_stream(self, chat_id: int, file_path, speed, playing):
        assistant = await group_assistant(self, chat_id)
        # ... (apna purana speedup code yahi rakho, unchanged)
        pass

    async def force_stop_stream(self, chat_id: int):
        assistant = await group_assistant(self, chat_id)
        try:
            await delete_last_message(chat_id)
            check = db.get(chat_id)
            if check:
                check.pop(0)
        except:
            pass
        await remove_active_video_chat(chat_id)
        await remove_active_chat(chat_id)
        try:
            await assistant.leave_group_call(chat_id)
        except:
            pass

    async def skip_stream(self, chat_id: int, link: str, video: Union[bool, str] = None, image: Union[bool, str] = None):
        assistant = await group_assistant(self, chat_id)
        await delete_last_message(chat_id)
        if video:
            stream = AudioVideoPiped(link, audio_parameters=HighQualityAudio(), video_parameters=MediumQualityVideo())
        else:
            stream = AudioPiped(link, audio_parameters=HighQualityAudio())
        await assistant.change_stream(chat_id, stream)

    async def seek_stream(self, chat_id, file_path, to_seek, duration, mode):
        assistant = await group_assistant(self, chat_id)
        stream = (
            AudioVideoPiped(file_path, audio_parameters=HighQualityAudio(), video_parameters=MediumQualityVideo(), additional_ffmpeg_parameters=f"-ss {to_seek} -to {duration}")
            if mode == "video"
            else AudioPiped(file_path, audio_parameters=HighQualityAudio(), additional_ffmpeg_parameters=f"-ss {to_seek} -to {duration}")
        )
        await assistant.change_stream(chat_id, stream)

    async def stream_call(self, link):
        assistant = await group_assistant(self, config.LOG_GROUP_ID)
        await assistant.join_group_call(config.LOG_GROUP_ID, AudioVideoPiped(link), stream_type=StreamType().pulse_stream)
        await asyncio.sleep(0.2)
        await assistant.leave_group_call(config.LOG_GROUP_ID)

    async def join_call(self, chat_id: int, original_chat_id: int, link, video: Union[bool, str] = None, image: Union[bool, str] = None):
        assistant = await group_assistant(self, chat_id)
        language = await get_lang(chat_id)
        _ = get_string(language)
        if video:
            stream = AudioVideoPiped(link, audio_parameters=HighQualityAudio(), video_parameters=MediumQualityVideo())
        else:
            stream = AudioPiped(link, audio_parameters=HighQualityAudio())
        try:
            await assistant.join_group_call(chat_id, stream, stream_type=StreamType().pulse_stream)
        except NoActiveGroupCall:
            raise AssistantErr(_["call_8"])
        except AlreadyJoinedError:
            raise AssistantErr(_["call_9"])
        except TelegramServerError:
            raise AssistantErr(_["call_10"])
        await add_active_chat(chat_id)
        await music_on(chat_id)
        if video:
            await add_active_video_chat(chat_id)
        if await is_autoend():
            counter[chat_id] = {}
            users = len(await assistant.get_participants(chat_id))
            if users == 1:
                autoend[chat_id] = datetime.now() + timedelta(minutes=1)

    async def change_stream(self, client, chat_id):
        check = db.get(chat_id)
        popped = None
        loop = await get_loop(chat_id)
        try:
            if loop == 0:
                popped = check.pop(0)
            else:
                loop = loop - 1
                await set_loop(chat_id, loop)
            await auto_clean(popped)
            if not check:
                await delete_last_message(chat_id)
                await send_song_ended(chat_id)
                await _clear_(chat_id)
                return await client.leave_group_call(chat_id)
        except:
            try:
                await delete_last_message(chat_id)
                await send_song_ended(chat_id)
                await _clear_(chat_id)
                return await client.leave_group_call(chat_id)
            except:
                return
        else:
            # ... (baaki ka change_stream code same rakho, bas send_now_playing call karo)
            # Tumhara existing code yahi rahega, bas jahan jahan pehle message send hota tha
            # wahan send_now_playing use karo
            
            # EXAMPLE - Tumhare code mein jahan yeh line hai:
            # run = await app.send_photo(...)
            # Use send_now_playing instead
            
            pass

    async def ping(self):
        pings = []
        if config.STRING1:
            pings.append(await self.one.ping)
        if config.STRING2:
            pings.append(await self.two.ping)
        if config.STRING3:
            pings.append(await self.three.ping)
        if config.STRING4:
            pings.append(await self.four.ping)
        if config.STRING5:
            pings.append(await self.five.ping)
        return str(round(sum(pings) / len(pings), 3))

    async def start(self):
        LOGGER(__name__).info("Starting PyTgCalls Client...\n")
        if config.STRING1:
            await self.one.start()
        if config.STRING2:
            await self.two.start()
        if config.STRING3:
            await self.three.start()
        if config.STRING4:
            await self.four.start()
        if config.STRING5:
            await self.five.start()

    async def decorators(self):
        @self.one.on_kicked()
        @self.two.on_kicked()
        @self.three.on_kicked()
        @self.four.on_kicked()
        @self.five.on_kicked()
        @self.one.on_closed_voice_chat()
        @self.two.on_closed_voice_chat()
        @self.three.on_closed_voice_chat()
        @self.four.on_closed_voice_chat()
        @self.five.on_closed_voice_chat()
        @self.one.on_left()
        @self.two.on_left()
        @self.three.on_left()
        @self.four.on_left()
        @self.five.on_left()
        async def stream_services_handler(_, chat_id: int):
            await delete_last_message(chat_id)
            await self.stop_stream(chat_id)

        @self.one.on_stream_end()
        @self.two.on_stream_end()
        @self.three.on_stream_end()
        @self.four.on_stream_end()
        @self.five.on_stream_end()
        async def stream_end_handler1(client, update: Update):
            if not isinstance(update, StreamAudioEnded):
                return
            await self.change_stream(client, update.chat_id)


Venom = Call()
