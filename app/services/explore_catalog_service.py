from dataclasses import dataclass


@dataclass(frozen=True)
class ExploreTrade:
    id: str
    category_id: str
    title: str
    examples: tuple[str, ...]
    image_filename: str
    alt_text: str
    search_term: str


@dataclass(frozen=True)
class ExploreCategory:
    id: str
    title: str
    trades: tuple[ExploreTrade, ...]


EXPLORE_CATALOG = (
    ExploreCategory(
        id="climatizacion-y-gas",
        title="Climatización y gas",
        trades=(
            ExploreTrade(
                id="aire-acondicionado",
                category_id="climatizacion-y-gas",
                title="Aire acondicionado",
                examples=("Equipos split", "Mantenimiento preventivo", "Revisión de fallas"),
                image_filename="aire-acondicionado.webp",
                alt_text="Escena ilustrativa de un técnico revisando un equipo de aire acondicionado split.",
                search_term="Técnico en Aire Acondicionado",
            ),
            ExploreTrade(
                id="calderas-y-calefaccion",
                category_id="climatizacion-y-gas",
                title="Calderas y calefacción",
                examples=("Calderas", "Pisos radiantes", "Controles de presión"),
                image_filename="calderas-y-calefaccion.webp",
                alt_text="Escena ilustrativa de un técnico controlando una caldera y su circuito de calefacción.",
                search_term="Calderas y calefacción",
            ),
            ExploreTrade(
                id="gas-y-artefactos",
                category_id="climatizacion-y-gas",
                title="Gas y artefactos",
                examples=("Calefones", "Artefactos a gas", "Control de conexiones"),
                image_filename="gas-y-artefactos.webp",
                alt_text="Escena ilustrativa de un técnico revisando las conexiones de un calefón a gas.",
                search_term="Gas y artefactos",
            ),
            ExploreTrade(
                id="refrigeracion-comercial",
                category_id="climatizacion-y-gas",
                title="Refrigeración comercial",
                examples=("Vitrinas refrigeradas", "Cámaras de frío", "Diagnóstico técnico"),
                image_filename="refrigeracion-comercial.webp",
                alt_text="Escena ilustrativa de un técnico trabajando en una vitrina de refrigeración comercial.",
                search_term="Refrigeración comercial",
            ),
        ),
    ),
    ExploreCategory(
        id="electricidad-seguridad-y-conectividad",
        title="Electricidad, seguridad y conectividad",
        trades=(
            ExploreTrade(
                id="electricidad-domiciliaria",
                category_id="electricidad-seguridad-y-conectividad",
                title="Electricidad domiciliaria",
                examples=("Tableros", "Circuitos", "Protecciones eléctricas"),
                image_filename="electricidad-domiciliaria.webp",
                alt_text="Escena ilustrativa de un electricista trabajando en un tablero domiciliario.",
                search_term="Electricista",
            ),
            ExploreTrade(
                id="electricidad-industrial-y-motores",
                category_id="electricidad-seguridad-y-conectividad",
                title="Electricidad industrial y motores",
                examples=("Motores eléctricos", "Tableros industriales", "Mediciones"),
                image_filename="electricidad-industrial-motores.webp",
                alt_text="Escena ilustrativa de un técnico midiendo un motor eléctrico industrial.",
                search_term="Electricidad industrial y motores",
            ),
            ExploreTrade(
                id="camaras-alarmas-y-porteros",
                category_id="electricidad-seguridad-y-conectividad",
                title="Cámaras, alarmas y porteros",
                examples=("Cámaras", "Alarmas", "Porteros eléctricos"),
                image_filename="camaras-alarmas-y-porteros.webp",
                alt_text="Escena ilustrativa de un instalador ajustando una cámara de seguridad exterior.",
                search_term="Cámaras, alarmas y porteros",
            ),
            ExploreTrade(
                id="redes-y-cableado-estructurado",
                category_id="electricidad-seguridad-y-conectividad",
                title="Redes y cableado estructurado",
                examples=("Racks", "Cableado de red", "Pruebas de conexión"),
                image_filename="redes-y-cableado-estructurado.webp",
                alt_text="Escena ilustrativa de un técnico trabajando en un rack con cables de red azules.",
                search_term="Redes y cableado estructurado",
            ),
        ),
    ),
    ExploreCategory(
        id="obra-y-remodelacion",
        title="Obra y remodelación",
        trades=(
            ExploreTrade(
                id="albanileria",
                category_id="obra-y-remodelacion",
                title="Albañilería",
                examples=("Mampostería", "Revoques", "Reparaciones"),
                image_filename="albanileria.webp",
                alt_text="Escena ilustrativa de un albañil aplicando revoque sobre una pared de ladrillos.",
                search_term="Albañilería",
            ),
            ExploreTrade(
                id="construccion-en-seco",
                category_id="obra-y-remodelacion",
                title="Construcción en seco",
                examples=("Tabiques", "Cielorrasos", "Placas de yeso"),
                image_filename="construccion-en-seco.webp",
                alt_text="Escena ilustrativa de una instaladora fijando placas sobre perfiles metálicos.",
                search_term="Construcción en seco",
            ),
            ExploreTrade(
                id="remodelacion-de-interiores",
                category_id="obra-y-remodelacion",
                title="Remodelación de interiores",
                examples=("Redistribución", "Renovaciones", "Terminaciones"),
                image_filename="remodelacion-interiores.webp",
                alt_text="Escena ilustrativa de un profesional midiendo perfilería durante una remodelación interior.",
                search_term="Remodelación de interiores",
            ),
            ExploreTrade(
                id="techos-e-impermeabilizacion",
                category_id="obra-y-remodelacion",
                title="Techos e impermeabilización",
                examples=("Membranas", "Sellados", "Cubiertas"),
                image_filename="techos-e-impermeabilizacion.webp",
                alt_text="Escena ilustrativa de un profesional aplicando impermeabilizante sobre una terraza.",
                search_term="Techos e impermeabilización",
            ),
            ExploreTrade(
                id="plomeria",
                category_id="obra-y-remodelacion",
                title="Plomería",
                examples=("Pérdidas", "Desagües", "Griferías"),
                image_filename="plomeria.webp",
                alt_text="Escena ilustrativa de un plomero reparando el desagüe debajo de un lavatorio.",
                search_term="Plomero",
            ),
        ),
    ),
    ExploreCategory(
        id="revestimientos-y-terminaciones",
        title="Revestimientos y terminaciones",
        trades=(
            ExploreTrade(
                id="ceramicos-y-porcelanato",
                category_id="revestimientos-y-terminaciones",
                title="Cerámicos y porcelanato",
                examples=("Pisos", "Revestimientos", "Nivelación"),
                image_filename="ceramicos-y-porcelanato.webp",
                alt_text="Escena ilustrativa de un colocador nivelando piezas de porcelanato sobre un piso.",
                search_term="Cerámicos y porcelanato",
            ),
            ExploreTrade(
                id="mesadas-de-porcelanato",
                category_id="revestimientos-y-terminaciones",
                title="Mesadas de porcelanato",
                examples=("Mesadas de cocina", "Ajustes", "Colocación"),
                image_filename="mesadas-porcelanato.webp",
                alt_text="Escena ilustrativa de dos instaladores colocando una mesada de porcelanato.",
                search_term="Mesadas de porcelanato",
            ),
            ExploreTrade(
                id="pintura",
                category_id="revestimientos-y-terminaciones",
                title="Pintura",
                examples=("Interiores", "Terminaciones", "Preparación de superficies"),
                image_filename="pintura.webp",
                alt_text="Escena ilustrativa de un pintor aplicando pintura con rodillo sobre una pared interior.",
                search_term="Pintura",
            ),
            ExploreTrade(
                id="pisos-de-madera-y-flotantes",
                category_id="revestimientos-y-terminaciones",
                title="Pisos de madera y flotantes",
                examples=("Pisos flotantes", "Reparaciones", "Terminaciones"),
                image_filename="pisos-madera-flotantes.webp",
                alt_text="Escena ilustrativa de un instalador colocando tablas de piso flotante.",
                search_term="Pisos de madera y flotantes",
            ),
        ),
    ),
    ExploreCategory(
        id="carpinteria-y-metal",
        title="Carpintería y metal",
        trades=(
            ExploreTrade(
                id="carpinteria-y-muebles",
                category_id="carpinteria-y-metal",
                title="Carpintería y muebles",
                examples=("Muebles a medida", "Puertas", "Ajustes"),
                image_filename="carpinteria-y-muebles.webp",
                alt_text="Escena ilustrativa de un carpintero instalando la puerta de un mueble de cocina.",
                search_term="Carpintería y muebles",
            ),
            ExploreTrade(
                id="herreria-rejas-y-portones",
                category_id="carpinteria-y-metal",
                title="Herrería, rejas y portones",
                examples=("Rejas", "Portones", "Estructuras metálicas"),
                image_filename="herreria-rejas-y-portones.webp",
                alt_text="Escena ilustrativa de un herrero ajustando el mecanismo de un portón metálico.",
                search_term="Herrería, rejas y portones",
            ),
            ExploreTrade(
                id="cortinas-metalicas",
                category_id="carpinteria-y-metal",
                title="Cortinas metálicas",
                examples=("Guías", "Motores", "Mantenimiento"),
                image_filename="cortinas-metalicas.webp",
                alt_text="Escena ilustrativa de un técnico ajustando una cortina metálica comercial.",
                search_term="Cortinas metálicas",
            ),
        ),
    ),
)


def get_explore_catalog():
    return EXPLORE_CATALOG
