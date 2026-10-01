const TABS = [
    { id: 'chat', label: '💬 Chat' },
    { id: 'playground', label: '🧪 Playground' },
    { id: 'history', label: '🕒 History' },
    { id: 'knowledge', label: '📚 Knowledge Bases' },
    { id: 'models', label: '🧠 Models' },
    { id: 'endpoints', label: '🔌 Endpoints' },
    { id: 'config', label: '⚙️ Config' },
]

export default function Sidebar({ activeTab, onSelectTab, health, user, onLogout }) {
    return (
        <aside className="sidebar">
            <div className="sidebar-title">LLM Playground</div>
            <nav>
                {TABS.map((tab) => (
                    <button
                        key={tab.id}
                        className={`sidebar-link ${activeTab === tab.id ? 'active' : ''}`}
                        onClick={() => onSelectTab(tab.id)}
                    >
                        {tab.label}
                    </button>
                ))}
            </nav>
            <div className="sidebar-footer">
                <div className="health-row">
                    <span className={`dot ${health?.mongo === 'ok' ? 'dot-ok' : 'dot-error'}`} />
                    Mongo
                </div>
                <div className="health-row">
                    <span className={`dot ${health?.qdrant === 'ok' ? 'dot-ok' : 'dot-error'}`} />
                    Qdrant
                </div>
                {user && (
                    <div className="user-row">
                        <span className="muted">{user.name || user.email}</span>
                        <button className="link-button" onClick={onLogout}>
                            Log out
                        </button>
                    </div>
                )}
            </div>
        </aside>
    )
}