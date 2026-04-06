'use client'

import { useRouter } from 'next/navigation'

export default function PaymentCancel() {
  const router = useRouter()

  return (
    <main className="min-h-screen bg-gray-950 flex items-center justify-center px-4">
      <div className="text-center max-w-md">

        {/* Icône annulation */}
        <div className="w-24 h-24 bg-red-500/20 rounded-full flex items-center justify-center mx-auto mb-8">
          <span className="text-5xl">❌</span>
        </div>

        <h1 className="text-3xl font-bold text-white mb-4">
          Paiement annulé
        </h1>

        <p className="text-gray-400 mb-8">
          Ton paiement a été annulé. Aucun montant n'a été prélevé.
          Tu peux choisir un abonnement à tout moment.
        </p>

        <div className="flex gap-4 justify-center flex-wrap">
          <button
            onClick={() => router.push('/#abonnements')}
            className="px-8 py-3 bg-emerald-500 hover:bg-emerald-400 text-black font-bold rounded-xl transition"
          >
            Voir les abonnements
          </button>
          <button
            onClick={() => router.push('/dashboard')}
            className="px-8 py-3 border border-gray-700 hover:border-gray-500 text-white rounded-xl transition"
          >
            Retour au dashboard
          </button>
        </div>

      </div>
    </main>
  )
}