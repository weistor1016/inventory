import sqlite3
conn = sqlite3.connect('/mnt/c/Users/wei/Desktop/inventory/inventory.db')
try:
    conn.execute("ALTER TABLE day_record ADD COLUMN quantity_returned INTEGER DEFAULT 0")
    conn.execute("ALTER TABLE draft_record ADD COLUMN quantity_returned INTEGER DEFAULT 0")
    conn.execute("UPDATE day_record SET quantity_returned = quantity_out WHERE is_returned = 1")
    conn.execute("UPDATE draft_record SET quantity_returned = quantity_out WHERE is_returned = 1")
    conn.commit()
    print("DB patched")
except Exception as e:
    print("Already patched or error:", e)
conn.close()
