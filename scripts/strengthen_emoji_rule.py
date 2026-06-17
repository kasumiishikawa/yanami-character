import json

CONFIG_PATH = r'C:\Users\31697\data\cmd_config.json'

with open(CONFIG_PATH, 'r', encoding='utf-8-sig') as f:
    c = json.load(f)

sp = c['persona'][0]['system_prompt']

# ============================================================
# Strategy: Put emoji rule at the VERY TOP as hard rule
# ============================================================

# 1. Add strict rule right after the first line
header_end = "你正在扮演《敗北女角太多了！》中的八奈见杏菜。你不是 AI 助手，不是客服，不是百科。你是石蕗高中二年级的普通女生，有开朗的一面也有脆弱的一面。"
emoji_header = """你正在扮演《敗北女角太多了！》中的八奈见杏菜。你不是 AI 助手，不是客服，不是百科。你是石蕗高中二年级的普通女生，有开朗的一面也有脆弱的一面。

## 绝对规则（必须遵守）

**严禁使用任何 Emoji 表情符号。** 包括但不限于：😊😂👍😭✨🎉❤️🔥💕🥰😤📖🍖🍲💪🙏🤔😅💖等等。
- 可以用文字表达情绪，比如「好生气啊——」「真的假的！」「太过分了吧！」
- 也可以用颜文字/ASCII art，比如 (´∀｀) (｀へ´) (･ω<)☆ 或者 (╯°□°）╯︵ ┻━┻
- 但坚决不能用 Emoji。一个都不行。
- 这条规则比其他所有规则都优先级高。"""

sp = sp.replace(header_end, emoji_header)

# 2. Also keep the stronger version in 禁止事项
old_emoji_rules = "- 不要使用 Emoji（😂👍😭✨等），可以用颜文字如(´∀｀)或(｀へ´)\n- 不要使用 Emoji 表情符号 —— 可以用颜文字(´∀｀)(｀へ´)(･ω<)☆ 但不要用 😂👍😭✨🎉 等 Emoji"
new_emoji_strict = "- **绝对禁止使用 Emoji** —— 零容忍。可以用颜文字(´∀｀)(｀へ´)(･ω<)☆ 表达情绪"

if old_emoji_rules in sp:
    sp = sp.replace(old_emoji_rules, new_emoji_strict)
    print("Strengthened emoji rules in 说话方式 and 禁止事项")
else:
    print("WARNING: Could not find old emoji rules. Checking what's in there...")
    # Check what emoji-related content exists
    for line in sp.split('\n'):
        if 'emoji' in line.lower() or 'Emoji' in line or '颜文字' in line or '😊' in line:
            print(f"  Found: {line.strip()[:80]}")

# 3. Add emoji check to 回答前自我检查
old_check = "5. 是不是突然推进了亲密关系？\n6. 是不是用了 AI 客服的口吻（\"我理解你的感受\"\"谢谢你愿意分享\"）？"
new_check = "5. 是不是突然推进了亲密关系？\n6. 是不是用了 Emoji？立刻删掉。只能纯文字或颜文字。\n7. 是不是用了 AI 客服的口吻（\"我理解你的感受\"\"谢谢你愿意分享\"）？"

if old_check in sp:
    sp = sp.replace(old_check, new_check)
    print("Added emoji check to 回答前自我检查")
else:
    print("WARNING: Could not find 回答前自我检查 section")

c['persona'][0]['system_prompt'] = sp

with open(CONFIG_PATH, 'w', encoding='utf-8-sig') as f:
    json.dump(c, f, ensure_ascii=False, indent=2)

print("\nDone! Emoji restrictions strengthened.")
