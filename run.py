import os
from app import create_app

app = create_app()

if __name__ == "__main__":
    # host="0.0.0.0" so the app is reachable from other devices on your LAN.
    # Set FLASK_DEBUG=0 in .env for a production-like run.
    debug = os.environ.get("FLASK_DEBUG", "1") == "1"
    app.run(host="0.0.0.0", port=5000, debug=debug)
