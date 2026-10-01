export default function StatusBadge({ status }) {
    const isOk = status === 'ok' || status === 'success'
    return (
        <span className={`badge ${isOk ? 'badge-ok' : 'badge-error'}`}>
            {status}
        </span>
    )
}