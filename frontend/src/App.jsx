import { useEffect, useState } from 'react'
import Sidebar from './components/Sidebar'
import ChatPage from './pages/ChatPage'
import PlaygroundPage from './pages/PlaygroundPage'
import HistoryPage from './pages/HistoryPage'
import KnowledgeBasePage from './pages/Knowledgebasepage'
import ModelsPage from './pages/ModelsPage'
import EndpointsPage from './pages/EndpointsPage'
import ConfigPage from './pages/ConfigPage'
import LoginPage from './pages/LoginPage'
import OAuthCallbackPage from './pages/OAuthCallbackPage'
import { getDependencyHealth, getMe, getToken, setToken, clearToken } from './api/client'

const PAGES = {
    chat: ChatPage,
    playground: PlaygroundPage,
    history: HistoryPage,
    knowledge: KnowledgeBasePage,
    models: ModelsPage,
    endpoints: EndpointsPage,
    config: ConfigPage,
}

export default function App() {
    const [activeTab, setActiveTab] = useState('chat')
    const [health, setHealth] = useState(null)
    const [user, setUser] = useState(null)
    const [authChecked, setAuthChecked] = useState(false)

    const isOAuthCallback = window.location.pathname === '/oauth-callback'

    const loadUser = () => {
        if (!getToken()) {
            setUser(null)
            setAuthChecked(true)
            return
        }
        getMe()
            .then(setUser)
            .catch(() => setUser(null))
            .finally(() => setAuthChecked(true))
    }

    useEffect(loadUser, [])

    useEffect(() => {
        if (!user) return
        const check = () => getDependencyHealth().then((d) => setHealth(d.dependencies)).catch(() => { })
        check()
        const interval = setInterval(check, 15000)
        return () => clearInterval(interval)
    }, [user])

    const handleLoggedIn = (token) => {
        setToken(token)
        window.history.replaceState({}, '', '/')
        loadUser()
    }

    const handleLogout = () => {
        clearToken()
        setUser(null)
    }

    if (isOAuthCallback) {
        return <OAuthCallbackPage onLoggedIn={handleLoggedIn} />
    }

    if (!authChecked) {
        return <div className="page">Loading...</div>
    }

    if (!user) {
        return <LoginPage onLoggedIn={handleLoggedIn} />
    }

    const ActivePage = PAGES[activeTab]

    return (
        <div className="app-layout">
            <Sidebar activeTab={activeTab} onSelectTab={setActiveTab} health={health} user={user} onLogout={handleLogout} />
            <main className="main-content">
                <ActivePage />
            </main>
        </div>
    )
}