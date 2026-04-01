import re

with open('/mnt/c/Users/wei/Desktop/inventory/templates/index.html', 'r') as f:
    content = f.read()

content = content.replace('<h5 class="mt-3">New Record</h5>', '<h6 class="mt-3 mb-0 fw-bold text-nowrap">New Record</h6>')
content = content.replace('<h5 class="mt-3">History</h5>', '<h6 class="mt-3 mb-0 fw-bold text-nowrap">History</h6>')
content = content.replace('<h5 class="mt-3">Inventory</h5>', '<h6 class="mt-3 mb-0 fw-bold text-nowrap">Inventory</h6>')
content = content.replace('<h5 class="mt-3">Settings</h5>', '<h6 class="mt-3 mb-0 fw-bold text-nowrap">Settings</h6>')

# Reduce padding on mobile for those cards to ensure text fits
content = content.replace('p-3 hover-shadow', 'p-2 p-md-3 hover-shadow')

with open('/mnt/c/Users/wei/Desktop/inventory/templates/index.html', 'w') as f:
    f.write(content)
