import { useMemo, useState } from 'react'
import { AlertTriangle, ArrowRight, BarChart3, CalendarCheck2, Check, Clock3, CloudLightning, CloudRain, GitCompareArrows, Info, MapPinned, RotateCw, Sparkles, Users, Wind } from 'lucide-react'
import { Badge, Button, Modal, PageHeader, Panel, SourceFooter } from '../components'
import { initialSchedule, priorityFactors, revisedSchedule, type ScheduleItem } from '../data'
import { useRoute } from '../router'

type Props = {
  weatherChanged: boolean
  recalculated: boolean
  confirmed: boolean
  onWeatherChange: () => void
  onRecalculate: (after: () => void) => void
  onConfirm: () => void
  notify: (message: string) => void
}

export function Schedule({ weatherChanged, recalculated, confirmed, onWeatherChange, onRecalculate, onConfirm, notify }: Props) {
  const { navigate } = useRoute()
  const schedule = recalculated ? revisedSchedule : initialSchedule
  const [selectedId, setSelectedId] = useState('a')
  const [weatherModal, setWeatherModal] = useState(false)
  const [showCompare, setShowCompare] = useState(recalculated)
  const selected = useMemo(() => schedule.find((item) => item.id === selectedId && item.type === 'task') || schedule.find((item) => item.type === 'task')!, [schedule, selectedId])

  const simulateWeather = () => {
    onWeatherChange()
    setWeatherModal(true)
  }
  const recalculate = () => {
    setWeatherModal(false)
    onRecalculate(() => {
      setShowCompare(true)
      setSelectedId('a')
    })
  }

  return (
    <div className="page schedule-page">
      <PageHeader
        eyebrow={recalculated ? '기상 변화 반영 완료 · 일정 버전 2' : 'AI 추천 일정 · 일정 버전 1'}
        title={recalculated ? '기상 변화에 맞춰 일정을 다시 계산했습니다' : '오늘의 최적 작업 일정'}
        description="기상 작업창, 작업기한, 이동시간, 인력 3명과 장비 3종을 분석해 오늘의 일정을 생성했습니다."
        actions={<><Button variant="secondary" onClick={simulateWeather} icon={<CloudLightning size={18} />}>{weatherChanged ? '변경 기상 다시 보기' : '기상상황 변경 시뮬레이션'}</Button>{recalculated && <Button variant="secondary" onClick={() => setShowCompare((value) => !value)} icon={<GitCompareArrows size={18} />}>전후 일정 비교</Button>}</>}
      />

      <div className={`weather-banner ${weatherChanged ? 'weather-danger' : ''}`}>
        <div className="weather-banner-title"><span><CloudRain size={22} /></span><div><small>{weatherChanged ? '기상청 레이더 신규 관측' : '현재 기상 작업 조건'}</small><strong>{weatherChanged ? '강수 접근이 빨라졌습니다' : '오전 작업창 3시간 40분'}</strong></div></div>
        <WeatherMetric label="강수 접근" before="4시간" after="2시간 10분" changed={weatherChanged} />
        <WeatherMetric label="09시 풍속" before="4.8m/s" after="6.2m/s" changed={weatherChanged} />
        <WeatherMetric label="강수확률" before="30%" after="80%" changed={weatherChanged} />
        <WeatherMetric label="예상 강수량" before="8~15mm" after="15~25mm" changed={weatherChanged} />
        <span className="weather-source">기상청 레이더 · AWS<br />07:18 갱신</span>
      </div>

      {recalculated && showCompare && <ScheduleComparison />}

      <div className="schedule-layout">
        <Panel title={recalculated ? '변경된 작업 순서' : '추천 작업 순서'} description="작업을 선택하면 우측에서 우선순위 계산 근거를 확인할 수 있습니다." action={<Badge tone={recalculated ? 'orange' : 'blue'}>{recalculated ? '기상 변화 반영' : '예상 완료율 60%'}</Badge>}>
          <div className="timeline-head"><span>시간</span><span>작업 일정</span><span>배치 정보</span></div>
          <div className="schedule-timeline">
            {schedule.map((item, index) => (
              <ScheduleRow key={`${item.id}-${index}`} item={item} active={selected.id === item.id && item.type === 'task'} onClick={() => item.type === 'task' && setSelectedId(item.id)} last={index === schedule.length - 1} />
            ))}
          </div>
          <div className="schedule-actions">
            <Button variant="secondary" onClick={() => notify('이동거리보다 작업 완료율을 우선한 대안 일정을 준비했습니다.')} icon={<RotateCw size={17} />}>다른 일정 보기</Button>
            <div className="decision-note"><Info size={15} /><span>최종 결정은 농가 또는 운영 담당자가 수행합니다.</span></div>
            <Button onClick={onConfirm} disabled={confirmed} icon={confirmed ? <Check size={18} /> : <CalendarCheck2 size={18} />}>{confirmed ? '오늘 일정 확정됨' : '오늘 일정 확정'}</Button>
          </div>
        </Panel>

        <aside className="evidence-panel">
          <div className="evidence-title"><div><span style={{ background: selected.color }} /><div><small>{selected.farm}</small><h2>{selected.task}</h2></div></div><strong>{selected.score}<small>점</small></strong></div>
          {selected.status ? <div className="evidence-alert"><AlertTriangle size={18} /><span><strong>{selected.status}된 작업입니다.</strong>{selected.reason}</span></div> : <div className="recommendation"><Sparkles size={19} /><p>{selected.reason}</p></div>}
          <h3>우선순위 상세 근거</h3>
          <div className="factor-list">
            {priorityFactors.map((factor, index) => {
              const adjusted = selected.id === 'a' ? factor.value : Math.max(42, factor.value - (index * 6 + 5))
              return <div className="factor" key={factor.label}><div><span>{factor.label}</span><b>{index === 5 && selected.id !== 'a' ? '18분' : factor.note}</b></div><div className="factor-track"><i style={{ width: `${adjusted}%` }} /></div><strong>{adjusted}</strong></div>
            })}
          </div>
          <div className="evidence-resource"><div><Users size={17} /><span><small>작업자 배치</small><strong>{selected.workers}</strong></span></div><div><BarChart3 size={17} /><span><small>사용 장비</small><strong>{selected.equipment}</strong></span></div><div><Wind size={17} /><span><small>기상 적합도</small><strong>{selected.fit}%</strong></span></div></div>
          <Button variant="secondary" className="full-width" onClick={() => navigate('/records')}>작업 완료 기록으로 이동 <ArrowRight size={17} /></Button>
          <div className="ai-explain"><strong>농시는 이렇게 계산합니다</strong><p>작업별 긴급도와 기상 작업창, 인력·장비 가용성, 이동시간을 분석해 우선순위를 계산합니다.</p></div>
        </aside>
      </div>
      <SourceFooter />

      {weatherModal && (
        <Modal onClose={() => setWeatherModal(false)}>
          <div className="modal-weather-icon"><CloudLightning size={29} /></div>
          <Badge tone="red">기상청 데이터 변경</Badge>
          <h2>기상데이터 변경이 감지되었습니다.</h2>
          <p className="modal-lead">강수 접근시간이 단축되고 풍속이 상승했습니다. 기존 일정대로 작업할 경우 <strong>A과원 방제를 완료하지 못할 가능성</strong>이 있습니다.</p>
          <div className="modal-change-grid"><span><small>강수 접근</small><del>4시간</del><ArrowRight size={15} /><b>2시간 10분</b></span><span><small>예상 풍속</small><del>4.8m/s</del><ArrowRight size={15} /><b>6.2m/s</b></span><span><small>강수확률</small><del>30%</del><ArrowRight size={15} /><b>80%</b></span></div>
          <div className="modal-actions"><Button variant="ghost" onClick={() => setWeatherModal(false)}>기존 일정 유지</Button><Button onClick={recalculate} icon={<RotateCw size={18} />}>일정 다시 계산</Button></div>
        </Modal>
      )}
    </div>
  )
}

function WeatherMetric({ label, before, after, changed }: { label: string; before: string; after: string; changed: boolean }) {
  return <div className="weather-metric"><small>{label}</small><div>{changed && <del>{before}</del>}<strong>{changed ? after : before}</strong>{changed && <ArrowRight size={14} />}</div></div>
}

function ScheduleRow({ item, active, onClick, last }: { item: ScheduleItem; active: boolean; onClick: () => void; last: boolean }) {
  if (item.type === 'move') return <div className="move-row"><span>{item.time}</span><i><MapPinned size={14} /></i><p><strong>이동 · {item.duration}분</strong>{item.farm}</p></div>
  return (
    <button className={`schedule-row ${active ? 'active' : ''} ${item.status ? 'schedule-disabled' : ''}`} onClick={onClick}>
      <div className="schedule-time"><strong>{item.time}</strong>{item.duration > 0 && <small>{Math.floor(item.duration / 60) ? `${Math.floor(item.duration / 60)}시간 ` : ''}{item.duration % 60 ? `${item.duration % 60}분` : ''}</small>}</div>
      <div className="timeline-axis"><i style={{ background: item.color }} />{!last && <span />}</div>
      <div className="schedule-task"><div><span className="farm-dot" style={{ background: item.color }} /> <strong>{item.farm}</strong>{item.status && <Badge tone="gray">{item.status}</Badge>}</div><h3>{item.task}</h3><p>{item.reason}</p></div>
      <div className="schedule-resource"><span><Users size={15} /> {item.workers}</span><span>{item.equipment}</span><span className="score-small">우선순위 <b>{item.score}</b></span></div>
      <span className="row-arrow">›</span>
    </button>
  )
}

function ScheduleComparison() {
  const metrics = [
    ['예상 작업 완료율', '60%', '80%'],
    ['작업창 내 완료', '2개', '3개'],
    ['불필요한 관수', '1건', '0건'],
    ['예상 대기시간', '70분', '25분'],
  ]
  return (
    <section className="comparison-panel">
      <div className="comparison-head"><div><Badge tone="orange">기상청 데이터 반영</Badge><h2>변경 전·후 일정 비교</h2><p>강수 접근 1시간 50분 단축과 풍속 상승을 반영해 작업 순서가 달라졌습니다.</p></div><div className="comparison-time"><Clock3 size={17} /> 07:18 자동 재계획</div></div>
      <div className="comparison-body">
        <MiniSchedule title="변경 전" tone="before" items={[['06:40', 'A과원 방제'], ['08:40', 'B밭 관수'], ['10:20', 'C밭 정식'], ['14:00', 'D밭 확인']]} />
        <div className="compare-arrow"><ArrowRight /></div>
        <MiniSchedule title="변경 후" tone="after" items={[['06:30', 'A과원 방제 · 10분 앞당김'], ['08:30', 'C밭 정식 · 인력 재배치'], ['취소', 'B밭 관수 · 강수량 증가'], ['연기', 'D밭 확인 · 다음 날']]} />
        <div className="metric-compare-grid">{metrics.map(([label, before, after]) => <div key={label}><small>{label}</small><p><del>{before}</del><ArrowRight size={14} /><strong>{after}</strong></p></div>)}</div>
      </div>
    </section>
  )
}

function MiniSchedule({ title, tone, items }: { title: string; tone: string; items: string[][] }) {
  return <div className={`mini-schedule ${tone}`}><h3>{title}</h3>{items.map(([time, task]) => <div key={`${time}-${task}`}><span>{time}</span><strong>{task}</strong></div>)}</div>
}
