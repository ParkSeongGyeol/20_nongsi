import { useEffect, useState } from "react";

import type { DeviceSnapshot, StreamStatus } from "./types";

export function useLiveDevice(deviceId: string) {
  const [snapshot, setSnapshot] = useState<DeviceSnapshot | null>(null);
  const [streamStatus, setStreamStatus] =
    useState<StreamStatus>("connecting");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;

    fetch(`/api/devices/${encodeURIComponent(deviceId)}/snapshot`)
      .then(async (response) => {
        if (response.status === 404) return null;
        if (!response.ok) throw new Error(`초기 데이터 요청 실패 (${response.status})`);
        return (await response.json()) as DeviceSnapshot;
      })
      .then((data) => {
        if (active && data) setSnapshot(data);
      })
      .catch((reason: unknown) => {
        if (active) {
          setError(reason instanceof Error ? reason.message : "초기 데이터 요청 실패");
        }
      });

    const source = new EventSource(
      `/api/devices/${encodeURIComponent(deviceId)}/live`,
    );
    source.onopen = () => {
      if (!active) return;
      setStreamStatus("connected");
      setError(null);
    };
    source.addEventListener("telemetry", (event) => {
      if (!active) return;
      try {
        setSnapshot(JSON.parse(event.data) as DeviceSnapshot);
        setError(null);
      } catch {
        setError("실시간 데이터 형식을 해석하지 못했습니다.");
      }
    });
    source.onerror = () => {
      if (!active) return;
      setStreamStatus("reconnecting");
      setError("실시간 연결을 복구하는 중입니다.");
    };

    return () => {
      active = false;
      source.close();
    };
  }, [deviceId]);

  return { snapshot, streamStatus, error };
}
