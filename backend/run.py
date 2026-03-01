import os
from src import create_app

app = create_app()

if __name__ == "__main__":
    # Railway sets the PORT environmental variable
    port = int(os.environ.get("PORT", 7860))
    app.run(host="0.0.0.0", port=port, debug=False)
