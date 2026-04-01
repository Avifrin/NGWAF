from app import create_app
from app.extensions import db

app = create_app()

@app.cli.command()
def init_db():
    """Создать таблицы БД"""
    with app.app_context():
        db.create_all()

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
