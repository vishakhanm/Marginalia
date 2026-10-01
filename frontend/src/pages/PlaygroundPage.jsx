import { useEffect, useState } from 'react'
import { listModelsCached, playgroundChat } from '../api/client'
import Card from '../components/Card'

export default function PlaygroundPage() {
    const [models, setModels] = useState([])
    const [model, setModel] = useState('')
    const [temperature, setTemperature] = useState(0.7)
    const [preamble, setPreamble] = useState('')
    const [input, setInput] = useState('')
    const [messages, setMessages] = useState([]) // [{role, content}] — in-memory only
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState(null)

    useEffect(() => {
        listModelsCached()
            .then((data) => {
                setModels(data.models)
                if (data.models.length > 0) setModel(data.models[0].name)
            })
            .catch(() => setError('Could not load models. Is Ollama running?'))
    }, [])

    const handleSend = async (e) => {
        e.preventDefault()
        if (!input.trim() || !model) return
        const nextMessages = [...messages, { role: 'user', content: input }]
        setMessages(nextMessages)
        setInput('')
        setLoading(true)
        setError(null)
        try {
            const data = await playgroundChat({
                messages: nextMessages,
                model,
                temperature: parseFloat(temperature),
                preamble: preamble || undefined,
            })
            setMessages((prev) => [...prev, { role: 'assistant', content: data.answer }])
        } catch (err) {
            setError(err.response?.data?.detail || 'Something went wrong.')
        } finally {
            setLoading(false)
        }
    }

    const handleClear = () => setMessages([])

    return (
        <div className="page">
            <div className="page-header-row">
                <h2>Playground</h2>
                {messages.length > 0 && (
                    <button className="link-button" onClick={handleClear}>
                        Clear chat
                    </button>
                )}
            </div>
            <p className="muted">
                Free-form chat with any local model — no knowledge base involved. Nothing here is saved;
                refreshing the page clears everything.
            </p>

            <Card title="Settings">
                <div className="form-row">
                    <label>
                        Model
                        <select value={model} onChange={(e) => setModel(e.target.value)}>
                            {models.length === 0 && <option value="">No models available</option>}
                            {models.map((m) => (
                                <option key={m.name} value={m.name}>
                                    {m.name}
                                </option>
                            ))}
                        </select>
                    </label>
                    <label>
                        Temperature: {temperature}
                        <input
                            type="range"
                            min="0"
                            max="2"
                            step="0.1"
                            value={temperature}
                            onChange={(e) => setTemperature(e.target.value)}
                        />
                    </label>
                </div>
                <label>
                    System prompt (optional)
                    <input value={preamble} onChange={(e) => setPreamble(e.target.value)} placeholder="e.g. You are a concise assistant." />
                </label>
            </Card>

            {error && <div className="error-box">{error}</div>}

            <Card title="Conversation (not saved)">
                <div className="message-list">
                    {messages.map((m, i) => (
                        <div key={i} className={`message message-${m.role}`}>
                            <strong>{m.role === 'user' ? 'You' : 'Assistant'}</strong>
                            <p>{m.content}</p>
                        </div>
                    ))}
                    {messages.length === 0 && <p className="muted">Send a message to start.</p>}
                </div>

                <form onSubmit={handleSend} className="form-row" style={{ marginTop: '1rem' }}>
                    <input
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        placeholder="Type a message..."
                        style={{ flex: 1 }}
                    />
                    <button type="submit" disabled={loading || !model}>
                        {loading ? 'Thinking...' : 'Send'}
                    </button>
                </form>
            </Card>
        </div>
    )
}