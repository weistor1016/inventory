from app import app
import os

if __name__ == '__main__':
    # On AWS, Gunicorn will ignore this entire 'if' block.
    # This block is ONLY for when you run 'python serve.py' manually.
    port = int(os.environ.get("PORT", 8080))
    print(f"Starting development server on port {port}...")
    
    # Switch to standard Flask runner for local dev, 
    # or keep waitress if you prefer it for local testing.
    app.run(host='0.0.0.0', port=port, debug=True)