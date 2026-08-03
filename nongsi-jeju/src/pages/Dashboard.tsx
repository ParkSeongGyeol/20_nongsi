import { useState } from 'react'
import { AlertTriangle, ArrowRight, BriefcaseBusiness, Clock3, CloudRainWind, MapPinned, Route, Sparkles, Users } from 'lucide-react'
import { Badge, Button, KpiCard, PageHeader, Panel, SourceFooter } from '../components'
import { farms } from '../data'
import { useRoute } from '../router'

export function Dashboard({ onGenerate }: { onGenerate: (after: () => void) => void }) {
  const { navigate } = useRoute()
  const [selected, setSelected] = useState('a')
  const selectedFarm = farms.find((farm) => farm.id === selected)!

  const generate = () => onGenerate(() => navigate('/schedule'))

  return (
    <div className="page dashboard-page">
      <PageHeader
        eyebrow="9월 9일 화요일 · 영농 브리핑"
        title="좋은 아침입니다, 김농부님"
        description="비가 오기 전 남은 작업창을 기준으로 오늘의 우선 작업을 확인하세요."
        actions={<div className="weather-chip"><CloudRainWind size={22} /><span><small>애월읍 현재</small><strong>24.8℃</strong></span><i /> <span><small>강수확률</small><strong>30%</strong></span></div>}
      />

      <div className="kpi-grid six">
        <KpiCard label="오늘 작업 후보" value="5개" note="기한 임박 2개" tone="blue" icon={<BriefcaseBusiness />} />
        <KpiCard label="완료 가능 작업" value="3개" note="현재 자원 기준" tone="green" icon={<Sparkles />} />
        <KpiCard label="작업 충돌" value="2건" note="조정이 필요해요" tone="red" icon={<AlertTriangle />} />
        <KpiCard label="사용 가능 인력" value="3명" note="외부 작업자 2명" tone="purple" icon={<Users />} />
        <KpiCard label="기상 작업창" value="3시간 40분" note="강풍 시작 전" tone="orange" icon={<Clock3 />} />
        <KpiCard label="예상 이동거리" value="18.4km" note="기존 순서 대비 -3.2km" tone="gray" icon={<Route />} />
      </div>

      <section className="hero-alert">
        <div className="alert-visual"><AlertTriangle size={27} /></div>
        <div className="alert-copy">
          <Badge tone="red">오늘의 핵심 판단</Badge>
          <h2>오늘 모든 작업을 완료할 수 없습니다.</h2>
          <p>오전 9시 이후 풍속 증가와 오후 강수가 예상됩니다. <strong>방제와 관수 작업의 우선순위를 조정</strong>해야 합니다.</p>
          <div className="weather-points"><span>09:00 풍속 <b>4.8m/s</b></span><span>강수 접근 <b>4시간 후</b></span><span>오후 강수 <b>8~15mm</b></span></div>
        </div>
        <Button onClick={generate} icon={<Sparkles size={18} />}>AI 일정 생성 <ArrowRight size={18} /></Button>
      </section>

      <div className="dashboard-grid">
        <Panel title="농지별 작업 우선순위" description="카드를 선택하면 지도와 작업 조건을 함께 확인할 수 있습니다." action={<span className="updated-dot"><i /> 07:12 분석 완료</span>}>
          <div className="farm-card-list">
            {farms.map((farm) => (
              <button className={`farm-card ${selected === farm.id ? 'selected' : ''}`} key={farm.id} onClick={() => setSelected(farm.id)}>
                <div className="farm-score" style={{ '--score-color': farm.color } as React.CSSProperties}><strong>{farm.score}</strong><small>우선순위</small></div>
                <div className="farm-main">
                  <div className="farm-title"><span style={{ background: farm.color }} /> <h3>{farm.name}</h3><Badge tone={farm.risk === '높음' ? 'red' : farm.risk === '보통' ? 'orange' : 'green'}>지연 위험 {farm.risk}</Badge></div>
                  <p>{farm.crop} · {farm.area} · {farm.location}</p>
                  <strong className="task-name">{farm.task}</strong>
                  <div className="farm-meta"><span><Clock3 size={14} /> {farm.duration}</span><span><Users size={14} /> {farm.people}명</span><span>{farm.equipment}</span></div>
                </div>
                <div className="fit-meter"><span>기상 적합도 <b>{farm.weatherFit}%</b></span><div><i style={{ width: `${farm.weatherFit}%`, background: farm.weatherFit > 80 ? '#2f9d72' : farm.weatherFit > 65 ? '#e99b32' : '#e45846' }} /></div><small>{farm.deadline} 마감</small></div>
                <Chevron />
              </button>
            ))}
          </div>
        </Panel>

        <Panel title="농지 위치와 이동 동선" description="애월읍 농지 4곳 · 총 예상 이동 18.4km" action={<Badge tone="blue">추천 동선</Badge>}>
          <div className="mock-map">
            <div className="map-sea">JEJU SEA</div>
            <div className="map-road road-one" /><div className="map-road road-two" /><div className="map-road road-three" />
            <span className="map-label label-one">애월해안로</span><span className="map-label label-two">일주서로</span>
            <svg className="route-line" viewBox="0 0 500 320" preserveAspectRatio="none"><path d="M115 90 C170 60, 230 105, 268 150 S355 212, 395 260" /></svg>
            {farms.map((farm, index) => <button key={farm.id} className={`map-pin pin-${index + 1} ${selected === farm.id ? 'active' : ''}`} onClick={() => setSelected(farm.id)} style={{ '--pin-color': farm.color } as React.CSSProperties}><span>{index + 1}</span><b>{farm.name}</b><small>{farm.location.replace('애월읍 ', '')}</small></button>)}
            <div className="map-legend"><span><i className="line" /> 추천 이동경로</span><span><i className="danger" /> 기상 위험 높음</span></div>
          </div>
          <div className="map-selection">
            <div><span className="selection-mark" style={{ background: selectedFarm.color }}><MapPinned size={19} /></span><span><small>선택 농지</small><strong>{selectedFarm.name} · {selectedFarm.crop}</strong></span></div>
            <div><small>우선 작업</small><strong>{selectedFarm.task}</strong></div>
            <div><small>작업 기한</small><strong>{selectedFarm.deadline}</strong></div>
            <div><small>예상 소요</small><strong>{selectedFarm.duration}</strong></div>
          </div>
        </Panel>
      </div>
      <SourceFooter />
    </div>
  )
}

function Chevron() {
  return <span className="card-chevron">›</span>
}
