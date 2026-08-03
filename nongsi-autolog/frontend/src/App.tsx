import { useEffect, useMemo, useRef, useState } from "react";
import type { CSSProperties } from "react";
import { MapContainer, Polyline, TileLayer, useMap } from "react-leaflet";

import type {
  Catalog,
  DeviceSnapshot,
  LocationPoint,
  StreamStatus,
  WorkEvent,
  WorkSession,
  WorkState,
} from "./types";
import { useLiveDevice } from "./useLiveDevice";

const DEVICE_ID = "sprayer-001";
const DEMO_CENTER: [number, number] = [33.25235, 126.50921];
const DEMO_ROUTE: Array<[number, number]> = [
  [33.25235, 126.50921],
  [33.25243, 126.50931],
  [33.25252, 126.50944],
  [33.25261, 126.50955],
  [33.25269, 126.50966],
  [33.25277, 126.50954],
  [33.25268, 126.50942],
  [33.25259, 126.50929],
  [33.25249, 126.50917],
  [33.2524, 126.50908],
];

const STATE_LABEL: Record<WorkState, string> = {
  OFFLINE: "오프라인",
  IDLE: "대기",
  MOVING: "이동 중",
  SPRAYING: "정상 분사",
  PRESSURE_FAULT: "압력 이상",
  SENSOR_FAULT: "센서 이상",
  SESSION_FINISHED: "작업 종료",
};

const STATE_COLOR: Record<WorkState, string> = {
  OFFLINE: "#68756f",
  IDLE: "#4384a4",
  MOVING: "#d79a2b",
  SPRAYING: "#31845b",
  PRESSURE_FAULT: "#cf5645",
  SENSOR_FAULT: "#9c4138",
  SESSION_FINISHED: "#68756f",
};

type Screen = "dashboard" | "start" | "live" | "result";
type StartForm = {
  farm_id: string;
  parcel_id: string;
  device_id: string;
  crop: string;
  input_material_id: string;
  product_name: string;
  dilution_ratio: string;
  nozzle_id: string;
  location_mode: "demo" | "browser";
};

async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(path, {
    ...init,
    headers: init?.body
      ? { "Content-Type": "application/json", ...init.headers }
      : init?.headers,
  });
  if (!response.ok) {
    const body = (await response.json().catch(() => null)) as { detail?: string } | null;
    throw new Error(body?.detail ?? `요청 실패 (${response.status})`);
  }
  return (await response.json()) as T;
}

function StreamBadge({ status }: { status: StreamStatus }) {
  const text = {
    connecting: "연결 중",
    connected: "실시간 연결",
    reconnecting: "재연결 중",
  }[status];
  return <span className={`stream-badge ${status}`}><i />{text}</span>;
}

function Recenter({ center }: { center: [number, number] }) {
  const map = useMap();
  useEffect(() => {
    map.setView(center, map.getZoom(), { animate: true });
  }, [center, map]);
  return null;
}

function RouteMap({ points }: { points: LocationPoint[] }) {
  const center = useMemo<[number, number]>(() => {
    const last = points.at(-1);
    return last ? [last.latitude, last.longitude] : DEMO_CENTER;
  }, [points]);
  return (
    <MapContainer center={center} zoom={18} scrollWheelZoom className="route-map">
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      <Recenter center={center} />
      {points.slice(1).map((point, index) => (
        <Polyline
          key={`${point.sequence}-${index}`}
          positions={[
            [points[index].latitude, points[index].longitude],
            [point.latitude, point.longitude],
          ]}
          pathOptions={{ color: STATE_COLOR[point.state], weight: 7, opacity: 0.92 }}
        />
      ))}
    </MapContainer>
  );
}

function SnapshotCards({ snapshot }: { snapshot: DeviceSnapshot | null }) {
  if (!snapshot) {
    return <div className="waiting-card"><span className="loader" />장치 데이터를 기다리는 중입니다.</div>;
  }
  const pressure = snapshot.features.pressure_bar_avg ?? snapshot.reading.pressure_bar;
  const current = snapshot.features.pump_current_a_avg ?? snapshot.reading.pump_current_a;
  const vibration = snapshot.features.vibration_rms_avg ?? snapshot.reading.imu_rms;
  return (
    <div className="snapshot-grid">
      <article className="state-card" style={{ "--state-color": STATE_COLOR[snapshot.state] } as CSSProperties}>
        <p>현재 작업 상태</p>
        <h3>{STATE_LABEL[snapshot.state]}</h3>
        <span>{snapshot.state}</span>
        <small>{snapshot.reason}</small>
      </article>
      <article className="number-card"><p>펌프 전류</p><strong>{current?.toFixed(2) ?? "-"}<em>A</em></strong></article>
      <article className="number-card"><p>배관 압력</p><strong>{pressure?.toFixed(2) ?? "-"}<em>bar</em></strong></article>
      <article className="number-card"><p>진동 RMS</p><strong>{vibration?.toFixed(3) ?? "-"}<em>g</em></strong></article>
    </div>
  );
}

function useElapsedSeconds(startTime: string) {
  const [now, setNow] = useState(Date.now());
  useEffect(() => {
    const timer = window.setInterval(() => setNow(Date.now()), 1000);
    return () => window.clearInterval(timer);
  }, []);
  return Math.max(0, Math.floor((now - new Date(startTime).getTime()) / 1000));
}

function Dashboard({ snapshot, onStart }: { snapshot: DeviceSnapshot | null; onStart: () => void }) {
  return (
    <>
      <section className="page-intro">
        <div><p className="eyebrow">FIELD OPERATION · JEJU</p><h2>방제 작업을<br /><em>기록하고 설명합니다.</em></h2></div>
        <div className="intro-action"><p>센서 원본과 규칙 판정, 위치, 기상 위험을 하나의 작업 이벤트로 묶습니다.</p><button className="primary" onClick={onStart}>새 작업 시작</button></div>
      </section>
      <SnapshotCards snapshot={snapshot} />
      <section className="info-strip">
        <div><b>01</b><span>센서 상태 판정</span></div>
        <div><b>02</b><span>GNSS 경로 기록</span></div>
        <div><b>03</b><span>살포량 추정</span></div>
        <div><b>04</b><span>기상 위험 설명</span></div>
      </section>
    </>
  );
}

function StartScreen({ catalog, onStart, busy }: { catalog: Catalog; onStart: (form: StartForm) => void; busy: boolean }) {
  const [form, setForm] = useState<StartForm>({
    farm_id: catalog.farms[0]?.farm_id ?? "",
    parcel_id: catalog.parcels[0]?.parcel_id ?? "",
    device_id: catalog.devices[0]?.device_id ?? DEVICE_ID,
    crop: catalog.parcels[0]?.crop ?? "open_field_citrus",
    input_material_id: catalog.input_materials[0]?.material_id ?? "",
    product_name: catalog.input_materials[0]?.name ?? "물(안전 시연용)",
    dilution_ratio: "1",
    nozzle_id: catalog.nozzles[0]?.nozzle_id ?? "nozzle-A",
    location_mode: "demo",
  });
  const change = (key: keyof StartForm, value: string) => setForm((current) => ({ ...current, [key]: value }));
  return (
    <section className="form-layout">
      <div className="form-copy"><p className="eyebrow">NEW OPERATION</p><h2>작업 조건을<br />먼저 남겨주세요.</h2><p>실증 기본값은 저전압 물 펌프입니다. 실제 농약 사용을 전제로 하지 않습니다.</p></div>
      <form className="start-form" onSubmit={(event) => { event.preventDefault(); onStart(form); }}>
        <label>농장<select value={form.farm_id} onChange={(event) => change("farm_id", event.target.value)}>{catalog.farms.map((item) => <option key={item.farm_id} value={item.farm_id}>{item.name}</option>)}</select></label>
        <label>필지<select value={form.parcel_id} onChange={(event) => change("parcel_id", event.target.value)}>{catalog.parcels.filter((item) => item.farm_id === form.farm_id).map((item) => <option key={item.parcel_id} value={item.parcel_id}>{item.name}</option>)}</select></label>
        <label>장치<select value={form.device_id} onChange={(event) => change("device_id", event.target.value)}>{catalog.devices.map((item) => <option key={item.device_id} value={item.device_id}>{item.name}</option>)}</select></label>
        <label>작물<input value={form.crop} onChange={(event) => change("crop", event.target.value)} /></label>
        <label>투입물<select value={form.input_material_id} onChange={(event) => change("input_material_id", event.target.value)}>{catalog.input_materials.map((item) => <option key={item.material_id} value={item.material_id}>{item.name}</option>)}</select></label>
        <label>희석 배수<input type="number" min="0.1" step="0.1" value={form.dilution_ratio} onChange={(event) => change("dilution_ratio", event.target.value)} /></label>
        <label>노즐<select value={form.nozzle_id} onChange={(event) => change("nozzle_id", event.target.value)}>{catalog.nozzles.map((item) => <option key={item.nozzle_id} value={item.nozzle_id}>{item.nozzle_id}</option>)}</select></label>
        <fieldset><legend>위치 기록</legend><label className="radio"><input type="radio" checked={form.location_mode === "demo"} onChange={() => change("location_mode", "demo")} />데모 경로</label><label className="radio"><input type="radio" checked={form.location_mode === "browser"} onChange={() => change("location_mode", "browser")} />브라우저 GNSS</label></fieldset>
        <button className="primary wide" disabled={busy}>{busy ? "작업을 여는 중…" : "기록 시작"}</button>
      </form>
    </section>
  );
}

function LiveScreen({ session, snapshot, onFinish, busy }: { session: WorkSession; snapshot: DeviceSnapshot | null; onFinish: () => void; busy: boolean }) {
  const elapsedSeconds = useElapsedSeconds(session.start_time);
  const sprayPointCount = session.locations.filter((point) => point.is_spraying).length;
  const provisionalLiters = sprayPointCount * 2 * 2.8 / 60;
  return (
    <>
      <section className="live-heading"><div><p className="eyebrow">RECORDING · {session.session_id}</p><h2>작업 경로 기록 중</h2></div><button className="danger" onClick={onFinish} disabled={busy}>{busy ? "결과 계산 중…" : "작업 종료"}</button></section>
      <SnapshotCards snapshot={snapshot} />
      <section className="live-facts"><div><span>경과 시간</span><b>{Math.floor(elapsedSeconds / 60)}분 {elapsedSeconds % 60}초</b></div><div><span>분사 표식</span><b>{sprayPointCount}개</b></div><div><span>실시간 임시 추정</span><b>{provisionalLiters.toFixed(2)} L</b><small>종료 후 센서 시계열로 재계산</small></div><div><span>센서 연결</span><b className={snapshot?.online ? "ok" : "warn"}>{snapshot?.online ? "ONLINE" : "OFFLINE"}</b></div></section>
      <section className="map-card"><RouteMap points={session.locations} /><div className="map-status"><strong>{session.locations.length}</strong><span>위치 포인트</span><i /> <span>{session.location_mode === "demo" ? "데모 경로" : "브라우저 GNSS"}</span></div></section>
      <div className="legend"><span><i style={{ background: STATE_COLOR.MOVING }} />이동</span><span><i style={{ background: STATE_COLOR.SPRAYING }} />분사</span><span><i style={{ background: STATE_COLOR.PRESSURE_FAULT }} />압력 이상</span></div>
    </>
  );
}

function RiskPill({ label, value }: { label: string; value: "low" | "medium" | "high" }) {
  return <div className={`risk-pill ${value}`}><span>{label}</span><b>{value.toUpperCase()}</b></div>;
}

function ResultScreen({ event, points, onConfirm }: { event: WorkEvent; points: LocationPoint[]; onConfirm: () => void }) {
  return (
    <>
      <section className="result-hero"><div><p className="eyebrow">OPERATION COMPLETE</p><h2>작업 이벤트가<br />생성되었습니다.</h2></div><div className="result-id"><span>EVENT ID</span><b>{event.event_id}</b><small>{new Date(event.end_time).toLocaleString("ko-KR")}</small></div></section>
      <section className="result-grid">
        <article><p>전체 작업</p><strong>{Math.round(event.duration_seconds)}<em>초</em></strong></article>
        <article><p>분사 판정</p><strong>{Math.round(event.spray_duration_seconds)}<em>초</em></strong></article>
        <article><p>추정 살포량</p><strong>{event.estimated_spray_liters.toFixed(2)}<em>L</em></strong></article>
        <article><p>평균 압력</p><strong>{event.pressure_summary.average_bar?.toFixed(2) ?? "-"}<em>bar</em></strong></article>
      </section>
      <section className="result-times"><div><span>작업 시작</span><b>{new Date(event.start_time).toLocaleString("ko-KR")}</b></div><i /><div><span>작업 종료</span><b>{new Date(event.end_time).toLocaleString("ko-KR")}</b></div></section>
      <section className="result-panels">
        <article className="map-card"><RouteMap points={points} /></article>
        <article className="risk-card"><p className="eyebrow">WEATHER & RISK · {event.weather_summary.simulated ? "MOCK" : event.weather_summary.provider}</p><h3>예상 강우 접근 <b>{event.weather_summary.rain_approach_minutes ?? "-"}분</b></h3><div className="risk-list"><RiskPill label="강우 노출" value={event.risk.rain_exposure} /><RiskPill label="바람 비산" value={event.risk.wind_drift} /><RiskPill label="압력 이상" value={event.risk.pressure_fault} /></div><ul>{event.risk_explanations.map((text) => <li key={text}>{text}</li>)}</ul></article>
      </section>
      <p className="estimation-note">※ {event.estimation_notice} {event.confidence_notice}</p>
      <section className="result-actions"><a className="secondary" href={`/api/sessions/${event.session_id}/export.json`}>JSON 내려받기</a><a className="secondary" href={`/api/sessions/${event.session_id}/export.csv`}>CSV 내려받기</a><button className="primary" disabled={event.farmer_confirmed} onClick={onConfirm}>{event.farmer_confirmed ? "농가 확인 완료" : "내용 확인"}</button></section>
    </>
  );
}

export default function App() {
  const { snapshot, streamStatus, error: streamError } = useLiveDevice(DEVICE_ID);
  const [screen, setScreen] = useState<Screen>("dashboard");
  const [catalog, setCatalog] = useState<Catalog | null>(null);
  const [session, setSession] = useState<WorkSession | null>(null);
  const [result, setResult] = useState<WorkEvent | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const sequenceRef = useRef(0);

  useEffect(() => {
    api<Catalog>("/api/catalog").then(setCatalog).catch((reason: Error) => setError(reason.message));
  }, []);

  const activeSessionId = session?.status === "ACTIVE" ? session.session_id : null;
  const locationMode = session?.location_mode;
  useEffect(() => {
    if (!activeSessionId || !locationMode) return;
    let stopped = false;
    let watchId: number | null = null;
    sequenceRef.current = session?.locations.length ?? 0;

    const postLocation = async (latitude: number, longitude: number, accuracy: number | null, source: "browser_gnss" | "demo_route") => {
      const sequence = sequenceRef.current++;
      try {
        await api<LocationPoint>(`/api/sessions/${activeSessionId}/locations`, {
          method: "POST",
          body: JSON.stringify({ timestamp: new Date().toISOString(), sequence, latitude, longitude, accuracy_m: accuracy, source }),
        });
        const updated = await api<WorkSession>(`/api/sessions/${activeSessionId}`);
        if (!stopped) setSession(updated);
      } catch (reason) {
        if (!stopped) setError(reason instanceof Error ? reason.message : "위치 기록 실패");
      }
    };

    let timer: number | undefined;
    if (locationMode === "demo") {
      timer = window.setInterval(() => {
        const point = DEMO_ROUTE[sequenceRef.current % DEMO_ROUTE.length];
        void postLocation(point[0], point[1], 4.5, "demo_route");
      }, 2000);
    } else if (navigator.geolocation) {
      watchId = navigator.geolocation.watchPosition(
        (position) => void postLocation(position.coords.latitude, position.coords.longitude, position.coords.accuracy, "browser_gnss"),
        (geoError) => setError(`GNSS 오류: ${geoError.message}`),
        { enableHighAccuracy: true, maximumAge: 1000, timeout: 10000 },
      );
    } else {
      setError("이 브라우저는 GNSS 위치 기록을 지원하지 않습니다.");
    }
    return () => {
      stopped = true;
      if (timer) window.clearInterval(timer);
      if (watchId != null) navigator.geolocation.clearWatch(watchId);
    };
  }, [activeSessionId, locationMode]);

  const startSession = async (form: StartForm) => {
    setBusy(true); setError(null);
    try {
      const created = await api<WorkSession>("/api/sessions", {
        method: "POST",
        body: JSON.stringify({ ...form, event_type: "spraying", dilution_ratio: Number(form.dilution_ratio), product_name: catalog?.input_materials.find((item) => item.material_id === form.input_material_id)?.name ?? form.product_name }),
      });
      sequenceRef.current = 0;
      setSession(created); setScreen("live");
    } catch (reason) { setError(reason instanceof Error ? reason.message : "작업 시작 실패"); }
    finally { setBusy(false); }
  };

  const finishSession = async () => {
    if (!session) return;
    setBusy(true); setError(null);
    try {
      const event = await api<WorkEvent>(`/api/sessions/${session.session_id}/finish`, { method: "POST", body: "{}" });
      const finished = await api<WorkSession>(`/api/sessions/${session.session_id}`);
      setSession(finished); setResult(event); setScreen("result");
    } catch (reason) { setError(reason instanceof Error ? reason.message : "작업 종료 실패"); }
    finally { setBusy(false); }
  };

  const confirmResult = async () => {
    if (!result) return;
    try {
      const confirmed = await api<WorkEvent>(`/api/events/${result.event_id}/confirm`, { method: "POST", body: JSON.stringify({ confirmed: true, note: "PWA 결과 화면에서 확인" }) });
      setResult(confirmed);
    } catch (reason) { setError(reason instanceof Error ? reason.message : "확인 저장 실패"); }
  };

  return (
    <main className="app-shell">
      <header className="topbar">
        <button className="brand" onClick={() => setScreen("dashboard")}><span className="brand-mark">N</span><span><b>농시 AutoLog</b><small>노지 감귤 방제 작업 검증</small></span></button>
        <div className="topbar-meta"><span className="demo-chip">WATER-ONLY DEMO</span><StreamBadge status={streamStatus} /></div>
      </header>
      {(error || streamError) && <div className="notice"><b>!</b>{error ?? streamError}<button onClick={() => setError(null)}>×</button></div>}
      {screen === "dashboard" && <Dashboard snapshot={snapshot} onStart={() => setScreen("start")} />}
      {screen === "start" && catalog && <StartScreen catalog={catalog} onStart={startSession} busy={busy} />}
      {screen === "start" && !catalog && <div className="waiting-card"><span className="loader" />기본 정보를 불러오는 중입니다.</div>}
      {screen === "live" && session && <LiveScreen session={session} snapshot={snapshot} onFinish={finishSession} busy={busy} />}
      {screen === "result" && result && <ResultScreen event={result} points={session?.locations ?? []} onConfirm={confirmResult} />}
      <footer><span>농시 AutoLog · MVP 0.3</span><span>규칙 기반 추정 결과이며 학습 AI 정확도를 주장하지 않습니다.</span></footer>
    </main>
  );
}
