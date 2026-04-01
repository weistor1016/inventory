import re

with open('/mnt/c/Users/wei/Desktop/inventory/templates/records.html', 'r') as f:
    content = f.read()

old_qty = """<td class="text-center fw-bold">
                                {{ entry.qty }}
                            </td>"""

new_qty = """<td class="text-center fw-bold">
                                {% if entry.qty_returned > 0 and entry.qty_returned < entry.qty %}
                                    {{ entry.qty - entry.qty_returned }} <small class="text-muted fw-normal">({{ entry.qty_returned }} ret)</small>
                                {% else %}
                                    {{ entry.qty }}
                                {% endif %}
                            </td>"""

content = content.replace(old_qty, new_qty)

with open('/mnt/c/Users/wei/Desktop/inventory/templates/records.html', 'w') as f:
    f.write(content)
