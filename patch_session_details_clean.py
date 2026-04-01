import re

with open('/mnt/c/Users/wei/Desktop/inventory/templates/session_details.html', 'r') as f:
    content = f.read()

status_old = """<td class="text-center">
                        {% if r.is_sold %}
                            <span class="badge bg-dark px-3 py-2">
                                <i class="bi bi-cash-stack me-1"></i> Sold
                            </span>
                        {% else %}
                            {% if r.quantity_returned >= r.quantity_out %}
                                <span class="badge bg-success px-3 py-2 mb-1 d-block">
                                    <i class="bi bi-check-lg me-1"></i> Returned ({{ r.quantity_returned }})
                                </span>
                            {% elif r.quantity_returned > 0 %}
                                <span class="badge bg-warning text-dark px-2 py-1 mb-1 d-block">
                                    <i class="bi bi-box-arrow-up me-1"></i> Out ({{ r.quantity_out - r.quantity_returned }})
                                </span>
                                <span class="badge bg-success px-2 py-1 d-block">
                                    <i class="bi bi-check-lg me-1"></i> Returned ({{ r.quantity_returned }})
                                </span>
                            {% else %}
                                <span class="badge bg-warning text-dark px-3 py-2">
                                    <i class="bi bi-box-arrow-up me-1"></i> Out ({{ r.quantity_out }})
                                </span>
                            {% endif %}
                        {% endif %}
                    </td>"""

status_new = """<td class="text-center">
                        {% if r.is_sold %}
                            <span class="badge bg-dark px-3 py-2">
                                <i class="bi bi-cash-stack me-1"></i> Sold
                            </span>
                        {% elif r.is_returned %}
                            <span class="badge bg-success px-3 py-2">
                                <i class="bi bi-check-lg me-1"></i> Returned
                            </span>
                        {% elif r.item_is_archived %}
                            <span class="badge bg-secondary px-3 py-2 text-white">
                                <i class="bi bi-archive-fill me-1"></i> Out (Archived)
                            </span>
                        {% else %}
                            <span class="badge bg-warning text-dark px-3 py-2">
                                <i class="bi bi-box-arrow-up me-1"></i> Out
                            </span>
                        {% endif %}
                        {% if r.quantity_returned > 0 and r.quantity_returned < r.quantity_out %}
                            <br><small class="text-muted fw-bold">{{ r.quantity_returned }} returned</small>
                        {% endif %}
                    </td>"""

actions_old = """<div class="d-flex flex-column align-items-end gap-1">
                                {% if not r.is_sold %}
                                    
                                    {% if r.quantity_returned < r.quantity_out %}
                                    <form action="{{ url_for('toggle_return', record_id=r.id) }}" method="POST" class="m-0 p-0">
                                        <input type="hidden" name="action" value="return">
                                        <div class="input-group input-group-sm shadow-sm">
                                            <input type="number" name="qty" min="1" max="{{ r.quantity_out - r.quantity_returned }}" value="{{ r.quantity_out - r.quantity_returned }}" class="form-control text-center px-1" style="max-width: 50px;">
                                            <button type="submit" class="btn btn-outline-success" title="Return items">
                                                Return
                                            </button>
                                        </div>
                                    </form>
                                    {% endif %}
                                    
                                    {% if r.quantity_returned > 0 %}
                                    <form action="{{ url_for('toggle_return', record_id=r.id) }}" method="POST" class="m-0 p-0">
                                        <input type="hidden" name="action" value="undo">
                                        <div class="input-group input-group-sm shadow-sm">
                                            <input type="number" name="qty" min="1" max="{{ r.quantity_returned }}" value="{{ r.quantity_returned }}" class="form-control text-center px-1" style="max-width: 50px;">
                                            <button type="submit" class="btn btn-outline-danger" title="Undo return">
                                                Undo Return
                                            </button>
                                        </div>
                                    </form>
                                    {% endif %}
                                    
                                {% endif %}
                                
                                {% if r.quantity_returned < r.quantity_out %}
                                <a href="{{ url_for('toggle_sold', record_id=r.id) }}" 
                                   class="btn btn-sm {{ 'btn-dark text-white' if r.is_sold else 'btn-outline-dark' }} shadow-sm w-100 mt-1" 
                                   onclick="return confirm('{{ 'Undo mark as sold?' if r.is_sold else 'Mark this as sold? Inventory will NOT be replenished.' }}')"
                                   title="{{ 'Unmark as Sold' if r.is_sold else 'Mark as Sold' }}">
                                    <i class="bi bi-cart-plus"></i> {{ 'Undo Sold' if r.is_sold else 'Sell' }}
                                </a>
                                {% endif %}
                            </div>"""

actions_new = """<div class="btn-group shadow-sm">
                                {% if not r.is_sold %}
                                    <form action="{{ url_for('toggle_return', record_id=r.id) }}" method="POST" id="form_history_{{ r.id }}" class="m-0 p-0" style="display: inline-block;">
                                        <input type="hidden" name="qty" id="qty_history_{{ r.id }}" value="1">
                                        <input type="hidden" name="action" id="action_history_{{ r.id }}" value="return">
                                        
                                        {% if r.is_returned %}
                                            <button type="button" class="btn btn-sm btn-success" 
                                                    style="border-top-right-radius: 0; border-bottom-right-radius: 0;"
                                                    onclick="handleReturn('history_{{ r.id }}', {{ r.quantity_returned }}, 'undo')" title="Undo Return">
                                                <i class="bi bi-arrow-left-right"></i> Return
                                            </button>
                                        {% else %}
                                            <button type="button" class="btn btn-sm btn-outline-primary" 
                                                    style="border-top-right-radius: 0; border-bottom-right-radius: 0;"
                                                    onclick="handleReturn('history_{{ r.id }}', {{ r.quantity_out - r.quantity_returned }}, 'return')" title="Toggle Return">
                                                <i class="bi bi-arrow-left-right"></i> Return
                                            </button>
                                        {% endif %}
                                    </form>
                                {% endif %}
                                
                                {% if not r.is_returned %}
                                <a href="{{ url_for('toggle_sold', record_id=r.id) }}" 
                                   class="btn btn-sm {{ 'btn-dark text-white' if r.is_sold else 'btn-outline-dark' }}" 
                                   onclick="return confirm('{{ 'Undo mark as sold?' if r.is_sold else 'Mark this as sold? Inventory will NOT be replenished.' }}')"
                                   title="{{ 'Unmark as Sold' if r.is_sold else 'Mark as Sold' }}">
                                    <i class="bi bi-cart-plus"></i> {{ 'Undo Sold' if r.is_sold else 'Sell' }}
                                </a>
                                {% endif %}
                            </div>"""

content = content.replace(status_old, status_new).replace(actions_old, actions_new)

script = """
{% endblock %}
<script>
function handleReturn(formId, maxQty, actionType) {
    let qty = 1;
    if (maxQty > 1) {
        let actionText = actionType === 'undo' ? 'undo return for' : 'return';
        let input = prompt(`How many items do you want to ${actionText}? (Max: ${maxQty})`, maxQty);
        if (input === null) return; // User cancelled
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
if "<script>" not in content:
    content = content.replace("{% endblock %}", script)

with open('/mnt/c/Users/wei/Desktop/inventory/templates/session_details.html', 'w') as f:
    f.write(content)
