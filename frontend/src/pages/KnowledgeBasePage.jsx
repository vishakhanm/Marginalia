import { useEffect, useState } from 'react'
import {
    listKnowledgeBases, createKnowledgeBase, updateKnowledgeBase,
    deleteKnowledgeBase, uploadDocuments,
} from '../api/client'
import Card from '../components/Card'

export default function KnowledgeBasePage() {
    const [knowledgeBases, setKnowledgeBases] = useState([])
    const [name, setName] = useState('')
    const [description, setDescription] = useState('')
    const [error, setError] = useState(null)
    const [uploadingFor, setUploadingFor] = useState(null)
    const [uploadMessage, setUploadMessage] = useState('')
    const [editingId, setEditingId] = useState(null)
    const [editName, setEditName] = useState('')
    const [editDescription, setEditDescription] = useState('')

    const refresh = () => {
        listKnowledgeBases()
            .then((data) => setKnowledgeBases(data.knowledge_bases))
            .catch(() => setError('Could not load knowledge bases.'))
    }

    useEffect(refresh, [])

    const handleCreate = async (e) => {
        e.preventDefault()
        if (!name.trim()) return
        try {
            await createKnowledgeBase({ name, description: description || undefined })
            setName('')
            setDescription('')
            refresh()
        } catch (err) {
            setError(err.response?.data?.detail || 'Could not create knowledge base.')
        }
    }

    const handleDelete = async (kbId) => {
        if (!confirm('Delete this knowledge base and all its documents?')) return
        await deleteKnowledgeBase(kbId)
        refresh()
    }

    const handleUpload = async (kbId, fileList) => {
        if (!fileList || fileList.length === 0) return
        setUploadingFor(kbId)
        setUploadMessage('')
        try {
            const result = await uploadDocuments(kbId, Array.from(fileList))
            const parts = []
            if (result.uploaded.length > 0) {
                const totalChunks = result.uploaded.reduce((sum, u) => sum + u.chunks_created, 0)
                parts.push(`Uploaded ${result.uploaded.length} file(s), ${totalChunks} chunks created.`)
            }
            if (result.failed.length > 0) {
                parts.push(`Failed: ${result.failed.map((f) => `${f.filename} (${f.error})`).join('; ')}`)
            }
            setUploadMessage(parts.join(' '))
            refresh()
        } catch (err) {
            setUploadMessage(err.response?.data?.detail || 'Upload failed.')
        } finally {
            setUploadingFor(null)
        }
    }

    const startEdit = (kb) => {
        setEditingId(kb.id)
        setEditName(kb.name)
        setEditDescription(kb.description || '')
    }

    const cancelEdit = () => setEditingId(null)

    const saveEdit = async (kbId) => {
        try {
            await updateKnowledgeBase(kbId, { name: editName, description: editDescription })
            setEditingId(null)
            refresh()
        } catch (err) {
            setError(err.response?.data?.detail || 'Could not update knowledge base.')
        }
    }

    return (
        <div className="page">
            <h2>Knowledge Bases</h2>

            <Card title="Create a new knowledge base">
                <form onSubmit={handleCreate} className="form-grid">
                    <label>
                        Name
                        <input value={name} onChange={(e) => setName(e.target.value)} placeholder="e.g. Product Docs" />
                    </label>
                    <label>
                        Description (optional)
                        <input value={description} onChange={(e) => setDescription(e.target.value)} />
                    </label>
                    <button type="submit">Create</button>
                </form>
            </Card>

            {error && <div className="error-box">{error}</div>}
            {uploadMessage && <div className="info-box">{uploadMessage}</div>}

            <div className="card-list">
                {knowledgeBases.map((kb) => (
                    <Card
                        key={kb.id}
                        title={editingId === kb.id ? undefined : kb.name}
                        actions={
                            editingId !== kb.id && (
                                <div style={{ display: 'flex', gap: '0.5rem' }}>
                                    <button className="secondary small" onClick={() => startEdit(kb)}>
                                        Edit
                                    </button>
                                    <button className="danger" onClick={() => handleDelete(kb.id)}>
                                        Delete
                                    </button>
                                </div>
                            )
                        }
                    >
                        {editingId === kb.id ? (
                            <div className="form-grid">
                                <label>
                                    Name
                                    <input value={editName} onChange={(e) => setEditName(e.target.value)} />
                                </label>
                                <label>
                                    Description
                                    <input value={editDescription} onChange={(e) => setEditDescription(e.target.value)} />
                                </label>
                                <div className="form-row">
                                    <button onClick={() => saveEdit(kb.id)}>Save</button>
                                    <button className="secondary" onClick={cancelEdit}>
                                        Cancel
                                    </button>
                                </div>
                            </div>
                        ) : (
                            <>
                                <p className="muted">{kb.description || 'No description'}</p>
                                <p>
                                    {kb.document_count} document{kb.document_count === 1 ? '' : 's'} · {kb.chunk_count} chunks
                                </p>
                                <label className="upload-label">
                                    Upload files (PDF / DOCX / TXT / CSV / XLSX) — select multiple at once
                                    <input
                                        type="file"
                                        multiple
                                        accept=".pdf,.docx,.txt,.csv,.xlsx"
                                        disabled={uploadingFor === kb.id}
                                        onChange={(e) => handleUpload(kb.id, e.target.files)}
                                    />
                                </label>
                                {uploadingFor === kb.id && <p className="muted">Uploading & embedding...</p>}
                            </>
                        )}
                    </Card>
                ))}
                {knowledgeBases.length === 0 && <p className="muted">No knowledge bases yet — create one above.</p>}
            </div>
        </div>
    )
}