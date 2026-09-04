from alembic.script import ScriptDirectory


REQUIRED_SPRINT7_ANCESTOR = "20260726_07"


def assert_database_at_repository_head(
    config,
    applied_revisions,
    required_ancestor=REQUIRED_SPRINT7_ANCESTOR,
):
    """Require one repository head, one applied revision, and the Sprint 7 lineage."""
    script = ScriptDirectory.from_config(config)
    heads = tuple(script.get_heads())
    if len(heads) != 1:
        raise RuntimeError(f"Alembic debe tener exactamente un head; encontrados: {heads}")

    revisions = tuple(applied_revisions)
    if len(revisions) != 1:
        raise RuntimeError(
            "alembic_version debe contener exactamente una revision; "
            f"encontradas: {revisions}"
        )

    applied = revisions[0]
    try:
        applied_script = script.get_revision(applied)
    except Exception as exc:
        raise RuntimeError(f"Revision Alembic aplicada desconocida: {applied}") from exc
    if applied_script is None:
        raise RuntimeError(f"Revision Alembic aplicada desconocida: {applied}")

    head = heads[0]
    if applied != head:
        raise RuntimeError(f"La base no esta en el head vigente {head}: {applied}")

    try:
        ancestor_script = script.get_revision(required_ancestor)
    except Exception as exc:
        raise RuntimeError(f"Falta la revision historica {required_ancestor}") from exc
    if ancestor_script is None:
        raise RuntimeError(f"Falta la revision historica {required_ancestor}")

    try:
        lineage = tuple(
            script.revision_map.iterate_revisions(
                head,
                required_ancestor,
                inclusive=True,
            )
        )
    except Exception as exc:
        raise RuntimeError(
            f"{required_ancestor} no es ancestro del head vigente {head}"
        ) from exc
    if required_ancestor not in {revision.revision for revision in lineage}:
        raise RuntimeError(f"{required_ancestor} no es ancestro del head vigente {head}")

    return head
