import re

with open('/mnt/c/Users/wei/Desktop/inventory/templates/records.html', 'r') as f:
    content = f.read()

old_thead = """<table class="table align-middle mb-0" style="table-layout: fixed; width: 100%;">
                    <thead class="table-light">
                        <tr>
                            <th style="width: 40%;">Client / Item</th>
                            <th class="text-center" style="width: 15%;">Qty</th>
                            <th class="text-center" style="width: 30%;">Status</th>
                            <th class="text-end" style="width: 15%;">Action</th>
                        </tr>
                    </thead>"""

new_thead = """<table class="table align-middle mb-0">
                    <thead class="table-light">
                        <tr>
                            <th class="text-nowrap" style="width: 35%;">Client / Item</th>
                            <th class="text-center text-nowrap" style="width: 10%;">Qty</th>
                            <th class="text-center text-nowrap" style="width: 35%;">Status</th>
                            <th class="text-end text-nowrap" style="width: 20%;">Action</th>
                        </tr>
                    </thead>"""

content = content.replace(old_thead, new_thead)

with open('/mnt/c/Users/wei/Desktop/inventory/templates/records.html', 'w') as f:
    f.write(content)
