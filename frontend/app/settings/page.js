'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'

const API = process.env.NEXT_PUBLIC_API_URL

const BROKERS = [
  { id: 'alpaca', name: 'Alpaca', type: 'Stocks & Crypto', logo: '📈', fields: ['API Key', 'API Secret'] },
  { id: 'binance', name: 'Binance', type: 'Crypto', logo: '🟡', fields: ['API Key', 'API Secret'] },
  { id: 'mt5', name: 'MetaTrader 5', type: 'Forex & CFD', logo: '📊', fields: ['Login', 'Password', 'Server'] },
  { id: 'oanda', name: 'OANDA', type: 'Forex', logo: '💱', fields: ['API Key', 'Account ID'] },
]

export default function SettingsPage() {
  const [user, setUser] = useState(null)
  const [selectedBroker, setSelectedBroker] = useState(null)
  const [apiKey, setApiKey] = useState('')
  const [apiSecret, setApiSecret] = useState('')
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
        if (data.broker_api_key) setApiKey(data.broker_api_key)
        if (data.broker_api_secret) setApiSecret(data.broker_api_secret)
      })
      .catch(() => router.push('/register'))
  }, [router])

  const showMessage = (text, type = 'success') => {
    setMessage({ text, type })
    setTimeout(() => setMessage({ text: '', type: '' }), 3000)
  }

  const handleSave = async () => {
    const token = localStorage.getItem('token')
    if (!apiKey || !apiSecret) {
      showMessage('Veuillez remplir tous les champs', 'error')
      return
    }

    setLoading(true)

    try {
      const res = await fetch(`${API}/users/me/broker?token=${token}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          broker_api_key: apiKey,
          broker_api_secret: apiSecret
        })
      })

      if (res.ok) {
        showMessage('Clés broker sauvegardées avec succès !')
      } else {
        showMessage('Erreur lors de la sauvegarde', 'error')
      }
    } catch {
      showMessage('Impossible de contacter le serveur', 'error')
    }

    setLoading(false)
  }

  return (
    <main className="min-h-screen bg-gray-950 text-white">

      {/* Navbar */}
      <nav className="flex items-center justify-between px-8 py-4 border-b border-gray-800">
        <div className="text-2xl font-bold text-emerald-400">
          Flux<span className="text-white">Trade</span>
        </div>
        <div className="flex items-center gap-4">
          <a href="/dashboard" className="text-sm text-gray-400 hover:text-white transition">
            ← Dashboard
          </a>
        </div>
      </nav>

      <div className="max-w-4xl mx-auto px-8 py-12">
        <h1 className="text-3xl font-bold mb-2">Paramètres</h1>
        <p className="text-gray-400 mb-12">Configure ton broker pour activer le trading automatique</p>

        {/* Alerte si pas d'abonnement */}
        {user?.subscription_type === 'none' && (
          <div className="mb-8 p-4 bg-amber-500/10 border border-amber-500/30 rounded-xl text-amber-400 text-sm">
            ⚠️ Tu n'as pas d'abonnement actif. Le bot ne pourra pas trader même avec des clés configurées.{' '}
            <a href="/pricing" className="underline hover:text-amber-300">Choisir un plan →</a>
          </div>
        )}

        {/* Sélection du broker */}
        <div className="mb-8">
          <h2 className="text-lg font-semibold mb-4">1. Choisis ton broker</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {BROKERS.map(broker => (
              <button
                key={broker.id}
                onClick={() => setSelectedBroker(broker)}
                className={`p-4 rounded-xl border-2 text-left transition ${
                  selectedBroker?.id === broker.id
                    ? 'border-emerald-500 bg-emerald-500/10'
                    : 'border-gray-700 bg-gray-900 hover:border-gray-500'
                }`}
              >
                <div className="text-2xl mb-2">{broker.logo}</div>
                <div className="font-semibold text-sm">{broker.name}</div>
                <div className="text-gray-500 text-xs">{broker.type}</div>
              </button>
            ))}
          </div>
        </div>

        {/* Formulaire clés API */}
        {selectedBroker && (
          <div className="p-6 bg-gray-900 rounded-2xl border border-gray-800 mb-8">
            <h2 className="text-lg font-semibold mb-2">
              2. Entre tes clés {selectedBroker.name}
            </h2>
            <p className="text-gray-500 text-sm mb-6">
              Tes clés sont chiffrées et stockées de manière sécurisée. 
              Utilise des clés avec permission de trading uniquement — jamais de permission de retrait.
            </p>

            <div className="space-y-4 max-w-lg">
              <div>
                <label className="block text-xs text-gray-500 uppercase tracking-widest mb-2">
                  API Key
                </label>
                <input
                  type="text"
                  value={apiKey}
                  onChange={e => setApiKey(e.target.value)}
                  placeholder="Colle ta clé API ici"
                  className="w-full bg-gray-800 border border-gray-700 rounded-xl px-4 py-3 text-white placeholder-gray-600 focus:outline-none focus:border-emerald-500 transition font-mono text-sm"
                />
              </div>

              <div>
                <label className="block text-xs text-gray-500 uppercase tracking-widest mb-2">
                  API Secret
                </label>
                <input
                  type="password"
                  value={apiSecret}
                  onChange={e => setApiSecret(e.target.value)}
                  placeholder="Colle ton secret API ici"
                  className="w-full bg-gray-800 border border-gray-700 rounded-xl px-4 py-3 text-white placeholder-gray-600 focus:outline-none focus:border-emerald-500 transition font-mono text-sm"
                />
              </div>

              {/* Message retour */}
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
                className="px-8 py-3 bg-emerald-500 hover:bg-emerald-400 disabled:opacity-50 text-black font-bold rounded-xl transition"
              >
                {loading ? 'Sauvegarde...' : 'Sauvegarder les clés'}
              </button>
            </div>
          </div>
        )}

        {/* Infos sécurité */}
        <div className="p-6 bg-gray-900 rounded-2xl border border-gray-800">
          <h2 className="text-lg font-semibold mb-4">🔒 Sécurité de tes clés</h2>
          <ul className="space-y-3 text-gray-400 text-sm">
            <li>✅ Tes clés sont chiffrées en base de données</li>
            <li>✅ Elles ne sont jamais affichées en clair après sauvegarde</li>
            <li>✅ Le bot utilise uniquement les permissions de trading</li>
            <li>⚠️ Ne donne jamais de permission de retrait à tes clés API</li>
            <li>⚠️ En cas de problème, révoque tes clés directement sur le site de ton broker</li>
          </ul>
        </div>

      </div>
    </main>
  )
}