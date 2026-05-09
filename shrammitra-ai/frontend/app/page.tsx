import Link from "next/link";

const WORKER_CATEGORIES = [
  {
    icon: "🌾",
    title: "Agricultural Workers",
    desc: "Crop harvesting, farm labour, seasonal migrants",
    color: "bg-green-50 border-green-200 hover:bg-green-100",
    badge: "bg-green-100 text-green-800",
  },
  {
    icon: "🏗️",
    title: "Construction Workers",
    desc: "Building sites, BOCW rights, safety entitlements",
    color: "bg-orange-50 border-orange-200 hover:bg-orange-100",
    badge: "bg-orange-100 text-orange-800",
  },
  {
    icon: "🏠",
    title: "Domestic Workers",
    desc: "Household help, minimum wage, leave rights",
    color: "bg-purple-50 border-purple-200 hover:bg-purple-100",
    badge: "bg-purple-100 text-purple-800",
  },
  {
    icon: "🧱",
    title: "Brick Kiln Workers",
    desc: "Bonded labour protection, advance repayment rights",
    color: "bg-red-50 border-red-200 hover:bg-red-100",
    badge: "bg-red-100 text-red-800",
  },
  {
    icon: "🪡",
    title: "Garment & Textile",
    desc: "Factory Act, overtime pay, maternity benefit",
    color: "bg-pink-50 border-pink-200 hover:bg-pink-100",
    badge: "bg-pink-100 text-pink-800",
  },
  {
    icon: "🍵",
    title: "Plantation Workers",
    desc: "Tea, coffee, plantation labour laws, housing",
    color: "bg-teal-50 border-teal-200 hover:bg-teal-100",
    badge: "bg-teal-100 text-teal-800",
  },
  {
    icon: "🚛",
    title: "Transport & Logistics",
    desc: "Motor Transport Act, driving hour limits",
    color: "bg-blue-50 border-blue-200 hover:bg-blue-100",
    badge: "bg-blue-100 text-blue-800",
  },
  {
    icon: "🍽️",
    title: "Hospitality & Food",
    desc: "Hotel workers, restaurants, tip regulations",
    color: "bg-yellow-50 border-yellow-200 hover:bg-yellow-100",
    badge: "bg-yellow-100 text-yellow-800",
  },
];

const LANGUAGES = ["हिंदी", "ಕನ್ನಡ", "தமிழ்", "తెలుగు", "বাংলা", "ଓଡ଼ିଆ", "English"];

const QUICK_QUESTIONS = [
  "What is the minimum wage for construction workers in Karnataka?",
  "How do I register under e-Shram portal?",
  "What are my rights if my employer doesn't pay on time?",
  "Am I eligible for EPFO provident fund?",
  "What safety equipment must my employer provide?",
  "How do I file a complaint against my contractor?",
];

export default function HomePage() {
  return (
    <main className="min-h-screen bg-gradient-to-b from-blue-950 via-blue-900 to-slate-900 text-white">

      {/* ── Nav ── */}
      <nav className="flex items-center justify-between px-6 py-4 max-w-6xl mx-auto">
        <div className="flex items-center gap-2">
          <span className="text-2xl">⚖️</span>
          <span className="font-bold text-xl tracking-tight">ShramMitra AI</span>
        </div>
        <div className="flex gap-3">
          <Link href="/chat"
            className="px-4 py-2 bg-white text-blue-900 rounded-lg font-semibold text-sm hover:bg-blue-50 transition">
            Start Chat
          </Link>
          <Link href="/admin/analytics"
            className="px-4 py-2 border border-white/30 rounded-lg text-sm hover:bg-white/10 transition">
            Admin
          </Link>
        </div>
      </nav>

      {/* ── Hero ── */}
      <section className="text-center px-6 pt-16 pb-12 max-w-4xl mx-auto">
        <div className="inline-flex items-center gap-2 bg-white/10 rounded-full px-4 py-1.5 text-sm mb-6">
          <span className="w-2 h-2 bg-green-400 rounded-full animate-pulse" />
          AI-Powered · Free · Multilingual
        </div>
        <h1 className="text-4xl md:text-6xl font-extrabold leading-tight mb-4">
          Know Your Rights as a<br />
          <span className="text-yellow-400">Migrant Worker</span>
        </h1>
        <p className="text-lg md:text-xl text-blue-200 mb-8 max-w-2xl mx-auto">
          Get instant answers about wages, safety, contracts, and legal protections —
          in your own language, powered by official Indian labour laws.
        </p>

        {/* Language pills */}
        <div className="flex flex-wrap justify-center gap-2 mb-10">
          {LANGUAGES.map((lang) => (
            <span key={lang}
              className="px-3 py-1 bg-white/15 rounded-full text-sm font-medium">
              {lang}
            </span>
          ))}
        </div>

        <Link href="/chat"
          className="inline-flex items-center gap-2 bg-yellow-400 hover:bg-yellow-300 text-blue-950 font-bold text-lg px-8 py-4 rounded-xl transition shadow-lg shadow-yellow-400/20">
          💬 Ask Your Question Now
          <span className="text-xl">→</span>
        </Link>
      </section>

      {/* ── Worker Categories ── */}
      <section className="max-w-6xl mx-auto px-6 py-12">
        <h2 className="text-2xl font-bold text-center mb-2">Who is this for?</h2>
        <p className="text-blue-300 text-center mb-8">
          Covering rights for all major migrant worker sectors in Bengaluru & Karnataka
        </p>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {WORKER_CATEGORIES.map((cat) => (
            <Link key={cat.title} href={`/chat?topic=${encodeURIComponent(cat.title)}`}
              className={`${cat.color} border rounded-xl p-4 text-gray-800 transition cursor-pointer group`}>
              <div className="text-3xl mb-2">{cat.icon}</div>
              <div className="font-semibold text-sm leading-tight mb-1">{cat.title}</div>
              <div className="text-xs text-gray-500">{cat.desc}</div>
            </Link>
          ))}
        </div>
      </section>

      {/* ── Quick Questions ── */}
      <section className="max-w-4xl mx-auto px-6 py-8">
        <h2 className="text-xl font-semibold text-center mb-6">Common questions workers ask</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {QUICK_QUESTIONS.map((q) => (
            <Link key={q} href={`/chat?q=${encodeURIComponent(q)}`}
              className="flex items-start gap-3 bg-white/8 hover:bg-white/15 border border-white/10 rounded-lg px-4 py-3 text-sm transition">
              <span className="text-yellow-400 mt-0.5">→</span>
              <span className="text-blue-100">{q}</span>
            </Link>
          ))}
        </div>
      </section>

      {/* ── Stats strip ── */}
      <section className="max-w-4xl mx-auto px-6 py-10">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-6 text-center">
          {[
            ["16+", "Official sources indexed"],
            ["7", "Indian languages"],
            ["100%", "Free to use"],
            ["24/7", "Always available"],
          ].map(([num, label]) => (
            <div key={label}>
              <div className="text-3xl font-extrabold text-yellow-400">{num}</div>
              <div className="text-sm text-blue-300 mt-1">{label}</div>
            </div>
          ))}
        </div>
      </section>

      {/* ── Footer ── */}
      <footer className="border-t border-white/10 mt-8 py-6 text-center text-sm text-blue-400">
        ShramMitra AI · Built for migrant workers of Bengaluru ·{" "}
        <span className="text-blue-300">Not a substitute for legal advice</span>
      </footer>
    </main>
  );
}

