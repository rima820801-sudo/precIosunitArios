import argparse

from catalogos.app import app, db, User


def parse_args():
    parser = argparse.ArgumentParser(
        description="Crear o actualizar usuarios en la base de datos de precios unitarios."
    )
    parser.add_argument("username", help="Nombre de usuario nuevo.")
    parser.add_argument("password", help="Contraseña en texto plano.")
    parser.add_argument(
        "--admin",
        action="store_true",
        help="Marca el usuario como administrador (por defecto es usuario normal).",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Forzar reemplazo si el usuario ya existe.",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    with app.app_context():
        existing = User.query.filter_by(username=args.username).first()
        if existing and not args.force:
            print(f"El usuario '{args.username}' ya existe. Usa --force para actualizarlo.")
            return

        if existing:
            user = existing
            message = "actualizado"
        else:
            user = User(username=args.username)
            message = "creado"

        user.set_password(args.password)
        user.is_admin = args.admin
        if not existing:
            db.session.add(user)
        db.session.commit()
        print(f"Usuario '{args.username}' {message} correctamente. Admin={args.admin}")


if __name__ == "__main__":
    main()
