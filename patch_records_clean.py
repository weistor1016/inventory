import re

with open('/mnt/c/Users/wei/Desktop/inventory/templates/records.html', 'r') as f:
    content = f.read()

old_td = """<td class="text-center" style="min-width: 180px;">
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

new_td = """<td class="text-center">
                                <form action="{{ url_for('toggle_session_return', entry_id=entry.id) }}" method="POST" id="form_draft_{{ entry.id }}" class="m-0 p-0 d-inline">
                                    <input type="hidden" name="qty" id="qty_draft_{{ entry.id }}" value="1">
                                    <input type="hidden" name="action" id="action_draft_{{ entry.id }}" value="return">
                                    
                                    {% if entry.is_returned %}
                                        <button type="button" class="btn btn-sm w-75 btn-success" 
                                                onclick="handleReturn('draft_{{ entry.id }}', {{ entry.qty_returned }}, 'undo')">
                                            Returned
                                        </button>
                                    {% else %}
                                        <button type="button" class="btn btn-sm w-75 btn-outline-secondary"
                                                onclick="handleReturn('draft_{{ entry.id }}', {{ entry.qty - entry.qty_returned }}, 'return')">
                                            Out
                                        </button>
                                    {% endif %}
                                </form>
                            </td>"""

content = content.replace(old_td, new_td)

script = """
{% endblock %}
<script>
function handleReturn(formId, maxQty, actionType) {
    let qty = 1;
    if (maxQty > 1) {
        let actionText = actionType === 'undo' ? 'undo return for' : 'return';
        let input = prompt(`How many items do you want to ${actionText}? (Max: ${maxQty})`, maxQty);
        if (input === null) return; // cancelled
        qty = parseInt(input);
        if (isNaN(qty) || qty <= 0 || qty > maxQty) {
            alert("Invalid quantity entered.");
            return;
        }
    } else {
        qty = 1;
    }
    
    document.getElementById('qty_' + formId).value = qty;
    document.getElementById('action_' + formId).value = actionType;
    document.getElementById('form_' + formId).submit();
}
</script>
"""

content = content.replace("{% endblock %}", script)

with open('/mnt/c/Users/wei/Desktop/inventory/templates/records.html', 'w') as f:
    f.write(content)
