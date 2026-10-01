import axios from 'axios'

const baseURL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

const http = axios.create({ baseURL })

// ---- Token storage ----
const TOKEN_KEY = 'llm_playground_token'
export const getToken = () => localStorage.getItem(TOKEN_KEY)
export const setToken = (token) => localStorage.setItem(TOKEN_KEY, token)
export const clearToken = () => localStorage.removeItem(TOKEN_KEY)

// Attach the bearer token to every request automatically
http.interceptors.request.use((config) => {
    const token = getToken()
    if (token) config.headers.Authorization = `Bearer ${token}`
    return config
})

// If the backend ever says the token is invalid/expired, clear it so the
// app falls back to the login screen instead of looping on 401s.
http.interceptors.response.use(
    (response) => response,
    (error) => {
        if (error.response?.status === 401) clearToken()
        return Promise.reject(error)
    }
)

// ---- Health ----
export const getHealth = () => http.get('/health').then((r) => r.data)
export const getDependencyHealth = () => http.get('/health/dependencies').then((r) => r.data)

// ---- Auth (Step 11) ----
export const registerUser = (payload) => http.post('/auth/register', payload).then((r) => r.data)
export const loginUser = (email, password) => {
    const form = new URLSearchParams()
    form.append('username', email)
    form.append('password', password)
    return http
        .post('/auth/login', form, { headers: { 'Content-Type': 'application/x-www-form-urlencoded' } })
        .then((r) => r.data)
}
export const getMe = () => http.get('/auth/me').then((r) => r.data)
export const googleLoginUrl = () => `${baseURL}/auth/google/login`

// ---- Models (Step 3), with a simple in-memory cache (point 7) ----
// Once fetched, the models list is reused across pages (Models, Chat, Playground)
// instead of re-calling the backend/Ollama every time a page mounts.
let _modelsCache = null

export const listModels = () => http.get('/models').then((r) => r.data)

/** Returns the cached models list, fetching once if it hasn't been loaded yet. */
export const listModelsCached = async () => {
    if (_modelsCache) return _modelsCache
    _modelsCache = await listModels()
    return _modelsCache
}

/** Call after a pull/delete so the next read reflects the change. */
export const invalidateModelsCache = () => {
    _modelsCache = null
}

export const pullModel = (name) =>
    http.post('/models/pull', { name }).then((r) => {
        invalidateModelsCache()
        return r.data
    })

export const deleteModel = (name) =>
    http.delete(`/models/${encodeURIComponent(name)}`).then((r) => {
        invalidateModelsCache()
        return r.data
    })

// ---- Knowledge bases (Step 4 & 6) ----
export const listKnowledgeBases = () => http.get('/knowledge').then((r) => r.data)
export const createKnowledgeBase = (payload) => http.post('/knowledge', payload).then((r) => r.data)
export const getKnowledgeBase = (kbId) => http.get(`/knowledge/${kbId}`).then((r) => r.data)
export const updateKnowledgeBase = (kbId, payload) =>
    http.patch(`/knowledge/${kbId}`, payload).then((r) => r.data)
export const deleteKnowledgeBase = (kbId) => http.delete(`/knowledge/${kbId}`).then((r) => r.data)

/** Accepts a single File or an array of Files — uploads them together in one request. */
export const uploadDocuments = (kbId, files) => {
    const formData = new FormData()
    const fileArray = Array.isArray(files) ? files : [files]
    fileArray.forEach((f) => formData.append('files', f))
    return http
        .post(`/knowledge/${kbId}/upload`, formData, {
            headers: { 'Content-Type': 'multipart/form-data' },
        })
        .then((r) => r.data)
}
export const updateKbHyperparameters = (kbId, hyperparameters) =>
    http.patch(`/knowledge/${kbId}/hyperparameters`, hyperparameters).then((r) => r.data)

// ---- Chat / RAG (Step 5) ----
export const chat = (payload) => http.post('/chat', payload).then((r) => r.data)

// ---- Global config (Step 6) ----
export const getGlobalConfig = () => http.get('/config').then((r) => r.data)
export const updateGlobalConfig = (payload) => http.put('/config', payload).then((r) => r.data)

// ---- Published endpoints (Step 7) ----
export const listEndpoints = () => http.get('/endpoints').then((r) => r.data)
export const createEndpoint = (payload) => http.post('/endpoints', payload).then((r) => r.data)
export const getEndpoint = (endpointId) => http.get(`/endpoints/${endpointId}`).then((r) => r.data)
export const deleteEndpoint = (endpointId) =>
    http.delete(`/endpoints/${endpointId}`).then((r) => r.data)
export const invokeEndpoint = (endpointId, query) =>
    http.post(`/inference/${endpointId}`, { query }).then((r) => r.data)

// ---- Chat history (Step 12) ----
export const listConversations = () => http.get('/history').then((r) => r.data)
export const getConversation = (conversationId) =>
    http.get(`/history/${conversationId}`).then((r) => r.data)
export const deleteConversation = (conversationId) =>
    http.delete(`/history/${conversationId}`).then((r) => r.data)

// ---- Playground — no persistence, nothing here is ever saved ----
export const playgroundChat = (payload) => http.post('/playground/chat', payload).then((r) => r.data)

export default http