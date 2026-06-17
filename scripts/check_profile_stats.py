import re, os

fpath = r'D:\character\data\extracted\yanami_profile.md'
with open(fpath, 'r', encoding='utf-8') as f:
    text = f.read()

lines = text.count('\n')
chars = len(text)
chinese = sum(1 for c in text if '一' <= c <= '鿿')

scene_refs = set(re.findall(r'yanami-candidate-\d+', text))
size = os.path.getsize(fpath)

print(f'文件大小: {size} bytes')
print(f'总行数: {lines}')
print(f'总字符: {chars}')
print(f'中文字符: {chinese}')
print(f'引用不同场景ID: {len(scene_refs)}')
print()

# Section breakdown
sections = re.split(r'\n(?=## )', text)
for s in sections:
    title = s.split('\n')[0]
    slines = s.count('\n') + 1
    print(f'  [{slines:2d}行] {title}')
