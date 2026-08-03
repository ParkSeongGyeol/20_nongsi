import { useState } from 'react'
import { CalendarCheck2, Check, CheckCircle2, Clock3, FileText, Mic, Mic2, Sparkles, Tractor, Users, WandSparkles } from 'lucide-react'
import { Badge, Button, KpiCard, Modal, PageHeader, Panel, SourceFooter } from '../components'

export function RecordsPage({ completed, onComplete, notify }: { completed: boolean; onComplete: () => void; notify: (message: string) => void }) {
  const [modal, setModal] = useState(false)
  const [listening, setListening] = useState(false)
  const [structured, setStructured] = useState(false)

  const simulateVoice = () => {
    setListening(true)
    setStructured(false)
    window.setTimeout(() => {
      setListening(false)
      setStructured(true)
    }, 1400)
  }
  const save = () => {
    onComplete()
    setModal(false)
  }

  return (
    <div className="page records-page">
      <PageHeader eyebrow="영농기록 자동화" title="작업 완료 및 기록" description="추천 일정의 실행 결과를 간편하게 남기고 다음 일정 계산에 반영하세요." actions={<Button onClick={() => setModal(true)} disabled={completed} icon={completed ? <Check size={18} /> : <CheckCircle2 size={18} />}>{completed ? 'A과원 기록 완료' : 'A과원 작업 완료 처리'}</Button>} />
      <div className="kpi-grid four"><KpiCard label="오늘 완료 작업" value={completed ? '3개' : '2개'} note="목표 3개" tone="green" icon={<CheckCircle2 />} /><KpiCard label="누적 작업시간" value={completed ? '5시간 18분' : '3시간 50분'} note="인력 합산 12.4시간" icon={<Clock3 />} /><KpiCard label="추천 일정 사용" value="92%" note="이번 달 평균" tone="purple" icon={<Sparkles />} /><KpiCard label="작성된 영농기록" value={completed ? '48건' : '47건'} note="9월 누적" tone="orange" icon={<FileText />} /></div>

      <div className="records-layout">
        <Panel title="오늘의 작업 진행" description="확정된 일정의 진행 상태입니다." action={<Badge tone="blue">2026. 9. 9</Badge>}>
          <div className="today-progress">
            <RecordTask time="06:30~08:10" farm="A과원" task="병해충 방제" people="3명" equipment="분무기" status={completed ? '완료' : '진행 대기'} onClick={() => !completed && setModal(true)} featured />
            <RecordTask time="08:30~11:00" farm="C밭" task="양배추 정식" people="3명" equipment="운반차" status="완료" />
            <RecordTask time="자동 취소" farm="B밭" task="파종 후 관수" people="-" equipment="관수장비" status="취소" />
            <RecordTask time="다음 날" farm="D밭" task="생육 확인" people="1명" equipment="없음" status="연기" />
          </div>
        </Panel>
        <Panel title="최근 영농기록" description="음성 입력과 수기 입력을 구조화한 기록입니다." action={<button className="text-button" onClick={() => notify('전체 영농기록 47건을 불러왔습니다.')}>전체 기록 보기</button>}>
          <div className="record-history">
            {completed && <HistoryItem date="오늘 08:10" farm="A과원" task="병해충 방제" meta="1시간 28분 · 3명 · 분무기" note="풍속 상승으로 작업 조기 종료" highlighted />}
            <HistoryItem date="오늘 11:03" farm="C밭" task="양배추 정식" meta="2시간 27분 · 3명 · 운반차" note="활착 상태 양호, 2일 후 관수 확인" />
            <HistoryItem date="어제 16:20" farm="D밭" task="생육 확인" meta="38분 · 1명" note="잎색 정상, 병해충 흔적 없음" />
            <HistoryItem date="9월 7일" farm="A과원" task="낙과 정리" meta="1시간 05분 · 2명 · 운반차" note="동측 구역 집중 정리" />
            <HistoryItem date="9월 6일" farm="B밭" task="토양 수분 확인" meta="24분 · 1명" note="수분 18%, 관수 검토 필요" />
          </div>
        </Panel>
      </div>

      <section className="record-learning"><span><WandSparkles /></span><div><Badge tone="purple">다음 추천에 반영</Badge><h2>실제 작업시간이 쌓일수록 일정의 현실성이 높아집니다.</h2><p>완료 기록의 실제 소요시간과 투입 인원을 같은 작업의 다음 추천 일정 계산에 반영합니다.</p></div><div><small>최근 30일 시간 보정</small><strong>-12분/작업</strong><em>계획 대비 오차 감소</em></div></section>
      <SourceFooter />

      {modal && (
        <Modal onClose={() => setModal(false)} wide>
          <div className="record-modal-head"><div className="modal-record-icon"><CalendarCheck2 /></div><div><Badge tone="green">작업 완료 기록</Badge><h2>A과원 병해충 방제</h2><p>실행 결과를 확인하고 영농기록으로 저장하세요.</p></div></div>
          <div className="record-form-grid">
            <label><span>실제 시작시간</span><input defaultValue="06:42" type="time" /></label>
            <label><span>실제 종료시간</span><input defaultValue="08:10" type="time" /></label>
            <label><span>참여 인원</span><select defaultValue="3"><option value="3">3명</option><option value="2">2명</option><option value="1">1명</option></select></label>
            <label><span>사용 장비</span><select defaultValue="sprayer"><option value="sprayer">분무기 1대</option><option value="none">사용 안 함</option></select></label>
            <label><span>작업 결과</span><select defaultValue="partial"><option value="done">계획대로 완료</option><option value="partial">조기 종료·핵심 구역 완료</option><option value="issue">문제 발생</option></select></label>
            <label><span>추천 일정 사용 여부</span><select defaultValue="yes"><option value="yes">추천 순서대로 작업</option><option value="adjust">일부 조정</option><option value="no">사용 안 함</option></select></label>
          </div>
          <div className={`voice-box ${listening ? 'listening' : ''}`}>
            <div className="voice-title"><div><Mic2 size={18} /><strong>말로 작업 기록하기</strong><Badge tone="blue">시뮬레이션</Badge></div><Button variant={listening ? 'danger' : 'secondary'} onClick={simulateVoice} disabled={listening} icon={<Mic size={17} />}>{listening ? '듣고 있어요…' : '음성 입력 시작'}</Button></div>
            <blockquote>{listening ? '음성을 인식하고 있습니다…' : '“A과원 방제 끝났고 작업자 세 명이 한 시간 반 걸렸어. 바람 때문에 조금 일찍 끝냈어.”'}</blockquote>
            {structured && <div className="structured-result"><div><WandSparkles /><span><strong>말씀하신 내용을 정리했습니다.</strong><small>저장 전에 내용을 확인하세요.</small></span></div><ul><li><span>작업</span><b>A과원 병해충 방제</b></li><li><span>실제 소요시간</span><b>1시간 28분</b></li><li><span>참여 인원</span><b>3명</b></li><li><span>특이사항</span><b>풍속 상승으로 작업 조기 종료</b></li><li><span>다음 추천 반영</span><b>실제 작업시간 보정</b></li></ul></div>}
          </div>
          <div className="problem-check"><span>문제가 발생했나요?</span><label><input type="radio" name="problem" defaultChecked /> 아니요</label><label><input type="radio" name="problem" /> 예, 별도 확인 필요</label></div>
          <div className="modal-actions"><Button variant="ghost" onClick={() => setModal(false)}>취소</Button><Button onClick={save} icon={<CheckCircle2 size={18} />}>완료 기록 저장</Button></div>
        </Modal>
      )}
    </div>
  )
}

function RecordTask({ time, farm, task, people, equipment, status, featured, onClick }: { time: string; farm: string; task: string; people: string; equipment: string; status: string; featured?: boolean; onClick?: () => void }) {
  const tone = status === '완료' ? 'green' : status === '진행 대기' ? 'blue' : 'gray'
  return <button className={`record-task ${featured ? 'featured' : ''}`} onClick={onClick} disabled={!onClick}><span className="record-status-dot"><i /></span><div className="record-time"><strong>{time}</strong><Badge tone={tone}>{status}</Badge></div><div><small>{farm}</small><strong>{task}</strong></div><div><span><Users size={14} /> {people}</span><span><Tractor size={14} /> {equipment}</span></div>{onClick && <em>완료 처리 ›</em>}</button>
}

function HistoryItem({ date, farm, task, meta, note, highlighted }: { date: string; farm: string; task: string; meta: string; note: string; highlighted?: boolean }) {
  return <div className={`history-item ${highlighted ? 'highlighted' : ''}`}><span className="history-check"><Check size={15} /></span><div><div><small>{date} · {farm}</small>{highlighted && <Badge tone="green">방금 저장</Badge>}</div><strong>{task}</strong><p>{meta}</p><em>{note}</em></div></div>
}
