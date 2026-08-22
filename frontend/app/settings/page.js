'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'

const API = process.env.NEXT_PUBLIC_API_URL

export default function SettingsPage() {
  const [user, setUser] = useState(null)
  const [accountId, setAccountId] = useState('')
  const [newUsername, setNewUsername] = useState('')
  const [loading, setLoading] = useState(false)
  const [message, setMessage] = useState({ text: '', type: '' })
  const router = useRouter()

  useEffect(() => {
    const token = localStorage.getItem('token')
    if (!token) { router.push('/register'); return }

    fetch(`${API}/users/me?token=${token}`)
      .then(r => r.json())
      .then(data => {
        setUser(data)
        if (data.broker_api_key) {
          try {
            const creds = JSON.parse(data.broker_api_key)
            setAccountId(creds.metaapi_account_id || '')
          } catch {}
        }
      })
      .catch(() => router.push('/register'))
  }, [router])

  const showMessage = (text, type = 'success') => {
    setMessage({ text, type })
    setTimeout(() => setMessage({ text: '', type: '' }), 3000)
  }

  const handleUsernameChange = async () => {
    const token = localStorage.getItem('token')
    if (!newUsername) return

    const res = await fetch(`${API}/users/me/username?token=${token}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username: newUsername })
    })
    const data = await res.json()
    if (res.ok) {
      setUser(data)
      setNewUsername('')
      showMessage('Nom d\'utilisateur mis à jour !')
    } else {
      showMessage(data.detail || 'Erreur', 'error')
    }
  }

  const handleSave = async () => {
    const token = localStorage.getItem('token')
    if (!accountId) {
      showMessage('Veuillez entrer votre Account ID MetaApi', 'error')
      return
    }

    setLoading(true)
    try {
      const res = await fetch(`${API}/users/me/broker?token=${token}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ metaapi_account_id: accountId })
      })

      if (res.ok) {
        showMessage('Compte broker connecté avec succès !')
        const updated = await res.json()
        setUser(updated)
        await fetch(`${API}/agent/start?token=${token}`, { method: 'POST' })
      } else {
        const data = await res.json()
        showMessage(data.detail || 'Erreur', 'error')
      }
    } catch {
      showMessage('Impossible de contacter le serveur', 'error')
    }
    setLoading(false)
  }

  return (
    <main className="min-h-screen bg-gray-950 text-white">
      <nav className="flex items-center justify-between px-8 py-4 border-b border-gray-800">
        <div className="text-2xl font-bold text-emerald-400">
          Flux<span className="text-white">Trade</span>
        </div>
        <a href="/dashboard" className="text-sm text-gray-400 hover:text-white">
          ← Dashboard
        </a>
      </nav>

      <div className="max-w-2xl mx-auto px-8 py-12">
        <h1 className="text-3xl font-bold mb-2">Connexion broker</h1>
        <p className="text-gray-400 mb-8">
          Connecte ton compte MT5 via MetaApi — aucune installation requise
        </p>

        {user?.subscription_type === 'none' && (
          <div className="mb-6 p-4 bg-amber-500/10 border border-amber-500/30 rounded-xl text-amber-400 text-sm">
            ⚠️ Aucun abonnement actif.{' '}
            <a href="/pricing" className="underline">Choisir un plan →</a>
          </div>
        )}

        {/* Changer le nom d'utilisateur */}
        <div className="mb-6 p-6 bg-gray-900 rounded-2xl border border-gray-800">
          <h2 className="font-semibold mb-4">Nom d'utilisateur</h2>
          <p className="text-gray-500 text-sm mb-4">Actuel : {user?.username}</p>
          <div className="flex gap-3">
            <input
              type="text"
              value={newUsername}
              onChange={e => setNewUsername(e.target.value)}
              placeholder="Nouveau nom d'utilisateur"
              className="flex-1 bg-gray-800 border border-gray-700 rounded-xl px-4 py-3 text-white placeholder-gray-600 focus:outline-none focus:border-emerald-500 transition"
            />
            <button
              onClick={handleUsernameChange}
              className="px-6 py-3 bg-gray-700 hover:bg-gray-600 text-white font-semibold rounded-xl transition"
            >
              Modifier
            </button>
          </div>
        </div>

        {/* Statut */}
        <div className="mb-6 p-4 bg-gray-900 rounded-xl border border-gray-800 flex items-center gap-3">
          <div className={`w-3 h-3 rounded-full ${user?.broker_api_key ? 'bg-emerald-400 animate-pulse' : 'bg-red-400'}`} />
          <span className="text-sm text-gray-300">
            {user?.broker_api_key ? '✓ Broker connecté via MetaApi' : 'Aucun broker connecté'}
          </span>
        </div>

        {/* Guide étapes */}
        <div className="mb-8 p-6 bg-gray-900 rounded-2xl border border-gray-800">
          <h2 className="font-semibold mb-4">Comment connecter ton broker ?</h2>
          <ol className="space-y-3 text-sm text-gray-400">
            <li className="flex gap-3">
              <span className="w-6 h-6 bg-emerald-500/20 text-emerald-400 rounded-full flex items-center justify-center text-xs font-bold flex-shrink-0">1</span>
              <span>Va sur <a href="https://metaapi.cloud" target="_blank" className="text-emerald-400 underline">metaapi.cloud</a> et crée un compte gratuit</span>
            </li>
            <li className="flex gap-3">
              <span className="w-6 h-6 bg-emerald-500/20 text-emerald-400 rounded-full flex items-center justify-center text-xs font-bold flex-shrink-0">2</span>
              <span>Clique sur <strong className="text-white">"Connect MT5 account"</strong> et entre les credentials de ton broker</span>
            </li>
            <li className="flex gap-3">
              <span className="w-6 h-6 bg-emerald-500/20 text-emerald-400 rounded-full flex items-center justify-center text-xs font-bold flex-shrink-0">3</span>
              <span>Copie l'<strong className="text-white">Account ID</strong> généré et colle-le ci-dessous</span>
            </li>
          </ol>
        </div>

        {/* Formulaire */}
        <div className="p-6 bg-gray-900 rounded-2xl border border-gray-800 space-y-4">
          <div>
            <label className="block text-xs text-gray-500 uppercase tracking-widest mb-2">
              MetaApi Account ID
            </label>
            <input
              type="text"
              value={accountId}
              onChange={e => setAccountId(e.target.value)}
              placeholder="ex: abc123def456..."
              className="w-full bg-gray-800 border border-gray-700 rounded-xl px-4 py-3 text-white placeholder-gray-600 focus:outline-none focus:border-emerald-500 transition font-mono text-sm"
            />
          </div>

          {message.text && (
            <div className={`p-3 rounded-xl text-sm ${
              message.type === 'success'
                ? 'bg-emerald-500/10 border border-emerald-500/30 text-emerald-400'
                : 'bg-red-500/10 border border-red-500/30 text-red-400'
            }`}>
              {message.text}
            </div>
          )}

          <button
            onClick={handleSave}
            disabled={loading}
            className="w-full py-3 bg-emerald-500 hover:bg-emerald-400 disabled:opacity-50 text-black font-bold rounded-xl transition"
          >
            {loading ? 'Connexion...' : 'Connecter mon broker'}
          </button>
        </div>

        {/* Sécurité */}
        <div className="mt-6 p-6 bg-gray-900 rounded-2xl border border-gray-800">
          <h2 className="font-semibold mb-4">🔒 Sécurité</h2>
          <ul className="space-y-2 text-gray-400 text-sm">
            <li>✅ Tes credentials restent sur MetaApi — FluxTrade ne les voit jamais</li>
            <li>✅ FluxTrade ne peut que trader — jamais retirer des fonds</li>
            <li>✅ Tu peux révoquer l'accès depuis MetaApi à tout moment</li>
            <li>⚠️ Commence toujours sur un compte démo avant le réel</li>
          </ul>
        </div>

        {/* Danger zone */}
        <div className="mt-6 p-6 bg-red-500/5 rounded-2xl border border-red-500/20">
          <h2 className="font-semibold text-red-400 mb-2">Zone dangereuse</h2>
          <p className="text-gray-500 text-sm mb-4">
            La suppression de ton compte est irréversible. Tous tes trades et données seront perdus.
          </p>
          <button
            onClick={async () => {
              if (!confirm('Es-tu sûr ? Cette action est irréversible.')) return
              if (!confirm('Dernière confirmation — supprimer définitivement ton compte ?')) return
              const token = localStorage.getItem('token')
              const res = await fetch(`${API}/users/me?token=${token}`, { method: 'DELETE' })
              if (res.ok) {
                localStorage.removeItem('token')
                window.location.href = '/'
              }
            }}
            className="px-6 py-3 bg-red-500/20 hover:bg-red-500/30 text-red-400 border border-red-500/30 rounded-xl text-sm font-semibold transition"
          >
            🗑️ Supprimer mon compte définitivement
          </button>
        </div>
      </div>
    </main>
  )
}