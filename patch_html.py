import re

with open('/mnt/c/Users/wei/Desktop/inventory/templates/session_details.html', 'r') as f:
    content = f.read()

old_block = """<div class="btn-group shadow-sm">
                                {% if not r.is_sold %}
                                <a href="{{ url_for('toggle_return', record_id=r.id) }}" 
                                   class="btn btn-sm {{ 'btn-success' if r.is_returned else 'btn-outline-primary' }}" 
                                   title="Toggle Return">
                                    <i class="bi bi-arrow-left-right"></i> Return
                                </a>
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

new_block = """<div class="d-flex justify-content-end gap-1">
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

content = content.replace(old_block, new_block)

with open('/mnt/c/Users/wei/Desktop/inventory/templates/session_details.html', 'w') as f:
    f.write(content)
