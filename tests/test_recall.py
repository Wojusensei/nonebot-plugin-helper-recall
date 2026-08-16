"""帮撤回命令测试（nonebug）"""
from nonebot.adapters.onebot.v11 import Bot as OB11Bot, Message, MessageSegment
from nonebot.adapters.onebot.v11.event import (
    GroupMessageEvent,
    PrivateMessageEvent,
    Reply,
    Sender,
)

from nonebot_plugin_helper_recall import recall_cmd


def make_group_event(text: str, group_id: int = 10000, user_id: int = 20000,
                     reply: Reply = None) -> GroupMessageEvent:
    msg = Message(text)
    if reply:
        msg = Message([MessageSegment.reply(reply.message_id), MessageSegment.text(text)])
    return GroupMessageEvent(
        time=1122,
        self_id=1,
        post_type="message",
        sub_type="normal",
        user_id=user_id,
        message_type="group",
        message_id=1234,
        message=msg,
        raw_message=str(msg),
        font=0,
        sender=Sender(user_id=user_id, nickname="test"),
        group_id=group_id,
        reply=reply,
    )


def make_reply(quoted_user_id: int = 20000, message_id: int = 5678) -> Reply:
    return Reply(
        time=1100,
        message_type="group",
        message_id=message_id,
        real_id=message_id,
        sender=Sender(user_id=quoted_user_id, nickname="quoted"),
        message=Message("被引用的内容"),
    )


def make_private_event(text: str, user_id: int = 20000) -> PrivateMessageEvent:
    return PrivateMessageEvent(
        time=1122,
        self_id=1,
        post_type="message",
        sub_type="friend",
        user_id=user_id,
        message_type="private",
        message_id=1234,
        message=Message(text),
        raw_message=text,
        font=0,
        sender=Sender(user_id=user_id, nickname="test"),
    )


async def test_casual_mention_does_not_trigger(app):
    """回归：日常聊天中提到"撤回"二字不应触发任何回复"""
    async with app.test_matcher() as ctx:
        adapter = ctx.create_adapter()
        bot = ctx.create_bot(adapter=adapter, base=OB11Bot, self_id="1")
        # 带引用的普通聊天（内容含"撤回"）也不应触发
        ctx.receive_event(bot, make_group_event("你撤回干嘛"))
        ctx.receive_event(
            bot,
            make_group_event("我说错话了想撤回", reply=make_reply()),
        )


async def test_private_gets_reply(app):
    """回归：私聊应提示仅支持群聊，而不是无响应"""
    async with app.test_matcher() as ctx:
        adapter = ctx.create_adapter()
        bot = ctx.create_bot(adapter=adapter, base=OB11Bot, self_id="1")
        event = make_private_event("/撤回")
        ctx.receive_event(bot, event)
        ctx.should_call_send(event, "该命令仅支持群聊使用", result=None, bot=bot)
        ctx.should_finished(recall_cmd)


async def test_no_reply_prompt(app):
    async with app.test_matcher() as ctx:
        adapter = ctx.create_adapter()
        bot = ctx.create_bot(adapter=adapter, base=OB11Bot, self_id="1")
        event = make_group_event("/撤回")
        ctx.receive_event(bot, event)
        ctx.should_call_send(event, "请先引用要撤回的消息，再发送 /撤回", result=None, bot=bot)
        ctx.should_finished(recall_cmd)


async def test_only_own_messages(app):
    async with app.test_matcher() as ctx:
        adapter = ctx.create_adapter()
        bot = ctx.create_bot(adapter=adapter, base=OB11Bot, self_id="1")
        # 引用的是别人的消息
        event = make_group_event("/撤回", user_id=20000, reply=make_reply(quoted_user_id=30000))
        ctx.receive_event(bot, event)
        ctx.should_call_send(event, "仅支持撤回自己的消息哦~", result=None, bot=bot)
        ctx.should_finished(recall_cmd)


async def test_bot_not_admin(app):
    async with app.test_matcher() as ctx:
        adapter = ctx.create_adapter()
        bot = ctx.create_bot(adapter=adapter, base=OB11Bot, self_id="1")
        event = make_group_event("/撤回", reply=make_reply())
        ctx.receive_event(bot, event)
        ctx.should_call_api(
            "get_group_member_info",
            data={"group_id": 10000, "user_id": 1},
            result={"role": "member", "user_id": 1, "nickname": "bot"},
        )
        ctx.should_call_send(event, "群主没有给我配置撤回权限捏", result=None, bot=bot)
        ctx.should_finished(recall_cmd)


async def test_recall_success_no_extra_error(app):
    """回归：撤回成功后不应再追加一条失败提示（finish 在 try 内被吞）"""
    async with app.test_matcher() as ctx:
        adapter = ctx.create_adapter()
        bot = ctx.create_bot(adapter=adapter, base=OB11Bot, self_id="1")
        event = make_group_event("/撤回", reply=make_reply())
        ctx.receive_event(bot, event)
        ctx.should_call_api(
            "get_group_member_info",
            data={"group_id": 10000, "user_id": 1},
            result={"role": "admin", "user_id": 1, "nickname": "bot"},
        )
        ctx.should_call_api("delete_msg", data={"message_id": 5678}, result={})
        ctx.should_call_send(event, "后悔药生效了喵，撤回成功了喵awa", result=None, bot=bot)
        ctx.should_finished(recall_cmd)


async def test_recall_timeout_error(app):
    async with app.test_matcher() as ctx:
        adapter = ctx.create_adapter()
        bot = ctx.create_bot(adapter=adapter, base=OB11Bot, self_id="1")
        event = make_group_event("/撤回", reply=make_reply())
        ctx.receive_event(bot, event)
        ctx.should_call_api(
            "get_group_member_info",
            data={"group_id": 10000, "user_id": 1},
            result={"role": "admin", "user_id": 1, "nickname": "bot"},
        )
        ctx.should_call_api(
            "delete_msg",
            data={"message_id": 5678},
            exception=Exception("消息已超时，无法撤回"),
        )
        ctx.should_call_send(event, "该消息已超出可撤回时限，撤回失败喵", result=None, bot=bot)
        ctx.should_finished(recall_cmd)


async def test_recall_other_error_no_leak(app):
    """回归：其他错误不应把原始 API 错误信息发到群里"""
    async with app.test_matcher() as ctx:
        adapter = ctx.create_adapter()
        bot = ctx.create_bot(adapter=adapter, base=OB11Bot, self_id="1")
        event = make_group_event("/撤回", reply=make_reply())
        ctx.receive_event(bot, event)
        ctx.should_call_api(
            "get_group_member_info",
            data={"group_id": 10000, "user_id": 1},
            result={"role": "admin", "user_id": 1, "nickname": "bot"},
        )
        ctx.should_call_api(
            "delete_msg",
            data={"message_id": 5678},
            exception=Exception("InternalServerError: secret-token-123"),
        )
        ctx.should_call_send(event, "诶诶撤回失败了喵，请稍后再试", result=None, bot=bot)
        ctx.should_finished(recall_cmd)
