export type Risk = '높음' | '보통' | '낮음'

export type Farm = {
  id: string
  name: string
  crop: string
  area: string
  location: string
  task: string
  deadline: string
  duration: string
  people: number
  equipment: string
  weatherFit: number
  risk: Risk
  score: number
  color: string
}

export const farms: Farm[] = [
  { id: 'a', name: 'A과원', crop: '노지감귤', area: '8,200㎡', location: '애월읍 상귀리', task: '병해충 방제', deadline: '오늘 오전', duration: '1시간 40분', people: 3, equipment: '분무기', weatherFit: 72, risk: '높음', score: 94, color: '#f46a4e' },
  { id: 'b', name: 'B밭', crop: '당근', area: '5,400㎡', location: '애월읍 하귀리', task: '파종 후 관수', deadline: '오늘', duration: '1시간 20분', people: 1, equipment: '관수장비', weatherFit: 61, risk: '보통', score: 76, color: '#e99b32' },
  { id: 'c', name: 'C밭', crop: '양배추', area: '6,100㎡', location: '애월읍 고성리', task: '양배추 정식', deadline: '내일', duration: '2시간 30분', people: 2, equipment: '운반차', weatherFit: 84, risk: '높음', score: 87, color: '#526cde' },
  { id: 'd', name: 'D밭', crop: '단호박', area: '3,800㎡', location: '애월읍 광령리', task: '생육 확인', deadline: '이번 주', duration: '40분', people: 1, equipment: '없음', weatherFit: 91, risk: '낮음', score: 52, color: '#2f9d72' },
]

export type ScheduleItem = {
  id: string
  time: string
  farm: string
  task: string
  type: 'task' | 'move'
  duration: number
  score?: number
  workers?: string
  equipment?: string
  fit?: number
  reason?: string
  status?: '취소' | '연기'
  color?: string
}

export const initialSchedule: ScheduleItem[] = [
  { id: 'a', time: '06:40~08:20', farm: 'A과원', task: '병해충 방제', type: 'task', duration: 100, score: 94, workers: '김농부 외 2명', equipment: '분무기 1대', fit: 72, color: '#f46a4e', reason: '오전 9시 이후 풍속 증가가 예상돼 분무 작업을 첫 번째로 배치했습니다.' },
  { id: 'm1', time: '08:20~08:40', farm: '상귀리 → 하귀리', task: '이동', type: 'move', duration: 20 },
  { id: 'b', time: '08:40~10:00', farm: 'B밭', task: '최소 관수', type: 'task', duration: 80, score: 76, workers: '김농부', equipment: '관수장비 1세트', fit: 61, color: '#e99b32', reason: '오후 강수 가능성이 있으나 현재 토양 수분이 낮아 최소 관수를 유지했습니다.' },
  { id: 'm2', time: '10:00~10:20', farm: '하귀리 → 고성리', task: '이동', type: 'move', duration: 20 },
  { id: 'c', time: '10:20~12:50', farm: 'C밭', task: '양배추 정식', type: 'task', duration: 150, score: 87, workers: '외부 작업자 2명', equipment: '운반차 1대', fit: 84, color: '#526cde', reason: '작업기한이 내일이며 외부 작업자 2명을 연속 배치하면 오늘 완료할 수 있습니다.' },
  { id: 'd', time: '14:00~14:40', farm: 'D밭', task: '생육 확인', type: 'task', duration: 40, score: 52, workers: '김농부', equipment: '없음', fit: 91, color: '#2f9d72', reason: '기상 영향이 적고 우선순위가 낮아 오후 확인 일정으로 배치했습니다.' },
]

export const revisedSchedule: ScheduleItem[] = [
  { id: 'a', time: '06:30~08:10', farm: 'A과원', task: '병해충 방제', type: 'task', duration: 100, score: 98, workers: '김농부 외 2명', equipment: '분무기 1대', fit: 68, color: '#f46a4e', reason: '강풍 시작 전에 완료하도록 기존보다 10분 앞당겼습니다.' },
  { id: 'm1', time: '08:10~08:30', farm: '상귀리 → 고성리', task: '이동', type: 'move', duration: 20 },
  { id: 'c', time: '08:30~11:00', farm: 'C밭', task: '양배추 정식', type: 'task', duration: 150, score: 92, workers: '김농부 외 2명', equipment: '운반차 1대', fit: 78, color: '#526cde', reason: '관수 취소로 남은 작업자 2명을 합류시켜 강수 전 완료 가능성을 높였습니다.' },
  { id: 'b', time: '자동 취소', farm: 'B밭', task: '파종 후 관수', type: 'task', duration: 0, score: 38, workers: '-', equipment: '관수장비', fit: 22, status: '취소', color: '#94a3b8', reason: '예상 강수량 증가로 불필요한 관수를 방지합니다.' },
  { id: 'd', time: '다음 날', farm: 'D밭', task: '생육 확인', type: 'task', duration: 0, score: 44, workers: '-', equipment: '없음', fit: 47, status: '연기', color: '#94a3b8', reason: '우선순위가 낮고 강수 영향을 고려해 다음 날로 이동합니다.' },
]

export const priorityFactors = [
  { label: '작업기한 긴급도', value: 96, note: '오늘 오전까지' },
  { label: '기상 작업창', value: 92, note: '강풍 전 2시간 20분' },
  { label: '지연 예상손실', value: 88, note: '방제 적기 이탈 위험' },
  { label: '작업자 가용성', value: 100, note: '3명 모두 가능' },
  { label: '장비 가용성', value: 100, note: '분무기 확보' },
  { label: '이동시간', value: 74, note: '차고지에서 10분' },
]

export const centerRequests = [
  { farm: '완탱이 농장', task: '감귤 방제', location: '상귀리', people: 3, time: '06:30~09:00', risk: '높음', status: '배치 완료' },
  { farm: '고성 푸른농장', task: '양배추 정식', location: '고성리', people: 4, time: '08:30~12:00', risk: '높음', status: '배치 완료' },
  { farm: '하귀 채소원', task: '당근 파종', location: '하귀리', people: 3, time: '07:00~11:00', risk: '보통', status: '배치 중' },
  { farm: '광령 단호박', task: '유인 작업', location: '광령리', people: 2, time: '13:00~16:00', risk: '낮음', status: '미배치' },
  { farm: '장전 감귤원', task: '적과', location: '장전리', people: 4, time: '09:00~15:00', risk: '보통', status: '배치 완료' },
]

export const performanceData = [
  { day: '월', completed: 78, wait: 42, jobs: 18 },
  { day: '화', completed: 82, wait: 38, jobs: 21 },
  { day: '수', completed: 76, wait: 51, jobs: 19 },
  { day: '목', completed: 88, wait: 31, jobs: 24 },
  { day: '금', completed: 91, wait: 25, jobs: 26 },
  { day: '토', completed: 86, wait: 29, jobs: 22 },
  { day: '일', completed: 93, wait: 22, jobs: 28 },
]

export const weekDays = [
  { day: '월', date: '9.8', weather: '맑음 25°', danger: false, tasks: [{ name: '감귤 방제', farm: 'A과원', tone: 'orange' }, { name: '당근 파종', farm: 'B밭', tone: 'blue' }] },
  { day: '화', date: '9.9', weather: '강풍 24°', danger: true, tasks: [{ name: '방제 앞당김', farm: 'A과원', tone: 'red' }, { name: '양배추 정식', farm: 'C밭', tone: 'blue' }] },
  { day: '수', date: '9.10', weather: '비 23°', danger: true, tasks: [{ name: '관수 자동 취소', farm: 'B밭', tone: 'gray' }, { name: '생육 확인 연기', farm: 'D밭', tone: 'gray' }] },
  { day: '목', date: '9.11', weather: '흐림 24°', danger: false, tasks: [{ name: '생육 확인', farm: 'D밭', tone: 'green' }] },
  { day: '금', date: '9.12', weather: '맑음 26°', danger: false, tasks: [{ name: '양배추 추비', farm: 'C밭', tone: 'blue' }] },
  { day: '토', date: '9.13', weather: '맑음 27°', danger: false, tasks: [{ name: '감귤 적과', farm: 'A과원', tone: 'orange' }] },
  { day: '일', date: '9.14', weather: '구름 26°', danger: false, tasks: [] },
]

export const annualRows = [
  { crop: '노지감귤', color: '#f47b45', tasks: [{ name: '전정', start: 1, span: 2 }, { name: '방제', start: 3, span: 5 }, { name: '관수', start: 5, span: 3 }, { name: '적과', start: 6, span: 3 }, { name: '수확', start: 10, span: 2 }] },
  { crop: '당근', color: '#e6a237', tasks: [{ name: '파종', start: 7, span: 2 }, { name: '발아관리', start: 8, span: 2 }, { name: '관수', start: 8, span: 2 }, { name: '병해충관리', start: 9, span: 2 }, { name: '수확', start: 11, span: 2 }] },
  { crop: '양배추', color: '#566cdf', tasks: [{ name: '육묘', start: 6, span: 2 }, { name: '정식', start: 8, span: 2 }, { name: '추비', start: 9, span: 2 }, { name: '방제', start: 10, span: 2 }, { name: '수확', start: 11, span: 2 }] },
  { crop: '단호박', color: '#2fa378', tasks: [{ name: '파종', start: 2, span: 2 }, { name: '유인', start: 4, span: 2 }, { name: '수정', start: 5, span: 2 }, { name: '방제', start: 6, span: 2 }, { name: '수확', start: 7, span: 2 }] },
]

export const dataSources = ['기상청 초단기예보', '기상청 단기예보', '기상청 레이더 강수정보', '기상청 지상관측 AWS', '농촌진흥청 농업기상정보', '제주특별자치도 농업 공공데이터']
