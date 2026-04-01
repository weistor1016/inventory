import re

with open('/mnt/c/Users/wei/Desktop/inventory/templates/records.html', 'r') as f:
    content = f.read()

# Give the client select an ID
content = content.replace('<select name="client_id" class="form-select" required>', 
                          '<select name="client_id" id="clientSelect" class="form-select" required>')
                          
# Make the add form section identifiable to scroll to it
content = content.replace('<h5 class="fw-bold mb-3">Add Entry</h5>', 
                          '<h5 id="addEntryHeading" class="fw-bold mb-3">Add Entry</h5>')

# Add click event to the client grouping row
old_tr = """<tr class="table-secondary">
                            <td colspan="4" class="fw-bold py-2">
                                <i class="bi bi-person-circle me-2"></i> {{ client_name }}
                            </td>
                        </tr>"""

new_tr = """<tr class="table-secondary" style="cursor: pointer;" onclick="autoSelectClient('{{ items[0].client_id }}')" title="Click to auto-select this client">
                            <td colspan="4" class="fw-bold py-2 text-primary">
                                <i class="bi bi-person-circle me-2"></i> {{ client_name }}
                                <small class="float-end fw-normal pt-1"><i class="bi bi-reply-fill"></i> Add</small>
                            </td>
                        </tr>"""

content = content.replace(old_tr, new_tr)

# Inject JS function
js_func = """
function autoSelectClient(clientId) {
    let select = document.getElementById('clientSelect');
    if (select) {
        select.value = clientId;
        // Scroll to the "Add Entry" section
        document.getElementById('addEntryHeading').scrollIntoView({behavior: 'smooth', block: 'start'});
        // Optionally flash the select box to show it changed
        select.style.boxShadow = "0 0 10px #0d6efd";
        setTimeout(() => select.style.boxShadow = "", 800);
    }
}
"""

content = content.replace("</script>", js_func + "</script>")

with open('/mnt/c/Users/wei/Desktop/inventory/templates/records.html', 'w') as f:
    f.write(content)
