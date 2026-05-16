import { useState } from 'react'
import { CloudUpload, Play } from 'lucide-react'

export function BatchView() {
  const [isDragOver, setIsDragOver] = useState(false)

  return (
    <div className="flex flex-col gap-4 p-1">
      <h1 className="text-2xl font-bold text-text-light">批量音檔轉字幕</h1>

      <div
        className={`h-[220px] rounded-[14px] border-2 flex flex-col items-center justify-center cursor-pointer transition-all duration-200 ${
          isDragOver
            ? 'bg-bg-panel-light border-primary'
            : 'bg-bg-panel border-border hover:border-primary-muted'
        }`}
        onDragOver={(e) => {
          e.preventDefault()
          setIsDragOver(true)
        }}
        onDragLeave={() => setIsDragOver(false)}
        onDrop={(e) => {
          e.preventDefault()
          setIsDragOver(false)
        }}
      >
        <CloudUpload className="w-10 h-10 text-text-muted mb-2" />
        <span className="text-lg text-text-light">點擊此處瀏覽檔案</span>
        <span className="text-sm text-text-muted mt-1">
          支援 MP3, WAV, MP4, M4A, AAC, FLAC
        </span>
      </div>

      <div className="bg-bg-panel rounded-[14px] px-5 py-4">
        <label className="flex items-center gap-3 text-text-light">
          <input
            type="checkbox"
            defaultChecked
            className="w-[22px] h-[22px] accent-primary"
          />
          <span className="text-sm">產生雙語 SRT 字幕檔</span>
        </label>
      </div>

      <button className="self-end h-12 px-6 rounded-xl bg-primary hover:bg-primary-hover text-text-light text-[15px] font-medium transition-colors flex items-center gap-2">
        <Play className="w-4 h-4" />
        選擇檔案並轉換
      </button>
    </div>
  )
}