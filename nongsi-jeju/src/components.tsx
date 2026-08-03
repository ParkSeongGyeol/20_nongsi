import { useEffect, useState, type ReactNode } from 'react'
import { Link, useRoute } from './router'
import {
  Bell,
  Building2,
  CalendarDays,
  Check,
  ChevronRight,
  ClipboardCheck,
  CloudSun,
  Download,
  LandPlot,
  LayoutDashboard,
  MapPin,
  Menu,
  RefreshCcw,
  Settings,
  Sprout,
  Users,
  X,
} from 'lucide-react'
import { dataSources } from './data'

export type Tone = 'red' | 'orange' | 'green' | 'blue' | 'gray' | 'purple'

export function Badge({ children, tone = 'gray' }: { children: ReactNode; tone?: Tone }) {
  return <span className={`badge badge-${tone}`}>{children}</span>
}

export function KpiCard({ label, value, note, icon, tone = 'blue' }: { label: string; value: string; note?: string; icon?: ReactNode; tone?: Tone }) {
  return (
    <div className="kpi-card">
      <div className={`kpi-icon tone-${tone}`}>{icon}</div>
      <div>
        <div className="kpi-label">{label}</div>
        <div className="kpi-value">{value}</div>
        {note && <div className="kpi-note">{note}</div>}
      </div>
    </div>
  )
}

export function PageHeader({ eyebrow, title, description, actions }: { eyebrow?: string; title: string; description: string; actions?: ReactNode }) {
  return (
    <div className="page-heading">
      <div>
        {eyebrow && <div className="eyebrow">{eyebrow}</div>}
        <h1>{title}</h1>
        <p>{description}</p>
      </div>
      {actions && <div className="page-actions">{actions}</div>}
    </div>
  )
}

export function Panel({ title, description, action, children, className = '' }: { title?: string; description?: string; action?: ReactNode; children: ReactNode; className?: string }) {
  return (
    <section className={`panel ${className}`}>
      {(title || action) && (
        <div className="panel-head">
          <div>
            {title && <h2>{title}</h2>}
            {description && <p>{description}</p>}
          </div>
          {action}
        </div>
      )}
      {children}
    </section>
  )
}

export function Button({ children, variant = 'primary', icon, onClick, disabled, className = '', type = 'button' }: { children: ReactNode; variant?: 'primary' | 'secondary' | 'danger' | 'ghost'; icon?: ReactNode; onClick?: () => void; disabled?: boolean; className?: string; type?: 'button' | 'submit' }) {
  return <button type={type} className={`button button-${variant} ${className}`} onClick={onClick} disabled={disabled}>{icon}{children}</button>
}

export function Modal({ children, onClose, wide = false }: { children: ReactNode; onClose: () => void; wide?: boolean }) {
  useEffect(() => {
    const close = (event: KeyboardEvent) => event.key === 'Escape' && onClose()
    window.addEventListener('keydown', close)
    return () => window.removeEventListener('keydown', close)
  }, [onClose])
  return (
    <div className="modal-backdrop" onMouseDown={onClose} role="presentation">
      <div className={`modal-card ${wide ? 'modal-wide' : ''}`} onMouseDown={(event) => event.stopPropagation()} role="dialog" aria-modal="true">
        <button className="modal-close" onClick={onClose} aria-label="닫기"><X size={20} /></button>
        {children}
      </div>
    </div>
  )
}

export function SourceFooter() {
  return (
    <footer className="source-footer">
      <div className="source-list">{dataSources.map((source) => <span key={source}><Check size={12} />{source}</span>)}</div>
      <p>현재 화면은 공공데이터 활용 구조를 검증하기 위한 시연용 데이터입니다.</p>
    </footer>
  )
}

export function LoadingOverlay({ message }: { message: string }) {
  return (
    <div className="loading-overlay">
      <div className="loader-orbit"><span /><span /><span /></div>
      <h3>{message}</h3>
      <p>기상 작업창 · 인력 · 장비 · 이동시간을 함께 분석하고 있습니다.</p>
    </div>
  )
}

const navItems = [
  { label: '오늘의 작업', path: '/', icon: LayoutDashboard },
  { label: '주간 계획', path: '/calendar', icon: CalendarDays },
  { label: '농장 관리', path: '/farms', icon: LandPlot },
  { label: '작업 요청', path: '/center', icon: Users },
  { label: '운영센터', path: '/center', icon: Building2 },
  { label: '작업 기록', path: '/records', icon: ClipboardCheck },
]

export function Layout({ children, resetDemo, notify }: { children: ReactNode; resetDemo: () => void; notify: (message: string) => void }) {
  const { pathname } = useRoute()
  const [mobileOpen, setMobileOpen] = useState(false)
  const [now, setNow] = useState(new Date())

  useEffect(() => {
    const timer = window.setInterval(() => setNow(new Date()), 30000)
    return () => window.clearInterval(timer)
  }, [])
  useEffect(() => setMobileOpen(false), [pathname])

  const timeText = now.toLocaleTimeString('ko-KR', { hour: '2-digit', minute: '2-digit', hour12: false })
  const dateText = now.toLocaleDateString('ko-KR', { month: 'long', day: 'numeric', weekday: 'short' })

  return (
    <div className="app-shell">
      <header className="topbar">
        <button className="mobile-menu" onClick={() => setMobileOpen(true)} aria-label="메뉴 열기"><Menu /></button>
        <Link className="brand" to="/">
          <span className="brand-symbol"><Sprout size={23} /></span>
          <span><strong>농시</strong><small>NONGSI JEJU</small></span>
        </Link>
        <div className="header-context">
          <div className="header-location"><MapPin size={16} /><span><small>현재 지역</small>제주특별자치도 제주시 애월읍</span></div>
          <div className="header-meta"><span>{dateText} · {timeText}</span><span><CloudSun size={15} /> 기상데이터 07:12 갱신</span></div>
        </div>
        <div className="header-actions">
          <button className="reset-button" onClick={resetDemo}><RefreshCcw size={15} /> 데모 초기화</button>
          <button className="icon-button notification" onClick={() => notify('확인하지 않은 기상 알림이 2건 있습니다.')} aria-label="알림"><Bell size={20} /><i>2</i></button>
          <button className="profile" onClick={() => notify('완탱이 농장 계정으로 시연 중입니다.')}>
            <span className="avatar">김</span>
            <span><small>완탱이 농장</small><strong>김농부</strong></span>
            <ChevronRight size={16} />
          </button>
        </div>
      </header>
      {mobileOpen && <div className="mobile-scrim" onClick={() => setMobileOpen(false)} />}
      <aside className={`sidebar ${mobileOpen ? 'sidebar-open' : ''}`}>
        <div className="sidebar-label">농가 업무</div>
        <nav>
          {navItems.map((item, index) => {
            const active = pathname === item.path && (item.path !== '/center' || index === 4)
            const Icon = item.icon
            return <Link key={`${item.label}-${index}`} to={item.path} className={active ? 'active' : ''}><Icon size={20} /><span>{item.label}</span>{item.label === '작업 요청' && <em>4</em>}</Link>
          })}
          <button onClick={() => notify('설정 화면은 정식 서비스에서 제공됩니다.')}><Settings size={20} /><span>설정</span></button>
        </nav>
        <div className="sidebar-card">
          <div className="sidebar-card-icon"><CloudSun size={20} /></div>
          <small>오늘의 기상 작업창</small>
          <strong>3시간 40분</strong>
          <div className="progress"><i style={{ width: '64%' }} /></div>
          <p>오전 9시 이후 바람이 강해져요</p>
        </div>
        <div className="sidebar-footer"><span>농가용</span><button onClick={() => notify('운영센터 메뉴에서 기관용 화면을 확인할 수 있습니다.')}>기관용 전환 <ChevronRight size={13} /></button></div>
      </aside>
      <main className="main-content">{children}</main>
    </div>
  )
}

export function Toast({ message }: { message: string }) {
  return <div className="toast"><span><Check size={17} /></span>{message}</div>
}

export const icons = { Download }
