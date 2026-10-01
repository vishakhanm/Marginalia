import { useEffect } from 'react'

/**
 * The backend redirects here as /oauth-callback?token=... after a successful
 * Google login. We just need to pull the token out of the URL and hand it
 * back to App.jsx — there's nothing else on this "page".
 */
export default function OAuthCallbackPage({ onLoggedIn }) {
    useEffect(() => {
        const params = new URLSearchParams(window.location.search)
        const token = params.get('token')
        if (token) {
            onLoggedIn(token)
        }
        // Clean the token out of the visible URL either way
        window.history.replaceState({}, '', '/')
    }, [onLoggedIn])

    return <div className="page">Signing you in...</div>
}