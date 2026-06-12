from nonebot import require, get_plugin_config, on_command
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent
from nonebot.params import CommandArg
from nonebot.plugin import PluginMetadata
from nonebot.log import logger

from .config import Config

require("nonebot_plugin_localstore")
require("nonebot_plugin_alconna")
from nonebot_plugin_alconna import message_reaction

# ----------------------------------------------------------------
# 插件元数据
# ----------------------------------------------------------------

__plugin_meta__ = PluginMetadata(
    name="帮撤回",
    description="帮助普通群员撤回自己超时无法撤回的消息",
    usage="引用自己发送的消息，并发送「/撤回」指令",
    type="application",
    homepage="https://github.com/Wojusensei/nonebot-plugin-helper-recall",
    config=Config,
    supported_adapters={"~onebot.v11"},
)

# ----------------------------------------------------------------
# 读取配置
# ----------------------------------------------------------------

plugin_config = get_plugin_config(Config)

# ----------------------------------------------------------------
# 命令注册
# ----------------------------------------------------------------

recall = on_command("/撤回", aliases={"撤回"}, priority=10, block=True)


# ----------------------------------------------------------------
# 撤回命令处理函数
# ----------------------------------------------------------------

@recall.handle()
async def handle_recall(bot: Bot, event: GroupMessageEvent, args: str = CommandArg()):
    # ----------------------------------------------------------------
    # 获取引用消息
    # ----------------------------------------------------------------
    reply = event.reply
    if not reply:
        await recall.finish("请引用一条消息后再使用 /撤回 命令")

    # ----------------------------------------------------------------
    # 检查是否为那个用户发送的消息
    # ----------------------------------------------------------------

    if reply.sender.user_id != event.user_id:
        await recall.finish("仅支持撤回自己的消息哦~")

    # ----------------------------------------------------------------
    # 检查bot是否有管理员权限
    # ----------------------------------------------------------------
    try:
        bot_info = await bot.get_group_member_info(group_id=event.group_id, user_id=int(bot.self_id))
        if bot_info.get("role") not in ("admin", "owner"):
            await recall.finish("群主没有给我配置撤回权限捏")
    except Exception as e:
        logger.error(f"获取bot权限失败: {e}")
        await recall.finish("权限检查失败，请稍后再试")

    # ----------------------------------------------------------------
    # 表示正在处理中
    # ----------------------------------------------------------------
    try:
        await message_reaction(
            event=event,
            reaction="/whl",
            target_msg_id=event.message_id,
            set=True
        )
    except Exception as e:
        logger.warning(f"添加表情失败: {e}")

    # ----------------------------------------------------------------
    # 执行撤回
    # ----------------------------------------------------------------
    try:
        await bot.delete_msg(message_id=reply.message_id)
        # ----------------------------------------------------------------
        # 撤回成功 将表情改为喝彩
        # ----------------------------------------------------------------
        try:
            await message_reaction(
                event=event,
                reaction="/hec",
                target_msg_id=event.message_id,
                set=True
            )
        except Exception as e:
            logger.warning(f"修改表情失败: {e}")
        await recall.finish("撤回成功！")
    except Exception as e:
        error_msg = str(e)
        if "时间" in error_msg or "超时" in error_msg or "过期" in error_msg:
            await recall.finish("消息已超过可撤回时间，无法撤回")
        else:
            logger.error(f"撤回失败: {e}")
            await recall.finish(f"撤回失败：{error_msg}")