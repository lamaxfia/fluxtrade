'use client'

import { useState, useEffect, useRef } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'

const API = process.env.NEXT_PUBLIC_API_URL

export default function VerifyPage() {
  const [code, setCode] = useState(['', '', '', '', '', ''])
  const [email, setEmail] = useState('')
  const [loading, setLoading] = useState(false)
  const [resending, setResending] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState(false)
  const [countdown, setCountdown] = useState(60)
  const [canResend, setCanResend] = useState(false)
  const inputs = useRef([])
  const router = useRouter()
  const searchParams = useSearchParams()

  useEffect(() => {
    const emailParam = searchParams.get('email')
    if (emailParam) setEmail(emailParam)

    // Compte à rebours avant de pouvoir renvoyer
    const timer = setInterval(() => {
      setCountdown(prev => {
        if (prev <= 1) {
          clearInterval(timer)
          setCanResend(true)
          return 0
        }
        return prev - 1
      })
    }, 1000)
    return () => clearInterval(timer)
  }, [searchParams])

  const handleChange = (index, value) => {
    if (!/^\d*$/.test(value)) return  // seulement des chiffres
    const newCode = [...code]
    newCode[index] = value.slice(-1)  // garde seulement le dernier caractère
    setCode(newCode)
    setError('')

    // Passe au champ suivant automatiquement
    if (value && index < 5) {
      inputs.current[index + 1]?.focus()
    }

    // Soumet automatiquement si tous les champs sont remplis
    if (newCode.every(c => c !== '') && value) {
      handleVerify(newCode.join(''))
    }
  }

  const handleKeyDown = (index, e) => {
    if (e.key === 'Backspace' && !code[index] && index > 0) {
      inputs.current[index - 1]?.focus()
    }
  }

  const handleVerify = async (codeStr = null) => {
    const finalCode = codeStr || code.join('')
    if (finalCode.length !== 6) {
      setError('Entre les 6 chiffres du code')
      return
    }

    setLoading(true)
    setError('')

    try {
      const res = await fetch(`${API}/auth/verify-email`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, code: finalCode })
      })

      const data = await res.json()

      if (res.ok) {
        setSuccess(true)
        setTimeout(() => router.push('/register'), 3000)
      } else {
        setError(data.detail || 'Code invalide')
        setCode(['', '', '', '', '', ''])
        inputs.current[0]?.focus()
      }
    } catch {
      setError('Impossible de contacter le serveur')
    }

    setLoading(false)
  }

  const handleResend = async () => {
    setResending(true)
    try {
      await fetch(`${API}/auth/resend-verification?email=${email}`, {
        method: 'POST'
      })
      setCanResend(false)
      setCountdown(60)
      // Relance le compte à rebours
      const timer = setInterval(() => {
        setCountdown(prev => {
          if (prev <= 1) {
            clearInterval(timer)
            setCanResend(true)
            return 0
          }
          return prev - 1
        })
      }, 1000)
    } catch {
      setError('Erreur lors du renvoi')
    }
    setResending(false)
  }

  if (success) {
    return (
      <main className="min-h-screen bg-gray-950 flex items-center justify-center px-4">
        <div className="text-center">
          <div className="text-6xl mb-6">✅</div>
          <h1 className="text-2xl font-bold text-white mb-2">Email vérifié !</h1>
          <p className="text-gray-400">Redirection vers la connexion...</p>
        </div>
      </main>
    )
  }

  return (
    <main className="min-h-screen bg-gray-950 flex items-center justify-center px-4">
      <div className="w-full max-w-md">

        {/* Logo */}
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-emerald-400">
            Flux<span className="text-white">Trade</span>
          </h1>
        </div>

        <div className="bg-gray-900 rounded-2xl border border-gray-800 p-8 text-center">

          {/* Icône */}
          <div className="text-5xl mb-4">📬</div>

          <h2 className="text-xl font-bold text-white mb-2">Vérifie ton email</h2>
          <p className="text-gray-400 text-sm mb-2">
            On a envoyé un code à 6 chiffres à
          </p>
          <p className="text-emerald-400 font-semibold mb-8">{email}</p>

          {/* Champs de code */}
          <div className="flex gap-3 justify-center mb-6">
            {code.map((digit, index) => (
              <input
                key={index}
                ref={el => inputs.current[index] = el}
                type="text"
                inputMode="numeric"
                maxLength={1}
                value={digit}
                onChange={e => handleChange(index, e.target.value)}
                onKeyDown={e => handleKeyDown(index, e)}
                className={`w-12 h-14 text-center text-xl font-bold bg-gray-800 border-2 rounded-xl text-white focus:outline-none transition ${
                  error
                    ? 'border-red-500'
                    : digit
                    ? 'border-emerald-500'
                    : 'border-gray-700 focus:border-emerald-500'
                }`}
              />
            ))}
          </div>

          {/* Erreur */}
          {error && (
            <div className="mb-4 p-3 bg-red-500/10 border border-red-500/30 rounded-xl text-red-400 text-sm">
              {error}
            </div>
          )}

          {/* Bouton vérifier */}
          <button
            onClick={() => handleVerify()}
            disabled={loading || code.some(c => c === '')}
            className="w-full py-3 bg-emerald-500 hover:bg-emerald-400 disabled:opacity-50 text-black font-bold rounded-xl transition mb-4"
          >
            {loading ? 'Vérification...' : 'Vérifier le code'}
          </button>

          {/* Renvoyer */}
          <div className="text-sm text-gray-500">
            {canResend ? (
              <button
                onClick={handleResend}
                disabled={resending}
                className="text-emerald-400 hover:underline"
              >
                {resending ? 'Envoi...' : 'Renvoyer le code'}
              </button>
            ) : (
              <span>Renvoyer disponible dans <span className="text-white">{countdown}s</span></span>
            )}
          </div>

          <p className="text-gray-600 text-xs mt-6">
            <a href="/" className="hover:text-gray-400 transition">← Retour à l'accueil</a>
          </p>
        </div>
      </div>
    </main>
  )
}