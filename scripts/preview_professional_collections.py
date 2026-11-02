"""Run only a disposable local simulation; Ctrl+C closes and deletes its database."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.services.isolated_collection_preview import isolated_app

if __name__ == "__main__":
    with isolated_app(enable_simulation=True) as app:
        print("SIMULACIÓN — no procesa dinero; SQLite temporal:", app.config["SQLALCHEMY_DATABASE_URI"])
        print("http://127.0.0.1:54954/login — profesional@example.test / Simulacion-local-2026!")
        app.run(host="127.0.0.1", port=54954, debug=False, use_reloader=False)
