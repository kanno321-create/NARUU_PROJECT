"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import {
  GoogleMap,
  useJsApiLoader,
  Marker,
  DirectionsRenderer,
  InfoWindow,
} from "@react-google-maps/api";
import Link from "next/link";
import AppShell from "@/components/layout/app-shell";
import { api } from "@/lib/api";
import type { Waypoint, PlaceResult } from "@/lib/types";
import ErrorBanner from "@/components/ui/error-banner";
import LoadingSpinner from "@/components/ui/loading-spinner";

const DAEGU_CENTER = { lat: 35.8714, lng: 128.5964 };
const MAP_STYLE = { width: "100%", height: "500px" };

const WAYPOINT_CATEGORIES = [
  { value: "tourism", label: "관광", color: "#3b82f6" },
  { value: "medical", label: "의료", color: "#ef4444" },
  { value: "restaurant", label: "맛집", color: "#f59e0b" },
  { value: "hotel", label: "숙박", color: "#8b5cf6" },
  { value: "shopping", label: "쇼핑", color: "#10b981" },
];

const MARKER_COLORS: Record<string, string> = {
  tourism: "blue",
  medical: "red",
  restaurant: "orange",
  hotel: "purple",
  shopping: "green",
};

export default function NewRoutePage() {
  const router = useRouter();

  // Google Maps
  const [mapsApiKey, setMapsApiKey] = useState<string>("");
  const [keyLoaded, setKeyLoaded] = useState(false);

  // Route form
  const [nameJa, setNameJa] = useState("");
  const [nameKo, setNameKo] = useState("");
  const [descJa, setDescJa] = useState("");
  const [descKo, setDescKo] = useState("");
  const [isTemplate, setIsTemplate] = useState(false);
  const [tags, setTags] = useState<string[]>([]);
  const [tagInput, setTagInput] = useState("");

  // Waypoints
  const [waypoints, setWaypoints] = useState<Waypoint[]>([]);
  const [selectedWp, setSelectedWp] = useState<number | null>(null);

  // Place search
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState<PlaceResult[]>([]);
  const [searching, setSearching] = useState(false);

  // Directions
  const [directions, setDirections] = useState<google.maps.DirectionsResult | null>(null);
  const [routeInfo, setRouteInfo] = useState<{
    distance: string;
    duration: string;
    totalWithStay: number;
  } | null>(null);

  // AI
  const [aiSuggestion, setAiSuggestion] = useState("");
  const [aiLoading, setAiLoading] = useState(false);

  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const mapRef = useRef<google.maps.Map | null>(null);

  // Load Google Maps API key from backend
  useEffect(() => {
    (async () => {
      try {
        const config = await api.get<{ api_key: string | null; configured: boolean }>(
          "/tour-routes/maps-config"
        );
        if (config.api_key) {
          setMapsApiKey(config.api_key);
        }
      } catch {
        setError("지도 설정을 불러오지 못했습니다.");
      } finally {
        setKeyLoaded(true);
      }
    })();
  }, []);

  const { isLoaded } = useJsApiLoader({
    googleMapsApiKey: mapsApiKey,
    libraries: ["places"],
  });

  const onMapLoad = useCallback((map: google.maps.Map) => {
    mapRef.current = map;
  }, []);

  // Map click → add waypoint
  const onMapClick = useCallback(
    (e: google.maps.MapMouseEvent) => {
      if (!e.latLng) return;
      const newWp: Waypoint = {
        order: waypoints.length + 1,
        name_ja: `地点 ${waypoints.length + 1}`,
        name_ko: `지점 ${waypoints.length + 1}`,
        lat: e.latLng.lat(),
        lng: e.latLng.lng(),
        category: "tourism",
        stay_minutes: 60,
      };
      setWaypoints((prev) => [...prev, newWp]);
    },
    [waypoints.length]
  );

  // Search places
  const searchPlaces = async () => {
    if (!searchQuery.trim()) return;
    setSearching(true);
    try {
      const data = await api.post<{ places: PlaceResult[] }>(
        "/tour-routes/places/search",
        { query: searchQuery, lat: DAEGU_CENTER.lat, lng: DAEGU_CENTER.lng }
      );
      setSearchResults(data.places);
    } catch {
      setError("장소 검색에 실패했습니다.");
    } finally {
      setSearching(false);
    }
  };

  // Add place from search results
  const addPlace = (place: PlaceResult) => {
    const newWp: Waypoint = {
      order: waypoints.length + 1,
      place_id: place.place_id,
      name_ja: place.name,
      name_ko: place.name,
      lat: place.lat,
      lng: place.lng,
      category: "tourism",
      stay_minutes: 60,
    };
    setWaypoints((prev) => [...prev, newWp]);
    setSearchResults([]);
    setSearchQuery("");

    // Pan to place
    mapRef.current?.panTo({ lat: place.lat, lng: place.lng });
  };

  // Remove waypoint
  const removeWaypoint = (index: number) => {
    setWaypoints((prev) => {
      const updated = prev.filter((_, i) => i !== index);
      return updated.map((wp, i) => ({ ...wp, order: i + 1 }));
    });
    setSelectedWp(null);
  };

  // Move waypoint order
  const moveWaypoint = (index: number, direction: -1 | 1) => {
    const newIndex = index + direction;
    if (newIndex < 0 || newIndex >= waypoints.length) return;
    setWaypoints((prev) => {
      const updated = [...prev];
      [updated[index], updated[newIndex]] = [updated[newIndex], updated[index]];
      return updated.map((wp, i) => ({ ...wp, order: i + 1 }));
    });
  };

  // Update waypoint field
  const updateWaypoint = (index: number, field: keyof Waypoint, value: unknown) => {
    setWaypoints((prev) =>
      prev.map((wp, i) => (i === index ? { ...wp, [field]: value } : wp))
    );
  };

  // Calculate route with Google Directions
  const calculateRoute = useCallback(() => {
    if (waypoints.length < 2 || !isLoaded) return;

    const directionsService = new google.maps.DirectionsService();
    const origin = { lat: waypoints[0].lat, lng: waypoints[0].lng };
    const destination = {
      lat: waypoints[waypoints.length - 1].lat,
      lng: waypoints[waypoints.length - 1].lng,
    };
    const waypointsList = waypoints.slice(1, -1).map((wp) => ({
      location: { lat: wp.lat, lng: wp.lng },
      stopover: true,
    }));

    directionsService.route(
      {
        origin,
        destination,
        waypoints: waypointsList,
        optimizeWaypoints: true,
        travelMode: google.maps.TravelMode.DRIVING,
      },
      (result, status) => {
        if (status === "OK" && result) {
          setDirections(result);

          // Calculate totals
          let totalDist = 0;
          let totalDur = 0;
          result.routes[0].legs.forEach((leg) => {
            totalDist += leg.distance?.value || 0;
            totalDur += leg.duration?.value || 0;
          });

          const totalStay = waypoints.reduce((sum, wp) => sum + wp.stay_minutes, 0);

          setRouteInfo({
            distance: `${(totalDist / 1000).toFixed(1)} km`,
            duration: `${Math.round(totalDur / 60)}분`,
            totalWithStay: Math.round(totalDur / 60) + totalStay,
          });
        }
      }
    );
  }, [waypoints, isLoaded]);

  // Auto-calculate when waypoints change
  useEffect(() => {
    if (waypoints.length >= 2) {
      calculateRoute();
    } else {
      setDirections(null);
      setRouteInfo(null);
    }
  }, [waypoints, calculateRoute]);

  // AI route suggestion
  const getAiSuggestion = async () => {
    setAiLoading(true);
    try {
      const data = await api.post<{ suggestion: string }>(
        "/tour-routes/suggest",
        {
          interests: tagInput || undefined,
          duration_days: 1,
          include_medical: tags.includes("의료"),
        }
      );
      setAiSuggestion(data.suggestion);
    } catch {
      setError("AI 추천에 실패했습니다.");
    } finally {
      setAiLoading(false);
    }
  };

  // Save route
  const handleSave = async () => {
    if (!nameJa || !nameKo || waypoints.length < 2) {
      setError("루트명과 최소 2개의 경유지가 필요합니다.");
      return;
    }
    setSaving(true);
    try {
      await api.post("/tour-routes", {
        name_ja: nameJa,
        name_ko: nameKo,
        description_ja: descJa || undefined,
        description_ko: descKo || undefined,
        waypoints,
        tags: tags.length > 0 ? tags : undefined,
        is_template: isTemplate,
      });
      router.push("/routes");
    } catch {
      setError("루트 저장에 실패했습니다.");
    } finally {
      setSaving(false);
    }
  };

  // Tag management
  const addTag = () => {
    const t = tagInput.trim();
    if (t && !tags.includes(t)) {
      setTags((prev) => [...prev, t]);
      setTagInput("");
    }
  };

  if (!keyLoaded) {
    return (
      <AppShell>
        <LoadingSpinner text="설정 로딩 중..." />
      </AppShell>
    );
  }

  return (
    <AppShell>
      <div className="flex items-center gap-3 mb-6">
        <Link href="/routes" className="text-gray-400 hover:text-gray-600">
          &larr; 목록
        </Link>
        <h2 className="text-2xl font-bold text-gray-800">관광 루트 생성</h2>
      </div>

      <ErrorBanner message={error} />

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Panel: Route Info + Waypoint List */}
        <div className="lg:col-span-1 space-y-4">
          {/* Route Name */}
          <div className="bg-white rounded-xl p-4 shadow-sm space-y-3">
            <h3 className="font-semibold text-gray-700 text-sm">루트 정보</h3>
            <input
              type="text"
              value={nameJa}
              onChange={(e) => setNameJa(e.target.value)}
              placeholder="ルート名 (日本語) *"
              aria-label="루트명 (일본어)"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm outline-none focus:ring-2 focus:ring-naruu-500"
            />
            <input
              type="text"
              value={nameKo}
              onChange={(e) => setNameKo(e.target.value)}
              placeholder="루트명 (한국어) *"
              aria-label="루트명 (한국어)"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm outline-none focus:ring-2 focus:ring-naruu-500"
            />
            <div className="flex gap-2">
              <input
                type="text"
                value={tagInput}
                onChange={(e) => setTagInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter") {
                    e.preventDefault();
                    addTag();
                  }
                }}
                placeholder="태그 추가"
                className="flex-1 px-3 py-1.5 border border-gray-300 rounded-lg text-sm outline-none"
              />
              <button onClick={addTag} className="px-3 py-1.5 bg-gray-100 rounded-lg text-sm">
                +
              </button>
            </div>
            <div className="flex flex-wrap gap-1">
              {tags.map((t) => (
                <span
                  key={t}
                  className="inline-flex items-center gap-1 px-2 py-0.5 bg-naruu-50 text-naruu-700 rounded text-xs"
                >
                  {t}
                  <button onClick={() => setTags(tags.filter((x) => x !== t))} className="hover:text-red-500">
                    x
                  </button>
                </span>
              ))}
            </div>
            <label className="flex items-center gap-2 text-sm text-gray-600">
              <input
                type="checkbox"
                checked={isTemplate}
                onChange={(e) => setIsTemplate(e.target.checked)}
                className="w-4 h-4 text-naruu-600 rounded"
              />
              템플릿으로 저장 (재사용 가능)
            </label>
          </div>

          {/* Place Search */}
          <div className="bg-white rounded-xl p-4 shadow-sm space-y-3">
            <h3 className="font-semibold text-gray-700 text-sm">장소 검색</h3>
            <div className="flex gap-2">
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter") searchPlaces();
                }}
                placeholder="대구 맛집, 병원, 관광지..."
                className="flex-1 px-3 py-2 border border-gray-300 rounded-lg text-sm outline-none focus:ring-2 focus:ring-naruu-500"
              />
              <button
                onClick={searchPlaces}
                disabled={searching}
                className="px-4 py-2 bg-naruu-600 text-white rounded-lg text-sm hover:bg-naruu-700 disabled:opacity-50"
              >
                {searching ? "..." : "검색"}
              </button>
            </div>
            {searchResults.length > 0 && (
              <div className="max-h-48 overflow-y-auto space-y-1">
                {searchResults.map((place) => (
                  <button
                    key={place.place_id}
                    onClick={() => addPlace(place)}
                    className="w-full text-left p-2 rounded-lg hover:bg-naruu-50 transition text-sm"
                  >
                    <p className="font-medium text-gray-800">{place.name}</p>
                    <p className="text-xs text-gray-500 truncate">{place.address}</p>
                    {place.rating && (
                      <span className="text-xs text-amber-600">★ {place.rating}</span>
                    )}
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Waypoint List */}
          <div className="bg-white rounded-xl p-4 shadow-sm space-y-3">
            <h3 className="font-semibold text-gray-700 text-sm">
              경유지 ({waypoints.length}곳)
            </h3>
            <p className="text-xs text-gray-400">지도를 클릭하거나 장소를 검색해서 추가하세요</p>

            <div className="space-y-2 max-h-64 overflow-y-auto">
              {waypoints.map((wp, i) => (
                <div
                  key={i}
                  className={`p-3 rounded-lg border text-sm ${
                    selectedWp === i
                      ? "border-naruu-400 bg-naruu-50"
                      : "border-gray-200"
                  }`}
                  onClick={() => setSelectedWp(i)}
                >
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <span className="w-6 h-6 flex items-center justify-center bg-naruu-600 text-white rounded-full text-xs font-bold">
                        {wp.order}
                      </span>
                      <input
                        type="text"
                        value={wp.name_ko}
                        onChange={(e) => updateWaypoint(i, "name_ko", e.target.value)}
                        className="font-medium text-gray-800 border-b border-transparent focus:border-naruu-400 outline-none bg-transparent w-24"
                      />
                    </div>
                    <div className="flex items-center gap-1">
                      <button
                        onClick={(e) => { e.stopPropagation(); moveWaypoint(i, -1); }}
                        className="text-gray-400 hover:text-gray-600 text-xs"
                        disabled={i === 0}
                      >
                        ▲
                      </button>
                      <button
                        onClick={(e) => { e.stopPropagation(); moveWaypoint(i, 1); }}
                        className="text-gray-400 hover:text-gray-600 text-xs"
                        disabled={i === waypoints.length - 1}
                      >
                        ▼
                      </button>
                      <button
                        onClick={(e) => { e.stopPropagation(); removeWaypoint(i); }}
                        className="text-red-400 hover:text-red-600 text-xs ml-1"
                      >
                        삭제
                      </button>
                    </div>
                  </div>
                  <div className="flex gap-2">
                    <select
                      value={wp.category}
                      onChange={(e) => updateWaypoint(i, "category", e.target.value)}
                      onClick={(e) => e.stopPropagation()}
                      className="px-2 py-1 border border-gray-200 rounded text-xs"
                    >
                      {WAYPOINT_CATEGORIES.map((c) => (
                        <option key={c.value} value={c.value}>
                          {c.label}
                        </option>
                      ))}
                    </select>
                    <div className="flex items-center gap-1">
                      <input
                        type="number"
                        value={wp.stay_minutes}
                        onChange={(e) =>
                          updateWaypoint(i, "stay_minutes", Number(e.target.value) || 0)
                        }
                        onClick={(e) => e.stopPropagation()}
                        className="w-14 px-2 py-1 border border-gray-200 rounded text-xs text-center"
                        min={0}
                      />
                      <span className="text-xs text-gray-400">분</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Route Summary */}
          {routeInfo && (
            <div className="bg-gradient-to-r from-blue-50 to-naruu-50 rounded-xl p-4 shadow-sm">
              <h3 className="font-semibold text-gray-700 text-sm mb-2">경로 요약</h3>
              <div className="grid grid-cols-3 gap-2 text-center">
                <div>
                  <p className="text-lg font-bold text-naruu-700">{routeInfo.distance}</p>
                  <p className="text-xs text-gray-500">총 거리</p>
                </div>
                <div>
                  <p className="text-lg font-bold text-naruu-700">{routeInfo.duration}</p>
                  <p className="text-xs text-gray-500">이동 시간</p>
                </div>
                <div>
                  <p className="text-lg font-bold text-violet-700">
                    {Math.floor(routeInfo.totalWithStay / 60)}시간 {routeInfo.totalWithStay % 60}분
                  </p>
                  <p className="text-xs text-gray-500">체류 포함</p>
                </div>
              </div>
            </div>
          )}

          {/* AI Suggestion */}
          <div className="bg-gradient-to-r from-violet-50 to-blue-50 rounded-xl p-4 shadow-sm space-y-2">
            <button
              onClick={getAiSuggestion}
              disabled={aiLoading}
              className="w-full py-2 bg-violet-600 text-white rounded-lg text-sm hover:bg-violet-700 disabled:opacity-50"
            >
              {aiLoading ? "AI 분석 중..." : "AI 루트 추천 받기"}
            </button>
            {aiSuggestion && (
              <div className="p-3 bg-white rounded-lg text-xs text-gray-700 whitespace-pre-wrap max-h-48 overflow-y-auto">
                {aiSuggestion}
              </div>
            )}
          </div>

          {/* Save */}
          <div className="flex gap-3">
            <button
              onClick={handleSave}
              disabled={saving || !nameJa || !nameKo || waypoints.length < 2}
              className="flex-1 py-3 bg-naruu-600 text-white rounded-lg font-medium hover:bg-naruu-700 disabled:opacity-50 transition"
            >
              {saving ? "저장 중..." : "루트 저장"}
            </button>
            <Link
              href="/routes"
              className="px-6 py-3 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition text-center"
            >
              취소
            </Link>
          </div>
        </div>

        {/* Right: Google Map */}
        <div className="lg:col-span-2">
          <div className="bg-white rounded-xl shadow-sm overflow-hidden">
            {!mapsApiKey ? (
              <div className="flex items-center justify-center h-[500px] bg-gray-50">
                <div className="text-center">
                  <p className="text-gray-500 mb-2">Google Maps API 키가 설정되지 않았습니다</p>
                  <p className="text-xs text-gray-400">
                    .env에 GOOGLE_MAPS_API_KEY를 추가하세요
                  </p>
                </div>
              </div>
            ) : !isLoaded ? (
              <div className="flex items-center justify-center h-[500px] bg-gray-50">
                <p className="text-gray-400">지도 로딩 중...</p>
              </div>
            ) : (
              <GoogleMap
                mapContainerStyle={MAP_STYLE}
                center={DAEGU_CENTER}
                zoom={13}
                onLoad={onMapLoad}
                onClick={onMapClick}
                options={{
                  mapTypeControl: true,
                  streetViewControl: false,
                  fullscreenControl: true,
                }}
              >
                {/* Waypoint markers */}
                {!directions &&
                  waypoints.map((wp, i) => (
                    <Marker
                      key={i}
                      position={{ lat: wp.lat, lng: wp.lng }}
                      label={{
                        text: String(wp.order),
                        color: "white",
                        fontWeight: "bold",
                      }}
                      onClick={() => setSelectedWp(i)}
                    />
                  ))}

                {/* Directions route */}
                {directions && (
                  <DirectionsRenderer
                    directions={directions}
                    options={{
                      suppressMarkers: false,
                      polylineOptions: {
                        strokeColor: "#2563eb",
                        strokeWeight: 4,
                      },
                    }}
                  />
                )}

                {/* InfoWindow for selected */}
                {selectedWp !== null && waypoints[selectedWp] && (
                  <InfoWindow
                    position={{
                      lat: waypoints[selectedWp].lat,
                      lng: waypoints[selectedWp].lng,
                    }}
                    onCloseClick={() => setSelectedWp(null)}
                  >
                    <div className="text-sm">
                      <p className="font-bold">{waypoints[selectedWp].name_ko}</p>
                      <p className="text-gray-500">{waypoints[selectedWp].name_ja}</p>
                      <p className="text-xs mt-1">
                        체류: {waypoints[selectedWp].stay_minutes}분
                      </p>
                    </div>
                  </InfoWindow>
                )}
              </GoogleMap>
            )}
          </div>

          {/* Category legend */}
          <div className="mt-3 flex gap-4 text-xs text-gray-500">
            {WAYPOINT_CATEGORIES.map((c) => (
              <span key={c.value} className="flex items-center gap-1">
                <span
                  className="w-3 h-3 rounded-full"
                  style={{ backgroundColor: c.color }}
                />
                {c.label}
              </span>
            ))}
          </div>
        </div>
      </div>
    </AppShell>
  );
}
