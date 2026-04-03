from waitress import serve
from app import app  # This imports the 'app' object from your app.py file

if __name__ == '__main__':
    print("Server is starting on Tailscale IP, port 8080...")
    serve(app, host='0.0.0.0', port=8080, threads=12)