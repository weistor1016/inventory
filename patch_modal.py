import re

with open('/mnt/c/Users/wei/Desktop/inventory/templates/settings.html', 'r', encoding='utf-8') as f:
    content = f.read()

modal_block = """{% block modals %}
    {% if user.role == 'boss' %}
        {% for staff in staff_members %}
        <div class="modal" id="staffModal{{ staff.id }}" tabindex="-1" aria-labelledby="staffModalLabel{{ staff.id }}" aria-hidden="true">
            <div class="modal-dialog modal-dialog-centered modal-fullscreen-sm-down">
                <div class="modal-content">
                    <div class="modal-header bg-light">
                        <h5 class="modal-title fw-bold" id="staffModalLabel{{ staff.id }}">
                            <i class="bi bi-person-badge text-primary me-2"></i>Manage: {{ staff.display_name or staff.username }}
                        </h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                    </div>
                    <div class="modal-body">
                        <!-- View/Update Password -->
                        <div class="mb-4">
                            <h6 class="fw-bold text-secondary">Security</h6>
                            <form action="{{ url_for('update_staff_password', staff_id=staff.id) }}" method="POST">
                                <div class="input-group mb-3">
                                    <span class="input-group-text">Current Password:</span>
                                    <input type="text" class="form-control" value="{{ staff.password }}" readonly>
                                </div>
                                <div class="input-group mb-3">
                                    <input type="text" name="new_password" class="form-control" placeholder="New Password" required>
                                    <button class="btn btn-primary" type="submit">Update</button>
                                </div>
                            </form>
                        </div>
                        <!-- Account Status -->
                        <div class="mb-4">
                            <h6 class="fw-bold text-secondary">Account Status</h6>
                            <form action="{{ url_for('toggle_staff_status', staff_id=staff.id) }}" method="POST" class="d-inline">
                                {% if staff.is_active %}
                                    <p class="text-muted small mb-2">Deactivating will prevent this user from logging in.</p>
                                    <button class="btn btn-warning w-100 mb-2" type="submit"><i class="bi bi-pause-circle"></i> Deactivate Account</button>
                                {% else %}
                                    <p class="text-muted small mb-2">This account is currently deactivated.</p>
                                    <button class="btn btn-success w-100 mb-2" type="submit"><i class="bi bi-play-circle"></i> Reactivate Account</button>
                                {% endif %}
                            </form>
                        </div>
                        <!-- Danger Zone -->
                        <div class="mb-3 border-top pt-3">
                            <h6 class="fw-bold text-danger">Danger Zone</h6>
                            <form action="{{ url_for('delete_staff', staff_id=staff.id) }}" method="POST" class="d-inline" onsubmit="return confirm('WARNING: Permanently delete this staff account? This action cannot be undone and will fail if they have history records.');">
                                <button class="btn btn-outline-danger w-100" type="submit"><i class="bi bi-trash-fill"></i> Delete Permanently</button>
                            </form>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        {% endfor %}
    {% endif %}
{% endblock %}"""

content = re.sub(r'\{% block modals %\}.*?\{% endblock %\}', modal_block, content, flags=re.DOTALL)

with open('/mnt/c/Users/wei/Desktop/inventory/templates/settings.html', 'w', encoding='utf-8') as f:
    f.write(content)
