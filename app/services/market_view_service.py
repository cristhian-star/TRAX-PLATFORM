from dataclasses import dataclass


@dataclass(frozen=True)
class MarketIndicator:
    icon: str
    label: str
    value: str
    description: str


@dataclass(frozen=True)
class MarketWorkReference:
    name: str
    unit: str
    price_range: str = "$0 – $0"


@dataclass(frozen=True)
class MarketPriceReference:
    icon: str
    service: str
    search_term: str
    works: tuple[MarketWorkReference, ...]


@dataclass(frozen=True)
class MarketDemandReference:
    icon: str
    service: str
    values: tuple[int, int, int, int, int, int]
    closing_trend: str
    trend_symbol: str
    summary: str

    @property
    def chart_points(self) -> tuple[tuple[int, int], ...]:
        x_positions = (8, 52, 96, 140, 184, 228)
        return tuple((x, 92 - value) for x, value in zip(x_positions, self.values))

    @property
    def line_points(self) -> str:
        return " ".join(f"{x},{y}" for x, y in self.chart_points)

    @property
    def area_points(self) -> str:
        return f"8,92 {self.line_points} 228,92"


MARKET_INDICATORS = (
    MarketIndicator(
        icon="wallet",
        label="Ticket promedio",
        value="$32.400",
        description="Referencia simulada para servicios técnicos generales.",
    ),
    MarketIndicator(
        icon="range",
        label="Rango habitual",
        value="$18k–$65k",
        description="Estimación simulada según categoría y urgencia.",
    ),
    MarketIndicator(
        icon="demand",
        label="Demanda activa",
        value="1.284",
        description="Consultas simuladas para un período mensual.",
    ),
    MarketIndicator(
        icon="urgency",
        label="Urgencias",
        value="+23%",
        description="Variación semanal simulada de servicios urgentes.",
    ),
)


MARKET_PRICE_REFERENCES = (
    MarketPriceReference(
        icon="electricity",
        service="Electricidad",
        search_term="Electricidad",
        works=(
            MarketWorkReference("Visita y diagnóstico", "por visita"),
            MarketWorkReference("Cambio de tomacorriente o llave", "por unidad"),
            MarketWorkReference("Instalación de luminaria", "por unidad"),
            MarketWorkReference("Tablero eléctrico domiciliario", "por trabajo"),
            MarketWorkReference("Instalación eléctrica", "por punto"),
        ),
    ),
    MarketPriceReference(
        icon="cooling",
        service="Refrigeración y climatización",
        search_term="Refrigeracion A/C",
        works=(
            MarketWorkReference("Service preventivo de aire acondicionado", "por equipo"),
            MarketWorkReference("Recarga de gas refrigerante", "por equipo"),
            MarketWorkReference("Instalación de split frío-calor hasta 3.000 frigorías", "por equipo"),
            MarketWorkReference("Instalación de split de 3.001 a 5.500 frigorías", "por equipo"),
            MarketWorkReference("Reparación de equipo split", "por trabajo"),
        ),
    ),
    MarketPriceReference(
        icon="plumbing",
        service="Plomería",
        search_term="Plomeria",
        works=(
            MarketWorkReference("Visita y diagnóstico", "por visita"),
            MarketWorkReference("Reparación de pérdida visible", "por trabajo"),
            MarketWorkReference("Cambio de grifería", "por unidad"),
            MarketWorkReference("Destapación domiciliaria", "por trabajo"),
            MarketWorkReference("Instalación de sanitarios", "por unidad"),
        ),
    ),
    MarketPriceReference(
        icon="gas",
        service="Gas domiciliario",
        search_term="Gas domiciliario",
        works=(
            MarketWorkReference("Visita y diagnóstico", "por visita"),
            MarketWorkReference("Instalación de artefacto a gas", "por unidad"),
            MarketWorkReference("Reparación de fuga", "por trabajo"),
            MarketWorkReference("Conexión de cocina o calefón", "por unidad"),
            MarketWorkReference("Prueba de hermeticidad", "por instalación"),
        ),
    ),
    MarketPriceReference(
        icon="construction",
        service="Construcción en seco",
        search_term="Construccion en seco",
        works=(
            MarketWorkReference("Revestimiento con placa de yeso", "por m²"),
            MarketWorkReference("Cielorraso de placa de yeso", "por m²"),
            MarketWorkReference("Tabique divisorio", "por m²"),
            MarketWorkReference("Reparación de placa", "por trabajo"),
            MarketWorkReference("Aislación interior", "por m²"),
        ),
    ),
    MarketPriceReference(
        icon="finishes",
        service="Revestimientos y terminaciones",
        search_term="Pintura",
        works=(
            MarketWorkReference("Pintura interior", "por m²"),
            MarketWorkReference("Colocación de porcelanato", "por m²"),
            MarketWorkReference("Colocación de cerámicos", "por m²"),
            MarketWorkReference("Colocación de piso flotante", "por m²"),
            MarketWorkReference("Preparación de superficies", "por m²"),
        ),
    ),
)


MARKET_DEMAND_REFERENCES = (
    MarketDemandReference(
        icon="electricity",
        service="Electricidad",
        values=(42, 50, 47, 61, 67, 74),
        closing_trend="Cierre en alza",
        trend_symbol="↗",
        summary="La evolución simulada termina por encima de los períodos iniciales.",
    ),
    MarketDemandReference(
        icon="cooling",
        service="Refrigeración",
        values=(58, 63, 70, 68, 77, 72),
        closing_trend="Cierre con leve baja",
        trend_symbol="↘",
        summary="La evolución simulada baja en el último período después de un punto más alto.",
    ),
    MarketDemandReference(
        icon="plumbing",
        service="Plomería",
        values=(45, 52, 49, 55, 54, 62),
        closing_trend="Cierre en alza",
        trend_symbol="↗",
        summary="La evolución simulada cierra con una subida moderada.",
    ),
    MarketDemandReference(
        icon="metalwork",
        service="Herrería",
        values=(38, 42, 46, 45, 49, 51),
        closing_trend="Cierre estable al alza",
        trend_symbol="↗",
        summary="La evolución simulada muestra una subida gradual con una variación intermedia.",
    ),
)


def build_markets_page_context():
    """Return display-only simulated data for the public markets guide."""
    return {
        "market_indicators": MARKET_INDICATORS,
        "market_price_references": MARKET_PRICE_REFERENCES,
        "market_demand_references": MARKET_DEMAND_REFERENCES,
    }
