import { useState } from 'react'
import { Droplets, MapPin, Plus, Sprout, Tractor, Users, Warehouse, Wind } from 'lucide-react'
import { Badge, Button, KpiCard, PageHeader, Panel, SourceFooter } from '../components'
import { farms } from '../data'

export function FarmsPage({ notify }: { notify: (message: string) => void }) {
  const [selected, setSelected] = useState('a')
  const farm = farms.find((item) => item.id === selected)!
  return (
    <div className="page farms-page">
      <PageHeader eyebrow="완탱이 농장 · 4개 필지" title="농지 및 작물 관리" description="농지별 작물, 작업 현황과 가용 자원을 한곳에서 관리합니다." actions={<Button onClick={() => notify('새 농지 등록 양식은 데모에서 생략되었습니다.')} icon={<Plus size={18} />}>농지 등록</Button>} />
      <div className="kpi-grid four"><KpiCard label="전체 농지" value="4곳" note="총 23,500㎡" icon={<MapPin />} /><KpiCard label="재배 작물" value="4종" note="노지감귤 외 3종" tone="green" icon={<Sprout />} /><KpiCard label="가용 인력" value="3명" note="06:30~17:30" tone="purple" icon={<Users />} /><KpiCard label="보유 장비" value="3종" note="모두 사용 가능" tone="orange" icon={<Tractor />} /></div>
      <div className="farm-management-grid">
        <Panel title="등록 농지" description="작업 우선순위가 높은 순서입니다.">
          <div className="farm-table">
            {farms.map((item) => <button className={selected === item.id ? 'active' : ''} key={item.id} onClick={() => setSelected(item.id)}><i style={{ background: item.color }} /><span><strong>{item.name}</strong><small>{item.crop} · {item.area}</small></span><span><strong>{item.task}</strong><small>{item.location}</small></span><Badge tone={item.risk === '높음' ? 'red' : item.risk === '보통' ? 'orange' : 'green'}>{item.risk}</Badge><b>{item.score}</b></button>)}
          </div>
        </Panel>
        <Panel title={`${farm.name} 상세 현황`} description={`${farm.location} · 최근 관측 07:12`} action={<Badge tone="green">정상 수집</Badge>}>
          <div className="farm-detail-hero"><div><span style={{ background: farm.color }}><Sprout /></span><div><small>{farm.crop}</small><h2>{farm.area}</h2></div></div><button onClick={() => notify(`${farm.name} 위치를 지도에서 확인했습니다.`)}><MapPin size={16} /> 지도에서 보기</button></div>
          <div className="soil-grid"><div><Droplets /><span><small>토양 수분</small><strong>{farm.id === 'b' ? '18%' : '32%'}</strong></span><Badge tone={farm.id === 'b' ? 'orange' : 'green'}>{farm.id === 'b' ? '낮음' : '적정'}</Badge></div><div><Wind /><span><small>현재 풍속</small><strong>2.3m/s</strong></span><Badge tone="green">양호</Badge></div></div>
          <div className="current-task-box"><small>현재 예정 작업</small><div><span><strong>{farm.task}</strong><small>{farm.deadline} · {farm.duration}</small></span><Badge tone="blue">우선순위 {farm.score}점</Badge></div></div>
          <div className="resource-list"><h3>가용 자원</h3><div><span><Users />김농부 외 2명</span><b>3명</b></div><div><span><Tractor />{farm.equipment}</span><b>사용 가능</b></div><div><span><Warehouse />애월 공동창고</span><b>차량 8분</b></div></div>
        </Panel>
      </div>
      <SourceFooter />
    </div>
  )
}
