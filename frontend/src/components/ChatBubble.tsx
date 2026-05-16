interface BubbleData {
  id: string
  speaker: string
  original: string
  translated: string
  speakerId: number
  time: string
}

interface ChatBubbleProps {
  bubble: BubbleData
}

export function ChatBubble({ bubble }: ChatBubbleProps) {
  const isLeft = bubble.speakerId === 1
  const accentColor = isLeft ? '#3B82F6' : '#38BDF8'
  const bgColor = isLeft ? 'bg-bubble-left' : 'bg-bubble-right'

  return (
    <div className="flex justify-start px-[15px] py-[10px]">
      <div
        className={`${bgColor} rounded-[20px] px-3 py-2 max-w-[85%] shadow-lg shadow-black/20`}
      >
        <div className="flex items-center gap-2 px-2.5 pt-1.5 pb-1">
          <span
            className="text-xs font-bold font-chat"
            style={{ color: accentColor }}
          >
            {bubble.speaker}
          </span>
          <span className="text-[11px] text-text-dim font-chat">
            {bubble.time}
          </span>
        </div>

        <p className="text-text-muted italic px-3 pb-0.5 font-chat leading-relaxed">
          {bubble.original}
        </p>

        <p className="text-text-light font-bold px-3 pb-2 font-chat leading-relaxed">
          {bubble.translated}
        </p>
      </div>
    </div>
  )
}

interface ChatAreaProps {
  bubbles: BubbleData[]
}

export function ChatArea({ bubbles }: ChatAreaProps) {
  return (
    <div className="flex-1 overflow-y-auto px-1">
      {bubbles.length === 0 && (
        <div className="h-full flex items-center justify-center text-text-dim">
          <p className="text-sm">等待語音輸入...</p>
        </div>
      )}
      {bubbles.map((bubble) => (
        <ChatBubble key={bubble.id} bubble={bubble} />
      ))}
    </div>
  )
}