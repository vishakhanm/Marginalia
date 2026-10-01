import { useEffect, useState } from 'react'
import { listConversations, getConversation, deleteConversation } from '../api/client'
import Card from '../components/Card'

function formatTime(isoString) {
    return new Date(isoString).toLocaleString(undefined, {
        month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit',
    })
}

/** Pairs chronological [user, assistant, user, assistant, ...] messages into
 * exchanges, then reverses the list so the most recent exchange shows first —
 * while keeping each question directly above its answer. */
function pairIntoExchanges(messages) {
    const exchanges = []
    for (let i = 0; i < messages.length; i += 2) {
        exchanges.push({ user: messages[i], assistant: messages[i + 1] })
    }
    return exchanges.reverse()
}

export default function HistoryPage() {
    const [conversations, setConversations] = useState([])
    const [selectedId, setSelectedId] = useState(null)
    const [detail, setDetail] = useState(null)
    const [error, setError] = useState(null)

    // Conversations are already returned newest-updated-first by the backend
    const refreshList = () => {
        listConversations()
            .then((data) => setConversations(data.conversations))
            .catch(() => setError('Could not load conversation history.'))
    }

    useEffect(refreshList, [])

    const openConversation = (id) => {
        setSelectedId(id)
        getConversation(id)
            .then(setDetail)
            .catch(() => setError('Could not load this conversation.'))
    }

    const handleDelete = async (id) => {
        if (!confirm('Delete this conversation?')) return
        await deleteConversation(id)
        if (selectedId === id) {
            setSelectedId(null)
            setDetail(null)
        }
        refreshList()
    }

    const exchanges = detail ? pairIntoExchanges(detail.messages) : []

    return (
        <div className="page">
            <h2>Chat History</h2>
            {error && <div className="error-box">{error}</div>}

            <div className="history-layout">
                <Card title="Conversations">
                    <div className="card-list">
                        {conversations.map((c) => (
                            <div
                                key={c.id}
                                className={`history-item ${selectedId === c.id ? 'active' : ''}`}
                                onClick={() => openConversation(c.id)}
                            >
                                <div>
                                    <div>{c.title}</div>
                                    <div className="timestamp">{formatTime(c.updated_at)}</div>
                                </div>
                                <button
                                    className="danger small"
                                    onClick={(e) => {
                                        e.stopPropagation()
                                        handleDelete(c.id)
                                    }}
                                >
                                    Delete
                                </button>
                            </div>
                        ))}
                        {conversations.length === 0 && <p className="muted">No conversations yet — ask something in Chat.</p>}
                    </div>
                </Card>

                {detail && (
                    <Card title={detail.conversation.title}>
                        <div className="message-list">
                            {exchanges.map((ex, i) => (
                                <div key={i} className="exchange">
                                    <div className="message message-user">
                                        <strong>You</strong>
                                        <span className="timestamp">{formatTime(ex.user.created_at)}</span>
                                        <p>{ex.user.content}</p>
                                    </div>
                                    {ex.assistant && (
                                        <div className="message message-assistant">
                                            <strong>Assistant</strong>
                                            <span className="timestamp">{formatTime(ex.assistant.created_at)}</span>
                                            <p>{ex.assistant.content}</p>
                                        </div>
                                    )}
                                </div>
                            ))}
                        </div>
                    </Card>
                )}
            </div>
        </div>
    )
}