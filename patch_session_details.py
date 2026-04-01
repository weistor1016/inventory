import re

with open('/mnt/c/Users/wei/Desktop/inventory/templates/session_details.html', 'r') as f:
    content = f.read()

old_block = """<div class="d-flex justify-content-end gap-1">
                                {% if not r.is_sold %}
                                    {% if r.quantity_out > 1 %}
                                    <form action="{{ url_for('toggle_return', record_id=r.id) }}" method="POST" class="m-0 p-0 d-inline-block">
                                        <div class="input-group input-group-sm shadow-sm">
                                            <input type="number" name="qty" min="1" max="{{ r.quantity_out }}" value="1" class="form-control text-center px-1" style="max-width: 45px;">
                                            <button type="submit" class="btn {{ 'btn-success' if r.is_returned else 'btn-outline-primary' }}" title="Toggle partial return">
                                                <i class="bi bi-arrow-left-right"></i>
                                            </button>
                                        </div>
                                    </form>
                                    {% else %}
                                    <a href="{{ url_for('toggle_return', record_id=r.id) }}" 
                                       class="btn btn-sm {{ 'btn-success' if r.is_returned else 'btn-outline-primary' }} shadow-sm" 
                                       title="Toggle Return">
                                        <i class="bi bi-arrow-left-right"></i> Return
                                    </a>
                                    {% endif %}
                                {% endif %}
                                
                                {% if not r.is_returned %}
                                <a href="{{ url_for('toggle_sold', record_id=r.id) }}" 
                                   class="btn btn-sm {{ 'btn-dark text-white' if r.is_sold else 'btn-outline-dark' }} shadow-sm" 
                                   onclick="return confirm('{{ 'Undo mark as sold?' if r.is_sold else 'Mark this as sold? Inventory will NOT be replenished.' }}')"
                                   title="{{ 'Unmark as Sold' if r.is_sold else 'Mark as Sold' }}">
                                    <i class="bi bi-cart-plus"></i> {{ 'Undo Sold' if r.is_sold else 'Sell' }}
                                </a>
                                {% endif %}
                            </div>"""

new_block = """<div class="d-flex flex-column align-items-end gap-1">
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

status_old = """<td class="text-center">
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
                    </td>"""

status_new = """<td class="text-center">
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

content = content.replace(old_block, new_block).replace(status_old, status_new)

with open('/mnt/c/Users/wei/Desktop/inventory/templates/session_details.html', 'w') as f:
    f.write(content)
