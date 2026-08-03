import { useState } from 'react'
import { BarChart3, BellRing, BriefcaseBusiness, Building2, CheckCircle2, CloudLightning, Download, MapPinned, Navigation, Route, Send, Sparkles, UserCheck, Users, XCircle } from 'lucide-react'
import { Bar, BarChart, CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { Badge, Button, KpiCard, PageHeader, Panel, SourceFooter } from '../components'
import { centerRequests, performanceData } from '../data'

export function CenterPage({ notify }: { notify: (message: string) => void }) {
  const [allocated, setAllocated] = useState(false)
  const [metric, setMetric] = useState<'operation' | 'efficiency'>('operation')
  const runAllocation = () => {
    setAllocated(true)
    notify('AI 추천에 따라 작업자 6명의 배치를 조정했습니다.')
  }
  const download = () => {
    const report = '농시 제주 주간 작업실적\n배치 작업 수,158건\n농가 작업 완료율,93%\n평균 대기시간,25분\n총 이동거리,412km\n'
    const url = URL.createObjectURL(new Blob([report], { type: 'text/csv;charset=utf-8' }))
    const anchor = document.createElement('a')
    anchor.href = url
    anchor.download = '농시제주_주간작업실적.csv'
    anchor.click()
    URL.revokeObjectURL(url)
    notify('주간 작업실적 파일을 내려받았습니다.')
  }
  return (
    <div className="page center-page">
      <PageHeader
        eyebrow="기관용 운영 서비스 · B2B"
        title="농촌인력중개센터 운영 대시보드"
        description="애월읍 16개 농가의 작업 요청과 28명 작업자의 배치를 기상 변화에 맞춰 관리합니다."
        actions={<div className="role-card"><span><Building2 /></span><div><small>현재 사용자 역할</small><strong>애월농협 농촌인력중개센터 관리자</strong></div></div>}
      />
      <div className="kpi-grid six center-kpis">
        <KpiCard label="오늘 작업 요청 농가" value="16곳" note="전일 대비 +3" icon={<BriefcaseBusiness />} />
        <KpiCard label="배치 가능 작업자" value="28명" note="3개 작업반" tone="purple" icon={<Users />} />
        <KpiCard label="현재 배치 완료" value={allocated ? '25명' : '22명'} note={allocated ? '배치율 89%' : '배치율 79%'} tone="green" icon={<UserCheck />} />
        <KpiCard label="미배치 요청" value={allocated ? '2건' : '4건'} note="우선 검토 필요" tone="red" icon={<BellRing />} />
        <KpiCard label="기상 변경 일정" value="6건" note="레이더 예보 반영" tone="orange" icon={<CloudLightning />} />
        <KpiCard label="예상 작업 취소" value="3건" note="관수·방제 작업" tone="gray" icon={<XCircle />} />
      </div>

      <div className="center-actions">
        <Button onClick={runAllocation} disabled={allocated} icon={allocated ? <CheckCircle2 size={18} /> : <Sparkles size={18} />}>{allocated ? '자동 배치 완료' : '자동 배치 실행'}</Button>
        <Button variant="secondary" onClick={() => notify('22명에게 오늘 일정을 일괄 전송했습니다.')} icon={<Send size={17} />}>일정 일괄 전송</Button>
        <Button variant="secondary" onClick={() => notify('기상 변경 대상 농가 6곳에 알림을 보냈습니다.')} icon={<BellRing size={17} />}>변경 농가 알림</Button>
        <Button variant="secondary" onClick={download} icon={<Download size={17} />}>작업실적 다운로드</Button>
        <span>마지막 배치 계산 07:15 · 센터 담당자 승인 필요</span>
      </div>

      <div className="center-main-grid">
        <Panel className="request-panel" title="농가별 작업 요청" description="기상 위험과 작업기한을 기준으로 정렬했습니다." action={<Badge tone="red">미배치 {allocated ? 2 : 4}건</Badge>}>
          <div className="request-table-wrap"><table className="request-table"><thead><tr><th>농가 / 작업</th><th>위치</th><th>요청 인원</th><th>작업 가능시간</th><th>기상 위험</th><th>배치 상태</th></tr></thead><tbody>{centerRequests.map((request, index) => { const status = allocated && (index === 2 || index === 3) ? '배치 완료' : request.status; return <tr key={request.farm}><td><strong>{request.farm}</strong><small>{request.task}</small></td><td>{request.location}</td><td><b>{request.people}명</b></td><td>{request.time}</td><td><Badge tone={request.risk === '높음' ? 'red' : request.risk === '보통' ? 'orange' : 'green'}>{request.risk}</Badge></td><td><Badge tone={status === '배치 완료' ? 'green' : status === '배치 중' ? 'blue' : 'red'}>{status}</Badge></td></tr>})}</tbody></table></div>
        </Panel>

        <Panel className="crew-panel" title="작업반 배치 현황" description={`${allocated ? 25 : 22}명 · 오전 3개 작업반 운행 중`} action={<span className="live-label"><i /> 실시간</span>}>
          <div className="crew-list">
            <Crew team="1반" people="3명" task="A과원 방제" route="센터 → 상귀리 → 장전리" progress={68} tone="orange" />
            <Crew team="2반" people={allocated ? '6명' : '4명'} task="C밭 양배추 정식" route="센터 → 고성리 → 광령리" progress={46} tone="blue" />
            <Crew team="3반" people="3명" task="하귀 당근 파종" route="센터 → 하귀리 → 수산리" progress={29} tone="green" />
          </div>
          <div className="center-route-map"><div className="route-node center"><Building2 /><b>센터</b></div><div className="route-node node-a"><span>1</span><b>A과원</b></div><div className="route-node node-c"><span>2</span><b>C밭</b></div><div className="route-node node-b"><span>3</span><b>하귀</b></div><svg viewBox="0 0 400 160" preserveAspectRatio="none"><path d="M200 110 C145 92 105 70 58 40" /><path d="M200 110 C220 80 270 55 320 35" /><path d="M200 110 C260 125 325 122 365 100" /></svg></div>
        </Panel>

        <section className="ai-allocation-panel">
          <div className="ai-allocation-head"><span><Sparkles /></span><div><Badge tone="purple">AI 배치 추천</Badge><h2>강풍 전 방제 작업에 1반을 우선 배치하세요.</h2></div><strong>추천 신뢰도<em>92</em></strong></div>
          <p>1반은 오전 9시 이전 방제가 필요한 A과원에 우선 배치하고, 작업 완료 후 인근 감귤 농가로 이동하는 것이 이동거리와 대기시간을 최소화합니다.</p>
          <div className="allocation-reasons"><span><Navigation />이동거리 <b>6.2km 단축</b></span><span><Users />대기 인력 <b>3명 해소</b></span><span><CloudLightning />강풍 전 방제 <b>완료 가능</b></span></div>
        </section>
      </div>

      <Panel title="주간 운영 성과" description="인력 배치 최적화 전후의 운영 지표를 확인합니다." action={<div className="segmented compact"><button className={metric === 'operation' ? 'active' : ''} onClick={() => setMetric('operation')}>완료율·작업 수</button><button className={metric === 'efficiency' ? 'active' : ''} onClick={() => setMetric('efficiency')}>대기시간</button></div>}>
        <div className="performance-wrap"><div className="chart-area">{metric === 'operation' ? <ResponsiveContainer width="100%" height="100%"><BarChart data={performanceData} margin={{ top: 8, right: 10, left: -20, bottom: 0 }}><CartesianGrid strokeDasharray="4 4" vertical={false} stroke="#e8ebf1" /><XAxis dataKey="day" tickLine={false} axisLine={false} /><YAxis tickLine={false} axisLine={false} /><Tooltip /><Legend /><Bar dataKey="completed" name="작업 완료율(%)" fill="#526cde" radius={[5, 5, 0, 0]} /><Bar dataKey="jobs" name="배치 작업 수" fill="#9caaf1" radius={[5, 5, 0, 0]} /></BarChart></ResponsiveContainer> : <ResponsiveContainer width="100%" height="100%"><LineChart data={performanceData} margin={{ top: 8, right: 15, left: -20, bottom: 0 }}><CartesianGrid strokeDasharray="4 4" vertical={false} stroke="#e8ebf1" /><XAxis dataKey="day" tickLine={false} axisLine={false} /><YAxis tickLine={false} axisLine={false} /><Tooltip /><Line type="monotone" dataKey="wait" name="평균 대기시간(분)" stroke="#e46d4f" strokeWidth={3} dot={{ r: 4, fill: '#e46d4f' }} /></LineChart></ResponsiveContainer>}</div><div className="performance-stats"><span><small>농가 작업 완료율</small><strong>93%</strong><em>+11%p</em></span><span><small>평균 작업자 대기</small><strong>25분</strong><em>-45분</em></span><span><small>기상 취소율</small><strong>8.4%</strong><em>-3.1%p</em></span><span><small>주간 이동거리</small><strong>412km</strong><em>-18%</em></span></div></div>
      </Panel>
      <SourceFooter />
    </div>
  )
}

function Crew({ team, people, task, route, progress, tone }: { team: string; people: string; task: string; route: string; progress: number; tone: string }) {
  return <div className="crew-card"><div className={`crew-number crew-${tone}`}>{team}</div><div><strong>{task}</strong><span><Users size={13} /> {people} · <Route size={13} /> {route}</span><div className="crew-progress"><i style={{ width: `${progress}%` }} /></div></div><b>{progress}%</b></div>
}
