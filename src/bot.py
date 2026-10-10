"""
Telegram MTProto High-Speed NSFW Auto-Delete Bot
Powered by Telethon + Local Hybrid ONNX Engine (OpenNSFW + NudeNet).
Processes and deletes 18+ stickers, porn photos, and erotic media in <50ms.
"""

import os
import sys
import time
import asyncio
import logging
from telethon import TelegramClient, events, Button
from telethon.tl import types
from telethon.tl.types import (
    DocumentAttributeSticker,
    DocumentAttributeAnimated,
    DocumentAttributeVideo,
)

from . import config
from . import database
from .engine import engine

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [MTPROTO_BOT] %(message)s"
)
logger = logging.getLogger("telethon_bot")

API_ID = config.TELEGRAM_API_ID
API_HASH = config.TELEGRAM_API_HASH
BOT_TOKEN = config.TELEGRAM_BOT_TOKEN
SUPPORT_URL = config.SUPPORT_CHANNEL_URL
LOG_GROUP_ID = config.LOG_GROUP_ID
OWNER_ID = config.OWNER_ID

session_file = os.path.join(config.ROOT_DIR, "nsfw_shield")
client = TelegramClient(session_file, API_ID, API_HASH)


async def send_log(text: str):
    """Send audit log message to the configured log group."""
    try:
        await client.send_message(LOG_GROUP_ID, text, parse_mode="html")
    except Exception as e:
        logger.warning(f"Failed to dispatch message to log group ({LOG_GROUP_ID}): {e}")


async def check_admin_and_auto_leave(chat_id: int, chat_title: str) -> bool:
    """If bot was removed from admin in a group, automatically leave and send log."""
    me = await client.get_me()
    try:
        perms = await client.get_permissions(chat_id, me.id)
        if not perms.is_admin:
            logger.warning(f"Bot was removed from admin in {chat_title} ({chat_id}). Auto-leaving...")
            try:
                await client.send_message(
                    chat_id,
                    "⚠️ **Administrator Rights Missing / Revoked!**\n\n"
                    "Since my administrator permissions were removed, I am leaving the group.\n"
                    "Please re-add me as Administrator with **Delete Messages** permission to protect your chat!"
                )
            except Exception:
                pass

            await client.delete_dialog(chat_id)
            database.remove_group(chat_id)

            await send_log(
                f"🚪 <b>#AUTO_LEFT_GROUP</b>\n\n"
                f"👥 <b>Group Name:</b> <b>{chat_title}</b>\n"
                f"🆔 <b>Group ID:</b> <code>{chat_id}</code>\n"
                f"⚠️ <b>Reason:</b> Removed from Administrator, auto-left group."
            )
            return True
    except Exception as e:
        logger.error(f"Error checking admin perms in {chat_id}: {e}")
    return False


async def is_authorized_admin(event) -> bool:
    """Check if the sender is the bot owner or a group admin."""
    sender_id = event.sender_id
    if sender_id == OWNER_ID:
        return True
    if event.is_private:
        return True
    try:
        perms = await client.get_permissions(event.chat_id, sender_id)
        return perms.is_admin
    except Exception:
        return False


def get_chat_sensitivity(chat_id: int) -> str:
    settings = database.get_group_settings(chat_id)
    return settings.get("sensitivity", config.DEFAULT_SENSITIVITY)


def get_support_buttons():
    return [
        [
            Button.url("Updates 📢", SUPPORT_URL),
            Button.url("Support 💬", SUPPORT_URL),
        ]
    ]


async def auto_delete_msg(chat_id: int, message_id: int, delay_sec: int = 15):
    """Asynchronously delete warning message after delay."""
    await asyncio.sleep(delay_sec)
    try:
        await client.delete_messages(chat_id, message_id)
    except Exception:
        pass


def identify_media_type(message) -> str:
    """Identify if media is a sticker, photo, GIF, or document."""
    if message.photo:
        return "Photo"
    if message.document:
        for attr in message.document.attributes:
            if isinstance(attr, DocumentAttributeSticker):
                return "Sticker"
            if isinstance(attr, DocumentAttributeAnimated):
                return "GIF/Animation"
            if isinstance(attr, DocumentAttributeVideo):
                return "Video"
        if message.document.mime_type and "image" in message.document.mime_type:
            return "Image"
    return "Media"


def get_welcome_content(sender_id: int, sender_name: str, bot_username: str):
    caption = (
        f"👋 Hey, - <a href=\"tg://user?id={sender_id}\">{sender_name}</a>\n\n"
        "<blockquote>• <b>Edit Guardian Bot</b> keeps your group safe & clean!\n\n"
        "🚫 Auto-deletes 18+ porn stickers & explicit media in real time.\n"
        "🛑 Auto-deletes edited messages to prevent spam & scams.\n\n"
        "🌟 Add me to your group with <b>Delete Messages</b> rights!</blockquote>"
    )
    buttons = [
        [Button.url("Add me to your group", f"https://t.me/{bot_username}?startgroup=true")],
        [Button.inline("❓ Help and commands", b"help_menu")],
        [
            Button.url("Updates 📢", SUPPORT_URL),
            Button.url("Support 💬", SUPPORT_URL),
        ]
    ]
    return caption, buttons


@client.on(events.NewMessage(pattern="/start"))
async def start_handler(event):
    sender = await event.get_sender()
    sender_id = sender.id if sender else event.sender_id
    first = getattr(sender, "first_name", "") or getattr(sender, "title", "") or "User"
    username = getattr(sender, "username", None)

    me = await client.get_me()
    bot_username = me.username or "SayaDemoBot"

    if event.is_private:
        database.add_or_update_user(sender_id, username, first)
        user_link = f"@{username}" if username else f"<a href=\"tg://user?id={sender_id}\">{first}</a>"
        await send_log(
            f"📝 <b>#NEW_USER_STARTED</b>\n\n"
            f"👤 <b>User:</b> {user_link}\n"
            f"🆔 <b>User ID:</b> <code>{sender_id}</code>\n"
            f"🔗 <b>Username:</b> @{username or 'None'}\n"
            f"🤖 <b>Action:</b> Started the bot in private"
        )

    caption, buttons = get_welcome_content(sender_id, first, bot_username)
    banner_file = config.BANNER_PATH if os.path.exists(config.BANNER_PATH) else config.BANNER_URL

    try:
        uploaded = await client.upload_file(banner_file)
        media = types.InputMediaUploadedPhoto(file=uploaded, spoiler=True)
        await client.send_file(
            event.chat_id,
            media,
            caption=caption,
            parse_mode="html",
            buttons=buttons
        )
    except Exception as e:
        logger.error(f"Error sending spoiler banner: {e}", exc_info=True)
        await event.reply(caption, parse_mode="html", buttons=buttons)


@client.on(events.ChatAction)
async def chat_action_handler(event):
    if event.is_private:
        return

    me = await client.get_me()
    chat_id = event.chat_id
    chat = await event.get_chat()
    chat_title = getattr(chat, "title", "Group")

    # 1. Bot added to group
    if event.user_added and event.user_id == me.id:
        adder = await event.get_added_by()
        adder_id = adder.id if adder else 0
        adder_name = getattr(adder, "first_name", "User") if adder else "Unknown"
        adder_user = getattr(adder, "username", None)
        adder_link = f"@{adder_user}" if adder_user else f"<a href=\"tg://user?id={adder_id}\">{adder_name}</a>"

        members_count = getattr(chat, "participants_count", 0) or 0
        database.add_or_update_group(chat_id, chat_title, members_count)

        await send_log(
            f"📢 <b>#NEW_GROUP_ADDED</b>\n\n"
            f"👥 <b>Group Name:</b> <b>{chat_title}</b>\n"
            f"🆔 <b>Group ID:</b> <code>{chat_id}</code>\n"
            f"📊 <b>Members Count:</b> <code>{members_count}</code>\n"
            f"👤 <b>Added By:</b> {adder_link} (<code>{adder_id}</code>)"
        )

        # Check if bot was granted admin rights; auto-leave if not admin
        await asyncio.sleep(2)
        await check_admin_and_auto_leave(chat_id, chat_title)
        return

    # 2. Check if admin permissions revoked
    await check_admin_and_auto_leave(chat_id, chat_title)


@client.on(events.CallbackQuery(data=b"help_menu"))
async def help_menu_callback(event):
    help_text = (
        "⚙️ <b>Help and commands</b>\n\n"
        "<blockquote>🛡️ <b>NSFW Auto-Deletion Shield:</b>\n"
        "• Real-time scan and deletion of 18+ porn stickers, couple sex positions, Desi & Russian explicit media, and exposed anatomy in <b>&lt;40ms</b>.\n"
        "• Protects all group members & administrators.\n\n"
        "🚫 <b>Edit Guardian:</b>\n"
        "• Deletes edited messages to maintain transparency and stop copyright violations.\n\n"
        "⚡ <b>Commands:</b>\n"
        "• <code>/nsfw on</code> | <code>/nsfw off</code> — Toggle NSFW Auto-Delete Shield\n"
        "• <code>/edit on</code> | <code>/edit off</code> — Toggle Edit Guardian Deletion\n"
        "• <code>/settings</code> — Interactive group protection panel\n"
        "• <code>/check</code> — Reply to any sticker or photo to test AI verdict\n"
        "• <code>/stats</code> — Real-time scan & deletion statistics\n\n"
        "✅ Just add me to your group & grant <b>Delete Messages</b> rights!</blockquote>"
    )
    buttons = [
        [Button.inline("« Back", b"back_start")]
    ]
    await event.edit(help_text, parse_mode="html", buttons=buttons)


@client.on(events.CallbackQuery(data=b"back_start"))
async def back_start_callback(event):
    sender = await event.get_sender()
    sender_id = sender.id if sender else event.sender_id
    first = getattr(sender, "first_name", "") or getattr(sender, "title", "") or "User"

    me = await client.get_me()
    bot_username = me.username or "SayaDemoBot"

    caption, buttons = get_welcome_content(sender_id, first, bot_username)
    await event.edit(caption, parse_mode="html", buttons=buttons)


@client.on(events.NewMessage(pattern=r"(?i)^/nsfw(?:\s+(on|off))?$"))
async def nsfw_toggle_handler(event):
    if not await is_authorized_admin(event):
        return await event.reply("❌ Only Group Admins and the Bot Owner can configure NSFW Shield.")

    arg = event.pattern_match.group(1)
    chat_id = event.chat_id

    if not arg:
        settings = database.get_group_settings(chat_id)
        status = "🟢 ENABLED" if settings["nsfw_enabled"] else "🔴 DISABLED"
        return await event.reply(
            f"🛡️ **NSFW Auto-Deletion Shield:** `{status}`\n\n"
            f"• Use `/nsfw on` to enable\n"
            f"• Use `/nsfw off` to disable"
        )

    enabled = arg.lower() == "on"
    database.set_nsfw_status(chat_id, enabled)
    status_str = "🟢 **ENABLED**" if enabled else "🔴 **DISABLED**"
    await event.reply(f"✅ NSFW 18+ Sticker & Media Shield is now {status_str} for this chat.")


@client.on(events.NewMessage(pattern=r"(?i)^/(?:edit|editguard)(?:\s+(on|off))?$"))
async def editguard_toggle_handler(event):
    if not await is_authorized_admin(event):
        return await event.reply("❌ Only Group Admins and the Bot Owner can configure Edit Guardian.")

    arg = event.pattern_match.group(1)
    chat_id = event.chat_id

    if not arg:
        settings = database.get_group_settings(chat_id)
        status = "🟢 ENABLED" if settings["edit_guard_enabled"] else "🔴 DISABLED"
        return await event.reply(
            f"🚫 **Edit Guardian:** `{status}`\n\n"
            f"• Use `/edit on` to enable\n"
            f"• Use `/edit off` to disable"
        )

    enabled = arg.lower() == "on"
    database.set_edit_guard_status(chat_id, enabled)
    status_str = "🟢 **ENABLED**" if enabled else "🔴 **DISABLED**"
    await event.reply(f"✅ Edit Guardian (auto-deleting edited messages) is now {status_str} for this chat.")


async def render_settings_view(chat_id: int):
    settings = database.get_group_settings(chat_id)
    nsfw_icon = "🟢 ON" if settings["nsfw_enabled"] else "🔴 OFF"
    edit_icon = "🟢 ON" if settings["edit_guard_enabled"] else "🔴 OFF"
    sens = settings["sensitivity"].upper()

    buttons = [
        [
            Button.inline(f"NSFW Shield: {nsfw_icon}", b"toggle_nsfw"),
            Button.inline(f"Edit Guardian: {edit_icon}", b"toggle_edit"),
        ],
        [
            Button.inline("Permissive", b"sens_permissive"),
            Button.inline("Balanced", b"sens_balanced"),
            Button.inline("Strict", b"sens_strict"),
        ]
    ]

    text = (
        "⚙️ **Group Protection Control Panel:**\n\n"
        f"• **NSFW Shield (18+ Stickers/Media):** `{nsfw_icon}`\n"
        f"• **Edit Guardian (Edited Messages):** `{edit_icon}`\n"
        f"• **AI Sensitivity Level:** `{sens}`\n\n"
        "_Tap buttons below to toggle features instantly!_"
    )
    return text, buttons


@client.on(events.NewMessage(pattern=r"^/settings$"))
async def settings_handler(event):
    if not await is_authorized_admin(event):
        return await event.reply("❌ Only Group Admins and the Bot Owner can access settings.")

    text, buttons = await render_settings_view(event.chat_id)
    await event.reply(text, buttons=buttons)


@client.on(events.CallbackQuery(data=b"toggle_nsfw"))
async def toggle_nsfw_cb(event):
    if not await is_authorized_admin(event):
        return await event.answer("❌ Only Admins can change settings.", alert=True)

    chat_id = event.chat_id
    settings = database.get_group_settings(chat_id)
    new_status = not settings["nsfw_enabled"]
    database.set_nsfw_status(chat_id, new_status)
    await event.answer(f"NSFW Shield: {'ON' if new_status else 'OFF'}")
    text, buttons = await render_settings_view(chat_id)
    await event.edit(text, buttons=buttons)


@client.on(events.CallbackQuery(data=b"toggle_edit"))
async def toggle_edit_cb(event):
    if not await is_authorized_admin(event):
        return await event.answer("❌ Only Admins can change settings.", alert=True)

    chat_id = event.chat_id
    settings = database.get_group_settings(chat_id)
    new_status = not settings["edit_guard_enabled"]
    database.set_edit_guard_status(chat_id, new_status)
    await event.answer(f"Edit Guardian: {'ON' if new_status else 'OFF'}")
    text, buttons = await render_settings_view(chat_id)
    await event.edit(text, buttons=buttons)


@client.on(events.CallbackQuery(pattern=b"sens_"))
async def sensitivity_callback(event):
    if not await is_authorized_admin(event):
        return await event.answer("❌ Only Admins can change sensitivity.", alert=True)

    sens = event.data.decode().replace("sens_", "")
    database.set_group_sensitivity(event.chat_id, sens)
    await event.answer(f"Sensitivity set to {sens.upper()}")
    text, buttons = await render_settings_view(event.chat_id)
    await event.edit(text, buttons=buttons)


@client.on(events.NewMessage(pattern=r"^/broadcast(?:$|\s+(.*))"))
async def broadcast_handler(event):
    sender_id = event.sender_id
    if sender_id != OWNER_ID:
        return await event.reply("❌ Unauthorized: Only the Bot Owner (ID: `8677818347`) can broadcast.")

    broadcast_text = event.pattern_match.group(1)
    reply_msg = await event.get_reply_message() if event.is_reply else None

    if not broadcast_text and not reply_msg:
        return await event.reply("⚠️ Usage: `/broadcast <message>` or reply to any photo/sticker/post with `/broadcast`.")

    users = database.get_all_users()
    groups = database.get_all_groups()

    total_targets = len(users) + len(groups)
    status_msg = await event.reply(
        f"⏳ **Broadcasting started...**\n\n"
        f"• **Target Users:** `{len(users)}`\n"
        f"• **Target Groups:** `{len(groups)}`\n"
        f"• **Total Targets:** `{total_targets}`"
    )

    success_users = 0
    success_groups = 0
    failed = 0

    # Broadcast to Users
    for uid in users:
        try:
            if reply_msg:
                await client.send_message(uid, reply_msg)
            else:
                await client.send_message(uid, broadcast_text)
            success_users += 1
            await asyncio.sleep(0.04)
        except Exception:
            failed += 1

    # Broadcast to Groups
    for g in groups:
        gid = g["chat_id"]
        try:
            if reply_msg:
                await client.send_message(gid, reply_msg)
            else:
                await client.send_message(gid, broadcast_text)
            success_groups += 1
            await asyncio.sleep(0.04)
        except Exception:
            failed += 1

    await status_msg.edit(
        "✅ **Broadcast Completed!**\n\n"
        f"👤 **Users Reached:** `{success_users}/{len(users)}`\n"
        f"👥 **Groups Reached:** `{success_groups}/{len(groups)}`\n"
        f"⚠️ **Failed / Blocked:** `{failed}`"
    )


@client.on(events.NewMessage(pattern="/stats"))
async def stats_handler(event):
    s = engine.get_stats()
    users_count = len(database.get_all_users())
    groups_count = len(database.get_all_groups())
    text = (
        "📊 **Real-Time Moderation Metrics:**\n\n"
        f"• **Registered Users:** `{users_count}`\n"
        f"• **Active Groups:** `{groups_count}`\n"
        f"• **Total Media Scanned:** `{s['total_scans']}`\n"
        f"• **Total Auto-Deleted:** `{s['total_deletions']}`\n"
        f"• **In-Memory Cache Hits:** `{s['cache_hits']}`\n"
        f"• **Average Latency:** `{s['avg_latency_ms']} ms`\n"
        f"• **MTProto Connection:** `Active 24/7 (Direct Socket)`"
    )
    await event.reply(text, buttons=get_support_buttons())


@client.on(events.NewMessage(pattern="/check"))
async def check_command_handler(event):
    if not event.is_reply:
        await event.reply("ℹ️ Reply to any photo, sticker, or GIF with `/check` to test it!")
        return

    reply_msg = await event.get_reply_message()
    if not reply_msg.media:
        await event.reply("⚠️ The replied message does not contain inspectable image or sticker media.")
        return

    status_msg = await event.reply("🔍 Analyzing media with MTProto AI engine...")
    t0 = time.perf_counter()

    # Download media in RAM
    media_bytes = await reply_msg.download_media(file=bytes, thumb=-1)
    if not media_bytes or len(media_bytes) < 100:
        media_bytes = await reply_msg.download_media(file=bytes)

    if not media_bytes:
        await status_msg.edit("⚠️ Failed to download media bytes.")
        return

    sens = get_chat_sensitivity(event.chat_id)
    res = engine.process_image_bytes(media_bytes, sensitivity=sens)

    media_type = identify_media_type(reply_msg)
    is_del = res["decision"]["should_delete"]
    icon = "🚨" if is_del else "✅"
    clean_reason = res["decision"]["reason"].replace("_", " ")

    reply_text = (
        f"{icon} **Scan Result for {media_type.upper()}:**\n\n"
        f"• **Verdict:** `{'DELETE (NSFW)' if is_del else 'SAFE (PASS)'}`\n"
        f"• **NSFW Score:** `{res['nsfw_score']*100:.1f}%`\n"
        f"• **Action:** `{res['decision']['action']}`\n"
        f"• **Reason:** {clean_reason}\n"
        f"• **Latency:** `{res['latency_ms']} ms`"
    )
    await status_msg.edit(reply_text, buttons=get_support_buttons())

    if is_del:
        # Delete the offensive replied message immediately!
        try:
            await reply_msg.delete()
            logger.info(f"🚨 Deleted replied NSFW {media_type} via /check")
        except Exception as e:
            logger.error(f"Error deleting replied message: {e}")

        if config.TELEGRAM_WARNING_AUTO_DELETE_SEC > 0:
            asyncio.create_task(auto_delete_msg(event.chat_id, status_msg.id, config.TELEGRAM_WARNING_AUTO_DELETE_SEC))


# Intercept new media messages and edited messages
@client.on(events.NewMessage)
@client.on(events.MessageEdited)
async def media_auto_moderator(event):
    message = event.message
    if not message.media:
        return

    # Skip command messages
    if message.text and message.text.startswith("/"):
        return

    chat_id = event.chat_id
    message_id = message.id

    # Resolve sender name / clickable mention
    sender = await event.get_sender()
    if sender:
        first = getattr(sender, "first_name", "") or getattr(sender, "title", "") or "User"
        sender_mention = f"[{first}](tg://user?id={sender.id})"
    else:
        sender_mention = "User"

    media_type = identify_media_type(message)
    logger.info(f"Incoming {media_type} from {sender_mention} in chat {chat_id}")

    try:
        # 1. Download preview directly into RAM bytes over MTProto
        t0 = time.perf_counter()
        media_bytes = await message.download_media(file=bytes, thumb=-1)
        if not media_bytes or len(media_bytes) < 100:
            media_bytes = await message.download_media(file=bytes)

        if not media_bytes or len(media_bytes) < 100:
            return

        # 2. Check if NSFW Shield is enabled for this chat
        settings = database.get_group_settings(chat_id)
        if not settings.get("nsfw_enabled", True):
            return

        sens = settings.get("sensitivity", "balanced")
        res = engine.process_image_bytes(media_bytes, sensitivity=sens)
        total_time_ms = round((time.perf_counter() - t0) * 1000, 2)

        logger.info(
            f"Evaluated {media_type}: should_delete={res['decision']['should_delete']}, "
            f"score={res['nsfw_score']}, total_latency={total_time_ms}ms"
        )

        # 3. Auto-delete if NSFW
        if res["decision"]["should_delete"]:
            try:
                # Instant MTProto deletion
                await message.delete()
                logger.warning(
                    f"🚨 DELETED {media_type} from {sender_mention} in chat {chat_id}: "
                    f"{res['decision']['reason']} ({total_time_ms}ms)"
                )

                # Send formatted notification matching Edit-Guardians style
                if config.TELEGRAM_SEND_WARNING:
                    warn_text = f"🚨 - {sender_mention} sent 18+ NSFW {media_type.lower()}, and I deleted it 🔞."
                    sent = await client.send_message(
                        chat_id,
                        warn_text,
                        buttons=get_support_buttons()
                    )
                    if config.TELEGRAM_WARNING_AUTO_DELETE_SEC > 0:
                        asyncio.create_task(
                            auto_delete_msg(chat_id, sent.id, config.TELEGRAM_WARNING_AUTO_DELETE_SEC)
                        )

            except Exception as del_err:
                logger.error(f"❌ Error deleting message: {del_err}")
                err_str = str(del_err).lower()
                if "rights" in err_str or "admin" in err_str or "permission" in err_str:
                    chat = await event.get_chat()
                    chat_title = getattr(chat, "title", "Group")
                    await check_admin_and_auto_leave(chat_id, chat_title)
                elif "can't be deleted" in err_str:
                    clean_reason = res["decision"]["reason"].replace("_", " ")
                    await client.send_message(
                        chat_id,
                        f"⚠️ **18+ NSFW Detected from Admin/Creator ({sender_mention})!**\n"
                        f"_Reason: {clean_reason}_\n"
                        f"*(Telegram restricts bots from deleting Group Creator messages. Please delete manually!)*"
                    )

    except Exception as err:
        logger.error(f"Error handling media message: {err}", exc_info=True)


# Edit-Guardian Feature: Auto-delete edited messages in groups
@client.on(events.MessageEdited)
async def edited_message_guardian(event):
    if event.is_private:
        return

    chat_id = event.chat_id

    # Check if Edit Guardian is enabled for this chat
    settings = database.get_group_settings(chat_id)
    if not settings.get("edit_guard_enabled", True):
        return

    # If it has media, the media_auto_moderator also inspects it
    message = event.message

    sender = await event.get_sender()
    if sender:
        first = getattr(sender, "first_name", "") or getattr(sender, "title", "") or "User"
        sender_mention = f"[{first}](tg://user?id={sender.id})"
    else:
        sender_mention = "User"

    try:
        await message.delete()
        warn_text = f"🚨 - {sender_mention} just edited a message, and I deleted it 🐸."
        sent = await client.send_message(chat_id, warn_text, buttons=get_support_buttons())
        if config.TELEGRAM_WARNING_AUTO_DELETE_SEC > 0:
            asyncio.create_task(auto_delete_msg(chat_id, sent.id, config.TELEGRAM_WARNING_AUTO_DELETE_SEC))
    except Exception as e:
        logger.error(f"Error deleting edited message: {e}")
        err_str = str(e).lower()
        if "rights" in err_str or "admin" in err_str or "permission" in err_str:
            chat = await event.get_chat()
            chat_title = getattr(chat, "title", "Group")
            await check_admin_and_auto_leave(chat_id, chat_title)


async def run_bot_session():
    while True:
        try:
            logger.info("Connecting to Telegram MTProto...")
            await client.start(bot_token=BOT_TOKEN)
            me = await client.get_me()
            logger.info(f"🚀 Telethon MTProto Bot running 24/7 as @{me.username} (ID: {me.id})")
            await client.run_until_disconnected()
        except (ConnectionError, asyncio.TimeoutError, OSError) as net_err:
            logger.warning(f"⚠️ Network connection dropped: {net_err}. Auto-reconnecting in 5s...")
            await asyncio.sleep(5)
        except Exception as err:
            logger.error(f"⚠️ Unexpected bot error: {err}. Auto-reconnecting in 10s...", exc_info=True)
            await asyncio.sleep(10)


def main():
    while True:
        try:
            asyncio.run(run_bot_session())
        except KeyboardInterrupt:
            logger.info("Bot stopped by user.")
            break
        except Exception as fatal_err:
            logger.critical(f"FATAL Exception: {fatal_err}. Restarting event loop in 5s...")
            time.sleep(5)


if __name__ == "__main__":
    main()
