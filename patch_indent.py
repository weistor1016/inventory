with open('/mnt/c/Users/wei/Desktop/inventory/app.py', 'r') as f:
    content = f.read()
import re
content = re.sub(r'today_date=today_str\), \n                           items=display_items, \n                           clients=clients, \n                           grouped_entries=grouped_entries,\n                           last_client_id=session.get\(\'last_client_id\'\),\n                           today_date=today_str\)', 'today_date=today_str)', content)
with open('/mnt/c/Users/wei/Desktop/inventory/app.py', 'w') as f:
    f.write(content)
