import { useEffect, useState } from 'react'
import {
    listEndpoints,
    createEndpoint,
    deleteEndpoint,
    invokeEndpoint,
    listKnowledgeBases,
} from '../api/client'
import Card from '../components/Card'

export default function EndpointsPage() {
    const [endpoints, setEndpoints] = useState([])
    const [knowledgeBases, setKnowledgeBases] = useState([])
    const [name, setName] = useState('')
    const [kbId, setKbId] = useState('')
    const [temperature, setTemperature] = useState('')
    const [topK, setTopK] = useState('')
    const [error, setError] = useState(null)

    const [testQuery, setTestQuery] = useState({})
    const [testResult, setTestResult] = useState({})

    const refresh = () => {
        listEndpoints()
            .then((data) => setEndpoints(data.endpoints))
            .catch(() => setError('Could not load endpoints. Is the backend running?'))
        listKnowledgeBases().then((data) => {
            setKnowledgeBases(data.knowledge_bases)
            if (data.knowledge_bases.length > 0 && !kbId) setKbId(data.knowledge_bases[0].id)
        })
    }

    useEffect(refresh, [])

    const handleCreate = async (e) => {
        e.preventDefault()
        if (!name.trim() || !kbId) return
        const hyperparameters = {}
        if (temperature !== '') hyperparameters.temperature = parseFloat(temperature)
        if (topK !== '') hyperparameters.top_k = parseInt(topK, 10)

        try {
            await createEndpoint({
                name,
                kb_id: kbId,
                hyperparameters: Object.keys(hyperparameters).length > 0 ? hyperparameters : undefined,
            })
            setName('')
            setTemperature('')
            setTopK('')
            refresh()
        } catch (err) {
            setError(err.response?.data?.detail || 'Could not create endpoint.')
        }
    }

    const handleDelete = async (id) => {
        if (!confirm('Unpublish this endpoint?')) return
        await deleteEndpoint(id)
        refresh()
    }

    const handleTest = async (id) => {
        const query = testQuery[id]
        if (!query?.trim()) return
        setTestResult((prev) => ({ ...prev, [id]: { loading: true } }))
        try {
            const result = await invokeEndpoint(id, query)
            setTestResult((prev) => ({ ...prev, [id]: { answer: result.answer } }))
        } catch (err) {
            setTestResult((prev) => ({
                ...prev,
                [id]: { error: err.response?.data?.detail || 'Invocation failed.' },
            }))
        }
    }

    return (
        <div className="page">
            <h2>Published Endpoints</h2>

            <Card title="Publish a new endpoint">
                <form onSubmit={handleCreate} className="form-grid">
                    <label>
                        Name
                        <input value={name} onChange={(e) => setName(e.target.value)} placeholder="e.g. legal-contracts-qa" />
                    </label>
                    <label>
                        Knowledge base
                        <select value={kbId} onChange={(e) => setKbId(e.target.value)}>
                            {knowledgeBases.map((kb) => (
                                <option key={kb.id} value={kb.id}>
                                    {kb.name}
                                </option>
                            ))}
                        </select>
                    </label>
                    <div className="form-row">
                        <label>
                            Temperature (optional)
                            <input
                                type="number"
                                step="0.1"
                                value={temperature}
                                onChange={(e) => setTemperature(e.target.value)}
                                placeholder="default"
                            />
                        </label>
                        <label>
                            Top K (optional)
                            <input
                                type="number"
                                value={topK}
                                onChange={(e) => setTopK(e.target.value)}
                                placeholder="default"
                            />
                        </label>
                    </div>
                    <button type="submit" disabled={!kbId}>
                        Publish
                    </button>
                </form>
            </Card>

            {error && <div className="error-box">{error}</div>}

            <div className="card-list">
                {endpoints.map((ep) => (
                    <Card
                        key={ep.id}
                        title={ep.name}
                        actions={
                            <button className="danger" onClick={() => handleDelete(ep.id)}>
                                Delete
                            </button>
                        }
                    >
                        <p className="muted">
                            KB: {ep.kb_id} · Calls: {ep.call_count}
                        </p>
                        <code className="endpoint-path">POST /inference/{ep.id}</code>

                        <div className="form-row" style={{ marginTop: '0.75rem' }}>
                            <input
                                placeholder="Test query..."
                                value={testQuery[ep.id] || ''}
                                onChange={(e) => setTestQuery((prev) => ({ ...prev, [ep.id]: e.target.value }))}
                            />
                            <button onClick={() => handleTest(ep.id)}>Test</button>
                        </div>

                        {testResult[ep.id]?.loading && <p className="muted">Running...</p>}
                        {testResult[ep.id]?.answer && <p className="answer-text">{testResult[ep.id].answer}</p>}
                        {testResult[ep.id]?.error && <p className="error-box">{testResult[ep.id].error}</p>}
                    </Card>
                ))}
                {endpoints.length === 0 && <p className="muted">No endpoints published yet.</p>}
            </div>
        </div>
    )
}