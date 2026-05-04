import { useState, useRef } from "react"
import axios from "axios"
import { Paperclip, Send, FileText, FileSpreadsheet, File, BookOpen } from "lucide-react"

const API = "http://localhost:8000"

const getFileIcon = (name) => {
  if (name.endsWith(".pdf")) return <FileText size={13} />
  if (name.endsWith(".csv") || name.endsWith(".xlsx")) return <FileSpreadsheet size={13} />
  return <File size={13} />
}

const getFileBadgeStyle = (name) => {
  if (name.endsWith(".pdf")) return { bg: "bg-red-100 text-red-700" }
  if (name.endsWith(".csv")) return { bg: "bg-emerald-100 text-emerald-700" }
  if (name.endsWith(".xlsx")) return { bg: "bg-emerald-100 text-emerald-700" }
  if (name.endsWith(".docx")) return { bg: "bg-blue-100 text-blue-700" }
  return { bg: "bg-gray-100 text-gray-600" }
}

export default function App() {
  const [docs, setDocs] = useState([])
  const [messages, setMessages] = useState([])
  const [question, setQuestion] = useState("")
  const [attachedFile, setAttachedFile] = useState(null)
  const [uploading, setUploading] = useState(false)
  const [asking, setAsking] = useState(false)
  const fileInputRef = useRef(null)
  const bottomRef = useRef(null)

  const handleFileChange = (e) => {
    const file = e.target.files[0]
    if (!file) return
    setAttachedFile(file)
  }

  const uploadFile = async (file) => {
    setUploading(true)
    const formData = new FormData()
    formData.append("file", file)
    try {
      const res = await axios.post(`${API}/upload`, formData)
      setDocs((prev) => [...prev, { name: file.name, size: file.size, chunks: res.data.chunks_stored }])
      setAttachedFile(null)
    } catch (err) {
      console.error("Upload failed", err)
    } finally {
      setUploading(false)
      if (fileInputRef.current) fileInputRef.current.value = ""
    }
  }

const handleSend = async () => {
  if (!question.trim() && !attachedFile) return
  const userQuestion = question
  setMessages((prev) => [...prev, { role: "user", content: userQuestion }])
  setQuestion("")
  setAsking(true)

  if (attachedFile) await uploadFile(attachedFile)
  if (!userQuestion.trim()) { setAsking(false); return }

  setMessages((prev) => [...prev, { role: "assistant", content: "" }])

  try {
    const res = await fetch(`${API}/ask`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question: userQuestion }),
    })

    const reader = res.body.getReader()
    const decoder = new TextDecoder()

    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      const chunk = decoder.decode(value, { stream: true })
      setMessages((prev) => {
        const updated = [...prev]
        updated[updated.length - 1] = {
          ...updated[updated.length - 1],
          content: updated[updated.length - 1].content + chunk,
        }
        return updated
      })
      bottomRef.current?.scrollIntoView({ behavior: "smooth" }) 
    }
  } catch (err) {
    setMessages((prev) => {
      const updated = [...prev]
      updated[updated.length - 1] = { role: "assistant", content: "Something went wrong. Please try again." }
      return updated
    })
  } finally {
    setAsking(false)
    setTimeout(() => bottomRef.current?.scrollIntoView({ behavior: "smooth" }), 100)
  }
}

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const formatSize = (bytes) => {
    if (bytes < 1024) return `${bytes} B`
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
  }

  return (
    <div className="flex h-screen bg-white">

      {/* Sidebar */}
      <div className="w-64 border-r border-gray-200 flex flex-col bg-gray-50">

        {/* Logo */}
        <div className="px-5 py-5 border-b border-gray-200">
          <div className="flex items-center gap-2.5 mb-1">
            <div className="w-8 h-8 rounded-lg bg-black flex items-center justify-center flex-shrink-0">
              <BookOpen size={15} color="white" />
            </div>
            <span className="text-lg font-semibold tracking-tight text-gray-900">DocQA</span>
          </div>
          <p className="text-xs text-gray-400 ml-10">
            {docs.length === 0 ? "No documents yet" : `${docs.length} document${docs.length !== 1 ? "s" : ""} indexed`}
          </p>
        </div>

        {/* Doc list */}
        <div className="flex-1 overflow-y-auto px-3 py-3">
          {docs.length === 0 ? (
            <div className="mt-6 text-center px-4">
              <div className="w-10 h-10 rounded-xl bg-gray-100 flex items-center justify-center mx-auto mb-3">
                <Paperclip size={16} className="text-gray-400" />
              </div>
              <p className="text-xs text-gray-400 leading-relaxed">
                Attach a file using the paperclip in the chat below
              </p>
            </div>
          ) : (
            <div className="space-y-1">
              <p className="text-xs font-medium text-gray-400 uppercase tracking-wider px-2 mb-2">Uploaded</p>
              {docs.map((doc, i) => {
                const style = getFileBadgeStyle(doc.name)
                return (
                  <div key={i} className="flex items-center gap-2.5 px-2 py-2 rounded-lg hover:bg-gray-100 transition-colors">
                    <div className={`w-7 h-7 rounded-md flex items-center justify-center flex-shrink-0 ${style.bg}`}>
                      {getFileIcon(doc.name)}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-xs font-medium text-gray-700 truncate">{doc.name}</p>
                      <p className="text-xs text-gray-400">{formatSize(doc.size)} · {doc.chunks} chunks</p>
                    </div>
                    <div className="w-1.5 h-1.5 rounded-full bg-emerald-400 flex-shrink-0" />
                  </div>
                )
              })}
            </div>
          )}
        </div>
      </div>

      {/* Main */}
      <div className="flex-1 flex flex-col min-w-0">

        {/* Header */}
        <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between bg-white">
          <div>
            <h2 className="text-base font-semibold text-gray-900">Ask your documents</h2>
            <p className="text-xs text-gray-400 mt-0.5">
              {docs.length === 0 ? "Upload a document to get started" : `Searching across ${docs.length} document${docs.length !== 1 ? "s" : ""}`}
            </p>
          </div>
          {docs.length > 0 && (
            <span className="text-xs font-medium bg-emerald-50 text-emerald-700 px-2.5 py-1 rounded-full border border-emerald-200">
              {docs.length} ready
            </span>
          )}
        </div>

        {/* Chat area */}
        <div className="flex-1 overflow-y-auto px-6 py-6">
          {messages.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full text-center">
              <div className="w-14 h-14 rounded-2xl bg-gray-100 flex items-center justify-center mb-4">
                <BookOpen size={24} className="text-gray-400" />
              </div>
              <p className="text-sm font-medium text-gray-700">No messages yet</p>
              <p className="text-xs text-gray-400 mt-1">Upload a document and ask a question</p>
            </div>
          ) : (
            <div className="flex flex-col gap-5 max-w-3xl mx-auto">
              {messages.map((msg, i) => (
                <div key={i} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
                  <div className={`max-w-[75%] px-4 py-3 rounded-2xl text-sm leading-relaxed ${
                    msg.role === "user"
                      ? "bg-gray-900 text-white rounded-br-sm"
                      : "bg-gray-100 text-gray-800 rounded-bl-sm"
                  }`}>
                    {msg.content}
                  </div>
                </div>
              ))}
              {asking && (
                <div className="flex justify-start">
                  <div className="bg-gray-100 px-4 py-3 rounded-2xl rounded-bl-sm text-sm text-gray-400 flex items-center gap-1.5">
                    <span className="w-1.5 h-1.5 rounded-full bg-gray-400 animate-bounce" style={{ animationDelay: "0ms" }} />
                    <span className="w-1.5 h-1.5 rounded-full bg-gray-400 animate-bounce" style={{ animationDelay: "150ms" }} />
                    <span className="w-1.5 h-1.5 rounded-full bg-gray-400 animate-bounce" style={{ animationDelay: "300ms" }} />
                  </div>
                </div>
              )}
              <div ref={bottomRef} />
            </div>
          )}
        </div>

        {/* Input */}
        <div className="px-6 py-4 border-t border-gray-200 bg-white">
          {attachedFile && (
            <div className="flex items-center gap-1.5 mb-2.5 bg-gray-100 border border-gray-200 rounded-lg px-3 py-1.5 w-fit text-xs text-gray-600">
              <Paperclip size={11} />
              <span>{attachedFile.name}</span>
              <button onClick={() => setAttachedFile(null)} className="ml-1 text-gray-400 hover:text-gray-700">✕</button>
            </div>
          )}
          <div className="flex items-end gap-2 bg-gray-50 border border-gray-200 rounded-2xl px-4 py-3 focus-within:border-gray-400 transition-colors">
            <input
              type="file"
              ref={fileInputRef}
              onChange={handleFileChange}
              className="hidden"
              accept=".pdf,.txt,.csv,.xlsx,.docx,.png,.jpg,.jpeg"
            />
            <button
              className="text-gray-400 hover:text-gray-700 transition-colors flex-shrink-0 pb-0.5 disabled:opacity-40"
              onClick={() => fileInputRef.current.click()}
              disabled={uploading}
            >
              <Paperclip size={16} />
            </button>
            <textarea
              className="flex-1 bg-transparent text-sm text-gray-800 placeholder:text-gray-400 resize-none outline-none min-h-[22px] max-h-[120px] py-0"
              placeholder="Ask a question about your documents..."
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              onKeyDown={handleKeyDown}
              rows={1}
            />
  <button
  className={`w-7 h-7 rounded-lg flex items-center justify-center flex-shrink-0 transition-colors
    ${asking || uploading || (!question.trim() && !attachedFile)
      ? "bg-gray-200 cursor-not-allowed"
      : "bg-gray-900 hover:bg-gray-700 cursor-pointer"
    }`}
  onClick={handleSend}
  disabled={asking || uploading || (!question.trim() && !attachedFile)}
>
  <Send size={13} color={asking || uploading || (!question.trim() && !attachedFile) ? "#9ca3af" : "white"} />
</button>
          </div>
          <p className="text-xs text-gray-400 mt-2 px-1">Press Enter to send · Shift+Enter for new line</p>
        </div>
      </div>
    </div>
  )
}