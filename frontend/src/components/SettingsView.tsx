import { useState, useEffect } from 'react'
import { Save, CircleDot } from 'lucide-react'

interface SettingsViewProps {
  config: {
    asr_model: string
    translate_model: string
    translate_api_url: string
    translate_api_key: string
  }
  onSave: (settings: Record<string, string>) => void
  onTestConnection: (url: string, prefix: string) => Promise<boolean>
}

const ASR_MODELS = [
  'Qwen/Qwen3-ASR-1.7B',
  'Qwen/Qwen3-ASR-0.6B',
  'Qwen/Qwen3-ASR-1.7B-8bit',
]

export function SettingsView({ config, onSave, onTestConnection }: SettingsViewProps) {
  const [asrModel, setAsrModel] = useState(config.asr_model || ASR_MODELS[0])
  const [transModel, setTransModel] = useState(config.translate_model || '')
  const [transUrl, setTransUrl] = useState(config.translate_api_url || '')
  const [transKey, setTransKey] = useState(config.translate_api_key || '')
  const [vadDuration, setVadDuration] = useState(1.5)
  const [transStatus, setTransStatus] = useState<'unknown' | 'testing' | 'connected' | 'failed'>('unknown')

  useEffect(() => {
    setAsrModel(config.asr_model || ASR_MODELS[0])
    setTransModel(config.translate_model || '')
    setTransUrl(config.translate_api_url || '')
    setTransKey(config.translate_api_key || '')
  }, [config])

  const statusColor = (s: string) => {
    if (s === 'connected') return 'text-success'
    if (s === 'testing') return 'text-warning'
    if (s === 'failed') return 'text-danger'
    return 'text-text-dim'
  }

  const handleTestTrans = async () => {
    setTransStatus('testing')
    const ok = await onTestConnection(transUrl, 'trans')
    setTransStatus(ok ? 'connected' : 'failed')
  }

  const handleSave = () => {
    onSave({
      asr_model: asrModel,
      translate_model: transModel,
      translate_api_url: transUrl,
      translate_api_key: transKey,
      vad_duration: vadDuration.toString(),
    })
  }

  return (
    <div className="flex flex-col gap-3 p-1">
      <h1 className="text-xl font-bold text-text-light mb-4">API 設定</h1>

      <div className="bg-bg-panel rounded-[14px]">
        <div className="flex items-center justify-between px-4 pt-3.5 pb-2">
          <span className="text-[15px] font-bold text-text-light">
            🎤 ASR 語音辨識 (本地 GPU)
          </span>
          <div className="flex items-center gap-2">
            <CircleDot className="w-3 h-3 text-success" />
            <span className="text-xs text-success">本地推理</span>
          </div>
        </div>
        <div className="px-4 pb-3.5">
          <label className="text-sm text-text-muted">模型選擇</label>
          <select
            value={asrModel}
            onChange={e => setAsrModel(e.target.value)}
            className="mt-2 w-full h-[34px] rounded-lg bg-bg-input text-text-light text-sm px-3 border-0 outline-none focus:ring-2 focus:ring-primary/50 font-sans"
          >
            {ASR_MODELS.map(m => (
              <option key={m} value={m}>{m}</option>
            ))}
          </select>
        </div>
      </div>

      <div className="bg-bg-panel rounded-[14px]">
        <div className="flex items-center justify-between px-4 pt-3.5 pb-2">
          <span className="text-[15px] font-bold text-text-light">
            🌐 翻譯引擎 (LM Studio API)
          </span>
          <div className="flex items-center gap-2">
            <CircleDot className={`w-3 h-3 ${statusColor(transStatus)}`} />
            <span className={`text-xs ${statusColor(transStatus)}`}>
              {transStatus === 'connected' ? '已連接' : transStatus === 'testing' ? '測試中...' : transStatus === 'failed' ? '連接失敗' : '未連接'}
            </span>
          </div>
        </div>
        <div className="space-y-1 px-4">
          <FieldRow label="API URL" value={transUrl} onChange={setTransUrl} placeholder="http://localhost:1234/v1" />
          <FieldRow label="模型名稱" value={transModel} onChange={setTransModel} placeholder="qwen/qwen3.5-9b" />
          <FieldRow label="API Key" value={transKey} onChange={setTransKey} placeholder="可選" />
        </div>
        <div className="px-4 pt-2 pb-3.5">
          <button onClick={handleTestTrans} className="h-8 px-3 rounded-lg bg-primary-muted hover:bg-primary text-xs text-text-light transition-colors">
            測試連接
          </button>
        </div>
      </div>

      <div className="bg-bg-panel rounded-[14px]">
        <div className="px-4 pt-3.5 pb-2">
          <span className="text-[15px] font-bold text-text-light">
            🔇 VAD 靜音分割
          </span>
        </div>
        <div className="px-4 pb-3.5 flex items-center gap-3">
          <span className="text-sm w-11">{vadDuration.toFixed(1)}s</span>
          <input
            type="range"
            min="0.5"
            max="3.0"
            step="0.1"
            value={vadDuration}
            onChange={e => setVadDuration(parseFloat(e.target.value))}
            className="w-[260px] accent-primary"
          />
        </div>
      </div>

      <div className="self-end">
        <button
          onClick={handleSave}
          className="h-10 px-5 rounded-lg bg-primary hover:bg-primary-hover text-sm font-medium text-text-light transition-colors flex items-center gap-2"
        >
          <Save className="w-4 h-4" />
          儲存設定
        </button>
      </div>
    </div>
  )
}

function FieldRow({ label, value, onChange, placeholder }: {
  label: string
  value: string
  onChange: (v: string) => void
  placeholder: string
}) {
  return (
    <div className="flex items-center gap-2 py-1">
      <span className="text-sm text-text-muted w-20 shrink-0">{label}</span>
      <input
        type="text"
        value={value}
        onChange={e => onChange(e.target.value)}
        placeholder={placeholder}
        className="h-[34px] flex-1 rounded-lg bg-bg-input text-text-light text-sm px-3 border-0 outline-none focus:ring-2 focus:ring-primary/50 font-sans"
      />
    </div>
  )
}