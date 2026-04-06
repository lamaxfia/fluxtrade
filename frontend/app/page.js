// page.js — Page d'accueil FluxTrade
// En Next.js, chaque fichier "page.js" dans le dossier app/ devient une page web
// Ce fichier = la page qu'on voit sur http://localhost:3000

export default function HomePage() {
  return (
    <main className="min-h-screen bg-gray-950 text-white">

      {/* ========== NAVBAR ========== */}
      <nav className="flex items-center justify-between px-8 py-4 border-b border-gray-800">
        {/* Logo */}
        <div className="text-2xl font-bold text-emerald-400">
          Flux<span className="text-white">Trade</span>
        </div>

        {/* Liens de navigation */}
        <div className="hidden md:flex gap-8 text-gray-300 text-sm">
          <a href="#fonctionnalites" className="hover:text-white transition">Fonctionnalités</a>
          <a href="#abonnements" className="hover:text-white transition">Abonnements</a>
          <a href="#contact" className="hover:text-white transition">Contact</a>
        </div>

        {/* Boutons connexion */}
        <div className="flex gap-3">
          <a href="/login" className="px-4 py-2 text-sm text-gray-300 hover:text-white transition">
            Connexion
          </a>
          <a href="/register" className="px-4 py-2 text-sm bg-emerald-500 hover:bg-emerald-400 text-black font-semibold rounded-lg transition">
            Commencer
          </a>
        </div>
      </nav>

      {/* ========== HERO (section principale) ========== */}
      <section className="flex flex-col items-center text-center px-6 py-32">
        {/* Badge */}
        <div className="mb-6 px-4 py-1 bg-emerald-500/10 border border-emerald-500/30 rounded-full text-emerald-400 text-sm">
          🤖 Trading automatisé par intelligence artificielle
        </div>

        {/* Titre principal */}
        <h1 className="text-5xl md:text-7xl font-bold leading-tight max-w-4xl">
          Laisse l'IA trader
          <span className="text-emerald-400"> à ta place</span>
        </h1>

        {/* Sous-titre */}
        <p className="mt-6 text-xl text-gray-400 max-w-2xl">
          FluxTrade analyse les marchés financiers 24h/24 et exécute des trades 
          automatiquement pendant que tu vis ta vie.
        </p>

        {/* Boutons d'action */}
        <div className="mt-10 flex gap-4 flex-wrap justify-center">
          <a href="/register" className="px-8 py-4 bg-emerald-500 hover:bg-emerald-400 text-black font-bold rounded-xl text-lg transition">
            Démarrer gratuitement
          </a>
          <a href="#abonnements" className="px-8 py-4 border border-gray-700 hover:border-gray-500 text-white rounded-xl text-lg transition">
            Voir les abonnements
          </a>
        </div>

        {/* Stats rapides */}
        <div className="mt-20 grid grid-cols-3 gap-12 text-center">
          <div>
            <div className="text-4xl font-bold text-emerald-400">24/7</div>
            <div className="text-gray-400 mt-1">Surveillance continue</div>
          </div>
          <div>
            <div className="text-4xl font-bold text-emerald-400">100%</div>
            <div className="text-gray-400 mt-1">Automatisé</div>
          </div>
          <div>
            <div className="text-4xl font-bold text-emerald-400">IA</div>
            <div className="text-gray-400 mt-1">Décisions intelligentes</div>
          </div>
        </div>
      </section>

      {/* ========== FONCTIONNALITES ========== */}
      <section id="fonctionnalites" className="px-8 py-24 bg-gray-900">
        <h2 className="text-3xl font-bold text-center mb-16">
          Pourquoi choisir <span className="text-emerald-400">FluxTrade</span> ?
        </h2>

        <div className="grid md:grid-cols-3 gap-8 max-w-5xl mx-auto">
          {/* Carte 1 */}
          <div className="p-6 bg-gray-800 rounded-2xl border border-gray-700">
            <div className="text-3xl mb-4">📈</div>
            <h3 className="text-xl font-semibold mb-2">Analyse en temps réel</h3>
            <p className="text-gray-400">
              Notre IA surveille les marchés en continu et détecte les opportunités 
              avant tout le monde.
            </p>
          </div>

          {/* Carte 2 */}
          <div className="p-6 bg-gray-800 rounded-2xl border border-gray-700">
            <div className="text-3xl mb-4">🔒</div>
            <h3 className="text-xl font-semibold mb-2">Sécurisé & privé</h3>
            <p className="text-gray-400">
              Tes clés API broker ne quittent jamais nos serveurs chiffrés. 
              Tu gardes le contrôle total.
            </p>
          </div>

          {/* Carte 3 */}
          <div className="p-6 bg-gray-800 rounded-2xl border border-gray-700">
            <div className="text-3xl mb-4">🌍</div>
            <h3 className="text-xl font-semibold mb-2">Paiement mondial</h3>
            <p className="text-gray-400">
              PayPal, carte bancaire, Mobile Money — on accepte les paiements 
              depuis partout en Afrique et dans le monde.
            </p>
          </div>
        </div>
      </section>

      {/* ========== ABONNEMENTS ========== */}
      <section id="abonnements" className="px-8 py-24">
        <h2 className="text-3xl font-bold text-center mb-4">Nos abonnements</h2>
        <p className="text-center text-gray-400 mb-16">
          Tous les plans incluent le trading IA automatique 24h/24
        </p>

        <div className="grid md:grid-cols-3 gap-8 max-w-5xl mx-auto">

          {/* Plan Basic */}
          <div className="p-8 bg-gray-900 rounded-2xl border border-gray-700 flex flex-col">
            <div>
              <h3 className="text-xl font-bold mb-1">Basic</h3>
              <p className="text-gray-500 text-sm mb-4">Pour débuter avec le trading automatisé</p>
              <div className="text-4xl font-bold my-4">
                29.99€<span className="text-lg text-gray-400">/mois</span>
              </div>
              <p className="text-gray-500 text-xs mb-6">≈ $32 / 19 650 FCFA</p>

              <div className="border-t border-gray-700 pt-6 mb-6">
                <p className="text-xs text-gray-500 uppercase tracking-widest mb-4">Inclus</p>
                <ul className="space-y-3 text-gray-300">
                  <li className="flex items-start gap-2">
                    <span className="text-emerald-400 mt-0.5">✓</span>
                    <span>Trading IA automatique 24h/24</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-emerald-400 mt-0.5">✓</span>
                    <span>Long trading — analyse toutes les 4h</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-emerald-400 mt-0.5">✓</span>
                    <span>3 trades actifs simultanés</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-emerald-400 mt-0.5">✓</span>
                    <span>Support standard</span>
                  </li>
                </ul>
              </div>
            </div>

            <div className="mt-auto">
              <a href="/register" className="block text-center px-6 py-3 border border-gray-600 hover:border-emerald-500 hover:text-emerald-400 rounded-xl transition">
                Commencer
              </a>
            </div>
          </div>

          {/* Plan Premium */}
          <div className="p-8 bg-emerald-500/10 rounded-2xl border-2 border-emerald-500 relative flex flex-col">
            <div className="absolute -top-4 left-1/2 -translate-x-1/2 px-4 py-1 bg-emerald-500 text-black text-sm font-bold rounded-full whitespace-nowrap">
              Le plus populaire
            </div>
            <div>
              <h3 className="text-xl font-bold mb-1">Premium</h3>
              <p className="text-gray-400 text-sm mb-4">Trading day & long avec signaux avancés</p>
              <div className="text-4xl font-bold my-4">
                119.99€<span className="text-lg text-gray-400">/mois</span>
              </div>
              <p className="text-gray-500 text-xs mb-6">≈ $129 / 78 650 FCFA</p>

              <div className="border-t border-emerald-500/30 pt-6 mb-6">
                <p className="text-xs text-gray-500 uppercase tracking-widest mb-4">Tout Basic, plus</p>
                <ul className="space-y-3 text-gray-300">
                  <li className="flex items-start gap-2">
                    <span className="text-emerald-400 mt-0.5">✓</span>
                    <span>Day trading — analyse toutes les 2h et 1h</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-emerald-400 mt-0.5">✓</span>
                    <span>5 signaux de trade simultanés</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-emerald-400 mt-0.5">✓</span>
                    <span>Support prioritaire</span>
                  </li>
                </ul>
              </div>
            </div>

            <div className="mt-auto">
              <a href="/register" className="block text-center px-6 py-3 bg-emerald-500 hover:bg-emerald-400 text-black font-bold rounded-xl transition">
                Choisir Premium
              </a>
            </div>
          </div>

          {/* Plan Partner */}
          <div className="p-8 bg-amber-500/5 rounded-2xl border border-amber-500/50 relative flex flex-col">
            <div className="absolute -top-4 left-1/2 -translate-x-1/2 px-4 py-1 bg-amber-500 text-black text-sm font-bold rounded-full whitespace-nowrap">
              Max Power
            </div>
            <div>
              <h3 className="text-xl font-bold mb-1 text-amber-400">Partner</h3>
              <p className="text-gray-400 text-sm mb-4">Puissance maximale pour traders sérieux</p>
              <div className="text-4xl font-bold my-4 text-amber-400">
                299.99€<span className="text-lg text-gray-400">/mois</span>
              </div>
              <p className="text-gray-500 text-xs mb-6">≈ $323 / 196 750 FCFA</p>

              <div className="border-t border-amber-500/30 pt-6 mb-6">
                <p className="text-xs text-gray-500 uppercase tracking-widest mb-4">Tout Premium, plus</p>
                <ul className="space-y-3 text-gray-300">
                  <li className="flex items-start gap-2">
                    <span className="text-amber-400 mt-0.5">✓</span>
                    <span>Scalping — analyse toutes les 30min</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-amber-400 mt-0.5">✓</span>
                    <span>Session continue 10min activable manuellement</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-amber-400 mt-0.5">✓</span>
                    <span>Jusqu'à 10 paires en simultané</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-amber-400 mt-0.5">✓</span>
                    <span>Alertes email en temps réel</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-amber-400 mt-0.5">✓</span>
                    <span>Analyses de marché détaillées</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-amber-400 mt-0.5">✓</span>
                    <span>Account manager dédié</span>
                  </li>
                </ul>
              </div>
            </div>

            <div className="mt-auto">
              <a href="/register" className="block text-center px-6 py-3 bg-amber-500 hover:bg-amber-400 text-black font-bold rounded-xl transition">
                Devenir Partner
              </a>
            </div>
          </div>

        </div>
      </section>

      {/* ========== FOOTER ========== */}
      <footer className="px-8 py-12 border-t border-gray-800 text-center text-gray-500 text-sm">
        <div className="text-xl font-bold text-emerald-400 mb-4">
          Flux<span className="text-white">Trade</span>
        </div>
        <p>© 2025 FluxTrade. Tous droits réservés.</p>
        <p className="mt-2">Le trading comporte des risques. Les performances passées ne garantissent pas les résultats futurs.</p>
      </footer>

    </main>
  )
}