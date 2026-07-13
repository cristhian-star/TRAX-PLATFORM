(function () {
    const MAX_RADIUS_KM = 200;
    const DEFAULT_RADIUS_KM = 10;
    const initializedMaps = new WeakSet();

    const toNumber = (value, fallback = null) => {
        const parsed = Number.parseFloat(value);
        return Number.isFinite(parsed) ? parsed : fallback;
    };

    const clampRadius = (radius) => {
        if (!Number.isFinite(radius)) {
            return DEFAULT_RADIUS_KM;
        }

        return Math.min(Math.max(radius, 1), MAX_RADIUS_KM);
    };

    const readRadius = (root) => {
        const select = document.querySelector("[data-coverage-radius]");
        const customInput = document.querySelector("[data-coverage-radius-custom]");

        if (select) {
            const rawValue = select.value === "PERSONALIZADO" ? customInput?.value : select.value;
            return clampRadius(Number.parseInt(rawValue, 10));
        }

        return clampRadius(Number.parseInt(root.dataset.radiusKm, 10));
    };

    const setFallbackState = (root, message) => {
        const fallback = root.querySelector("[data-coverage-map-fallback]");
        const canvas = root.querySelector("[data-coverage-map-canvas]");
        const fallbackText = fallback?.querySelector("small");

        root.classList.remove("is-map-ready");
        root.classList.add("is-map-fallback");

        if (canvas) {
            canvas.hidden = true;
        }

        if (fallback) {
            fallback.hidden = false;
        }

        if (fallbackText && message) {
            fallbackText.textContent = message;
        }
    };

    const getInitialCenter = (root) => {
        const lat = toNumber(root.dataset.lat);
        const lng = toNumber(root.dataset.lng);

        if (lat !== null && lng !== null) {
            return { lat, lng };
        }

        return {
            lat: toNumber(root.dataset.defaultLat, -34.603722),
            lng: toNumber(root.dataset.defaultLng, -58.381592),
        };
    };

    const updateHiddenCoordinates = (position) => {
        const latitudeInput = document.querySelector("[data-coverage-latitude]");
        const longitudeInput = document.querySelector("[data-coverage-longitude]");

        if (latitudeInput) {
            latitudeInput.value = position.lat().toFixed(6);
        }

        if (longitudeInput) {
            longitudeInput.value = position.lng().toFixed(6);
        }
    };

    const fitCircle = (map, circle) => {
        const bounds = circle.getBounds();

        if (bounds) {
            map.fitBounds(bounds, 32);
        }
    };

    const setMapReady = (root) => {
        const fallback = root.querySelector("[data-coverage-map-fallback]");
        const canvas = root.querySelector("[data-coverage-map-canvas]");

        root.classList.remove("is-map-fallback");
        root.classList.add("is-map-ready");

        if (canvas) {
            canvas.hidden = false;
        }

        if (fallback) {
            fallback.hidden = true;
        }
    };

    const initPrivateMap = (root, map, center) => {
        const marker = new google.maps.Marker({
            position: center,
            map,
            draggable: true,
            title: "Punto base de cobertura",
        });
        const circle = new google.maps.Circle({
            map,
            center,
            radius: readRadius(root) * 1000,
            strokeColor: "#0ea5b7",
            strokeOpacity: 0.8,
            strokeWeight: 2,
            fillColor: "#0ea5b7",
            fillOpacity: 0.16,
        });
        const syncCircle = () => {
            const radius = readRadius(root);
            circle.setRadius(radius * 1000);
            circle.setCenter(marker.getPosition());
            root.dataset.radiusKm = String(radius);
            fitCircle(map, circle);
        };

        updateHiddenCoordinates(marker.getPosition());
        fitCircle(map, circle);

        marker.addListener("dragend", () => {
            const position = marker.getPosition();
            circle.setCenter(position);
            updateHiddenCoordinates(position);
            fitCircle(map, circle);
        });

        document.querySelector("[data-coverage-radius]")?.addEventListener("change", syncCircle);
        document.querySelector("[data-coverage-radius-custom]")?.addEventListener("input", syncCircle);
    };

    const initPublicMap = (root, map, center) => {
        const circle = new google.maps.Circle({
            map,
            center,
            radius: readRadius(root) * 1000,
            strokeColor: "#0ea5b7",
            strokeOpacity: 0.8,
            strokeWeight: 2,
            fillColor: "#0ea5b7",
            fillOpacity: 0.16,
        });

        fitCircle(map, circle);
    };

    const initCoverageMap = (root) => {
        if (initializedMaps.has(root)) {
            return;
        }

        if (root.dataset.hasApiKey !== "true") {
            setFallbackState(root, "Mapa interactivo no disponible en este entorno.");
            initializedMaps.add(root);
            return;
        }

        if (!window.google?.maps) {
            return;
        }

        initializedMaps.add(root);

        const canvas = root.querySelector("[data-coverage-map-canvas]");
        const center = getInitialCenter(root);

        if (!canvas || center.lat === null || center.lng === null) {
            setFallbackState(root, "Mapa interactivo no disponible en este entorno.");
            return;
        }

        const map = new google.maps.Map(canvas, {
            center,
            clickableIcons: false,
            fullscreenControl: false,
            mapTypeControl: false,
            streetViewControl: false,
            zoom: 11,
        });

        if (root.dataset.mapMode === "private") {
            initPrivateMap(root, map, center);
        } else {
            initPublicMap(root, map, center);
        }

        setMapReady(root);
    };

    const initAllCoverageMaps = () => {
        document.querySelectorAll("[data-coverage-map]").forEach(initCoverageMap);
    };

    window.traxInitCoverageMaps = initAllCoverageMaps;

    document.addEventListener("DOMContentLoaded", initAllCoverageMaps);
}());
