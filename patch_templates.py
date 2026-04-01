import re

with open('/mnt/c/Users/wei/Desktop/inventory/templates/records.html', 'r') as f:
    content = f.read()

old_block = """<td class="text-center" style="min-width: 140px;">
                                {% if entry.qty > 1 %}
                                <form action="{{ url_for('toggle_session_return', entry_id=entry.id) }}" method="POST" class="d-inline-flex m-0 p-0 justify-content-center" style="max-width: 120px;">
                                    <div class="input-group input-group-sm shadow-sm">
                                        <input type="number" name="qty" min="1" max="{{ entry.qty }}" value="1" class="form-control text-center px-1" style="max-width: 45px;">
                                        <button type="submit" class="btn {{ 'btn-success' if entry.is_returned else 'btn-outline-secondary' }}">
                                            {{ 'Ret' if entry.is_returned else 'Out' }}
                                        </button>
                                    </div>
                                </form>
                                {% else %}
                                <a href="{{ url_for('toggle_session_return', entry_id=entry.id) }}" 
                                   class="btn btn-sm w-75 {{ 'btn-success' if entry.is_returned else 'btn-outline-secondary' }} shadow-sm">
                                    {{ 'Returned' if entry.is_returned else 'Out' }}
                                </a>
                                {% endif %}
                            </td>"""

new_block = """<td class="text-center" style="min-width: 180px;">
                                {% if entry.qty_returned > 0 %}
                                    <span class="badge bg-success mb-1 d-block">{{ entry.qty_returned }} Returned</span>
                                {% endif %}
                                {% if entry.qty > entry.qty_returned %}
                                <form action="{{ url_for('toggle_session_return', entry_id=entry.id) }}" method="POST" class="d-inline-flex m-0 p-0 justify-content-center w-100">
                                    <input type="hidden" name="action" value="return">
                                    <div class="input-group input-group-sm shadow-sm w-100">
                                        <input type="number" name="qty" min="1" max="{{ entry.qty - entry.qty_returned }}" value="{{ entry.qty - entry.qty_returned }}" class="form-control text-center px-1">
                                        <button type="submit" class="btn btn-outline-success">Return</button>
                                    </div>
                                </form>
                                {% endif %}
                                
                                {% if entry.qty_returned > 0 %}
                                <form action="{{ url_for('toggle_session_return', entry_id=entry.id) }}" method="POST" class="d-inline-flex m-0 p-0 justify-content-center w-100 mt-1">
                                    <input type="hidden" name="action" value="undo">
                                    <div class="input-group input-group-sm shadow-sm w-100">
                                        <input type="number" name="qty" min="1" max="{{ entry.qty_returned }}" value="{{ entry.qty_returned }}" class="form-control text-center px-1">
                                        <button type="submit" class="btn btn-outline-danger">Undo</button>
                                    </div>
                                </form>
                                {% endif %}
                            </td>"""

content = content.replace(old_block, new_block)

with open('/mnt/c/Users/wei/Desktop/inventory/templates/records.html', 'w') as f:
    f.write(content)
