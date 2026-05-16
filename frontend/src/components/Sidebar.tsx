import { useState } from 'react'
import {
  Zap,
  FolderUp,
  Settings,
  SquareStack,
  Type,
  CircleDot,
} from 'lucide-react'

const NAV_ITEMS = [
  { id: 'realtime', icon: Zap, label: '即時翻譯' },
  { id: 'batch', icon: FolderUp, label: '批量上傳' },
  { id: 'settings', icon: Settings, label: '系統設定' },
]

interface SidebarProps {
  activeView: string
  onNavClick: (viewId: string) => void
  onFloatingToggle: () => void
  onFontCycle: () => void
  fontLabel: string
  floatingActive: boolean
  status: string
  statusColor: string
}

export function Sidebar({
  activeView,
  onNavClick,
  onFloatingToggle,
  onFontCycle,
  fontLabel,
  floatingActive,
  status,
  statusColor,
}: SidebarProps) {
  const [expanded, setExpanded] = useState(true)
  const width = expanded ? 'w-[220px]' : 'w-[68px]'

  return (
    <aside
      className={`${width} h-full bg-[#0f172a] flex flex-col transition-all duration-300 border-r border-border shrink-0`}
    >
      <div className="px-3.5 pt-5 pb-4 flex items-center gap-3">
        <button
          onClick={() => setExpanded(!expanded)}
          className="w-11 h-11 rounded-[10px] bg-transparent hover:bg-bg-panel text-text-muted transition-colors flex items-center justify-center"
        >
          <Zap className="w-5 h-5 text-primary" />
        </button>
        {expanded && (
          <span className="text-xl font-bold text-primary tracking-tight">
            QwenASR
          </span>
        )}
      </div>

      <nav className="flex-1 px-3 space-y-1">
        {NAV_ITEMS.map(({ id, icon: Icon, label }) => (
          <button
            key={id}
            onClick={() => onNavClick(id)}
            className={`w-full h-12 rounded-[10px] flex items-center gap-3 px-3 transition-all duration-200 ${
              activeView === id
                ? 'bg-primary-muted text-primary'
                : 'bg-transparent text-text-muted hover:bg-bg-panel'
            }`}
          >
            <Icon className="w-5 h-5 shrink-0" />
            {expanded && <span className="text-[15px]">{label}</span>}
          </button>
        ))}
      </nav>

      <div className="px-3 space-y-1 pb-2">
        <button
          onClick={onFloatingToggle}
          className={`w-full h-12 rounded-[10px] flex items-center gap-3 px-3 transition-all duration-200 ${
            floatingActive
              ? 'bg-danger text-text-light'
              : 'bg-primary text-text-light hover:bg-primary-hover'
          }`}
        >
          <SquareStack className="w-5 h-5 shrink-0" />
          {expanded && (
            <span className="text-[15px]">
              {floatingActive ? '關閉浮動模式' : '浮動字幕模式'}
            </span>
          )}
        </button>

        <button
          onClick={onFontCycle}
          className="w-full h-12 rounded-[10px] bg-bg-panel text-text-light hover:bg-primary flex items-center gap-3 px-3 transition-all duration-200"
        >
          <Type className="w-5 h-5 shrink-0" />
          {expanded && (
            <span className="text-[15px]">文字大小：{fontLabel}</span>
          )}
        </button>
      </div>

      <div className="px-5 pb-5 flex items-center gap-2">
        <CircleDot
          className={`w-3.5 h-3.5 shrink-0`}
          style={{ color: statusColor }}
        />
        {expanded && (
          <span className="text-sm" style={{ color: statusColor }}>
            {status}
          </span>
        )}
      </div>
    </aside>
  )
}