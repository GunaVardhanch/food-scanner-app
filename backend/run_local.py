import os
from app import create_app

app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 7860))
    print(f"\n🚀 NutriScanner Backend starting on http://localhost:{port}")
    print("   Auth endpoints: /auth/register, /auth/login, /auth/me")
    print("   Scan endpoint:  POST /api/scan")
    print("   Analytics:      GET  /analytics")
    print("   History:        GET  /history\n")
    app.run(host="0.0.0.0", port=port, debug=True, use_reloader=False)
