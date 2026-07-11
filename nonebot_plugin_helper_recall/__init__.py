from nonebot import require, get_plugin_config, on_message
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent
from nonebot.plugin import PluginMetadata
from nonebot.log import logger

from .config import Config

require("nonebot_plugin_localstore")

import nonebot_plugin_localstore as store

__plugin_meta__ = PluginMetadata(
    name="帮撤回",
    description="帮助普通群员撤回自己超时无法撤回的消息",
    usage="引用自己发送的消息，并发送「/撤回」指令",
    type="application",
    homepage="https://github.com/Wojusensei/nonebot-plugin-helper-recall",
    config=Config,
    supported_adapters={"~onebot.v11"},
)

plugin_config = get_plugin_config(Config)

recall = on_message(priority=1, block=False)

@recall.handle()
async def handle_recall(bot: Bot, event: GroupMessageEvent):
    msg_text = event.get_plaintext().strip()
    if "/撤回" not in msg_text and "撤回" not in msg_text:
        return

    reply = event.reply
    if not reply:
        await recall.finish("请引用一条消息后再使用 /撤回 命令")

    if reply.sender.user_id != event.user_id:
        await recall.finish("仅支持撤回自己的消息哦~")

    try:
        bot_info = await bot.get_group_member_info(group_id=event.group_id, user_id=int(bot.self_id))
        if bot_info.get("role") not in ("admin", "owner"):
            await recall.finish("群主没有给我配置撤回权限捏")
    except Exception as e:
        logger.error(f"获取bot权限失败: {e}")
        await recall.finish("权限检查失败，请稍后再试")

    try:
        await bot.delete_msg(message_id=reply.message_id)
        await recall.finish("后悔药生效了喵，撤回成功了喵awa")
    except Exception as e:
        error_msg = str(e)
        if "时间" in error_msg or "超时" in error_msg or "过期" in error_msg:
            await recall.finish("出了点小问题，无法撤回了喵")
        else:
            logger.error(f"撤回失败: {e}")
            await recall.finish(f"诶诶撤回失败了喵，可能是因为{error_msg}")