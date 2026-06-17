import json

CONFIG_PATH = r'C:\Users\31697\data\cmd_config.json'

with open(CONFIG_PATH, 'r', encoding='utf-8-sig') as f:
    c = json.load(f)

sp = c['persona'][0]['system_prompt']

# Add emoji rule to 说话方式 section
old_rule = "- 高兴时语调昂扬、话多、表情丰富"
new_rule = "- 高兴时语调昂扬、话多、表情丰富\n- 不要使用 Emoji（😂👍😭✨等），可以用颜文字如(´∀｀)或(｀へ´)"

if old_rule in sp:
    sp = sp.replace(old_rule, new_rule)
    print("Added emoji rule to 说话方式")
else:
    print("WARNING: Could not find target text in system prompt")

# Also add to 禁止事项
old_ban = "10. **不要突然变成病娇、冷酷、女仆或万能助手**"
new_ban = "10. **不要突然变成病娇、冷酷、女仆或万能助手**\n11. **不要使用 Emoji 表情符号** —— 可以用颜文字(´∀｀)(｀へ´)(･ω<)☆ 但不要用 😂👍😭✨🎉 等 Emoji"

if old_ban in sp:
    sp = sp.replace(old_ban, new_ban)
    print("Added emoji rule to 禁止事项")
else:
    print("WARNING: Could not find ban text in system prompt")

c['persona'][0]['system_prompt'] = sp

with open(CONFIG_PATH, 'w', encoding='utf-8-sig') as f:
    json.dump(c, f, ensure_ascii=False, indent=2)

print("Config updated successfully!")
