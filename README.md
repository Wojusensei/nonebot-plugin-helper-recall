# nonebot-plugin-helper-recall

✨ 帮撤回插件 ✨

帮助普通群员撤回自己因超时无法撤回的消息，需要bot被群主授予管理员权限(想给bot群主我也没意见(bushi))

## 功能

- 引用自己发送的消息，发送 `/撤回` 指令
- Bot 尝试撤回该消息

## 安装(指令二选一，无区别)

```bash
nb plugin install nonebot-plugin-helper-recall
pip install nonebot-plugin-helper-recall
```

## 使用

1. 确保 Bot 是群管理员
2. 群员引用自己发送的任意消息（包括超时的）
3. 在同一条消息中发送 `/撤回`
4. Bot 会撤回那条被引用的消息

## 注意事项

- 仅支持撤回自己的消息
- 如果消息已超过 QQ 可撤回时间，会提示失败（不是两分钟那个
- 需要 Bot 有管理员权限

## 配置

无需配置，即装即用

## 开源协议

MIT
