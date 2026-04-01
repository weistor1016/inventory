with open('/mnt/c/Users/wei/Desktop/inventory/templates/records.html', 'r') as f:
    content = f.read()
content = content.replace("{% endblock %}\n<script>", "<script>")
content = content.replace("</script>", "</script>\n{% endblock %}")
with open('/mnt/c/Users/wei/Desktop/inventory/templates/records.html', 'w') as f:
    f.write(content)

with open('/mnt/c/Users/wei/Desktop/inventory/templates/session_details.html', 'r') as f:
    content = f.read()
content = content.replace("{% endblock %}\n<script>", "<script>")
content = content.replace("</script>", "</script>\n{% endblock %}")
with open('/mnt/c/Users/wei/Desktop/inventory/templates/session_details.html', 'w') as f:
    f.write(content)
