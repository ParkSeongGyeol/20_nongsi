import type { CSSProperties, ReactNode } from "react";

import type { DeviceSnapshot, StreamStatus, WorkState } from "./types";
import { useLiveDevice } from "./useLiveDevice";

const DEVICE_ID = "sprayer-001";

const STATE_META: Record<
  WorkState,
  { label: string; short: string; tone: string; message: string }
> = {
  OFFLINE: {
    label: "오프라인",
    short: "연결 대기",
    tone: "slate",
    message: "장치 telemetry가 수신되지 않고 있습니다.",
  },
  IDLE: {
    label: "대기 중",
    short: "IDLE",
    tone: "blue",
    message: "펌프 전류와 진동이 모두 기준 이하입니다.",
  },
  MOVING: {
    label: "이동 중",
    short: "MOVING",
    tone: "amber",
    message: "진동은 감지되지만 분사 신호는 없습니다.",
  },
  SPRAYING: {
    label: "정상 분사",
    short: "SPRAYING",
    tone: "green",
    message: "펌프 전류와 정상 압력이 함께 감지됩니다.",
  },
  PRESSURE_FAULT: {
    label: "압력 저하",
    short: "PRESSURE FAULT",
    tone: "red",
    message: "펌프가 작동하지만 압력이 설정 기준보다 낮습니다.",
  },
  SENSOR_FAULT: {
    label: "센서 이상",
    short: "SENSOR FAULT",
    tone: "red",
    message: "필수 센서값이 없거나 유효하지 않습니다.",
  },
  SESSION_FINISHED: {
    label: "작업 종료",
    short: "FINISHED",
    tone: "slate",
    message: "작업 세션이 종료됐습니다.",
  },
};

const PIPELINE: WorkState[] = ["IDLE", "MOVING", "SPRAYING", "PRESSURE_FAULT"];

function formatValue(value: number | null | undefined, digits = 2) {
  return value == null ? "—" : value.toFixed(digits);
}

function formatTimestamp(value?: string) {
  if (!value) return "수신 대기";
  return new Intl.DateTimeFormat("ko-KR", {
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    hour12: false,
  }).format(new Date(value));
}

function StreamBadge({ status }: { status: StreamStatus }) {
  const text = {
    connecting: "연결 중",
    connected: "실시간 연결",
    reconnecting: "재연결 중",
  }[status];
  return (
    <span className={`stream-badge ${status}`}>
      <i />
      {text}
    </span>
  );
}

function MetricCard({
  eyebrow,
  value,
  unit,
  note,
  progress,
  children,
}: {
  eyebrow: string;
  value: string;
  unit: string;
  note: string;
  progress: number;
  children: ReactNode;
}) {
  const width = `${Math.min(100, Math.max(0, progress))}%`;
  return (
    <article className="metric-card">
      <div className="metric-icon">{children}</div>
      <p className="eyebrow">{eyebrow}</p>
      <p className="metric-value">
        {value} <span>{unit}</span>
      </p>
      <div className="meter">
        <span style={{ width } as CSSProperties} />
      </div>
      <p className="metric-note">{note}</p>
    </article>
  );
}

function Dashboard({ snapshot }: { snapshot: DeviceSnapshot }) {
  const reading = snapshot.reading;
  const state = STATE_META[snapshot.state];
  const pressure = snapshot.features.pressure_bar_avg ?? reading.pressure_bar;
  const current = snapshot.features.pump_current_a_avg ?? reading.pump_current_a;
  const vibration = snapshot.features.vibration_rms_avg ?? reading.imu_rms;

  return (
    <>
      <section className="hero-grid">
        <article className={`state-panel tone-${state.tone}`}>
          <div className="panel-kicker">
            <span>현재 작업 상태</span>
            <span className="rule-chip">RULE BASED · v{snapshot.state_version}</span>
          </div>
          <div className="state-main">
            <div className="state-pulse"><span /></div>
            <div>
              <p className="state-code">{state.short}</p>
              <h2>{state.label}</h2>
            </div>
          </div>
          <p className="state-message">{state.message}</p>
          <p className="state-reason">판정 근거 · {snapshot.reason}</p>
          <div className="confidence-row">
            <span>규칙 판정 신뢰 지표</span>
            <strong>{Math.round(snapshot.confidence * 100)}%</strong>
          </div>
          <div className="confidence-track">
            <span style={{ width: `${snapshot.confidence * 100}%` }} />
          </div>
        </article>

        <article className="device-panel">
          <div className="device-heading">
            <div>
              <p className="eyebrow">연결 장치</p>
              <h2>{snapshot.device_id}</h2>
            </div>
            <span className={`online-pill ${snapshot.online ? "online" : "offline"}`}>
              {snapshot.online ? "ONLINE" : "OFFLINE"}
            </span>
          </div>
          <dl className="device-facts">
            <div><dt>마지막 수신</dt><dd>{formatTimestamp(reading.received_at)}</dd></div>
            <div><dt>Sequence</dt><dd>{reading.sequence}</dd></div>
            <div><dt>배터리</dt><dd>{formatValue(reading.battery_percent, 0)}%</dd></div>
            <div><dt>신호 세기</dt><dd>{formatValue(reading.signal_rssi, 0)} dBm</dd></div>
          </dl>
          <p className="quality-line">
            <span>데이터 품질</span>
            <strong>{reading.quality_flag.toUpperCase()}</strong>
          </p>
        </article>
      </section>

      <section className="metrics-grid" aria-label="실시간 센서값">
        <MetricCard
          eyebrow="펌프 전류"
          value={formatValue(current)}
          unit="A"
          note="이동평균 · 분사 판정 근거"
          progress={((current ?? 0) / 4) * 100}
        ><span>⚡</span></MetricCard>
        <MetricCard
          eyebrow="배관 압력"
          value={formatValue(pressure)}
          unit="bar"
          note="보정 전 모의 센서값"
          progress={((pressure ?? 0) / 10) * 100}
        ><span>◉</span></MetricCard>
        <MetricCard
          eyebrow="진동 RMS"
          value={formatValue(vibration, 3)}
          unit="g"
          note="3개 표본 이동평균"
          progress={((vibration ?? 0) / 0.8) * 100}
        ><span>〰</span></MetricCard>
      </section>

      <section className="timeline-card">
        <div className="section-heading">
          <div>
            <p className="eyebrow">상태 판정 흐름</p>
            <h2>장비 작동 구간</h2>
          </div>
          <p>히스테리시스 · 최소 지속시간 적용</p>
        </div>
        <div className="state-pipeline">
          {PIPELINE.map((item, index) => {
            const itemMeta = STATE_META[item];
            const active = item === snapshot.state;
            return (
              <div className="pipeline-group" key={item}>
                <div className={`pipeline-node ${active ? "active" : ""}`}>
                  <span>{String(index + 1).padStart(2, "0")}</span>
                  <div><strong>{itemMeta.label}</strong><small>{itemMeta.short}</small></div>
                </div>
                {index < PIPELINE.length - 1 && <i className="pipeline-line" />}
              </div>
            );
          })}
        </div>
      </section>
    </>
  );
}

export default function App() {
  const { snapshot, streamStatus, error } = useLiveDevice(DEVICE_ID);

  return (
    <main className="app-shell">
      <header className="topbar">
        <div className="brand">
          <div className="brand-mark"><span>농</span></div>
          <div><h1>농시 <b>AutoLog</b></h1><p>노지감귤 방제 작업 검증</p></div>
        </div>
        <div className="topbar-meta">
          <span className="demo-chip">WATER-ONLY DEMO</span>
          <StreamBadge status={streamStatus} />
        </div>
      </header>

      <section className="page-intro">
        <div>
          <p className="eyebrow">LIVE OPERATION · JEJU</p>
          <h2>방제기 상태를<br /><em>기록하고 증명합니다.</em></h2>
        </div>
        <p className="intro-copy">
          센서 원본과 규칙 기반 판정 결과를 분리 보관합니다.<br />
          현재 화면은 실제 농약이 아닌 물 펌프 시연용 모의 데이터입니다.
        </p>
      </section>

      {error && <div className="notice"><span>!</span>{error}</div>}
      {snapshot ? (
        <Dashboard snapshot={snapshot} />
      ) : (
        <section className="empty-state">
          <div className="loader" />
          <h2>센서 데이터를 기다리고 있습니다</h2>
          <p>시뮬레이터가 시작되면 이 화면이 자동으로 갱신됩니다.</p>
        </section>
      )}

      <footer>
        <span>농시 AutoLog · MVP 0.2</span>
        <span>규칙 기반 기준모델 — 학습 AI 정확도 주장이 아닙니다.</span>
      </footer>
    </main>
  );
}
