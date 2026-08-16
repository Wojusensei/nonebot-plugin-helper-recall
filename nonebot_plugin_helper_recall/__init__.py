from nonebot import on_message, get_driver, get_plugin_config
from nonebot.adapters.onebot.v11 import Bot, Event, GroupMessageEvent
from nonebot.plugin import PluginMetadata
from nonebot.log import logger

from .config import Config

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


async def is_recall_command(event: Event) -> bool:
    """精确匹配 /撤回 命令（遵从 command_start 配置）。

    不使用 on_command：引用消息时第一个消息段是 reply 段（非文本），
    nonebot 的命令前缀匹配只检查首段，会导致"引用 + /撤回"无法触发。
    """
    text = event.get_plaintext().strip()
    starts = set(get_driver().config.command_start) | {""}
    return any(text == f"{start}撤回" for start in starts)


recall_cmd = on_message(is_recall_command, priority=10, block=True)


@recall_cmd.handle()
async def handle_recall(bot: Bot, event: Event):
    if not isinstance(event, GroupMessageEvent):
        await recall_cmd.finish("该命令仅支持群聊使用")

    reply = event.reply
    if not reply:
        await recall_cmd.finish("请先引用要撤回的消息，再发送 /撤回")

    if reply.sender.user_id != event.user_id:
        await recall_cmd.finish("仅支持撤回自己的消息哦~")

    # Bot 自身需要群管理员/群主权限才能撤回他人消息
    try:
        bot_info = await bot.get_group_member_info(
            group_id=event.group_id, user_id=int(bot.self_id)
        )
    except Exception as e:
        logger.error(f"获取bot权限失败: {e}")
        await recall_cmd.finish("权限检查失败，请稍后再试")

    if bot_info.get("role") not in ("admin", "owner"):
        await recall_cmd.finish("群主没有给我配置撤回权限捏")

    try:
        await bot.delete_msg(message_id=reply.message_id)
    except Exception as e:
        error_msg = str(e)
        logger.error(f"撤回失败: {e}")
        if any(k in error_msg for k in ("时间", "超时", "过期", "time", "timeout")):
            await recall_cmd.finish("该消息已超出可撤回时限，撤回失败喵")
        # 不把原始 API 错误直接发到群里，详情见日志
        await recall_cmd.finish("诶诶撤回失败了喵，请稍后再试")

    await recall_cmd.finish("后悔药生效了喵，撤回成功了喵awa")
