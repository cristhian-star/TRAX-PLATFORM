from logging.config import fileConfig

from alembic import context

from app import create_app, db


config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

app = create_app(initialize_schema=False)


def database_url():
    with app.app_context():
        return app.config["SQLALCHEMY_DATABASE_URI"]


def run_migrations_offline():
    context.configure(
        url=database_url(),
        target_metadata=db.metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    with app.app_context():
        with db.engine.connect() as connection:
            context.configure(
                connection=connection,
                target_metadata=db.metadata,
                compare_type=True,
                render_as_batch=connection.dialect.name == "sqlite",
            )

            with context.begin_transaction():
                context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
