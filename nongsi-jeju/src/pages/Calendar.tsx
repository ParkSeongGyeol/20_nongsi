import { useState } from 'react'
import { AlertTriangle, CalendarRange, ChevronLeft, ChevronRight, CloudRain, MoveLeft, MoveRight, Users } from 'lucide-react'
import { Badge, Button, PageHeader, Panel, SourceFooter } from '../components'
import { annualRows, weekDays } from '../data'

export function CalendarPage() {
  const [view, setView] = useState<'annual' | 'weekly'>('annual')
  return (
    <div className="page calendar-page">
      <PageHeader
        eyebrow="연간 계획과 당일 실행 연결"
        title="농작업 계획 캘린더"
        description="작물의 생육 주기와 기상 전망을 함께 보며 미리 인력과 장비를 준비하세요."
        actions={<div className="segmented"><button className={view === 'annual' ? 'active' : ''} onClick={() => setView('annual')}>연간 보기</button><button className={view === 'weekly' ? 'active' : ''} onClick={() => setView('weekly')}>주간 보기</button></div>}
      />

      {view === 'annual' ? <AnnualView /> : <WeeklyView />}
      <div className="planning-flow"><div><span>1</span><strong>연간 계획</strong><small>작물별 작업 중첩 사전 확인</small></div><i><ChevronRight /></i><div><span>2</span><strong>주간 조정</strong><small>기상 전망으로 날짜 이동</small></div><i><ChevronRight /></i><div><span>3</span><strong>당일 재계획</strong><small>레이더·AWS로 작업 순서 변경</small></div></div>
      <SourceFooter />
    </div>
  )
}

function AnnualView() {
  return (
    <>
      <section className="calendar-toolbar"><div><Button variant="ghost" icon={<ChevronLeft size={17} />}>2025</Button><strong>2026년 영농 계획</strong><Button variant="ghost">2027 <ChevronRight size={17} /></Button></div><span><i className="today-mark" /> 현재 9월</span></section>
      <Panel className="gantt-panel" title="작물별 주요 작업" description="완탱이 농장의 연간 작업 계획 · 4개 작물, 20개 주요 작업" action={<Badge tone="blue">기상 평년값 반영</Badge>}>
        <div className="annual-gantt">
          <div className="gantt-months"><span>작물</span>{Array.from({ length: 12 }, (_, index) => <b className={index === 8 ? 'current' : ''} key={index}>{index + 1}월</b>)}</div>
          {annualRows.map((row) => (
            <div className="gantt-row" key={row.crop}>
              <strong><i style={{ background: row.color }} />{row.crop}</strong>
              <div className="gantt-track">
                {Array.from({ length: 12 }, (_, index) => <span className={index === 8 ? 'current-column' : ''} key={index} />)}
                {row.tasks.map((task) => <div key={`${row.crop}-${task.name}`} className="gantt-task" style={{ '--start': task.start, '--span': task.span, '--task-color': row.color } as React.CSSProperties}>{task.name}</div>)}
              </div>
            </div>
          ))}
        </div>
      </Panel>
      <section className="overlap-warning"><div className="overlap-icon"><AlertTriangle /></div><div><Badge tone="orange">9월 인력 수요 집중</Badge><h2>둘째 주에 주요 작업 3개가 중첩됩니다.</h2><p>감귤 방제, 당근 파종, 양배추 정식이 같은 주에 예정되어 있습니다. <strong>외부 작업자 2~3명 사전 확보</strong>를 권장합니다.</p></div><div className="overlap-stats"><span><Users size={18} /><small>예상 필요 인력</small><strong>최대 7명/일</strong></span><span><CalendarRange size={18} /><small>집중 기간</small><strong>9월 8~12일</strong></span></div></section>
    </>
  )
}

function WeeklyView() {
  return (
    <>
      <section className="calendar-toolbar"><div><Button variant="ghost" icon={<ChevronLeft size={17} />}>이전 주</Button><strong>2026년 9월 8일 — 14일</strong><Button variant="ghost">다음 주 <ChevronRight size={17} /></Button></div><span><CloudRain size={16} /> 9일 강풍 · 10일 강수 예보</span></section>
      <Panel title="이번 주 작업 일정" description="기상 변화가 예상되는 작업은 앞당김·연기 상태를 표시합니다." action={<Badge tone="orange">2건 자동 조정</Badge>}>
        <div className="week-grid">
          {weekDays.map((day) => <div className={`week-day ${day.danger ? 'danger' : ''}`} key={day.date}><div className="week-day-head"><span><strong>{day.day}</strong><small>{day.date}</small></span><Badge tone={day.danger ? 'red' : 'gray'}>{day.weather}</Badge></div><div className="week-tasks">{day.tasks.length ? day.tasks.map((task) => <div className={`week-task task-${task.tone}`} key={task.name}><strong>{task.name}</strong><small>{task.farm}</small>{task.name.includes('앞당김') && <span><MoveLeft size={12} /> 1일 앞당김</span>}{task.name.includes('연기') && <span><MoveRight size={12} /> 1일 연기</span>}</div>) : <p>예정 작업 없음</p>}</div></div>)}
        </div>
      </Panel>
      <section className="week-insight"><span><CloudRain /></span><div><Badge tone="blue">주간 기상 조정</Badge><h2>강수 전에 방제·정식 작업을 우선 배치했습니다.</h2><p>화요일 감귤 방제는 오전으로 앞당기고, 수요일 관수는 예상 강수량을 반영해 자동 취소했습니다. 생육 확인은 목요일로 이동했습니다.</p></div><div className="adjust-summary"><span><small>앞당긴 작업</small><strong>1건</strong></span><span><small>취소·연기</small><strong>2건</strong></span></div></section>
    </>
  )
}
