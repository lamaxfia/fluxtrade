'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'

export default function PaymentSuccess() {
  const [countdown, setCountdown] = useState(5)
  const router = useRouter()

  useEffect(() => {
    // Compte à rebours avant redirection vers le dashboard
    const timer = setInterval(() => {
      setCountdown(prev => {
        if (prev <= 1) {
          clearInterval(timer)
          router.push('/dashboard')
        }
        return prev - 1
      })
    }, 1000)

    return () => clearInterval(timer)
  }, [router])

  return (
    <main className="min-h-screen bg-gray-950 flex items-center justify-center px-4">
      <div className="text-center max-w-md">

        {/* Icône succès */}
        <div className="w-24 h-24 bg-emerald-500/20 rounded-full flex items-center justify-center mx-auto mb-8">
          <span className="text-5xl">✅</span>
        </div>

        <h1 className="text-3xl font-bold text-white mb-4">
          Paiement réussi !
        </h1>

        <p className="text-gray-400 mb-2">
          Ton abonnement FluxTrade est maintenant actif.
        </p>
        <p className="text-gray-400 mb-8">
          Le bot de trading IA va démarrer automatiquement.
        </p>

        <div className="p-4 bg-emerald-500/10 border border-emerald-500/30 rounded-2xl mb-8">
          <p className="text-emerald-400 text-sm">
            Redirection vers ton dashboard dans <span className="font-bold text-xl">{countdown}</span>s
          </p>
        </div>

        <button
          onClick={() => router.push('/dashboard')}
          className="px-8 py-3 bg-emerald-500 hover:bg-emerald-400 text-black font-bold rounded-xl transition"
        >
          Aller au dashboard maintenant
        </button>

      </div>
    </main>
  )
}