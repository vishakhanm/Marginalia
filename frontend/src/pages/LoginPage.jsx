import { useState } from 'react'
import { loginUser, registerUser, googleLoginUrl } from '../api/client'
import Card from '../components/Card'

export default function LoginPage({ onLoggedIn }) {
    const [mode, setMode] = useState('login') // 'login' | 'register'
    const [email, setEmail] = useState('')
    const [password, setPassword] = useState('')
    const [name, setName] = useState('')
    const [error, setError] = useState(null)
    const [loading, setLoading] = useState(false)

    const handleSubmit = async (e) => {
        e.preventDefault()
        setError(null)
        setLoading(true)
        try {
            if (mode === 'register') {
                await registerUser({ email, password, name: name || undefined })
            }
            const { access_token } = await loginUser(email, password)
            onLoggedIn(access_token)
        } catch (err) {
            setError(err.response?.data?.detail || 'Something went wrong.')
        } finally {
            setLoading(false)
        }
    }

    return (
        <div className="auth-page">
            <Card title={mode === 'login' ? 'Log in' : 'Create an account'}>
                <form onSubmit={handleSubmit} className="form-grid">
                    {mode === 'register' && (
                        <label>
                            Name (optional)
                            <input value={name} onChange={(e) => setName(e.target.value)} />
                        </label>
                    )}
                    <label>
                        Email
                        <input type="email" required value={email} onChange={(e) => setEmail(e.target.value)} />
                    </label>
                    <label>
                        Password
                        <input
                            type="password"
                            required
                            minLength={8}
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                        />
                    </label>
                    <button type="submit" disabled={loading}>
                        {loading ? 'Please wait...' : mode === 'login' ? 'Log in' : 'Register'}
                    </button>
                </form>

                {error && <div className="error-box">{error}</div>}

                <p className="muted" style={{ marginTop: '1rem' }}>
                    {mode === 'login' ? "Don't have an account? " : 'Already have an account? '}
                    <button className="link-button" onClick={() => setMode(mode === 'login' ? 'register' : 'login')}>
                        {mode === 'login' ? 'Register' : 'Log in'}
                    </button>
                </p>

                <div className="divider">or</div>

                <a className="google-button" href={googleLoginUrl()}>
                    Continue with Google
                </a>
            </Card>
        </div>
    )
}