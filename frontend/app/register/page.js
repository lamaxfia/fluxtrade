'use client'
// 'use client' est obligatoire quand on utilise useState ou des interactions
// Sans ça, Next.js essaie de rendre la page côté serveur et les boutons ne fonctionnent pas

import { useState } from 'react'
import { useRouter } from 'next/navigation'

const API_URL = process.env.NEXT_PUBLIC_API_URL

export default function AuthPage() {
  // onglet actif : 'login' ou 'register'
  const [tab, setTab] = useState(
  typeof window !== 'undefined' && window.location.search.includes('login') 
    ? 'login' 
    : 'register'
)
  
  // données du formulaire
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    password: '',
    confirmPassword: ''
  })

  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const router = useRouter()

  // Met à jour le champ correspondant dans formData quand l'utilisateur tape
  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value })
    setError('') // efface l'erreur dès que l'utilisateur retape
  }

  // Soumission du formulaire
  const handleSubmit = async (e) => {
    e.preventDefault() // empêche le rechargement de la page
    setLoading(true)
    setError('')

    // Vérification côté client avant d'envoyer au serveur
    if (tab === 'register' && formData.password !== formData.confirmPassword) {
      setError('Les mots de passe ne correspondent pas')
      setLoading(false)
      return
    }

    try {
      if (tab === 'register') {
        // Appel à notre API FastAPI
        const res = await fetch(`${API_URL}/auth/register`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            email: formData.email,
            username: formData.username,
            password: formData.password
          })
        })
        const data = await res.json()
        if (!res.ok) {
          setError(data.detail || 'Erreur lors de l\'inscription')
          setLoading(false)
          return
        }
        // Inscription réussie → redirige vers la connexion
        setTab('login')
        setError('')
        setFormData({ ...formData, password: '', confirmPassword: '' })

      } else {
        // Connexion
        const res = await fetch(`${API_URL}/auth/login`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            email: formData.email,
            password: formData.password
          })
        })
        const data = await res.json()
        if (!res.ok) {
          setError(data.detail || 'Email ou mot de passe incorrect')
          setLoading(false)
          return
        }
        // Sauvegarde le token dans localStorage pour les prochaines requêtes
        localStorage.setItem('token', data.access_token)
        // Redirige vers le dashboard
        router.push('/dashboard')
      }
    } catch (err) {
      setError('Impossible de contacter le serveur. Vérifiez que le backend tourne.')
    }

    setLoading(false)
  }

  return (
    <main className="min-h-screen bg-gray-950 flex items-center justify-center px-4">
      <div className="w-full max-w-md">

        {/* Logo */}
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-emerald-400">
            Flux<span className="text-white">Trade</span>
          </h1>
          <p className="text-gray-500 text-xs tracking-widest mt-1 uppercase">
            AI-Powered Trading Platform
          </p>
        </div>

        {/* Carte principale */}
        <div className="bg-gray-900 rounded-2xl border border-gray-800 p-8">

          {/* Onglets Login / Register */}
          <div className="flex bg-gray-800 rounded-xl p-1 mb-8">
            <button
              onClick={() => { setTab('login'); setError('') }}
              className={`flex-1 py-2 rounded-lg text-sm font-semibold transition ${
                tab === 'login'
                  ? 'bg-emerald-500 text-black'
                  : 'text-gray-400 hover:text-white'
              }`}
            >
              Connexion
            </button>
            <button
              onClick={() => { setTab('register'); setError('') }}
              className={`flex-1 py-2 rounded-lg text-sm font-semibold transition ${
                tab === 'register'
                  ? 'bg-emerald-500 text-black'
                  : 'text-gray-400 hover:text-white'
              }`}
            >
              Inscription
            </button>
          </div>

          {/* Formulaire */}
          <form onSubmit={handleSubmit} className="space-y-4">

            {/* Champ username — uniquement à l'inscription */}
            {tab === 'register' && (
              <div>
                <label className="block text-xs text-gray-500 uppercase tracking-widest mb-2">
                  Nom d'utilisateur
                </label>
                <input
                  type="text"
                  name="username"
                  placeholder="TraderXYZ"
                  value={formData.username}
                  onChange={handleChange}
                  required
                  className="w-full bg-gray-800 border border-gray-700 rounded-xl px-4 py-3 text-white placeholder-gray-600 focus:outline-none focus:border-emerald-500 transition"
                />
              </div>
            )}

            {/* Email */}
            <div>
              <label className="block text-xs text-gray-500 uppercase tracking-widest mb-2">
                Email
              </label>
              <input
                type="email"
                name="email"
                placeholder="vous@exemple.com"
                value={formData.email}
                onChange={handleChange}
                required
                className="w-full bg-gray-800 border border-gray-700 rounded-xl px-4 py-3 text-white placeholder-gray-600 focus:outline-none focus:border-emerald-500 transition"
              />
            </div>

            {/* Mot de passe */}
            <div>
              <label className="block text-xs text-gray-500 uppercase tracking-widest mb-2">
                Mot de passe
              </label>
              <input
                type="password"
                name="password"
                placeholder="Min 8 caractères"
                value={formData.password}
                onChange={handleChange}
                required
                minLength={8}
                className="w-full bg-gray-800 border border-gray-700 rounded-xl px-4 py-3 text-white placeholder-gray-600 focus:outline-none focus:border-emerald-500 transition"
              />
            </div>

            {/* Confirmation mot de passe — uniquement à l'inscription */}
            {tab === 'register' && (
              <div>
                <label className="block text-xs text-gray-500 uppercase tracking-widest mb-2">
                  Confirmer le mot de passe
                </label>
                <input
                  type="password"
                  name="confirmPassword"
                  placeholder="Répétez votre mot de passe"
                  value={formData.confirmPassword}
                  onChange={handleChange}
                  required
                  className="w-full bg-gray-800 border border-gray-700 rounded-xl px-4 py-3 text-white placeholder-gray-600 focus:outline-none focus:border-emerald-500 transition"
                />
              </div>
            )}

            {/* Message d'erreur */}
            {error && (
              <div className="bg-red-500/10 border border-red-500/30 rounded-xl px-4 py-3 text-red-400 text-sm">
                {error}
              </div>
            )}

            {/* Bouton submit */}
            <button
              type="submit"
              disabled={loading}
              className="w-full py-3 bg-emerald-500 hover:bg-emerald-400 disabled:bg-emerald-500/50 text-black font-bold rounded-xl transition mt-2"
            >
              {loading
                ? 'Chargement...'
                : tab === 'register'
                ? 'Créer mon compte'
                : 'Se connecter'
              }
            </button>

          </form>

          {/* Lien retour accueil */}
          <p className="text-center text-gray-600 text-sm mt-6">
            <a href="/" className="hover:text-gray-400 transition">
              ← Retour à l'accueil
            </a>
          </p>

        </div>
      </div>
    </main>
  )
}