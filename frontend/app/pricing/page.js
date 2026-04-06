'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'

const API = 'http://127.0.0.1:8000'

export default function PricingPage() {
  const [loading, setLoading] = useState(null) // plan en cours de chargement
  const [error, setError] = useState('')
  const [user, setUser] = useState(null)
  const router = useRouter()

  useEffect(() => {
    const token = localStorage.getItem('token')
    if (!token) { router.push('/register'); return }

    fetch(`${API}/users/me?token=${token}`)
      .then(r => r.json())
      .then(setUser)
      .catch(() => router.push('/register'))
  }, [router])

  const handleSubscribe = async (plan) => {
    const token = localStorage.getItem('token')
    if (!token) { router.push('/register'); return }

    setLoading(plan)
    setError('')

    try {
      const res = await fetch(`${API}/payments/create-checkout?token=${token}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ plan })
      })

      const data = await res.json()

      if (!res.ok) {
        setError(data.detail || 'Erreur lors de la création du paiement')
        setLoading(null)
        return
      }

      // Redirige vers la page de paiement Stripe
      window.location.href = data.checkout_url

    } catch (err) {
      setError('Impossible de contacter le serveur')
      setLoading(null)
    }
  }

  const plans = [
    {
      id: 'basic',
      name: 'Basic',
      price: '29.99€',
      usd: '≈ $32',
      fcfa: '19 650 FCFA',
      description: 'Pour débuter avec le trading automatisé',
      features: [
        '✅ Trading IA automatique 24h/24',
        '✅ Long trading — analyse toutes les 4h',
        '✅ 3 trades actifs simultanés',
        '✅ Support standard',
      ],
      color: 'border-gray-700',
      buttonClass: 'border border-gray-600 hover:border-emerald-500 hover:text-emerald-400',
      badge: null,
    },
    {
      id: 'premium',
      name: 'Premium',
      price: '119.99€',
      usd: '≈ $129',
      fcfa: '78 650 FCFA',
      description: 'Trading day & long avec signaux avancés',
      features: [
        '✅ Tout Basic inclus',
        '✅ Day trading — analyse 2h et 1h',
        '✅ 5 signaux de trade simultanés',
        '✅ Support prioritaire',
      ],
      color: 'border-emerald-500',
      buttonClass: 'bg-emerald-500 hover:bg-emerald-400 text-black font-bold',
      badge: { text: 'Le plus populaire', class: 'bg-emerald-500 text-black' },
    },
    {
      id: 'partner',
      name: 'Partner',
      price: '299.99€',
      usd: '≈ $323',
      fcfa: '196 750 FCFA',
      description: 'Puissance maximale pour traders sérieux',
      features: [
        '✅ Tout Premium inclus',
        '✅ Scalping — analyse 30min',
        '✅ Session continue 10min activable',
        '✅ Jusqu\'à 10 paires simultanées',
        '✅ Alertes email temps réel',
        '✅ Account manager dédié',
      ],
      color: 'border-amber-500/50',
      buttonClass: 'bg-amber-500 hover:bg-amber-400 text-black font-bold',
      badge: { text: 'Max Power', class: 'bg-amber-500 text-black' },
    },
  ]

  return (
    <main className="min-h-screen bg-gray-950 text-white">

      {/* Navbar */}
      <nav className="flex items-center justify-between px-8 py-4 border-b border-gray-800">
        <div className="text-2xl font-bold text-emerald-400">
          Flux<span className="text-white">Trade</span>
        </div>
        <div className="flex items-center gap-4">
          {user && (
            <span className="text-gray-400 text-sm">
              Connecté : <span className="text-white">{user.username}</span>
            </span>
          )}
          <a href="/dashboard" className="text-sm text-gray-400 hover:text-white transition">
            ← Dashboard
          </a>
        </div>
      </nav>

      <div className="max-w-6xl mx-auto px-8 py-16">

        <h1 className="text-4xl font-bold text-center mb-4">
          Choisissez votre plan
        </h1>
        <p className="text-center text-gray-400 mb-4">
          Tous les plans incluent le trading IA automatique 24h/24
        </p>

        {/* Abonnement actuel */}
        {user?.subscription_type !== 'none' && (
          <div className="text-center mb-8">
            <span className="px-4 py-2 bg-emerald-500/20 border border-emerald-500/30 rounded-full text-emerald-400 text-sm">
              Abonnement actuel : <strong>{user?.subscription_type}</strong>
            </span>
          </div>
        )}

        {/* Message d'erreur */}
        {error && (
          <div className="max-w-md mx-auto mb-8 p-4 bg-red-500/10 border border-red-500/30 rounded-xl text-red-400 text-center text-sm">
            {error}
          </div>
        )}

        {/* Cartes */}
        <div className="grid md:grid-cols-3 gap-8 mb-12">
          {plans.map(plan => (
            <div
              key={plan.id}
              className={`p-8 bg-gray-900 rounded-2xl border-2 ${plan.color} relative flex flex-col`}
            >
              {/* Badge */}
              {plan.badge && (
                <div className={`absolute -top-4 left-1/2 -translate-x-1/2 px-4 py-1 ${plan.badge.class} text-sm font-bold rounded-full whitespace-nowrap`}>
                  {plan.badge.text}
                </div>
              )}

              <div>
                <h2 className="text-xl font-bold mb-1">{plan.name}</h2>
                <p className="text-gray-400 text-sm mb-4">{plan.description}</p>

                <div className="text-4xl font-bold mb-1">{plan.price}</div>
                <div className="text-gray-500 text-xs mb-6">
                  {plan.usd} / {plan.fcfa} — par mois
                </div>

                <div className="border-t border-gray-700 pt-6 mb-6">
                  <ul className="space-y-3 text-sm text-gray-300">
                    {plan.features.map((f, i) => (
                      <li key={i}>{f}</li>
                    ))}
                  </ul>
                </div>
              </div>

              <div className="mt-auto">
                {user?.subscription_type === plan.id ? (
                  <div className="w-full py-3 text-center rounded-xl bg-gray-700 text-gray-400 text-sm font-semibold">
                    ✓ Plan actuel
                  </div>
                ) : (
                  <button
                    onClick={() => handleSubscribe(plan.id)}
                    disabled={loading === plan.id}
                    className={`w-full py-3 rounded-xl transition ${plan.buttonClass} disabled:opacity-50`}
                  >
                    {loading === plan.id ? 'Chargement...' : `Choisir ${plan.name}`}
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>

        {/* Sécurité */}
        <p className="text-center text-gray-600 text-sm">
          🔒 Paiement sécurisé par Stripe — Vos données bancaires ne transitent jamais par nos serveurs
        </p>
        <p className="text-center text-gray-700 text-xs mt-2">
          Le trading comporte des risques. Les performances passées ne garantissent pas les résultats futurs.
        </p>

      </div>
    </main>
  )
}