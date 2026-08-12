'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'

const API = process.env.NEXT_PUBLIC_API_URL

export default function AdminPanel() {
  const [user, setUser] = useState(null)
  const [token, setToken] = useState('')
  const [activeTab, setActiveTab] = useState('dashboard')
  const [users, setUsers] = useState([])
  const [stats, setStats] = useState(null)
  const [search, setSearch] = useState('')
  const [selectedUser, setSelectedUser] = useState(null)
  const [loading, setLoading] = useState(true)
  const [message, setMessage] = useState({ text: '', type: '' })
  const router = useRouter()

  const SUPER_ADMINS = [
    'lucasedzang29@gmail.com',
    'yanz.mwork@gmail.com',
    'narutobialex@gmail.com',
    'lamafia@gmail.com',
    'lamaxfia@gmail.com',
    'kombilhatkombilhat@gmail.com'
  ]

  // Vérifie que l'utilisateur est admin au chargement
  useEffect(() => {
    const t = localStorage.getItem('token')
    if (!t) { router.push('/register'); return }
    setToken(t)

    fetch(`${API}/users/me?token=${t}`)
      .then(r => r.json())
      .then(data => {
        if (!data.is_admin && !SUPER_ADMINS.includes(data.email)) {
          router.push('/dashboard')
          return
        }
        setUser(data)
        setLoading(false)
        fetchStats(t)
        fetchUsers(t)
      })
      .catch(() => router.push('/register'))
  }, [])

  const fetchStats = (t) => {
    fetch(`${API}/admin/stats?token=${t}`)
      .then(r => r.json())
      .then(setStats)
  }

  const fetchUsers = (t, q = '') => {
    const url = q
      ? `${API}/admin/users?token=${t}&search=${q}`
      : `${API}/admin/users?token=${t}`
    fetch(url)
      .then(r => r.json())
      .then(setUsers)
  }

  const showMessage = (text, type = 'success') => {
    setMessage({ text, type })
    setTimeout(() => setMessage({ text: '', type: '' }), 3000)
  }

  const handleSearch = (e) => {
    setSearch(e.target.value)
    fetchUsers(token, e.target.value)
  }

  const updateSubscription = async (userId, type, days = 30) => {
    const res = await fetch(`${API}/admin/users/${userId}/subscription?token=${token}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ subscription_type: type, duration_days: days })
    })
    if (res.ok) {
      showMessage('Abonnement mis à jour')
      fetchUsers(token, search)
      fetchStats(token)
      if (selectedUser?.id === userId) {
        setSelectedUser({ ...selectedUser, subscription_type: type })
      }
    }
  }

  const banUser = async (userId, reason) => {
    const res = await fetch(`${API}/admin/users/${userId}/ban?token=${token}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ reason })
    })
    if (res.ok) {
      showMessage('Utilisateur banni', 'warning')
      fetchUsers(token, search)
      setSelectedUser(null)
    }
  }

  const unbanUser = async (userId) => {
    const res = await fetch(`${API}/admin/users/${userId}/unban?token=${token}`, {
      method: 'PUT'
    })
    if (res.ok) {
      showMessage('Ban levé')
      fetchUsers(token, search)
    }
  }

  const grantAdmin = async (userId) => {
    const res = await fetch(`${API}/admin/users/${userId}/grant-admin?token=${token}`, {
      method: 'PUT'
    })
    if (res.ok) {
      showMessage('Droits admin attribués')
      fetchUsers(token, search)
    }
  }

  const revokeAdmin = async (userId) => {
    const res = await fetch(`${API}/admin/users/${userId}/revoke-admin?token=${token}`, {
      method: 'PUT'
    })
    if (res.ok) {
      showMessage('Droits admin retirés', 'warning')
      fetchUsers(token, search)
    } else {
      const data = await res.json()
      showMessage(data.detail, 'error')
    }
  }

  if (loading) {
    return (
      <main className="min-h-screen bg-gray-950 flex items-center justify-center">
        <div className="text-emerald-400 text-xl">Vérification des droits...</div>
      </main>
    )
  }

  const isSuperAdmin = SUPER_ADMINS.includes(user?.email)

  return (
    <main className="min-h-screen bg-gray-950 text-white flex">

      {/* ===== SIDEBAR ===== */}
      <aside className="w-64 bg-gray-900 border-r border-gray-800 flex flex-col">
        {/* Logo */}
        <div className="px-6 py-5 border-b border-gray-800">
          <div className="text-xl font-bold text-emerald-400">
            Flux<span className="text-white">Trade</span>
          </div>
          <div className="text-xs text-gray-500 mt-0.5">Panel Administration</div>
        </div>

        {/* Infos admin connecté */}
        <div className="px-6 py-4 border-b border-gray-800">
          <div className="text-sm font-semibold text-white">{user?.username}</div>
          <div className="text-xs text-gray-500 mt-0.5">{user?.email}</div>
          <div className={`mt-2 inline-block px-2 py-0.5 rounded text-xs font-bold ${
            isSuperAdmin ? 'bg-amber-500/20 text-amber-400' : 'bg-emerald-500/20 text-emerald-400'
          }`}>
            {isSuperAdmin ? '⚡ Super Admin' : '🛡️ Admin'}
          </div>
        </div>

        {/* Navigation */}
        <nav className="flex-1 px-3 py-4 space-y-1">
          {[
            { id: 'dashboard', label: '📊 Dashboard', },
            { id: 'users', label: '👥 Utilisateurs', },
            { id: 'subscriptions', label: '💳 Abonnements', },
            { id: 'announcements', label: '📢 Annonces', },
            { id: 'logs', label: '📋 Logs', },
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

        {/* Lien dashboard personnel */}
        <div className="px-3 pb-2">
          <a href="/dashboard?bypass=true" className="w-full px-4 py-2.5 text-sm text-gray-400 hover:text-emerald-400 hover:bg-emerald-500/10 rounded-xl transition flex items-center gap-2">
            📈 Mon dashboard trading
          </a>
        </div>

        {/* Bouton déconnexion */}
        <div className="px-3 py-4 border-t border-gray-800">
          <button
            onClick={() => { localStorage.removeItem('token'); router.push('/') }}
            className="w-full px-4 py-2.5 text-sm text-gray-400 hover:text-red-400 hover:bg-red-500/10 rounded-xl transition text-left"
          >
            🚪 Déconnexion
          </button>
        </div>
      </aside>

      {/* ===== CONTENU PRINCIPAL ===== */}
      <div className="flex-1 flex flex-col overflow-hidden">

        {/* Header */}
        <header className="px-8 py-4 border-b border-gray-800 flex items-center justify-between">
          <h1 className="text-lg font-semibold">
            {activeTab === 'dashboard' && 'Vue d\'ensemble'}
            {activeTab === 'users' && 'Gestion des utilisateurs'}
            {activeTab === 'subscriptions' && 'Gestion des abonnements'}
            {activeTab === 'announcements' && 'Annonces'}
            {activeTab === 'logs' && 'Logs d\'activité'}
          </h1>

          {/* Message de confirmation */}
          {message.text && (
            <div className={`px-4 py-2 rounded-lg text-sm font-semibold ${
              message.type === 'success' ? 'bg-emerald-500/20 text-emerald-400' :
              message.type === 'warning' ? 'bg-amber-500/20 text-amber-400' :
              'bg-red-500/20 text-red-400'
            }`}>
              {message.text}
            </div>
          )}
        </header>

        <div className="flex-1 overflow-auto p-8">

          {/* ===== ONGLET DASHBOARD ===== */}
          {activeTab === 'dashboard' && stats && (
            <div className="space-y-6">
              {/* Cartes stats */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="p-6 bg-gray-900 rounded-2xl border border-gray-800">
                  <p className="text-gray-500 text-xs uppercase tracking-widest mb-2">Total utilisateurs</p>
                  <p className="text-3xl font-bold text-white">{stats.total_users}</p>
                </div>
                <div className="p-6 bg-gray-900 rounded-2xl border border-gray-800">
                  <p className="text-gray-500 text-xs uppercase tracking-widest mb-2">Abonnés actifs</p>
                  <p className="text-3xl font-bold text-emerald-400">{stats.active_subscriptions}</p>
                </div>
                <div className="p-6 bg-gray-900 rounded-2xl border border-gray-800">
                  <p className="text-gray-500 text-xs uppercase tracking-widest mb-2">Utilisateurs bannis</p>
                  <p className="text-3xl font-bold text-red-400">{stats.banned_users}</p>
                </div>
                <div className="p-6 bg-gray-900 rounded-2xl border border-gray-800">
                  <p className="text-gray-500 text-xs uppercase tracking-widest mb-2">Revenus estimés</p>
                  <p className="text-3xl font-bold text-amber-400">
                    {(stats.subscriptions.basic * 29.99 +
                      stats.subscriptions.premium * 119.99 +
                      stats.subscriptions.partner * 299.99).toFixed(0)}€
                  </p>
                </div>
              </div>

              {/* Répartition abonnements */}
              <div className="p-6 bg-gray-900 rounded-2xl border border-gray-800">
                <h2 className="text-sm font-semibold text-gray-400 uppercase tracking-widest mb-4">
                  Répartition des abonnements
                </h2>
                <div className="grid grid-cols-3 gap-4">
                  {[
                    { label: 'Basic', count: stats.subscriptions.basic, price: '29.99€', color: 'text-white' },
                    { label: 'Premium', count: stats.subscriptions.premium, price: '119.99€', color: 'text-emerald-400' },
                    { label: 'Partner', count: stats.subscriptions.partner, price: '299.99€', color: 'text-amber-400' },
                  ].map(plan => (
                    <div key={plan.label} className="p-4 bg-gray-800 rounded-xl text-center">
                      <div className={`text-2xl font-bold ${plan.color}`}>{plan.count}</div>
                      <div className="text-gray-400 text-sm mt-1">{plan.label}</div>
                      <div className="text-gray-600 text-xs">{plan.price}/mois</div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* ===== ONGLET UTILISATEURS ===== */}
          {activeTab === 'users' && (
            <div className="flex gap-6">
              {/* Liste des users */}
              <div className="flex-1">
                {/* Barre de recherche */}
                <div className="mb-4">
                  <input
                    type="text"
                    placeholder="Rechercher par email ou nom d'utilisateur..."
                    value={search}
                    onChange={handleSearch}
                    className="w-full bg-gray-900 border border-gray-700 rounded-xl px-4 py-3 text-white placeholder-gray-600 focus:outline-none focus:border-emerald-500 transition"
                  />
                </div>

                {/* Tableau */}
                <div className="bg-gray-900 rounded-2xl border border-gray-800 overflow-hidden">
                  <table className="w-full">
                    <thead>
                      <tr className="border-b border-gray-800">
                        <th className="text-left px-4 py-3 text-xs text-gray-500 uppercase tracking-widest">Utilisateur</th>
                        <th className="text-left px-4 py-3 text-xs text-gray-500 uppercase tracking-widest">Abonnement</th>
                        <th className="text-left px-4 py-3 text-xs text-gray-500 uppercase tracking-widest">Statut</th>
                        <th className="text-left px-4 py-3 text-xs text-gray-500 uppercase tracking-widest">Action</th>
                      </tr>
                    </thead>
                    <tbody>
                      {users.map(u => (
                        <tr
                          key={u.id}
                          className={`border-b border-gray-800/50 hover:bg-gray-800/50 cursor-pointer transition ${
                            selectedUser?.id === u.id ? 'bg-emerald-500/5' : ''
                          }`}
                          onClick={() => setSelectedUser(u)}
                        >
                          <td className="px-4 py-3">
                            <div className="font-semibold text-sm">{u.username}</div>
                            <div className="text-gray-500 text-xs">{u.email}</div>
                          </td>
                          <td className="px-4 py-3">
                            <span className={`px-2 py-1 rounded text-xs font-bold ${
                              u.subscription_type === 'partner' ? 'bg-amber-500/20 text-amber-400' :
                              u.subscription_type === 'premium' ? 'bg-emerald-500/20 text-emerald-400' :
                              u.subscription_type === 'basic' ? 'bg-blue-500/20 text-blue-400' :
                              'bg-gray-700 text-gray-400'
                            }`}>
                              {u.subscription_type === 'none' ? 'Aucun' : u.subscription_type}
                            </span>
                          </td>
                          <td className="px-4 py-3">
                            {u.is_banned ? (
                              <span className="text-red-400 text-xs font-bold">🚫 Banni</span>
                            ) : u.is_admin ? (
                              <span className="text-amber-400 text-xs font-bold">🛡️ Admin</span>
                            ) : (
                              <span className="text-emerald-400 text-xs">● Actif</span>
                            )}
                          </td>
                          <td className="px-4 py-3">
                            <button
                              onClick={(e) => { e.stopPropagation(); setSelectedUser(u) }}
                              className="text-xs text-emerald-400 hover:underline"
                            >
                              Gérer →
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* Panneau détail user */}
              {selectedUser && (
                <div className="w-72 bg-gray-900 rounded-2xl border border-gray-800 p-6 space-y-4 self-start">
                  <div className="flex items-center justify-between">
                    <h3 className="font-semibold">Détails</h3>
                    <button onClick={() => setSelectedUser(null)} className="text-gray-600 hover:text-white">✕</button>
                  </div>

                  <div className="space-y-2 text-sm">
                    <div><span className="text-gray-500">Username : </span>{selectedUser.username}</div>
                    <div><span className="text-gray-500">Email : </span>{selectedUser.email}</div>
                    <div><span className="text-gray-500">Inscrit le : </span>{new Date(selectedUser.created_at).toLocaleDateString('fr-FR')}</div>
                    <div><span className="text-gray-500">Abonnement : </span>{selectedUser.subscription_type}</div>
                    {selectedUser.ban_reason && (
                      <div><span className="text-red-400">Raison ban : </span>{selectedUser.ban_reason}</div>
                    )}
                  </div>

                  {/* Modifier abonnement */}
                  <div className="border-t border-gray-800 pt-4">
                    <p className="text-xs text-gray-500 uppercase tracking-widest mb-2">Modifier abonnement</p>
                    <div className="space-y-2">
                      {['none', 'basic', 'premium', 'partner'].map(plan => (
                        <button
                          key={plan}
                          onClick={() => updateSubscription(selectedUser.id, plan)}
                          className={`w-full py-2 rounded-lg text-xs font-semibold transition ${
                            selectedUser.subscription_type === plan
                              ? 'bg-emerald-500 text-black'
                              : 'bg-gray-800 hover:bg-gray-700 text-gray-300'
                          }`}
                        >
                          {plan === 'none' ? 'Aucun' : plan.charAt(0).toUpperCase() + plan.slice(1)}
                        </button>
                      ))}
                    </div>
                  </div>

                  {/* Actions admin — uniquement pour les super admins */}
                  {isSuperAdmin && !SUPER_ADMINS.includes(selectedUser.email) && (
                    <div className="border-t border-gray-800 pt-4 space-y-2">
                      <p className="text-xs text-gray-500 uppercase tracking-widest mb-2">Actions admin</p>
                      {!selectedUser.is_admin ? (
                        <button
                          onClick={() => grantAdmin(selectedUser.id)}
                          className="w-full py-2 bg-amber-500/20 hover:bg-amber-500/30 text-amber-400 rounded-lg text-xs font-semibold transition"
                        >
                          🛡️ Attribuer admin
                        </button>
                      ) : (
                        <button
                          onClick={() => revokeAdmin(selectedUser.id)}
                          className="w-full py-2 bg-red-500/20 hover:bg-red-500/30 text-red-400 rounded-lg text-xs font-semibold transition"
                        >
                          ❌ Retirer admin
                        </button>
                      )}

                      {!selectedUser.is_banned ? (
                        <button
                          onClick={() => {
                            const reason = prompt('Raison du ban :')
                            if (reason) banUser(selectedUser.id, reason)
                          }}
                          className="w-full py-2 bg-red-500/20 hover:bg-red-500/30 text-red-400 rounded-lg text-xs font-semibold transition"
                        >
                          🚫 Bannir
                        </button>
                      ) : (
                        <button
                          onClick={() => unbanUser(selectedUser.id)}
                          className="w-full py-2 bg-emerald-500/20 hover:bg-emerald-500/30 text-emerald-400 rounded-lg text-xs font-semibold transition"
                        >
                          ✅ Lever le ban
                        </button>
                      )}
                    </div>
                  )}
                </div>
              )}
            </div>
          )}

          {/* ===== ONGLET ABONNEMENTS ===== */}
          {activeTab === 'subscriptions' && (
            <div className="space-y-6">
              <div className="p-6 bg-gray-900 rounded-2xl border border-gray-800">
                <h2 className="font-semibold mb-6">Utilisateurs par abonnement</h2>
                {['basic', 'premium', 'partner'].map(plan => (
                  <div key={plan} className="mb-6">
                    <h3 className={`text-sm font-bold uppercase tracking-widest mb-3 ${
                      plan === 'partner' ? 'text-amber-400' :
                      plan === 'premium' ? 'text-emerald-400' : 'text-blue-400'
                    }`}>
                      {plan} — {plan === 'basic' ? '29.99€' : plan === 'premium' ? '119.99€' : '299.99€'}/mois
                    </h3>
                    <div className="space-y-2">
                      {users.filter(u => u.subscription_type === plan).length === 0 ? (
                        <p className="text-gray-600 text-sm">Aucun abonné</p>
                      ) : (
                        users.filter(u => u.subscription_type === plan).map(u => (
                          <div key={u.id} className="flex items-center justify-between p-3 bg-gray-800 rounded-xl">
                            <div>
                              <span className="text-sm font-semibold">{u.username}</span>
                              <span className="text-gray-500 text-xs ml-2">{u.email}</span>
                            </div>
                            <button
                              onClick={() => { setSelectedUser(u); setActiveTab('users') }}
                              className="text-xs text-emerald-400 hover:underline"
                            >
                              Gérer →
                            </button>
                          </div>
                        ))
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* ===== ONGLET ANNONCES ===== */}
          {activeTab === 'announcements' && (
            <div className="p-6 bg-gray-900 rounded-2xl border border-gray-800">
              <h2 className="font-semibold mb-4">Créer une annonce</h2>
              <p className="text-gray-500 text-sm mb-6">
                Les annonces apparaîtront sur le dashboard de tous les utilisateurs.
              </p>
              <div className="space-y-4 max-w-xl">
                <input
                  type="text"
                  placeholder="Titre de l'annonce"
                  className="w-full bg-gray-800 border border-gray-700 rounded-xl px-4 py-3 text-white placeholder-gray-600 focus:outline-none focus:border-emerald-500"
                />
                <textarea
                  placeholder="Contenu de l'annonce..."
                  rows={4}
                  className="w-full bg-gray-800 border border-gray-700 rounded-xl px-4 py-3 text-white placeholder-gray-600 focus:outline-none focus:border-emerald-500 resize-none"
                />
                <button className="px-6 py-3 bg-emerald-500 hover:bg-emerald-400 text-black font-bold rounded-xl transition">
                  Publier l'annonce
                </button>
              </div>
            </div>
          )}

          {/* ===== ONGLET LOGS ===== */}
          {activeTab === 'logs' && (
            <div className="p-6 bg-gray-900 rounded-2xl border border-gray-800">
              <h2 className="font-semibold mb-4">Logs d'activité</h2>
              <p className="text-gray-500 text-sm">
                Les logs du bot de trading apparaîtront ici une fois l'agent IA connecté.
              </p>
              <div className="mt-6 font-mono text-sm text-gray-600 space-y-1">
                <p>{">"} Système prêt</p>
                <p>{">"} En attente de connexion de l'agent...</p>
              </div>
            </div>
          )}

        </div>
      </div>
    </main>
  )
}