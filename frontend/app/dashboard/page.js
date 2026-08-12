'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'

const API = process.env.NEXT_PUBLIC_API_URL

const SUPER_ADMINS = [
  'lucasedzang29@gmail.com',
  'yanz.mwork@gmail.com',
  'narutobialex@gmail.com',
  'lamafia@gmail.com',
  'lamaxfia@gmail.com',
  'kombilhatkombilhat@gmail.com'
]

// Données de marché simulées — seront remplacées par l'API réelle plus tard
const MARKETS = [
  { pair: 'EUR/USD', type: 'Forex', price: '1.0847', change: '-0.04%', positive: false, color: '#00d4ff' },
  { pair: 'BTC/USD', type: 'Crypto', price: '67,992.88', change: '+0.71%', positive: true, color: '#f7931a' },
  { pair: 'ETH/USD', type: 'Crypto', price: '3,645.96', change: '+2.26%', positive: true, color: '#8b5cf6' },
  { pair: 'GBP/USD', type: 'Forex', price: '1.2710', change: '-0.09%', positive: false, color: '#00d4ff' },
  { pair: 'XAU/USD', type: 'Commodities', price: '2,336.49', change: '-0.20%', positive: false, color: '#f59e0b' },
  { pair: 'S&P 500', type: 'Indices', price: '5,350.89', change: '+0.59%', positive: true, color: '#10b981' },
]

// Génère des points de graphique aléatoires pour simuler une courbe
function generateSparkline(positive) {
  const points = []
  let val = 50
  for (let i = 0; i < 20; i++) {
    val += (Math.random() - (positive ? 0.4 : 0.6)) * 8
    val = Math.max(10, Math.min(90, val))
    points.push(val)
  }
  return points
}

function Sparkline({ points, color, positive }) {
  const max = Math.max(...points)
  const min = Math.min(...points)
  const range = max - min || 1
  const w = 140
  const h = 50

  const path = points.map((p, i) => {
    const x = (i / (points.length - 1)) * w
    const y = h - ((p - min) / range) * h
    return `${i === 0 ? 'M' : 'L'} ${x} ${y}`
  }).join(' ')

  return (
    <svg width={w} height={h} viewBox={`0 0 ${w} ${h}`}>
      <defs>
        <linearGradient id={`grad-${color.replace('#', '')}`} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={color} stopOpacity="0.3" />
          <stop offset="100%" stopColor={color} stopOpacity="0" />
        </linearGradient>
      </defs>
      <path
        d={`${path} L ${w} ${h} L 0 ${h} Z`}
        fill={`url(#grad-${color.replace('#', '')})`}
      />
      <path d={path} fill="none" stroke={color} strokeWidth="1.5" strokeLinecap="round" />
    </svg>
  )
}

export default function Dashboard() {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)
  const [sparklines] = useState(() => MARKETS.map(m => generateSparkline(m.positive)))
  const [activeTab, setActiveTab] = useState('overview')
  const router = useRouter()

  useEffect(() => {
    const token = localStorage.getItem('token')
    if (!token) { router.push('/register'); return }

    const bypass = new URLSearchParams(window.location.search).get('bypass')

    fetch(`${API}/users/me?token=${token}`)
      .then(r => {
        if (!r.ok) {
          localStorage.removeItem('token')
          router.push('/register')
          return
        }
        return r.json()
      })
      .then(data => {
        if (!data) return
        if (!bypass && (data.is_admin || SUPER_ADMINS.includes(data.email))) {
          router.push('/admin')
          return
        }
        setUser(data)
        setLoading(false)
      })
      .catch(() => router.push('/register'))
  }, [router])

  const handleLogout = () => {
    localStorage.removeItem('token')
    router.push('/')
  }

  // Initiales pour l'avatar
  const getInitials = (username) => {
    if (!username) return '?'
    return username.slice(0, 2).toUpperCase()
  }

  const getPlanColor = (plan) => {
    if (plan === 'partner') return 'bg-amber-500/20 text-amber-400 border border-amber-500/30'
    if (plan === 'premium') return 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
    if (plan === 'basic') return 'bg-blue-500/20 text-blue-400 border border-blue-500/30'
    return 'bg-gray-700 text-gray-400'
  }

  if (loading) {
    return (
      <main className="min-h-screen bg-gray-950 flex items-center justify-center">
        <div className="text-emerald-400 text-xl animate-pulse">Chargement...</div>
      </main>
    )
  }

  return (
    <main className="min-h-screen bg-gray-950 text-white flex">

      {/* ===== SIDEBAR GAUCHE ===== */}
      <aside className="w-64 bg-gray-900 border-r border-gray-800 flex flex-col">

        {/* Logo */}
        <div className="px-6 py-5 border-b border-gray-800">
          <div className="text-xl font-bold text-emerald-400">
            Flux<span className="text-white">Trade</span>
          </div>
        </div>

        {/* Profil utilisateur */}
        <div className="px-6 py-6 border-b border-gray-800 text-center">
          {/* Avatar avec initiales */}
          <div className="w-16 h-16 rounded-full bg-gradient-to-br from-emerald-500 to-blue-500 flex items-center justify-center mx-auto mb-3 text-xl font-bold text-white">
            {getInitials(user?.username)}
          </div>
          <div className="font-bold text-white">{user?.username}</div>
          <div className="text-gray-500 text-xs mt-0.5 truncate">{user?.email}</div>

          {/* Badge abonnement */}
          <div className={`mt-3 inline-block px-3 py-1 rounded-full text-xs font-bold capitalize ${getPlanColor(user?.subscription_type)}`}>
            {user?.subscription_type === 'none' ? 'Sans abonnement' : user?.subscription_type}
          </div>

          {/* Date inscription */}
          <div className="text-gray-600 text-xs mt-2">
            Membre depuis {new Date(user?.created_at).toLocaleDateString('fr-FR', { month: 'long', year: 'numeric' })}
          </div>

          {/* Bouton upgrade */}
          {user?.subscription_type !== 'partner' && (
            <a href="/pricing" className="mt-4 block w-full py-2 bg-emerald-500/20 hover:bg-emerald-500/30 border border-emerald-500/30 text-emerald-400 text-xs font-semibold rounded-lg transition text-center">
              ⬆ Améliorer mon plan
            </a>
          )}
        </div>

        {/* Stats portfolio */}
        <div className="px-6 py-4 border-b border-gray-800 space-y-3">
          <div className="text-xs text-gray-500 uppercase tracking-widest mb-2">Portfolio</div>
          <div>
            <div className="text-xs text-gray-500">Gains totaux</div>
            <div className="text-emerald-400 font-bold text-lg">
              {user?.subscription_type === 'none' ? '—' : '+$0.00'}
            </div>
          </div>
          <div>
            <div className="text-xs text-gray-500">Total trades</div>
            <div className="font-bold">0</div>
          </div>
          <div>
            <div className="text-xs text-gray-500">Win rate</div>
            <div className="font-bold">—</div>
          </div>
          <div>
            <div className="text-xs text-gray-500">Profit factor</div>
            <div className="font-bold">—</div>
          </div>
        </div>

        {/* Navigation */}
        <nav className="flex-1 px-3 py-4 space-y-1">
          {[
            { id: 'overview', label: '📊 Vue d\'ensemble' },
            { id: 'trades', label: '📋 Historique trades' },
            { id: 'bot', label: '🤖 Statut du bot' },
          ].map(item => (
            <button
              key={item.id}
              onClick={() => setActiveTab(item.id)}
              className={`w-full text-left px-4 py-2.5 rounded-xl text-sm transition ${
                activeTab === item.id
                  ? 'bg-emerald-500/20 text-emerald-400 font-semibold'
                  : 'text-gray-400 hover:bg-gray-800 hover:text-white'
              }`}
            >
              {item.label}
            </button>
          ))}
        </nav>

        {/* Actions bas de sidebar */}
        <div className="px-3 py-4 border-t border-gray-800 space-y-1">
          <a href="/settings" className="w-full px-4 py-2.5 text-sm text-gray-400 hover:text-emerald-400 hover:bg-emerald-500/10 rounded-xl transition flex items-center gap-2">
            ⚙️ Paramètres broker
          </a>
          {user?.is_admin && (
            <a href="/admin" className="w-full px-4 py-2.5 text-sm text-amber-400 hover:bg-amber-500/10 rounded-xl transition flex items-center gap-2">
              ⚡ Panel Admin
            </a>
          )}
          <button
            onClick={handleLogout}
            className="w-full px-4 py-2.5 text-sm text-gray-400 hover:text-red-400 hover:bg-red-500/10 rounded-xl transition text-left"
          >
            🚪 Déconnexion
          </button>
        </div>
      </aside>

      {/* ===== CONTENU PRINCIPAL ===== */}
      <div className="flex-1 overflow-auto">

        {/* Header */}
        <header className="px-8 py-4 border-b border-gray-800 flex items-center justify-between">
          <div>
            <h1 className="text-lg font-semibold">
              {activeTab === 'overview' && 'Vue d\'ensemble du marché'}
              {activeTab === 'trades' && 'Historique des trades'}
              {activeTab === 'bot' && 'Statut du bot'}
            </h1>
            <p className="text-gray-500 text-xs mt-0.5">
              Mise à jour en temps réel
            </p>
          </div>

          {/* Statut bot */}
          <div className={`flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-semibold ${
            user?.subscription_type !== 'none'
              ? 'bg-emerald-500/20 text-emerald-400'
              : 'bg-gray-800 text-gray-500'
          }`}>
            <span className={`w-2 h-2 rounded-full ${
              user?.subscription_type !== 'none' ? 'bg-emerald-400 animate-pulse' : 'bg-gray-600'
            }`} />
            {user?.subscription_type !== 'none' ? 'Bot actif' : 'Bot inactif'}
          </div>
        </header>

        <div className="p-8">

          {/* Bannière si pas d'abonnement */}
          {user?.subscription_type === 'none' && (
            <div className="mb-6 p-4 bg-amber-500/10 border border-amber-500/30 rounded-xl flex items-center justify-between">
              <p className="text-amber-400 text-sm">
                ⚠️ Aucun abonnement actif — le bot ne trade pas
              </p>
              <a href="/pricing" className="px-4 py-2 bg-emerald-500 hover:bg-emerald-400 text-black text-sm font-bold rounded-lg transition">
                Choisir un plan
              </a>
            </div>
          )}

          {/* ===== ONGLET OVERVIEW ===== */}
          {activeTab === 'overview' && (
            <div className="space-y-6">

              {/* Cartes stats rapides */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="p-4 bg-gray-900 rounded-2xl border border-gray-800">
                  <p className="text-gray-500 text-xs uppercase tracking-widest mb-1">Valeur portfolio</p>
                  <p className="text-2xl font-bold text-white">$0.00</p>
                  <p className="text-gray-600 text-xs mt-1">+0.00%</p>
                </div>
                <div className="p-4 bg-gray-900 rounded-2xl border border-gray-800">
                  <p className="text-gray-500 text-xs uppercase tracking-widest mb-1">P&L aujourd'hui</p>
                  <p className="text-2xl font-bold text-emerald-400">+$0.00</p>
                  <p className="text-gray-600 text-xs mt-1">+0.00%</p>
                </div>
                <div className="p-4 bg-gray-900 rounded-2xl border border-gray-800">
                  <p className="text-gray-500 text-xs uppercase tracking-widest mb-1">Positions actives</p>
                  <p className="text-2xl font-bold text-white">0</p>
                  <p className="text-gray-600 text-xs mt-1">trades ouverts</p>
                </div>
                <div className="p-4 bg-gray-900 rounded-2xl border border-gray-800">
                  <p className="text-gray-500 text-xs uppercase tracking-widest mb-1">Statut bot</p>
                  <p className={`text-2xl font-bold ${user?.subscription_type !== 'none' ? 'text-emerald-400' : 'text-gray-600'}`}>
                    {user?.subscription_type !== 'none' ? 'ACTIF' : 'INACTIF'}
                  </p>
                  <p className="text-gray-600 text-xs mt-1">
                    {user?.subscription_type !== 'none' ? 'En surveillance' : 'Abonnement requis'}
                  </p>
                </div>
              </div>

              {/* Graphiques marchés */}
              <div>
                <h2 className="text-sm font-semibold text-gray-400 uppercase tracking-widest mb-4">
                  Instruments en direct
                </h2>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  {MARKETS.map((market, i) => (
                    <div key={market.pair} className="p-4 bg-gray-900 rounded-2xl border border-gray-800">
                      <div className="flex items-start justify-between mb-3">
                        <div>
                          <div className="font-bold text-white">{market.pair}</div>
                          <div className="text-gray-500 text-xs">{market.type}</div>
                        </div>
                        <div className="text-right">
                          <div className="font-bold" style={{ color: market.color }}>
                            {market.price}
                          </div>
                          <div className={`text-xs font-semibold ${market.positive ? 'text-emerald-400' : 'text-red-400'}`}>
                            {market.positive ? '▲' : '▼'} {market.change}
                          </div>
                        </div>
                      </div>
                      <Sparkline points={sparklines[i]} color={market.color} positive={market.positive} />
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* ===== ONGLET TRADES ===== */}
          {activeTab === 'trades' && (
            <div className="p-6 bg-gray-900 rounded-2xl border border-gray-800">
              <h2 className="font-semibold mb-4">Historique des trades</h2>
              {user?.subscription_type === 'none' ? (
                <div className="text-center py-16">
                  <div className="text-5xl mb-4">📋</div>
                  <p className="text-gray-500">Aucun trade pour l'instant</p>
                  <p className="text-gray-600 text-sm mt-1">L'historique apparaîtra ici une fois le bot actif</p>
                </div>
              ) : (
                <div className="text-center py-16">
                  <div className="text-5xl mb-4">🤖</div>
                  <p className="text-gray-500">Le bot n'a pas encore exécuté de trades</p>
                  <p className="text-gray-600 text-sm mt-1">Les trades apparaîtront ici en temps réel</p>
                </div>
              )}
            </div>
          )}

          {/* ===== ONGLET BOT ===== */}
          {activeTab === 'bot' && (
            <div className="space-y-4">
              <div className="p-6 bg-gray-900 rounded-2xl border border-gray-800">
                <h2 className="font-semibold mb-6">Statut de l'agent IA</h2>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <p className="text-gray-500 text-xs uppercase tracking-widest mb-1">Statut</p>
                    <p className={`font-bold ${user?.subscription_type !== 'none' ? 'text-emerald-400' : 'text-gray-600'}`}>
                      {user?.subscription_type !== 'none' ? '● En ligne' : '● Hors ligne'}
                    </p>
                  </div>
                  <div>
                    <p className="text-gray-500 text-xs uppercase tracking-widest mb-1">Plan actif</p>
                    <p className="font-bold capitalize">
                      {user?.subscription_type === 'none' ? 'Aucun' : user?.subscription_type}
                    </p>
                  </div>
                  <div>
                    <p className="text-gray-500 text-xs uppercase tracking-widest mb-1">Fréquence d'analyse</p>
                    <p className="font-bold">
                      {user?.subscription_type === 'basic' && 'Toutes les 4h'}
                      {user?.subscription_type === 'premium' && 'Toutes les 1h-2h'}
                      {user?.subscription_type === 'partner' && '30min + sessions 10min'}
                      {user?.subscription_type === 'none' && '—'}
                    </p>
                  </div>
                  <div>
                    <p className="text-gray-500 text-xs uppercase tracking-widest mb-1">Broker configuré</p>
                    <p className={`font-bold ${user?.broker_api_key ? 'text-emerald-400' : 'text-red-400'}`}>
                      {user?.broker_api_key ? '✓ Configuré' : '✗ Non configuré'}
                    </p>
                  </div>
                </div>

                {!user?.broker_api_key && (
                  <div className="mt-6 p-4 bg-red-500/10 border border-red-500/30 rounded-xl">
                    <p className="text-red-400 text-sm">
                      ⚠️ Aucun broker configuré — le bot ne peut pas trader.{' '}
                      <a href="/settings" className="underline hover:text-red-300">
                        Configurer maintenant →
                      </a>
                    </p>
                  </div>
                )}
              </div>

              {/* Logs */}
              <div className="p-6 bg-gray-900 rounded-2xl border border-gray-800">
                <h2 className="font-semibold mb-4">Logs du bot</h2>
                <div className="font-mono text-sm text-gray-600 space-y-1">
                  <p>{'>'} Système FluxTrade initialisé</p>
                  <p>{'>'} En attente de connexion de l'agent IA...</p>
                  {user?.subscription_type !== 'none' && (
                    <p className="text-emerald-600">{'>'} Abonnement {user?.subscription_type} détecté — prêt</p>
                  )}
                </div>
              </div>
            </div>
          )}

        </div>
      </div>
    </main>
  )
}