import { useEffect, useState } from 'react'
import { getGlobalConfig, updateGlobalConfig } from '../api/client'
import Card from '../components/Card'

export default function ConfigPage() {
    const [config, setConfig] = useState(null)
    const [form, setForm] = useState({})
    const [saving, setSaving] = useState(false)
    const [message, setMessage] = useState('')
    const [error, setError] = useState(null)

    const refresh = () => {
        getGlobalConfig()
            .then((data) => {
                setConfig(data)
                setForm(data)
            })
            .catch(() => setError('Could not load config. Is the backend running?'))
    }

    useEffect(refresh, [])

    const handleChange = (field, value) => setForm((prev) => ({ ...prev, [field]: value }))

    const handleSave = async (e) => {
        e.preventDefault()
        setSaving(true)
        setMessage('')
        try {
            const payload = {
                model: form.model,
                temperature: parseFloat(form.temperature),
                top_k: parseInt(form.top_k, 10),
                chunk_size: parseInt(form.chunk_size, 10),
                chunk_overlap: parseInt(form.chunk_overlap, 10),
                preamble: form.preamble,
            }
            const updated = await updateGlobalConfig(payload)
            setConfig(updated)
            setMessage('Saved.')
        } catch (err) {
            setMessage(err.response?.data?.detail || 'Save failed.')
        } finally {
            setSaving(false)
        }
    }

    if (error) return <div className="page error-box">{error}</div>
    if (!config) return <div className="page">Loading...</div>

    return (
        <div className="page">
            <h2>Global Hyperparameter Defaults</h2>
            <p className="muted">
                These apply to every request unless overridden by a knowledge base's own profile or a
                per-request value.
            </p>

            <Card title="Defaults">
                <form onSubmit={handleSave} className="form-grid">
                    <label>
                        Default model
                        <input value={form.model || ''} onChange={(e) => handleChange('model', e.target.value)} />
                    </label>
                    <div className="form-row">
                        <label>
                            Temperature
                            <input
                                type="number"
                                step="0.1"
                                min="0"
                                max="2"
                                value={form.temperature ?? ''}
                                onChange={(e) => handleChange('temperature', e.target.value)}
                            />
                        </label>
                        <label>
                            Top K
                            <input
                                type="number"
                                min="1"
                                max="20"
                                value={form.top_k ?? ''}
                                onChange={(e) => handleChange('top_k', e.target.value)}
                            />
                        </label>
                    </div>
                    <div className="form-row">
                        <label>
                            Chunk size (words)
                            <input
                                type="number"
                                value={form.chunk_size ?? ''}
                                onChange={(e) => handleChange('chunk_size', e.target.value)}
                            />
                        </label>
                        <label>
                            Chunk overlap (words)
                            <input
                                type="number"
                                value={form.chunk_overlap ?? ''}
                                onChange={(e) => handleChange('chunk_overlap', e.target.value)}
                            />
                        </label>
                    </div>
                    <label>
                        Preamble
                        <textarea
                            rows={3}
                            value={form.preamble || ''}
                            onChange={(e) => handleChange('preamble', e.target.value)}
                        />
                    </label>
                    <button type="submit" disabled={saving}>
                        {saving ? 'Saving...' : 'Save changes'}
                    </button>
                </form>
                {message && <p className="muted">{message}</p>}
            </Card>
        </div>
    )
}