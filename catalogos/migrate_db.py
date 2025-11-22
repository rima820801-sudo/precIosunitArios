# migratate_db.py (Asegúrate que este archivo está dentro de la carpeta 'catalogos')

import os
from sqlalchemy import text, inspect
# Importa los objetos necesarios de app.py (ajusta si la importación cambia)
from app import app, db, User 

def initialize_db():
    with app.app_context():
        # 1. Crea todas las tablas que no existan (incluyendo 'users')
        db.create_all()
        print("✅ Tablas creadas/verificadas.")

        # 2. Revisa y añade la columna 'is_admin' si es una migración vieja
        inspector = inspect(db.engine)
        if "users" in inspector.get_table_names():
            columns = {col["name"] for col in inspector.get_columns("users")}
            if "is_admin" not in columns:
                try:
                    db.engine.execute(text('ALTER TABLE users ADD COLUMN is_admin BOOLEAN NOT NULL DEFAULT FALSE'))
                    db.session.commit()
                    print("✅ Columna 'is_admin' agregada.")
                except Exception as e:
                    print(f"Error al agregar columna: {e}")
            
        # 3. Crea el usuario administrador si no existe
        if not User.query.filter_by(username="Sarsjs88").first():
            admin_password = os.environ.get('ADMIN_PASSWORD')
            if not admin_password:
                print("❌ Error: La variable de entorno ADMIN_PASSWORD no está definida.")
                print("No se puede crear el usuario administrador sin una contraseña.")
                return

            u = User(username="Sarsjs88", is_admin=True)
            u.set_password(admin_password)
            db.session.add(u)
            db.session.commit()
            print("👤 Usuario administrador 'Sarsjs88' creado exitosamente.")
        else:
            print("👤 Usuario administrador ya existe. Saltando creación.")
            
        print("Migración de inicialización completada.")

if __name__ == "__main__":
    # La aplicación debe usar la URL de PostgreSQL aquí (definida en app.py)
    if not os.environ.get('DATABASE_URL'):
        print("ADVERTENCIA: Usando SQLite local. Asegúrate de que DATABASE_URL esté definida en producción.")
    
    initialize_db()