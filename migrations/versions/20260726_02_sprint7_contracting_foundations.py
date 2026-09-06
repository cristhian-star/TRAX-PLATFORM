"""sprint 7 contracting core phase 2a foundations

Revision ID: 20260726_02
Revises: 20260726_01
Create Date: 2026-07-26
"""

import re

from alembic import op
import sqlalchemy as sa


revision = "20260726_02"
down_revision = "20260726_01"
branch_labels = None
depends_on = None


def _inspector():
    return sa.inspect(op.get_bind())


def _columns(table_name):
    inspector = _inspector()
    if not inspector.has_table(table_name):
        return set()
    return {column["name"] for column in inspector.get_columns(table_name)}


def _indexes(table_name):
    inspector = _inspector()
    if not inspector.has_table(table_name):
        return set()
    return {index["name"] for index in inspector.get_indexes(table_name)}


def _constraints(table_name, kind):
    inspector = _inspector()
    if not inspector.has_table(table_name):
        return set()
    if kind == "check":
        values = inspector.get_check_constraints(table_name)
    elif kind == "unique":
        values = inspector.get_unique_constraints(table_name)
    elif kind == "foreignkey":
        values = inspector.get_foreign_keys(table_name)
    else:
        values = []
    return {value["name"] for value in values if value.get("name")}


def _constraint_details(table_name, kind):
    inspector = _inspector()
    if not inspector.has_table(table_name):
        return []
    if kind == "check":
        return inspector.get_check_constraints(table_name)
    if kind == "unique":
        return inspector.get_unique_constraints(table_name)
    if kind == "foreignkey":
        return inspector.get_foreign_keys(table_name)
    return []


def _add_contract_columns():
    columns = _columns("contract_requests")
    with op.batch_alter_table("contract_requests") as batch_op:
        if "contracting_mode" not in columns:
            batch_op.add_column(sa.Column("contracting_mode", sa.String(length=20), nullable=True))
        if "version" not in columns:
            batch_op.add_column(sa.Column("version", sa.Integer(), nullable=True))

    op.execute(
        "UPDATE contract_requests "
        "SET contracting_mode = 'EXTERNAL' "
        "WHERE contracting_mode IS NULL"
    )
    op.execute(
        "UPDATE contract_requests "
        "SET version = 1 "
        "WHERE version IS NULL OR version < 1"
    )
    op.execute(
        "UPDATE contract_requests "
        "SET estado = 'CONFIRMADA' "
        "WHERE estado = 'CERRADA'"
    )

    checks = _constraints("contract_requests", "check")
    with op.batch_alter_table("contract_requests") as batch_op:
        batch_op.alter_column(
            "contracting_mode",
            existing_type=sa.String(length=20),
            nullable=False,
            server_default="EXTERNAL",
        )
        batch_op.alter_column(
            "version",
            existing_type=sa.Integer(),
            nullable=False,
            server_default="1",
        )
        if "ck_contract_requests_estado" not in checks:
            batch_op.create_check_constraint(
                "ck_contract_requests_estado",
                "estado in ('CREADA', 'ACEPTADA', 'EN_PROGRESO', 'COMPLETADA', "
                "'CORRECCION_SOLICITADA', 'CONFIRMADA', 'RECHAZADA', 'CANCELADA')",
            )
        if "ck_contract_requests_contracting_mode" not in checks:
            batch_op.create_check_constraint(
                "ck_contract_requests_contracting_mode",
                "contracting_mode = 'EXTERNAL'",
            )
        if "ck_contract_requests_version" not in checks:
            batch_op.create_check_constraint(
                "ck_contract_requests_version",
                "version >= 1",
            )


def _add_event_columns():
    columns = _columns("contract_events")
    with op.batch_alter_table("contract_events") as batch_op:
        if "sequence_no" not in columns:
            batch_op.add_column(sa.Column("sequence_no", sa.Integer(), nullable=True))
        if "correlation_id" not in columns:
            batch_op.add_column(sa.Column("correlation_id", sa.String(length=36), nullable=True))
        if "causation_event_id" not in columns:
            batch_op.add_column(sa.Column("causation_event_id", sa.Integer(), nullable=True))
        if "idempotency_key" not in columns:
            batch_op.add_column(sa.Column("idempotency_key", sa.String(length=160), nullable=True))

    bind = op.get_bind()
    rows = bind.execute(
        sa.text(
            "SELECT id, contract_id FROM contract_events "
            "ORDER BY contract_id, created_at, id"
        )
    ).fetchall()
    sequence_by_contract = {}
    for row in rows:
        contract_id = row[1]
        sequence_by_contract[contract_id] = sequence_by_contract.get(contract_id, 0) + 1
        bind.execute(
            sa.text(
                "UPDATE contract_events SET sequence_no = :sequence_no WHERE id = :event_id"
            ),
            {
                "sequence_no": sequence_by_contract[contract_id],
                "event_id": row[0],
            },
        )

    checks = _constraints("contract_events", "check")
    uniques = _constraints("contract_events", "unique")
    foreign_keys = _constraints("contract_events", "foreignkey")
    with op.batch_alter_table("contract_events") as batch_op:
        batch_op.alter_column(
            "sequence_no",
            existing_type=sa.Integer(),
            nullable=False,
        )
        if "ck_contract_events_sequence_positive" not in checks:
            batch_op.create_check_constraint(
                "ck_contract_events_sequence_positive",
                "sequence_no >= 1",
            )
        if "uq_contract_events_contract_sequence" not in uniques:
            batch_op.create_unique_constraint(
                "uq_contract_events_contract_sequence",
                ["contract_id", "sequence_no"],
            )
        if "uq_contract_events_idempotency_key" not in uniques:
            batch_op.create_unique_constraint(
                "uq_contract_events_idempotency_key",
                ["idempotency_key"],
            )
        if "fk_contract_events_causation_event_id" not in foreign_keys:
            batch_op.create_foreign_key(
                "fk_contract_events_causation_event_id",
                "contract_events",
                ["causation_event_id"],
                ["id"],
                ondelete="RESTRICT",
            )

    if "ix_contract_events_correlation_id" not in _indexes("contract_events"):
        op.create_index(
            "ix_contract_events_correlation_id",
            "contract_events",
            ["correlation_id"],
        )


def _add_audit_columns():
    columns = _columns("audit_logs")
    with op.batch_alter_table("audit_logs") as batch_op:
        if "correlation_id" not in columns:
            batch_op.add_column(sa.Column("correlation_id", sa.String(length=36), nullable=True))
        if "operation" not in columns:
            batch_op.add_column(sa.Column("operation", sa.String(length=80), nullable=True))
        if "metadata_json" not in columns:
            batch_op.add_column(sa.Column("metadata_json", sa.JSON(), nullable=True))

    indexes = _indexes("audit_logs")
    if "ix_audit_logs_correlation_id" not in indexes:
        op.create_index("ix_audit_logs_correlation_id", "audit_logs", ["correlation_id"])
    if "ix_audit_logs_operation" not in indexes:
        op.create_index("ix_audit_logs_operation", "audit_logs", ["operation"])


def _add_notification_columns():
    columns = _columns("activity_notifications")
    with op.batch_alter_table("activity_notifications") as batch_op:
        if "contract_event_id" not in columns:
            batch_op.add_column(sa.Column("contract_event_id", sa.Integer(), nullable=True))
        if "correlation_id" not in columns:
            batch_op.add_column(sa.Column("correlation_id", sa.String(length=36), nullable=True))
        if "idempotency_key" not in columns:
            batch_op.add_column(sa.Column("idempotency_key", sa.String(length=160), nullable=True))
        if "template_key" not in columns:
            batch_op.add_column(sa.Column("template_key", sa.String(length=80), nullable=True))
        if "channel" not in columns:
            batch_op.add_column(
                sa.Column(
                    "channel",
                    sa.String(length=20),
                    nullable=True,
                    server_default="INTERNAL",
                )
            )
        if "delivery_status" not in columns:
            batch_op.add_column(
                sa.Column(
                    "delivery_status",
                    sa.String(length=20),
                    nullable=True,
                    server_default="DELIVERED",
                )
            )
        if "attempt_count" not in columns:
            batch_op.add_column(
                sa.Column(
                    "attempt_count",
                    sa.Integer(),
                    nullable=True,
                    server_default="0",
                )
            )

    op.execute(
        "UPDATE activity_notifications SET channel = 'INTERNAL' WHERE channel IS NULL"
    )
    op.execute(
        "UPDATE activity_notifications "
        "SET delivery_status = 'DELIVERED' "
        "WHERE delivery_status IS NULL"
    )
    op.execute(
        "UPDATE activity_notifications SET attempt_count = 0 WHERE attempt_count IS NULL"
    )

    checks = _constraints("activity_notifications", "check")
    uniques = _constraints("activity_notifications", "unique")
    foreign_keys = _constraints("activity_notifications", "foreignkey")
    with op.batch_alter_table("activity_notifications") as batch_op:
        batch_op.alter_column(
            "channel",
            existing_type=sa.String(length=20),
            nullable=False,
            server_default="INTERNAL",
        )
        batch_op.alter_column(
            "delivery_status",
            existing_type=sa.String(length=20),
            nullable=False,
            server_default="DELIVERED",
        )
        batch_op.alter_column(
            "attempt_count",
            existing_type=sa.Integer(),
            nullable=False,
            server_default="0",
        )
        if "ck_activity_notifications_channel" not in checks:
            batch_op.create_check_constraint(
                "ck_activity_notifications_channel",
                "channel in ('INTERNAL')",
            )
        if "ck_activity_notifications_delivery_status" not in checks:
            batch_op.create_check_constraint(
                "ck_activity_notifications_delivery_status",
                "delivery_status in ('PENDING', 'DELIVERED', 'FAILED')",
            )
        if "ck_activity_notifications_attempt_count" not in checks:
            batch_op.create_check_constraint(
                "ck_activity_notifications_attempt_count",
                "attempt_count >= 0",
            )
        if "uq_activity_notifications_domain_delivery" not in uniques:
            batch_op.create_unique_constraint(
                "uq_activity_notifications_domain_delivery",
                ["user_id", "contract_event_id", "template_key", "channel"],
            )
        if "uq_activity_notifications_idempotency_key" not in uniques:
            batch_op.create_unique_constraint(
                "uq_activity_notifications_idempotency_key",
                ["idempotency_key"],
            )
        if "fk_activity_notifications_contract_event_id" not in foreign_keys:
            batch_op.create_foreign_key(
                "fk_activity_notifications_contract_event_id",
                "contract_events",
                ["contract_event_id"],
                ["id"],
                ondelete="RESTRICT",
            )

    for index_name, column_name in (
        ("ix_activity_notifications_contract_event_id", "contract_event_id"),
        ("ix_activity_notifications_correlation_id", "correlation_id"),
    ):
        if index_name not in _indexes("activity_notifications"):
            op.create_index(index_name, "activity_notifications", [column_name])


def _operation_command_columns():
    return {
        "id": (sa.Integer(), False),
        "actor_user_id": (sa.Integer(), False),
        "operation": (sa.String(length=80), False),
        "idempotency_key": (sa.String(length=160), False),
        "payload_hash": (sa.String(length=64), False),
        "status": (sa.String(length=20), False),
        "result_entity_type": (sa.String(length=80), True),
        "result_entity_id": (sa.Integer(), True),
        "correlation_id": (sa.String(length=36), False),
        "created_at": (sa.DateTime(), False),
        "completed_at": (sa.DateTime(), True),
        "failure_code": (sa.String(length=80), True),
    }


def _compatible_type(actual, expected):
    if isinstance(expected, sa.Integer):
        return isinstance(actual, sa.Integer)
    if isinstance(expected, sa.DateTime):
        return isinstance(actual, sa.DateTime)
    if isinstance(expected, sa.String):
        if not isinstance(actual, sa.String):
            return False
        return actual.length in (None, expected.length)
    return type(actual) is type(expected)


OPERATION_COMMAND_SEQUENCE = "operation_commands_id_phase2a_seq"
OPERATION_COMMAND_SEQUENCE_COMMENT = (
    "TRAX:20260726_02:operation_commands.id:migration-owned"
)
POSTGRES_INTEGER_MIN = 1
POSTGRES_INTEGER_MAX = 2147483647


def _quoted_sequence_name(details):
    preparer = op.get_bind().dialect.identifier_preparer
    return (
        f"{preparer.quote(details['schema_name'])}."
        f"{preparer.quote(details['sequence_name'])}"
    )


def _postgres_sequence_details(sequence_name):
    bind = op.get_bind()
    details = bind.execute(
        sa.text(
            "SELECT n.nspname AS schema_name, c.relname AS sequence_name, "
            "pg_get_userbyid(c.relowner) AS owner_name, "
            "current_user AS current_user_name, "
            "has_sequence_privilege(c.oid, 'USAGE') AS can_usage, "
            "has_sequence_privilege(c.oid, 'SELECT') AS can_select, "
            "has_sequence_privilege(c.oid, 'UPDATE') AS can_update, "
            "s.seqincrement AS increment_by, s.seqmin AS min_value, "
            "s.seqmax AS max_value, s.seqcycle AS cycle, "
            "obj_description(c.oid, 'pg_class') AS object_comment, "
            "(SELECT COUNT(*) FROM pg_depend d "
            " JOIN pg_attrdef ad "
            "   ON d.classid = 'pg_attrdef'::regclass AND d.objid = ad.oid "
            " JOIN pg_class dt ON dt.oid = ad.adrelid "
            " JOIN pg_attribute da "
            "   ON da.attrelid = ad.adrelid AND da.attnum = ad.adnum "
            " WHERE d.refclassid = 'pg_class'::regclass "
            "   AND d.refobjid = c.oid "
            "   AND NOT (dt.oid = 'operation_commands'::regclass "
            "            AND da.attname = 'id')) AS other_default_references "
            "FROM pg_class c "
            "JOIN pg_namespace n ON n.oid = c.relnamespace "
            "JOIN pg_sequence s ON s.seqrelid = c.oid "
            "WHERE c.oid = to_regclass(:sequence_name) AND c.relkind = 'S'"
        ),
        {"sequence_name": sequence_name},
    ).mappings().first()
    if details is None:
        return None

    result = dict(details)
    state = bind.execute(
        sa.text(
            f"SELECT last_value, is_called FROM {_quoted_sequence_name(result)}"
        )
    ).mappings().one()
    result["last_value"] = int(state["last_value"])
    result["is_called"] = bool(state["is_called"])
    result["effective_next_value"] = (
        result["last_value"] + int(result["increment_by"])
        if result["is_called"]
        else result["last_value"]
    )
    return result


def _operation_command_generator_preflight(columns):
    if op.get_bind().dialect.name != "postgresql":
        return {"action": "sqlite"}, []

    id_column = columns.get("id")
    if id_column is None:
        return None, []

    errors = []
    identity = id_column.get("identity")
    default = id_column.get("default")
    max_id = op.get_bind().execute(
        sa.text("SELECT MAX(id) FROM operation_commands")
    ).scalar()
    owned_sequence = op.get_bind().execute(
        sa.text(
            "SELECT pg_get_serial_sequence('operation_commands', 'id')"
        )
    ).scalar()

    if identity or owned_sequence:
        if not owned_sequence:
            errors.append("id declara identity pero PostgreSQL no informa su secuencia")
            return None, errors
        details = _postgres_sequence_details(owned_sequence)
        if details is None:
            errors.append("la secuencia generadora de id no existe")
            return None, errors
        authorized = (
            details["owner_name"] == details["current_user_name"]
            or (
                details["can_usage"]
                and details["can_select"]
                and details["can_update"]
            )
        )
        if not authorized:
            errors.append(
                "el usuario de migracion no posee ni puede operar la secuencia de id"
            )
        if details["other_default_references"]:
            errors.append(
                "la secuencia de id tambien es usada por otros defaults; "
                "no es seguro normalizar una secuencia compartida"
            )

        default_matches_owned = bool(identity)
        if default and not identity:
            match = re.search(
                r"nextval\(\(*'([^']+)'",
                str(default),
                flags=re.IGNORECASE,
            )
            if match is not None:
                default_matches_owned = bool(
                    op.get_bind().execute(
                        sa.text(
                            "SELECT to_regclass(:default_sequence) = "
                            "to_regclass(:owned_sequence)"
                        ),
                        {
                            "default_sequence": match.group(1),
                            "owned_sequence": owned_sequence,
                        },
                    ).scalar()
                )
            if not default_matches_owned:
                errors.append(
                    "el default de id no referencia su secuencia OWNED BY"
                )

        if max_id is not None and int(max_id) >= POSTGRES_INTEGER_MAX:
            errors.append(
                "MAX(id) alcanzo el limite INTEGER y no existe un siguiente "
                "valor generable sin colision o overflow"
            )

        target_next = max(
            POSTGRES_INTEGER_MIN,
            int(max_id) + 1 if max_id is not None else POSTGRES_INTEGER_MIN,
        )
        semantic_reasons = []
        if int(details["increment_by"]) <= 0:
            semantic_reasons.append("increment_by no es positivo")
        if int(details["increment_by"]) != 1:
            semantic_reasons.append("la secuencia no avanza unitariamente")
        if details["cycle"]:
            semantic_reasons.append("CYCLE esta habilitado")
        if int(details["min_value"]) != POSTGRES_INTEGER_MIN:
            semantic_reasons.append("min_value no es compatible con IDs positivos")
        if int(details["max_value"]) != POSTGRES_INTEGER_MAX:
            semantic_reasons.append("max_value no coincide con el rango INTEGER")
        effective_next = int(details["effective_next_value"])
        if max_id is not None and effective_next <= int(max_id):
            semantic_reasons.append(
                "el siguiente valor efectivo no supera MAX(id)"
            )
        if not POSTGRES_INTEGER_MIN <= effective_next <= POSTGRES_INTEGER_MAX:
            semantic_reasons.append(
                "el siguiente valor efectivo queda fuera del rango seguro"
            )
        if (
            semantic_reasons
            and details["owner_name"] != details["current_user_name"]
        ):
            errors.append(
                "la secuencia requiere normalizacion pero el usuario de "
                "migracion no es su propietario"
            )

        action = "valid"
        if not identity and default is None:
            action = "set_default_existing"
        if semantic_reasons:
            action = "normalize_existing"
        return {
            "action": action,
            "sequence_name": (
                f"{details['schema_name']}.{details['sequence_name']}"
            ),
            "identity": bool(identity),
            "set_default": not identity and default is None,
            "target_next": target_next,
            "semantic_reasons": semantic_reasons,
            "before": {
                "increment_by": int(details["increment_by"]),
                "min_value": int(details["min_value"]),
                "max_value": int(details["max_value"]),
                "cycle": bool(details["cycle"]),
                "last_value": int(details["last_value"]),
                "is_called": bool(details["is_called"]),
                "effective_next_value": effective_next,
            },
        }, errors

    if default:
        match = re.search(
            r"nextval\(\(*'([^']+)'",
            str(default),
            flags=re.IGNORECASE,
        )
        if match is None:
            errors.append(
                "id tiene un default incompatible; se esperaba identity o nextval"
            )
            return None, errors
        referenced_name = match.group(1)
        referenced = op.get_bind().execute(
            sa.text("SELECT to_regclass(:sequence_name)::text"),
            {"sequence_name": referenced_name},
        ).scalar()
        if referenced is not None:
            errors.append(
                "id usa una secuencia existente no asociada mediante OWNED BY; "
                "no es seguro apropiarla"
            )
            return None, errors
        return {"action": "replace_missing_sequence"}, errors

    deterministic = _postgres_sequence_details(OPERATION_COMMAND_SEQUENCE)
    if deterministic is not None:
        errors.append(
            f"la secuencia {OPERATION_COMMAND_SEQUENCE} ya existe pero no pertenece "
            "a operation_commands.id"
        )
        return None, errors
    return {"action": "create"}, errors


def _repair_operation_command_generator(generator):
    if not generator or generator["action"] == "sqlite":
        return

    bind = op.get_bind()
    action = generator["action"]
    sequence_name = generator.get("sequence_name")
    if action in ("create", "replace_missing_sequence"):
        if action == "replace_missing_sequence":
            op.execute(
                "ALTER TABLE operation_commands ALTER COLUMN id DROP DEFAULT"
            )
        op.execute(
            f"CREATE SEQUENCE {OPERATION_COMMAND_SEQUENCE} AS INTEGER "
            f"INCREMENT BY 1 MINVALUE {POSTGRES_INTEGER_MIN} "
            f"MAXVALUE {POSTGRES_INTEGER_MAX} NO CYCLE"
        )
        op.execute(
            f"ALTER SEQUENCE {OPERATION_COMMAND_SEQUENCE} "
            "OWNED BY operation_commands.id"
        )
        op.execute(
            f"COMMENT ON SEQUENCE {OPERATION_COMMAND_SEQUENCE} IS "
            f"'{OPERATION_COMMAND_SEQUENCE_COMMENT}'"
        )
        op.execute(
            "ALTER TABLE operation_commands ALTER COLUMN id SET DEFAULT "
            f"nextval('{OPERATION_COMMAND_SEQUENCE}'::regclass)"
        )
        sequence_name = OPERATION_COMMAND_SEQUENCE
    elif action == "set_default_existing":
        op.execute(
            "ALTER TABLE operation_commands ALTER COLUMN id SET DEFAULT "
            f"nextval('{sequence_name}'::regclass)"
        )
    elif generator.get("set_default"):
        op.execute(
            "ALTER TABLE operation_commands ALTER COLUMN id SET DEFAULT "
            f"nextval('{sequence_name}'::regclass)"
        )

    max_id = bind.execute(
        sa.text("SELECT MAX(id) FROM operation_commands")
    ).scalar()
    target_next = max(
        POSTGRES_INTEGER_MIN,
        int(max_id) + 1 if max_id is not None else POSTGRES_INTEGER_MIN,
    )
    details = _postgres_sequence_details(sequence_name)
    if action == "normalize_existing":
        op.execute(
            f"ALTER SEQUENCE {_quoted_sequence_name(details)} "
            f"INCREMENT BY 1 MINVALUE {POSTGRES_INTEGER_MIN} "
            f"MAXVALUE {POSTGRES_INTEGER_MAX} NO CYCLE "
            f"RESTART WITH {target_next}"
        )
    else:
        effective_next = int(details["effective_next_value"])
        if (
            effective_next <= (int(max_id) if max_id is not None else 0)
            or not POSTGRES_INTEGER_MIN
            <= effective_next
            <= POSTGRES_INTEGER_MAX
        ):
            op.execute(
                f"ALTER SEQUENCE {_quoted_sequence_name(details)} "
                f"RESTART WITH {target_next}"
            )


def _operation_command_preflight():
    bind = op.get_bind()
    inspector = _inspector()
    columns = {
        column["name"]: column
        for column in inspector.get_columns("operation_commands")
    }
    expected = _operation_command_columns()
    errors = []

    primary_key = inspector.get_pk_constraint("operation_commands")
    if primary_key.get("constrained_columns") != ["id"]:
        errors.append("primary key incompatible; se requiere id")
    if "id" not in columns:
        errors.append("falta la columna id y no puede agregarse como primary key en forma segura")

    row_count = bind.execute(sa.text("SELECT COUNT(*) FROM operation_commands")).scalar()
    compatible_columns = set()
    for name, (expected_type, expected_nullable) in expected.items():
        actual = columns.get(name)
        if actual is None:
            if not expected_nullable and row_count:
                errors.append(
                    f"falta la columna obligatoria {name} en una tabla con datos"
                )
            continue
        if not _compatible_type(actual["type"], expected_type):
            errors.append(
                f"tipo incompatible para {name}: {actual['type']} no coincide con "
                f"{expected_type}"
            )
        else:
            compatible_columns.add(name)
        if actual["nullable"] and not expected_nullable:
            null_count = bind.execute(
                sa.text(
                    f"SELECT COUNT(*) FROM operation_commands WHERE {name} IS NULL"
                )
            ).scalar()
            if null_count:
                errors.append(
                    f"{name} contiene NULL y no puede convertirse a NOT NULL"
                )

    foreign_keys = {
        item.get("name"): item
        for item in _constraint_details("operation_commands", "foreignkey")
        if item.get("name")
    }
    actor_fk = foreign_keys.get("fk_operation_commands_actor_user_id")
    if actor_fk and (
        actor_fk.get("constrained_columns") != ["actor_user_id"]
        or actor_fk.get("referred_table") != "users"
        or actor_fk.get("referred_columns") != ["id"]
    ):
        errors.append("fk_operation_commands_actor_user_id tiene una definicion incompatible")
    if "actor_user_id" in compatible_columns:
        orphan_count = bind.execute(
            sa.text(
                "SELECT COUNT(*) FROM operation_commands oc "
                "LEFT JOIN users u ON u.id = oc.actor_user_id "
                "WHERE oc.actor_user_id IS NOT NULL AND u.id IS NULL"
            )
        ).scalar()
        if orphan_count:
            errors.append("actor_user_id contiene referencias huerfanas")

    uniques = {
        item.get("name"): item
        for item in _constraint_details("operation_commands", "unique")
        if item.get("name")
    }
    command_unique = uniques.get("uq_operation_commands_actor_operation_key")
    unique_columns = ["actor_user_id", "operation", "idempotency_key"]
    if command_unique and command_unique.get("column_names") != unique_columns:
        errors.append(
            "uq_operation_commands_actor_operation_key tiene una definicion incompatible"
        )
    if all(name in columns for name in unique_columns):
        duplicate = bind.execute(
            sa.text(
                "SELECT 1 FROM operation_commands "
                "GROUP BY actor_user_id, operation, idempotency_key "
                "HAVING COUNT(*) > 1"
            )
        ).first()
        if duplicate:
            errors.append("existen comandos duplicados que impiden crear la unique")

    checks = {
        item.get("name"): item
        for item in _constraint_details("operation_commands", "check")
        if item.get("name")
    }
    status_check = checks.get("ck_operation_commands_status")
    if status_check:
        sqltext = (status_check.get("sqltext") or "").upper()
        if not all(value in sqltext for value in ("STATUS", "PROCESSING", "SUCCEEDED", "FAILED")):
            errors.append("ck_operation_commands_status tiene una definicion incompatible")
    if "status" in compatible_columns:
        invalid_status = bind.execute(
            sa.text(
                "SELECT COUNT(*) FROM operation_commands "
                "WHERE status IS NOT NULL "
                "AND status NOT IN ('PROCESSING', 'SUCCEEDED', 'FAILED')"
            )
        ).scalar()
        if invalid_status:
            errors.append("status contiene valores fuera del catalogo permitido")

    indexes = {
        item["name"]: item
        for item in inspector.get_indexes("operation_commands")
        if item.get("name")
    }
    for index_name, index_columns in (
        ("ix_operation_commands_actor_user_id", ["actor_user_id"]),
        ("ix_operation_commands_correlation_id", ["correlation_id"]),
    ):
        existing = indexes.get(index_name)
        if existing and existing.get("column_names") != index_columns:
            errors.append(f"{index_name} tiene una definicion incompatible")

    generator, generator_errors = _operation_command_generator_preflight(columns)
    errors.extend(generator_errors)

    if errors:
        raise RuntimeError(
            "operation_commands parcial incompatible; no se aplicaron reparaciones: "
            + "; ".join(errors)
        )

    return {
        "columns": columns,
        "foreign_keys": foreign_keys,
        "uniques": uniques,
        "checks": checks,
        "indexes": indexes,
        "generator": generator,
    }


def _create_operation_commands():
    if not _inspector().has_table("operation_commands"):
        op.create_table(
            "operation_commands",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("actor_user_id", sa.Integer(), nullable=False),
            sa.Column("operation", sa.String(length=80), nullable=False),
            sa.Column("idempotency_key", sa.String(length=160), nullable=False),
            sa.Column("payload_hash", sa.String(length=64), nullable=False),
            sa.Column("status", sa.String(length=20), nullable=False),
            sa.Column("result_entity_type", sa.String(length=80), nullable=True),
            sa.Column("result_entity_id", sa.Integer(), nullable=True),
            sa.Column("correlation_id", sa.String(length=36), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.Column("completed_at", sa.DateTime(), nullable=True),
            sa.Column("failure_code", sa.String(length=80), nullable=True),
            sa.CheckConstraint(
                "status in ('PROCESSING', 'SUCCEEDED', 'FAILED')",
                name="ck_operation_commands_status",
            ),
            sa.ForeignKeyConstraint(
                ["actor_user_id"],
                ["users.id"],
                name="fk_operation_commands_actor_user_id",
            ),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint(
                "actor_user_id",
                "operation",
                "idempotency_key",
                name="uq_operation_commands_actor_operation_key",
            ),
        )
        op.create_index(
            "ix_operation_commands_actor_user_id",
            "operation_commands",
            ["actor_user_id"],
        )
        op.create_index(
            "ix_operation_commands_correlation_id",
            "operation_commands",
            ["correlation_id"],
        )
        if op.get_bind().dialect.name == "postgresql":
            sequence_name = op.get_bind().execute(
                sa.text(
                    "SELECT pg_get_serial_sequence('operation_commands', 'id')"
                )
            ).scalar()
            details = _postgres_sequence_details(sequence_name)
            op.execute(
                f"COMMENT ON SEQUENCE {_quoted_sequence_name(details)} IS "
                f"'{OPERATION_COMMAND_SEQUENCE_COMMENT}'"
            )
        return

    structure = _operation_command_preflight()
    columns = structure["columns"]
    expected = _operation_command_columns()
    with op.batch_alter_table("operation_commands") as batch_op:
        for name, (column_type, nullable) in expected.items():
            if name not in columns:
                batch_op.add_column(
                    sa.Column(
                        name,
                        column_type,
                        nullable=True,
                        server_default=sa.func.now() if name == "created_at" else None,
                    )
                )
        for name, (column_type, nullable) in expected.items():
            if name == "id" or name not in columns and nullable:
                continue
            actual_nullable = columns.get(name, {}).get("nullable", True)
            if actual_nullable != nullable:
                batch_op.alter_column(
                    name,
                    existing_type=column_type,
                    nullable=nullable,
                )
        if "ck_operation_commands_status" not in structure["checks"]:
            batch_op.create_check_constraint(
                "ck_operation_commands_status",
                "status in ('PROCESSING', 'SUCCEEDED', 'FAILED')",
            )
        if "fk_operation_commands_actor_user_id" not in structure["foreign_keys"]:
            batch_op.create_foreign_key(
                "fk_operation_commands_actor_user_id",
                "users",
                ["actor_user_id"],
                ["id"],
            )
        if "uq_operation_commands_actor_operation_key" not in structure["uniques"]:
            batch_op.create_unique_constraint(
                "uq_operation_commands_actor_operation_key",
                ["actor_user_id", "operation", "idempotency_key"],
            )

    _repair_operation_command_generator(structure["generator"])

    for index_name, index_columns in (
        ("ix_operation_commands_actor_user_id", ["actor_user_id"]),
        ("ix_operation_commands_correlation_id", ["correlation_id"]),
    ):
        if index_name not in structure["indexes"]:
            op.create_index(index_name, "operation_commands", index_columns)


def upgrade():
    if _inspector().has_table("operation_commands"):
        _operation_command_preflight()
    _add_contract_columns()
    _add_event_columns()
    _add_audit_columns()
    _add_notification_columns()
    _create_operation_commands()


def _phase2a_data_exists(bind):
    if _inspector().has_table("operation_commands"):
        if bind.execute(sa.text("SELECT COUNT(*) FROM operation_commands")).scalar():
            return True

    contract_conditions = []
    contract_columns = _columns("contract_requests")
    if "version" in contract_columns:
        contract_conditions.append("version > 1")
    if "estado" in contract_columns:
        contract_conditions.append("estado = 'CORRECCION_SOLICITADA'")
    if contract_conditions and bind.execute(
        sa.text(
            "SELECT COUNT(*) FROM contract_requests WHERE "
            + " OR ".join(contract_conditions)
        )
    ).scalar():
        return True

    event_conditions = [
        f"{name} IS NOT NULL"
        for name in ("correlation_id", "idempotency_key")
        if name in _columns("contract_events")
    ]
    if event_conditions and bind.execute(
        sa.text(
            "SELECT COUNT(*) FROM contract_events WHERE "
            + " OR ".join(event_conditions)
        )
    ).scalar():
        return True

    notification_conditions = [
        f"{name} IS NOT NULL"
        for name in (
            "contract_event_id",
            "correlation_id",
            "idempotency_key",
            "template_key",
        )
        if name in _columns("activity_notifications")
    ]
    if notification_conditions and bind.execute(
        sa.text(
            "SELECT COUNT(*) FROM activity_notifications WHERE "
            + " OR ".join(notification_conditions)
        )
    ).scalar():
        return True
    return False


def downgrade():
    bind = op.get_bind()
    if _phase2a_data_exists(bind):
        raise RuntimeError(
            "Downgrade bloqueado: existen comandos o trazabilidad Fase 2A que el "
            "esquema anterior no puede representar sin perdida."
        )

    if _inspector().has_table("operation_commands"):
        if bind.dialect.name == "postgresql":
            sequence_name = bind.execute(
                sa.text(
                    "SELECT pg_get_serial_sequence('operation_commands', 'id')"
                )
            ).scalar()
            if sequence_name:
                details = _postgres_sequence_details(sequence_name)
                if (
                    details
                    and details["object_comment"]
                    != OPERATION_COMMAND_SEQUENCE_COMMENT
                ):
                    id_column = next(
                        (
                            column
                            for column in _inspector().get_columns(
                                "operation_commands"
                            )
                            if column["name"] == "id"
                        ),
                        None,
                    )
                    if id_column and id_column.get("identity"):
                        raise RuntimeError(
                            "Downgrade bloqueado: la identity de "
                            "operation_commands.id es preexistente y no puede "
                            "preservarse al eliminar la tabla."
                        )
                    op.execute(
                        f"ALTER SEQUENCE {_quoted_sequence_name(details)} "
                        "OWNED BY NONE"
                    )
        operation_indexes = _indexes("operation_commands")
        for index_name in (
            "ix_operation_commands_correlation_id",
            "ix_operation_commands_actor_user_id",
        ):
            if index_name in operation_indexes:
                op.drop_index(index_name, table_name="operation_commands")
        op.drop_table("operation_commands")

    for index_name in (
        "ix_activity_notifications_correlation_id",
        "ix_activity_notifications_contract_event_id",
    ):
        if index_name in _indexes("activity_notifications"):
            op.drop_index(index_name, table_name="activity_notifications")
    with op.batch_alter_table("activity_notifications") as batch_op:
        for name, kind in (
            ("fk_activity_notifications_contract_event_id", "foreignkey"),
            ("uq_activity_notifications_idempotency_key", "unique"),
            ("uq_activity_notifications_domain_delivery", "unique"),
            ("ck_activity_notifications_attempt_count", "check"),
            ("ck_activity_notifications_delivery_status", "check"),
            ("ck_activity_notifications_channel", "check"),
        ):
            if name in _constraints("activity_notifications", kind):
                batch_op.drop_constraint(name, type_=kind)
        for column_name in (
            "attempt_count",
            "delivery_status",
            "channel",
            "template_key",
            "idempotency_key",
            "correlation_id",
            "contract_event_id",
        ):
            if column_name in _columns("activity_notifications"):
                batch_op.drop_column(column_name)

    for index_name in ("ix_audit_logs_operation", "ix_audit_logs_correlation_id"):
        if index_name in _indexes("audit_logs"):
            op.drop_index(index_name, table_name="audit_logs")
    with op.batch_alter_table("audit_logs") as batch_op:
        for column_name in ("metadata_json", "operation", "correlation_id"):
            if column_name in _columns("audit_logs"):
                batch_op.drop_column(column_name)

    if "ix_contract_events_correlation_id" in _indexes("contract_events"):
        op.drop_index("ix_contract_events_correlation_id", table_name="contract_events")
    with op.batch_alter_table("contract_events") as batch_op:
        for name, kind in (
            ("fk_contract_events_causation_event_id", "foreignkey"),
            ("uq_contract_events_idempotency_key", "unique"),
            ("uq_contract_events_contract_sequence", "unique"),
            ("ck_contract_events_sequence_positive", "check"),
        ):
            if name in _constraints("contract_events", kind):
                batch_op.drop_constraint(name, type_=kind)
        for column_name in (
            "idempotency_key",
            "causation_event_id",
            "correlation_id",
            "sequence_no",
        ):
            if column_name in _columns("contract_events"):
                batch_op.drop_column(column_name)

    with op.batch_alter_table("contract_requests") as batch_op:
        for name in (
            "ck_contract_requests_version",
            "ck_contract_requests_contracting_mode",
            "ck_contract_requests_estado",
        ):
            if name in _constraints("contract_requests", "check"):
                batch_op.drop_constraint(name, type_="check")
        for column_name in ("version", "contracting_mode"):
            if column_name in _columns("contract_requests"):
                batch_op.drop_column(column_name)
