import { useEffect, useState } from 'react'
import { listModelsCached, pullModel, deleteModel } from '../api/client'
import Card from '../components/Card'

export default function ModelsPage() {
    const [models, setModels] = useState([])
    const [pullName, setPullName] = useState('')
    const [pulling, setPulling] = useState(false)
    const [error, setError] = useState(null)
    const [message, setMessage] = useState('')

    const refresh = () => {
        listModelsCached()
            .then((data) => setModels(data.models))
            .catch(() => setError('Could not load models. Is the backend / Ollama running?'))
    }

    useEffect(refresh, [])

    const handlePull = async (e) => {
        e.preventDefault()
        if (!pullName.trim()) return
        setPulling(true)
        setMessage('')
        try {
            await pullModel(pullName) // also invalidates the cache
            setMessage(`Pulled ${pullName} successfully.`)
            setPullName('')
            refresh()
        } catch (err) {
            setMessage(err.response?.data?.detail || 'Pull failed.')
        } finally {
            setPulling(false)
        }
    }

    const handleDelete = async (name) => {
        if (!confirm(`Delete model '${name}'?`)) return
        try {
            await deleteModel(name)
            refresh()
        } catch (err) {
            setMessage(err.response?.data?.detail || 'Delete failed.')
        }
    }

    return (
        <div className="page">
            <h2>Models</h2>

            <Card title="Pull a model from Ollama">
                <form onSubmit={handlePull} className="form-row">
                    <input value={pullName} onChange={(e) => setPullName(e.target.value)} placeholder="e.g. llama3.2" />
                    <button type="submit" disabled={pulling}>
                        {pulling ? 'Pulling...' : 'Pull'}
                    </button>
                </form>
                {message && <p className="muted">{message}</p>}
            </Card>

            {error && <div className="error-box">{error}</div>}

            <Card title="Locally available models">
                <table className="table">
                    <thead>
                        <tr>
                            <th>Name</th>
                            <th>Parameters</th>
                            <th>Size</th>
                            <th></th>
                        </tr>
                    </thead>
                    <tbody>
                        {models.map((m) => (
                            <tr key={m.name}>
                                <td>
                                    {m.name} {m.is_protected && <span className="badge-protected">default</span>}
                                </td>
                                <td>{m.parameter_size || '—'}</td>
                                <td>{m.size_bytes ? `${(m.size_bytes / 1e9).toFixed(2)} GB` : '—'}</td>
                                <td>
                                    <button
                                        className="danger"
                                        disabled={m.is_protected}
                                        title={m.is_protected ? "Default models can't be deleted" : undefined}
                                        onClick={() => handleDelete(m.name)}
                                    >
                                        Delete
                                    </button>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
                {models.length === 0 && <p className="muted">No models pulled yet.</p>}
            </Card>
        </div>
    )
}