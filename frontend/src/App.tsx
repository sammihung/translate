import { useState, useEffect, useCallback } from 'react'
import { Sidebar } from './components/Sidebar'
import { RealtimeView } from './components/RealtimeView'
import { BatchView } from './components/BatchView'
import { SettingsView } from './components/SettingsView'
import { useWebSocket } from './hooks/useWebSocket'
import { useChat } from './hooks/useChat'

const FONT_PRESETS = [
  { label: '小', original: 14, translated: 18 },
  { label: '標準', original: 16, translated: 20 },
  { label: '大', original: 18, translated: 24 },
  { label: '超大', original: 22, translated: 28 },
]

const DEFAULT_FONT_INDEX = 1

function App() {
  const [activeView, setActiveView] = useState('realtime')
  const [fontIndex, setFontIndex] = useState(DEFAULT_FONT_INDEX)
  const [floatingActive, setFloatingActive] = useState(false)
  const [isRecording, setIsRecording] = useState(false)
  const [enginesReady, setEnginesReady] = useState(false)
  const [audioLevel, setAudioLevel] = useState(0)
  const [status, setStatus] = useState('連接中...')
  const [statusColor, setStatusColor] = useState('#F59E0B')
  const [appConfig, setAppConfig] = useState({
    asr_model: '',
    asr_api_url: '',
    asr_api_key: '',
    translate_model: '',
    translate_api_url: '',
    translate_api_key: '',
  })

  const { send, on, off } = useWebSocket()
  const { bubbles, addBubble, updateBubble } = useChat()

  useEffect(() => {
    on('subtitle_update', (data) => {
      addBubble({
        bubble_id: (data.bubble_id as string) || '',
        original: (data.original as string) || '',
        translated: (data.translated as string) || '',
        speaker_id: (data.speaker_id as number) || 1,
      })
    })

    on('translation_complete', (data) => {
      updateBubble({
        bubble_id: (data.bubble_id as string) || '',
        translated: (data.translated as string) || '',
      })
    })

    on('status_change', (data) => {
      setStatus((data.status as string) || '')
      setStatusColor((data.color as string) || '#94A3B8')
    })

    on('audio_level', (data) => {
      setAudioLevel((data.level as number) || 0)
    })

    on('engines_ready', (data) => {
      setEnginesReady((data.ready as boolean) || false)
    })

    on('record_state', (data) => {
      setIsRecording((data.is_recording as boolean) || false)
    })
  }, [on, off, addBubble, updateBubble])

  useEffect(() => {
    fetch('/api/config')
      .then((r) => r.json())
      .then(setAppConfig)
      .catch(console.error)

    fetch('/api/status')
      .then((r) => r.json())
      .then((data) => {
        setEnginesReady(data.engines_ready || false)
        setIsRecording(data.is_recording || false)
      })
      .catch(console.error)
  }, [])

  const handleRecordClick = useCallback(() => {
    if (isRecording) {
      send({ type: 'stop_recording' })
      setIsRecording(false)
      setAudioLevel(0)
    } else {
      send({ type: 'start_recording' })
    }
  }, [isRecording, send])

  const handleSourceChange = useCallback(
    (source: string, targetApp: string) => {
      send({ type: 'set_source', source, target_app: targetApp })
    },
    [send]
  )

  const handleLangChange = useCallback(
    (src: string, tgt: string) => {
      send({ type: 'set_lang', src, tgt })
    },
    [send]
  )

  const handleFontCycle = useCallback(() => {
    const next = (fontIndex + 1) % FONT_PRESETS.length
    setFontIndex(next)
  }, [fontIndex])

  const handleSaveSettings = useCallback(
    (settings: Record<string, string>) => {
      send({ type: 'update_config', settings })
      fetch('/api/config', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(settings),
      }).catch(console.error)
    },
    [send]
  )

  const handleTestConnection = useCallback(
    async (_url: string, _prefix: string): Promise<boolean> => {
      try {
        const resp = await fetch(`${_url}/models`)
        return resp.status === 200
      } catch {
        return false
      }
    },
    []
  )

  const handleExportClick = useCallback(() => {
    const srtContent = bubbles
      .map((b: { original: string; translated: string }, i: number) => {
        const start = `00:00:${i.toString().padStart(2, '0')},000`
        const end = `00:00:${(i + 1).toString().padStart(2, '0')},000`
        return `${i + 1}\n${start} --> ${end}\n${b.original}\n${b.translated}\n`
      })
      .join('\n')

    const blob = new Blob([srtContent], { type: 'text/plain;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'subtitle.srt'
    a.click()
    URL.revokeObjectURL(url)
  }, [bubbles])

  return (
    <div className="h-screen flex bg-bg-dark overflow-hidden">
      <Sidebar
        activeView={activeView}
        onNavClick={setActiveView}
        onFloatingToggle={() => setFloatingActive(!floatingActive)}
        onFontCycle={handleFontCycle}
        fontLabel={FONT_PRESETS[fontIndex].label}
        floatingActive={floatingActive}
        status={status}
        statusColor={statusColor}
      />

      <main className="flex-1 flex flex-col min-w-0 p-4">
        {activeView === 'realtime' && (
          <RealtimeView
            isRecording={isRecording}
            enginesReady={enginesReady}
            audioLevel={audioLevel}
            bubbles={bubbles}
            onRecordClick={handleRecordClick}
            onSourceChange={handleSourceChange}
            onLangChange={handleLangChange}
            onExportClick={handleExportClick}
          />
        )}

        {activeView === 'batch' && <BatchView />}
        {activeView === 'settings' && (
          <SettingsView
            config={appConfig}
            onSave={handleSaveSettings}
            onTestConnection={handleTestConnection}
          />
        )}
      </main>
    </div>
  )
}

export default App