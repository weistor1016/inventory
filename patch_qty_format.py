import re

with open('/mnt/c/Users/wei/Desktop/inventory/templates/records.html', 'r') as f:
    content = f.read()

old_block = """<td class="text-center fw-bold">
                                {% if entry.qty_returned > 0 and entry.qty_returned < entry.qty %}
                                    {{ entry.qty - entry.qty_returned }} <small class="text-muted fw-normal">({{ entry.qty_returned }} ret)</small>
                                {% else %}
                                    {{ entry.qty }}
                                {% endif %}
                            </td>"""

new_block = """<td class="text-center fw-bold">
                                {% if entry.qty_returned > 0 and entry.qty_returned < entry.qty %}
                                    {{ entry.qty - entry.qty_returned }}<br>
                                    <small class="text-muted fw-normal text-nowrap">({{ entry.qty_returned }} ret)</small>
                                {% else %}
                                    {{ entry.qty }}
                                {% endif %}
                            </td>"""

content = content.replace(old_block, new_block)

with open('/mnt/c/Users/wei/Desktop/inventory/templates/records.html', 'w') as f:
    f.write(content)
