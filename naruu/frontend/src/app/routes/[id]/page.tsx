"use client";

import { useEffect, useState, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import {
  GoogleMap,
  useJsApiLoader,
  DirectionsRenderer,
  Marker,
  InfoWindow,
} from "@react-google-maps/api";
import AppShell from "@/components/layout/app-shell";
import { api } from "@/lib/api";
import type { TourRoute, Waypoint } from "@/lib/types";

const DAEGU_CENTER = { lat: 35.8714, lng: 128.5964 };
const MAP_STYLE = { width: "100%", height: "450px" };

const CATEGORY_LABELS: Record<string, string> = {
  tourism: "관광",
  medical: "의료",
  restaurant: "맛집",
  hotel: "숙박",
  shopping: "쇼핑",
};

export default function RouteDetailPage() {
  const params = useParams();
  const router = useRouter();
  const [route, setRoute] = useState<TourRoute | null>(null);
  const [loading, setLoading] = useState(true);
  const [mapsApiKey, setMapsApiKey] = useState("");
  const [directions, setDirections] = useState<google.maps.DirectionsResult | null>(null);
  const [selectedWp, setSelectedWp] = useState<number | null>(null);

  useEffect(() => {
    (async () => {
      try {
        const [routeData, config] = await Promise.all([
          api.get<TourRoute>(`/tour-routes/${params.id}`),
          api.get<{ api_key: string | null }>("/tour-routes/maps-config"),
        ]);
        setRoute(routeData);
        if (config.api_key) setMapsApiKey(config.api_key);
      } catch {
        router.push("/routes");
      } finally {
        setLoading(false);
      }
    })();
  }, [params.id, router]);

  const { isLoaded } = useJsApiLoader({
    googleMapsApiKey: mapsApiKey,
    libraries: ["places"],
  });

  // Calculate directions on map load
  const onMapLoad = useCallback(
    (map: google.maps.Map) => {
      if (!route?.waypoints || route.waypoints.length < 2 || !isLoaded) return;

      const sorted = [...route.waypoints].sort((a, b) => a.order - b.order);
      const directionsService = new google.maps.DirectionsService();

      directionsService.route(
        {
          origin: { lat: sorted[0].lat, lng: sorted[0].lng },
          destination: { lat: sorted[sorted.length - 1].lat, lng: sorted[sorted.length - 1].lng },
          waypoints: sorted.slice(1, -1).map((wp) => ({
            location: { lat: wp.lat, lng: wp.lng },
            stopover: true,
          })),
          travelMode: google.maps.TravelMode.DRIVING,
        },
        (result, status) => {
          if (status === "OK" && result) {
            setDirections(result);
          }
        }
      );
    },
    [route, isLoaded]
  );

  const handleDelete = async () => {
    if (!confirm("이 루트를 보관함으로 이동하시겠습니까?")) return;
    try {
      await api.delete(`/tour-routes/${params.id}`);
      router.push("/routes");
    } catch (err) {
      console.error("Delete failed:", err);
    }
  };

  const handleCalculate = async () => {
    try {
      const updated = await api.post<TourRoute>(
        `/tour-routes/${params.id}/calculate`
      );
      setRoute(updated);
      alert("경로 계산 완료!");
    } catch (err) {
      console.error("Calculate failed:", err);
      alert("경로 계산에 실패했습니다. Google Maps API 키를 확인하세요.");
    }
  };

  if (loading) {
    return (
      <AppShell>
        <p className="text-gray-400">로딩 중...</p>
      </AppShell>
    );
  }

  if (!route) return null;

  const sortedWaypoints = [...(route.waypoints || [])].sort(
    (a, b) => a.order - b.order
  );

  const formatDuration = (minutes: number | null) => {
    if (!minutes) return "-";
    const h = Math.floor(minutes / 60);
    const m = minutes % 60;
    return h > 0 ? `${h}시간 ${m}분` : `${m}분`;
  };

  return (
    <AppShell>
      <div className="flex items-center justify-between mb-6">
        <div>
          <Link href="/routes" className="text-sm text-naruu-600 hover:underline">
            &larr; 루트 목록
          </Link>
          <h2 className="text-2xl font-bold text-gray-800 mt-1">{route.name_ja}</h2>
          <p className="text-gray-500">{route.name_ko}</p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={handleCalculate}
            className="px-4 py-2 bg-blue-50 text-blue-700 rounded-lg hover:bg-blue-100 transition text-sm font-medium"
          >
            경로 재계산
          </button>
          <button
            onClick={handleDelete}
            className="px-4 py-2 bg-red-50 text-red-600 rounded-lg hover:bg-red-100 transition text-sm font-medium"
          >
            보관
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Map */}
        <div className="lg:col-span-2">
          <div className="bg-white rounded-xl shadow-sm overflow-hidden">
            {!mapsApiKey || !isLoaded ? (
              <div className="flex items-center justify-center h-[450px] bg-gray-50">
                <p className="text-gray-400">
                  {mapsApiKey ? "지도 로딩 중..." : "Google Maps API 키가 필요합니다"}
                </p>
              </div>
            ) : (
              <GoogleMap
                mapContainerStyle={MAP_STYLE}
                center={
                  sortedWaypoints.length > 0
                    ? { lat: sortedWaypoints[0].lat, lng: sortedWaypoints[0].lng }
                    : DAEGU_CENTER
                }
                zoom={13}
                onLoad={onMapLoad}
              >
                {directions && (
                  <DirectionsRenderer
                    directions={directions}
                    options={{
                      polylineOptions: {
                        strokeColor: "#2563eb",
                        strokeWeight: 4,
                      },
                    }}
                  />
                )}

                {!directions &&
                  sortedWaypoints.map((wp, i) => (
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

                {selectedWp !== null && sortedWaypoints[selectedWp] && (
                  <InfoWindow
                    position={{
                      lat: sortedWaypoints[selectedWp].lat,
                      lng: sortedWaypoints[selectedWp].lng,
                    }}
                    onCloseClick={() => setSelectedWp(null)}
                  >
                    <div>
                      <p className="font-bold">{sortedWaypoints[selectedWp].name_ko}</p>
                      <p className="text-sm text-gray-500">
                        {sortedWaypoints[selectedWp].name_ja}
                      </p>
                      <p className="text-xs mt-1">
                        체류: {sortedWaypoints[selectedWp].stay_minutes}분
                      </p>
                    </div>
                  </InfoWindow>
                )}
              </GoogleMap>
            )}
          </div>

          {/* Route Summary Cards */}
          {(route.total_distance_km || route.total_duration_minutes) && (
            <div className="mt-4 grid grid-cols-3 gap-4">
              <div className="bg-white rounded-xl p-4 shadow-sm text-center">
                <p className="text-2xl font-bold text-naruu-700">
                  {sortedWaypoints.length}곳
                </p>
                <p className="text-xs text-gray-500">경유지</p>
              </div>
              <div className="bg-white rounded-xl p-4 shadow-sm text-center">
                <p className="text-2xl font-bold text-naruu-700">
                  {route.total_distance_km || "-"} km
                </p>
                <p className="text-xs text-gray-500">총 거리</p>
              </div>
              <div className="bg-white rounded-xl p-4 shadow-sm text-center">
                <p className="text-2xl font-bold text-violet-700">
                  {formatDuration(route.total_duration_minutes)}
                </p>
                <p className="text-xs text-gray-500">총 소요시간 (체류 포함)</p>
              </div>
            </div>
          )}
        </div>

        {/* Waypoint Timeline */}
        <div className="lg:col-span-1">
          <div className="bg-white rounded-xl p-6 shadow-sm">
            <h3 className="font-semibold text-gray-700 mb-4">코스 일정</h3>

            <div className="space-y-0">
              {sortedWaypoints.map((wp, i) => (
                <div key={i} className="relative pl-8 pb-6 last:pb-0">
                  {/* Timeline line */}
                  {i < sortedWaypoints.length - 1 && (
                    <div className="absolute left-3 top-6 bottom-0 w-0.5 bg-naruu-200" />
                  )}
                  {/* Timeline dot */}
                  <div className="absolute left-0 top-0 w-6 h-6 bg-naruu-600 text-white rounded-full flex items-center justify-center text-xs font-bold">
                    {wp.order}
                  </div>

                  <div>
                    <p className="font-medium text-gray-800">{wp.name_ko}</p>
                    <p className="text-xs text-gray-500">{wp.name_ja}</p>
                    <div className="flex gap-2 mt-1">
                      <span className="px-2 py-0.5 bg-gray-100 text-gray-600 rounded text-xs">
                        {CATEGORY_LABELS[wp.category] || wp.category}
                      </span>
                      <span className="text-xs text-gray-400">
                        체류 {wp.stay_minutes}분
                      </span>
                    </div>
                    {wp.notes && (
                      <p className="text-xs text-gray-500 mt-1">{wp.notes}</p>
                    )}

                    {/* Travel time to next */}
                    {i < sortedWaypoints.length - 1 &&
                      route.route_data?.legs?.[i] && (
                        <div className="mt-2 text-xs text-blue-600 bg-blue-50 px-2 py-1 rounded inline-block">
                          → {route.route_data.legs[i].distance_km} km /{" "}
                          {route.route_data.legs[i].duration_minutes}분
                        </div>
                      )}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Tags */}
          {route.tags && route.tags.length > 0 && (
            <div className="mt-4 bg-white rounded-xl p-4 shadow-sm">
              <h3 className="font-semibold text-gray-700 text-sm mb-2">태그</h3>
              <div className="flex flex-wrap gap-1">
                {route.tags.map((tag) => (
                  <span
                    key={tag}
                    className="px-2 py-0.5 bg-naruu-50 text-naruu-700 rounded text-xs"
                  >
                    {tag}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </AppShell>
  );
}
