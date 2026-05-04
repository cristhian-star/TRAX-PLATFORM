from app import create_app
from app.database.db import init_db, insertar_datos_demo

app = create_app()

init_db()
insertar_datos_demo()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)