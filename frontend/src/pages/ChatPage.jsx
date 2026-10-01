import { useEffect, useState } from 'react'
import { listKnowledgeBases, listModelsCached, chat } from '../api/client'
import Card from '../components/Card'

function formatTime(date) {
    return date.toLocaleString(undefined, {
        month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit',
    })
}

export default function ChatPage() {
    const [knowledgeBases, setKnowledgeBases] = useState([])
    const [models, setModels] = useState([])
    const [kbId, setKbId] = useState('')
    const [model, setModel] = useState('') // empty = use KB/global default
    const [query, setQuery] = useState('')
    const [conversationId, setConversationId] = useState(null)
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState(null)
    const [exchanges, setExchanges] = useState([]) // [{query, result, timestamp}]

    useEffect(() => {
        listKnowledgeBases()
            .then((data) => {
                setKnowledgeBases(data.knowledge_bases)
                if (data.knowledge_bases.length > 0) setKbId(data.knowledge_bases[0].id)
            })
            .catch(() => setError('Could not load knowledge bases. Is the backend running?'))
        listModelsCached()
            .then((data) => setModels(data.models))
            .catch(() => { })
    }, [])

    const handleAsk = async (e) => {
        e.preventDefault()
        if (!kbId || !query.trim()) return
        setLoading(true)
        setError(null)
        try {
            const payload = { kb_id: kbId, query, conversation_id: conversationId }
            if (model) payload.model = model
            const data = await chat(payload)
            setConversationId(data.conversation_id)
            setExchanges((prev) => [...prev, { query, result: data, timestamp: new Date() }])
            setQuery('')
        } catch (err) {
            setError(err.response?.data?.detail || 'Something went wrong.')
        } finally {
            setLoading(false)
        }
    }

    const handleNewConversation = () => {
        setConversationId(null)
        setExchanges([])
    }

    // Newest exchange first, oldest at the bottom
    const orderedExchanges = [...exchanges].reverse()

    return (
        <div className="page">
            <div className="page-header-row">
                <h2>Chat</h2>
                {exchanges.length > 0 && (
                    <button className="link-button" onClick={handleNewConversation}>
                        Start new conversation
                    </button>
                )}
            </div>

            <Card title="Ask a question">
                <form onSubmit={handleAsk} className="form-grid">
                    <div className="form-row">
                        <label>
                            Knowledge base
                            <select value={kbId} onChange={(e) => setKbId(e.target.value)} disabled={exchanges.length > 0}>
                                {knowledgeBases.length === 0 && <option value="">No knowledge bases yet</option>}
                                {knowledgeBases.map((kb) => (
                                    <option key={kb.id} value={kb.id}>
                                        {kb.name} ({kb.chunk_count} chunks)
                                    </option>
                                ))}
                            </select>
                        </label>
                        <label>
                            Model
                            <select value={model} onChange={(e) => setModel(e.target.value)}>
                                <option value="">Use default</option>
                                {models.map((m) => (
                                    <option key={m.name} value={m.name}>
                                        {m.name}
                                    </option>
                                ))}
                            </select>
                        </label>
                    </div>

                    <label>
                        Question
                        <textarea
                            rows={3}
                            value={query}
                            onChange={(e) => setQuery(e.target.value)}
                            placeholder="Ask something about this knowledge base..."
                        />
                    </label>

                    <button type="submit" disabled={loading || !kbId}>
                        {loading ? 'Thinking...' : 'Ask'}
                    </button>
                </form>
            </Card>

            {error && <div className="error-box">{error}</div>}

            {orderedExchanges.map((ex, i) => (
                <Card key={i} title={ex.query}>
                    <p className="timestamp">{formatTime(ex.timestamp)}</p>
                    <p className="answer-text">{ex.result.answer}</p>
                    {ex.result.citations.length > 0 && (
                        <>
                            <h4>Sources</h4>
                            <ul className="citation-list">
                                {ex.result.citations.map((c, j) => (
                                    <li key={j}>
                                        <strong>
                                            {c.filename} (chunk {c.chunk_index})
                                        </strong>{' '}
                                        <span className="score">score: {c.score.toFixed(3)}</span>
                                        <p>{c.text_snippet}</p>
                                    </li>
                                ))}
                            </ul>
                        </>
                    )}
                </Card>
            ))}
        </div>
    )
}