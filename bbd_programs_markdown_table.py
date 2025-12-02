import re

with open('bbd.js', 'r') as f:
    content = f.read()

pattern = r'cpy:"([^"]+)",logo:[^,]+,ogImg:[^,]+,url:"([^"]+)",wbImg:[^,]+,ovrvw:"([^"]+)",'
matches = re.findall(pattern, content)

print("| programs | summary |")
print("|-|-|")
for cpy, url, ovrvw in matches:
    print(f"| [{cpy}]({url}) | {ovrvw} |")