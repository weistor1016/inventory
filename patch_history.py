import re

with open('/mnt/c/Users/wei/Desktop/inventory/templates/session_details.html', 'r') as f:
    content = f.read()

# Make history detail columns wider on mobile
content = content.replace("<th>Item Name</th>\n                    <th class=\"text-center\">Qty</th>\n                    <th class=\"text-center\">Status</th>\n                    <th class=\"text-end\">Action</th>", 
                          "<th class=\"text-nowrap\">Item Name</th>\n                    <th class=\"text-center text-nowrap\">Qty</th>\n                    <th class=\"text-center text-nowrap\">Status</th>\n                    <th class=\"text-end text-nowrap\">Action</th>")

with open('/mnt/c/Users/wei/Desktop/inventory/templates/session_details.html', 'w') as f:
    f.write(content)
