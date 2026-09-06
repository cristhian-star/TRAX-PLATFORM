from dataclasses import dataclass


@dataclass(frozen=True)
class TaxonomySpecialty:
    slug: str
    nombre: str
    aliases: tuple[str, ...] = ()


@dataclass(frozen=True)
class TaxonomyRubro:
    slug: str
    nombre: str
    aliases: tuple[str, ...] = ()
    especialidades: tuple[TaxonomySpecialty, ...] = ()


@dataclass(frozen=True)
class TaxonomyCategory:
    slug: str
    nombre: str
    aliases: tuple[str, ...] = ()
    rubros: tuple[TaxonomyRubro, ...] = ()


@dataclass(frozen=True)
class TaxonomyIndustry:
    slug: str
    nombre: str
    aliases: tuple[str, ...] = ()
    categorias: tuple[TaxonomyCategory, ...] = ()


TAXONOMY_VERSION = "trax-taxonomy-v1"


TRAX_TAXONOMY = (
    TaxonomyIndustry(
        slug="construccion",
        nombre="Construccion",
        aliases=("obra", "mantenimiento edilicio", "servicios tecnicos"),
        categorias=(
            TaxonomyCategory(
                slug="electricidad",
                nombre="Electricidad",
                aliases=("electrico", "electricista"),
                rubros=(
                    TaxonomyRubro(
                        slug="electricista",
                        nombre="Electricista",
                        aliases=("electricidad", "electricista matriculado"),
                        especialidades=(
                            TaxonomySpecialty(slug="industrial", nombre="Industrial"),
                            TaxonomySpecialty(slug="domiciliaria", nombre="Domiciliaria"),
                            TaxonomySpecialty(slug="tableros", nombre="Tableros"),
                        ),
                    ),
                ),
            ),
            TaxonomyCategory(
                slug="plomeria",
                nombre="Plomeria",
                aliases=("plomero", "sanitario"),
                rubros=(
                    TaxonomyRubro(
                        slug="plomero",
                        nombre="Plomero",
                        aliases=("plomeria", "plomero residencial y comercial"),
                        especialidades=(
                            TaxonomySpecialty(slug="residencial", nombre="Residencial"),
                            TaxonomySpecialty(slug="comercial", nombre="Comercial"),
                            TaxonomySpecialty(slug="fugas", nombre="Fugas"),
                        ),
                    ),
                ),
            ),
        ),
    ),
    TaxonomyIndustry(
        slug="hogar",
        nombre="Hogar",
        aliases=("vivienda", "domicilio"),
        categorias=(
            TaxonomyCategory(
                slug="refrigeracion",
                nombre="Refrigeracion",
                aliases=("climatizacion", "aire acondicionado", "refrigeracion a/c"),
                rubros=(
                    TaxonomyRubro(
                        slug="tecnico-aire-acondicionado",
                        nombre="Tecnico en Aire Acondicionado",
                        aliases=(
                            "refrigeracion a/c",
                            "tecnico en refrigeracion",
                            "tecnico en aire acondicionado",
                        ),
                        especialidades=(
                            TaxonomySpecialty(slug="split", nombre="Split"),
                            TaxonomySpecialty(slug="vrv", nombre="VRV"),
                            TaxonomySpecialty(slug="central", nombre="Central"),
                        ),
                    ),
                ),
            ),
        ),
    ),
)


def _normalize(value):
    return (value or "").strip().casefold()


def _matches(value, *candidates):
    normalized = _normalize(value)
    if not normalized:
        return False
    return any(normalized == _normalize(candidate) for candidate in candidates if candidate)


def _as_dict_industry(industry):
    return {
        "slug": industry.slug,
        "nombre": industry.nombre,
        "aliases": list(industry.aliases),
    }


def _as_dict_category(industry, category):
    return {
        "slug": category.slug,
        "nombre": category.nombre,
        "aliases": list(category.aliases),
        "industria": industry.nombre,
        "industria_slug": industry.slug,
    }


def _as_dict_rubro(industry, category, rubro):
    return {
        "slug": rubro.slug,
        "nombre": rubro.nombre,
        "aliases": list(rubro.aliases),
        "categoria": category.nombre,
        "categoria_slug": category.slug,
        "industria": industry.nombre,
        "industria_slug": industry.slug,
    }


def _as_dict_specialty(industry, category, rubro, specialty):
    return {
        "slug": specialty.slug,
        "nombre": specialty.nombre,
        "aliases": list(specialty.aliases),
        "rubro": rubro.nombre,
        "rubro_slug": rubro.slug,
        "categoria": category.nombre,
        "categoria_slug": category.slug,
        "industria": industry.nombre,
        "industria_slug": industry.slug,
    }


def obtener_industrias():
    return [_as_dict_industry(industry) for industry in TRAX_TAXONOMY]


def obtener_categorias(industria=None):
    categorias = []
    for industry in TRAX_TAXONOMY:
        if industria and not _matches(industria, industry.nombre, industry.slug, *industry.aliases):
            continue
        categorias.extend(_as_dict_category(industry, category) for category in industry.categorias)
    return categorias


def obtener_rubros(industria=None, categoria=None):
    rubros = []
    for industry in TRAX_TAXONOMY:
        if industria and not _matches(industria, industry.nombre, industry.slug, *industry.aliases):
            continue
        for category in industry.categorias:
            if categoria and not _matches(categoria, category.nombre, category.slug, *category.aliases):
                continue
            rubros.extend(_as_dict_rubro(industry, category, rubro) for rubro in category.rubros)
    return rubros


def obtener_especialidades(industria=None, categoria=None, rubro=None):
    especialidades = []
    for industry in TRAX_TAXONOMY:
        if industria and not _matches(industria, industry.nombre, industry.slug, *industry.aliases):
            continue
        for category in industry.categorias:
            if categoria and not _matches(categoria, category.nombre, category.slug, *category.aliases):
                continue
            for rubro_item in category.rubros:
                if rubro and not _matches(rubro, rubro_item.nombre, rubro_item.slug, *rubro_item.aliases):
                    continue
                especialidades.extend(
                    _as_dict_specialty(industry, category, rubro_item, specialty)
                    for specialty in rubro_item.especialidades
                )
    return especialidades


def buscar_por_taxonomia(industria=None, categoria=None, rubro=None, especialidad=None, termino=None):
    results = []
    normalized_term = _normalize(termino)

    for rubro_item in obtener_rubros(industria=industria, categoria=categoria):
        rubro_matches = (
            not rubro
            or _matches(rubro, rubro_item["nombre"], rubro_item["slug"], *rubro_item["aliases"])
        )
        term_matches = (
            not normalized_term
            or normalized_term in _normalize(rubro_item["nombre"])
            or any(normalized_term in _normalize(alias) for alias in rubro_item["aliases"])
            or normalized_term in _normalize(rubro_item["categoria"])
            or normalized_term in _normalize(rubro_item["industria"])
        )

        if rubro_matches and term_matches and not especialidad:
            results.append({**rubro_item, "nivel": "rubro"})

    for specialty in obtener_especialidades(industria=industria, categoria=categoria, rubro=rubro):
        specialty_matches = (
            not especialidad
            or _matches(especialidad, specialty["nombre"], specialty["slug"], *specialty["aliases"])
        )
        term_matches = (
            not normalized_term
            or normalized_term in _normalize(specialty["nombre"])
            or any(normalized_term in _normalize(alias) for alias in specialty["aliases"])
            or normalized_term in _normalize(specialty["rubro"])
            or normalized_term in _normalize(specialty["categoria"])
            or normalized_term in _normalize(specialty["industria"])
        )

        if specialty_matches and term_matches:
            results.append({**specialty, "nivel": "especialidad"})

    return results


def resolver_termino_legacy(servicio=None, categoria=None, rubro=None, especialidad=None):
    term = servicio or categoria or rubro or especialidad
    matches = buscar_por_taxonomia(termino=term)
    return matches[0] if matches else None
