from typing import Union
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

# Store queue message IDs globally
queue_message_ids = {}

def queue_markup(
    _,
    DURATION,
    CPLAY,
    videoid,
    played: Union[bool, int] = None,
    dur: Union[bool, int] = None,
):
    not_dur = [
        [
            InlineKeyboardButton(
                text=_["QU_B_1"],
                callback_data=f"GetQueued {CPLAY}|{videoid}",
            ),
            InlineKeyboardButton(
                text=_["CLOSE_BUTTON"],
                callback_data="close",
            ),
        ]
    ]
    dur = [
        [
            InlineKeyboardButton(
                text=_["QU_B_2"].format(played, dur),
                callback_data="GetTimer",
            )
        ],
        [
            InlineKeyboardButton(
                text=_["QU_B_1"],
                callback_data=f"GetQueued {CPLAY}|{videoid}",
            ),
            InlineKeyboardButton(
                text=_["CLOSE_BUTTON"],
                callback_data="close",
            ),
        ],
    ]
    upl = InlineKeyboardMarkup(not_dur if DURATION == "Unknown" else dur)
    return upl


def queue_back_markup(_, CPLAY):
    upl = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    text=_["BACK_BUTTON"],
                    callback_data=f"queue_back_timer {CPLAY}",
                ),
                InlineKeyboardButton(
                    text=_["CLOSE_BUTTON"],
                    callback_data="close",
                ),
            ]
        ]
    )
    return upl


def aq_markup(_, chat_id):
    buttons = [
        [
            InlineKeyboardButton(
                    text=_["CLOSE_BUTTON"],
                    callback_data="close_queue",
            ),
        ],
    ]
    return buttons


async def delete_queue_message(chat_id: int, app):
    """Delete queue message if exists"""
    try:
        if chat_id in queue_message_ids:
            msg_id = queue_message_ids[chat_id]
            try:
                await app.delete_messages(chat_id, msg_id)
                queue_message_ids[chat_id] = None
                return True
            except:
                pass
    except:
        pass
    return False


async def store_queue_message(chat_id: int, message_id: int):
    """Store queue message ID"""
    queue_message_ids[chat_id] = message_id
