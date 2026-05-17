import { useState, useEffect, useRef } from 'react'
import { Mic, Monitor, AppWindow, CircleStop, Download, CircleDot } from 'lucide-react'
import { ChatArea } from './ChatBubble'

function SourceCard({ icon, label, value, selected, onClick }: {
  icon: React.ReactNode
  label: string
  value: string
  selected: boolean
  onClick: (value: string) => void
}) {
  return (
    <button
      onClick={() => onClick(value)}
      className={`w-[80px] h-[80px] rounded-xl flex flex-col items-center justify-center gap-1 transition-all duration-200 ${
        selected
          ? 'bg-primary-muted border-2 border-primary text-text-light'
          : 'bg-bg-panel border-0 text-text-muted hover:bg-bg-panel-light'
      }`}
    >
      {icon}
      <span className="text-xs">{label}</span>
    </button>
  )
}

function LangButton({ label, selected, onClick }: {
  label: string
  selected: boolean
  onClick: () => void
}) {
  return (
    <button
      onClick={onClick}
      className={`h-8 w-[52px] rounded-lg text-xs transition-all duration-200 ${
        selected
          ? 'bg-primary text-text-light'
          : 'bg-bg-panel text-text-muted hover:bg-primary-muted'
      }`}
    >
      {label}
    </button>
  )
}

function AudioMeter({ level }: { level: number }) {
  const totalBars = 16
  const active = Math.min(totalBars, Math.floor(level * totalBars))

  return (
    <div className="flex items-center gap-1">
      <span className="text-xs text-text-muted w-8">{level.toFixed(2)}</span>
      <div className="flex gap-0.5">
        {Array.from({ length: totalBars }).map((_, i) => (
          <div
            key={i}
            className={`w-2 h-6 rounded-sm transition-colors duration-75 ${
              i < active
                ? i < 6 ? 'bg-success' : i < 11 ? 'bg-primary' : 'bg-danger'
                : 'bg-border'
            }`}
          />
        ))}
      </div>
    </div>
  )
}

interface BubbleData {
  id: string
  speaker: string
  original: string
  translated: string
  speakerId: number
  time: string
}

interface RealtimeViewProps {
  isRecording: boolean
  enginesReady: boolean
  translateReady: boolean
  audioLevel: number
  bubbles: BubbleData[]
  onRecordClick: (deviceIndex: number | null) => void
  onSourceChange: (source: string, targetApp: string) => void
  onLangChange: (src: string, tgt: string) => void
  onExportClick: () => void
}

interface DeviceInfo {
  name: string
  index: number | null
}

export function RealtimeView({
  isRecording,
  enginesReady,
  translateReady,
  audioLevel,
  bubbles,
  onRecordClick,
  onSourceChange,
  onLangChange,
  onExportClick,
}: RealtimeViewProps) {
  const [currentSource, setCurrentSource] = useState('mic')
  const [srcLang, setSrcLang] = useState('auto')
  const [tgtLang, setTgtLang] = useState('zh')
  const [micDevices, setMicDevices] = useState<DeviceInfo[]>([])
  const [selectedDevice, setSelectedDevice] = useState<number | null>(null)
  const sourceTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  const SRC_OPTIONS = [
    { label: '自動', code: 'auto' },
    { label: '日', code: 'ja' },
    { label: '英', code: 'en' },
    { label: '中', code: 'zh' },
  ]

  const TGT_OPTIONS = [
    { label: '中', code: 'zh' },
    { label: '英', code: 'en' },
    { label: '日', code: 'ja' },
    { label: '韓', code: 'ko' },
  ]

  useEffect(() => {
    fetch('/api/devices?source=mic')
      .then(r => r.json())
      .then(data => {
        const parsed: DeviceInfo[] = data.parsed || []
        setMicDevices(parsed)
        if (parsed.length > 0 && parsed[0].index !== null) {
          setSelectedDevice(parsed[0].index)
        }
      })
      .catch(() => {})
  }, [])

  const handleSourceChange = (source: string) => {
    setCurrentSource(source)
    if (sourceTimerRef.current) clearTimeout(sourceTimerRef.current)
    sourceTimerRef.current = setTimeout(() => {
      console.log('[UI] Source changed to:', source)
      onSourceChange(source, '')
    }, 300)
  }

  const handleSrcLang = (code: string) => {
    setSrcLang(code)
    onLangChange(code, tgtLang)
  }

  const handleTgtLang = (code: string) => {
    setTgtLang(code)
    onLangChange(srcLang, code)
  }

  const handleRecord = () => {
    onRecordClick(currentSource === 'mic' ? selectedDevice : null)
  }

  return (
    <div className="flex flex-col h-full gap-3">
      <div className="bg-bg-panel rounded-[14px] p-3.5 flex gap-4 shrink-0">
        <div className="flex flex-col">
          <span className="text-sm font-bold text-text-muted mb-2">
            音訊來源
          </span>
          <div className="flex gap-2">
            <SourceCard icon={<Mic className="w-6 h-6" />} label="麥克風" value="mic"
              selected={currentSource === 'mic'} onClick={handleSourceChange} />
            <SourceCard icon={<Monitor className="w-6 h-6" />} label="系統" value="system"
              selected={currentSource === 'system'} onClick={handleSourceChange} />
            <SourceCard icon={<AppWindow className="w-6 h-6" />} label="App" value="per-app"
              selected={currentSource === 'per-app'} onClick={handleSourceChange} />
          </div>

          {currentSource === 'mic' && micDevices.length > 0 && (
            <select
              value={selectedDevice ?? ''}
              onChange={e => setSelectedDevice(Number(e.target.value))}
              className="mt-3 h-9 rounded-lg bg-bg-input text-text-light text-sm px-3 border-0 outline-none focus:ring-2 focus:ring-primary/50 font-sans"
            >
              {micDevices.map(d => (
                <option key={d.index ?? 'none'} value={d.index ?? ''}>{d.name}</option>
              ))}
            </select>
          )}
        </div>

        <div className="flex flex-col items-center">
          <span className="text-sm font-bold text-text-muted mb-2">語言設定</span>
          <div className="flex items-center gap-1.5 mb-1.5">
            <span className="text-xs text-text-dim w-9">來源</span>
            {SRC_OPTIONS.map(({ label, code }) => (
              <LangButton key={code} label={label} selected={srcLang === code}
                onClick={() => handleSrcLang(code)} />
            ))}
          </div>
          <div className="flex items-center gap-1.5">
            <span className="text-xs text-text-dim w-9">目標</span>
            {TGT_OPTIONS.map(({ label, code }) => (
              <LangButton key={code} label={label} selected={tgtLang === code}
                onClick={() => handleTgtLang(code)} />
            ))}
          </div>
        </div>

        <div className="flex items-center gap-2 ml-auto">
          <CircleDot className={`w-4 h-4 shrink-0 ${enginesReady ? 'text-success' : 'text-text-dim'}`} />
          <span className="text-sm text-text-muted">{enginesReady ? '就緒' : '未連接'}</span>
          {!translateReady && enginesReady && (
            <span className="text-xs text-warning ml-2">(翻譯API未連接)</span>
          )}
        </div>
      </div>

      <ChatArea bubbles={bubbles} />

      <div className="bg-bg-panel rounded-[14px] h-20 px-4 py-3 flex items-center gap-4 shrink-0">
        <button
          onClick={handleRecord}
          disabled={!enginesReady}
          className={`w-14 h-14 rounded-full flex items-center justify-center transition-all duration-200 ${
            isRecording
              ? 'bg-[#334155] hover:bg-[#475569]'
              : enginesReady ? 'bg-danger hover:bg-danger-hover' : 'bg-border cursor-not-allowed'
          }`}
        >
          {isRecording ? <CircleStop className="w-6 h-6 text-text-light" /> : <Mic className="w-6 h-6 text-text-light" />}
        </button>

        <div className="flex flex-col gap-1">
          <span className="text-sm text-text-muted">
            {isRecording ? '錄音中' : enginesReady ? '準備就緒' : '未就緒'}
          </span>
          <AudioMeter level={audioLevel} />
        </div>

        <button
          onClick={onExportClick}
          className="ml-auto h-9 px-4 rounded-lg bg-primary hover:bg-primary-hover text-text-light text-sm font-medium transition-colors flex items-center gap-1.5"
        >
          <Download className="w-4 h-4" />
          匯出 SRT
        </button>
      </div>
    </div>
  )
}