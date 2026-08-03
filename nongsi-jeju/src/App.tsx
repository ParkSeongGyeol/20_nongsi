import { useCallback, useRef, useState } from 'react'
import { Layout, LoadingOverlay, Toast } from './components'
import { CalendarPage } from './pages/Calendar'
import { CenterPage } from './pages/Center'
import { Dashboard } from './pages/Dashboard'
import { FarmsPage } from './pages/Farms'
import { RecordsPage } from './pages/Records'
import { Schedule } from './pages/Schedule'
import { useRoute } from './router'

type LoadingState = { active: boolean; message: string }

export default function App() {
  const { pathname, navigate } = useRoute()
  const [weatherChanged, setWeatherChanged] = useState(false)
  const [recalculated, setRecalculated] = useState(false)
  const [confirmed, setConfirmed] = useState(false)
  const [completed, setCompleted] = useState(false)
  const [loading, setLoading] = useState<LoadingState>({ active: false, message: '' })
  const [toast, setToast] = useState('')
  const toastTimer = useRef<number | null>(null)

  const notify = useCallback((message: string) => {
    setToast(message)
    if (toastTimer.current) window.clearTimeout(toastTimer.current)
    toastTimer.current = window.setTimeout(() => setToast(''), 2800)
  }, [])

  const runLoading = (message: string, after: () => void, doneMessage: string, delay = 1500) => {
    setLoading({ active: true, message })
    window.setTimeout(() => {
      setLoading({ active: false, message: '' })
      after()
      notify(doneMessage)
    }, delay)
  }

  const generateSchedule = (after: () => void) => runLoading('오늘의 최적 일정을 생성하고 있습니다', after, '작업 우선순위 분석이 완료되었습니다.')
  const recalculateSchedule = (after: () => void) => runLoading('기상 변화로 일정을 다시 계산하고 있습니다', () => { setRecalculated(true); after() }, '기상청 데이터를 반영해 일정이 변경되었습니다.', 1750)

  const confirmSchedule = () => {
    setConfirmed(true)
    notify('오늘 일정이 확정되어 작업자 3명에게 공유되었습니다.')
  }

  const completeWork = () => {
    setCompleted(true)
    notify('A과원 방제 완료 기록이 저장되고 다음 추천에 반영되었습니다.')
  }

  const resetDemo = () => {
    setWeatherChanged(false)
    setRecalculated(false)
    setConfirmed(false)
    setCompleted(false)
    setLoading({ active: false, message: '' })
    navigate('/')
    notify('데모가 초기 상태로 돌아갔습니다.')
  }

  const pages: Record<string, React.ReactNode> = {
    '/': <Dashboard onGenerate={generateSchedule} />,
    '/schedule': <Schedule weatherChanged={weatherChanged} recalculated={recalculated} confirmed={confirmed} onWeatherChange={() => setWeatherChanged(true)} onRecalculate={recalculateSchedule} onConfirm={confirmSchedule} notify={notify} />,
    '/calendar': <CalendarPage />,
    '/farms': <FarmsPage notify={notify} />,
    '/center': <CenterPage notify={notify} />,
    '/records': <RecordsPage completed={completed} onComplete={completeWork} notify={notify} />,
  }

  return (
    <Layout resetDemo={resetDemo} notify={notify}>
      {pages[pathname] ?? pages['/']}
      {loading.active && <LoadingOverlay message={loading.message} />}
      {toast && <Toast message={toast} />}
    </Layout>
  )
}
