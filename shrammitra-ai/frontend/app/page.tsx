"use client";
import Link from "next/link";

function Logo() {
  return (
    <svg width="18" height="18" viewBox="0 0 256 256" fill="none">
      <path
        fill="rgb(84, 84, 84)"
        d="M 160 88 L 194 34 L 216 0 L 256 0 L 256 40 L 221.5 93.5 L 200 128 L 256 128 L 256 256 L 96 256 L 96 168 L 64.246 220 L 40 256 L 0 256 L 0 216 L 34 162 L 56 128 L 0 128 L 0 0 L 160 0 Z"
      />
    </svg>
  );
}

function Divider() {
  return <div className="w-full border-t border-gray-200" />;
}

const WORKER_CATEGORIES = [
  { title: "Agricultural Workers",  desc: "Crop harvesting, farm labour, seasonal migrants" },
  { title: "Construction Workers",  desc: "BOCW rights, safety entitlements, site wages" },
  { title: "Domestic Workers",      desc: "Minimum wage, leave rights, employment terms" },
  { title: "Brick Kiln Workers",    desc: "Bonded labour protection, advance repayment" },
  { title: "Garment & Textile",     desc: "Factory Act, overtime pay, maternity benefit" },
  { title: "Plantation Workers",    desc: "Tea & coffee labour laws, housing rights" },
  { title: "Transport & Logistics", desc: "Motor Transport Act, driving hour limits" },
  { title: "Hospitality & Food",    desc: "Hotel workers, restaurant staff, tip rules" },
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

const HOW_IT_WORKS = [
  ["01", "Describe your situation", "Type your question in plain language — in any of 7 Indian languages or English."],
  ["02", "Get an instant answer", "ShramMitra searches 16+ official sources and gives you a clear, cited response."],
  ["03", "Know your next step", "Understand your rights, file a complaint, or contact the right authority — from the answer."],
] as const;

export default function HomePage() {
  return (
    <main className="bg-[#f0f0ee] text-gray-900">

      {/* Hero */}
      <div className="relative min-h-screen overflow-hidden bg-[#f0f0ee]">
        <video
          className="absolute inset-0 w-full h-full object-cover"
          src="https://d8j0ntlcm91z4.cloudfront.net/user_38xzZboKViGWJOttwIXH07lWA1P/hf_20260508_215831_c6a8989c-d716-4d8d-8745-e972a2eec711.mp4"
          autoPlay muted loop playsInline
        />
        <div className="relative z-10 flex flex-col min-h-screen">
          <nav className="flex items-center justify-center pt-4 sm:pt-6 px-4 sm:px-8 gap-2 sm:gap-3">
            <div
              className="flex items-center justify-center rounded-full shrink-0"
              style={{ backgroundColor: "#EDEDED", width: "clamp(36px, 4vw, 44px)", height: "clamp(36px, 4vw, 44px)" }}
            >
              <Logo />
            </div>
            <div
              className="flex items-center rounded-xl"
              style={{ backgroundColor: "#EDEDED", gap: "clamp(16px, 4vw, 40px)", padding: "clamp(8px, 1vw, 12px) clamp(16px, 3vw, 32px)" }}
            >
              {(["Story", "Products", "Help", "Support"] as const).map((label) => {
                const href = label === "Products" ? "/chat" : label === "Support" ? "/admin/analytics" : "#";
                return (
                  <Link
                    key={label}
                    href={href}
                    className="font-medium text-gray-700 hover:text-gray-900 transition-colors duration-200 whitespace-nowrap"
                    style={{ fontFamily: "Arial, sans-serif", fontSize: "clamp(11px, 1.3vw, 14px)" }}
                  >
                    {label}
                  </Link>
                );
              })}
            </div>
          </nav>
          <div className="flex-1 flex items-end pb-10 sm:pb-16 lg:pb-20 px-6 sm:px-12 md:px-20 lg:px-28">
            <div className="max-w-[280px] sm:max-w-[320px] lg:max-w-[380px]">
              <Link
                href="#"
                className="inline-flex items-center gap-1.5 font-medium text-blue-500 hover:text-blue-600 transition-colors mb-3 group"
                style={{ fontFamily: "Arial, sans-serif", fontSize: "clamp(10px, 1.2vw, 11.5px)" }}
              >
                AI-Powered · Free · Multilingual
                <span className="inline-block transition-transform duration-200 group-hover:translate-x-0.5">→</span>
              </Link>
              <h1
                className="leading-[1.15] font-bold text-gray-900 tracking-tight mb-3"
                style={{ fontFamily: "Arial, sans-serif", fontSize: "clamp(22px, 4vw, 38px)" }}
              >
                Simple, smart legal aid made for workers who keep fighting.
              </h1>
              <p
                className="text-gray-400 font-normal mb-4"
                style={{ fontFamily: "Arial, sans-serif", fontSize: "clamp(11px, 1.3vw, 13px)" }}
              >
                Reclaim your rights now.
              </p>
              <Link
                href="/chat"
                className="inline-flex items-center gap-2 font-medium text-gray-700 border border-gray-300 rounded-full bg-white hover:bg-gray-50 hover:border-gray-400 transition-all duration-200 group"
                style={{ fontFamily: "Arial, sans-serif", fontSize: "clamp(11px, 1.3vw, 13px)", padding: "clamp(7px, 1vw, 10px) clamp(14px, 2vw, 20px)" }}
              >
                Try a free consultation
                <span className="transition-transform duration-200 group-hover:translate-x-0.5">→</span>
              </Link>
            </div>
          </div>
        </div>
      </div>

      {/* Below-fold */}
      <div className="bg-[#f0f0ee] text-gray-900">

        {/* Stats */}
        <Divider />
        <div className="max-w-5xl mx-auto px-6 sm:px-12 flex flex-wrap">
          {([ ["16+","Official sources"], ["7","Indian languages"], ["100%","Free to use"], ["24/7","Always available"] ] as const).map(([num, label], i) => (
            <div
              key={label}
              className="py-10 text-left"
              style={{ paddingRight: "2.5rem", borderLeft: i > 0 ? "1px solid #e5e7eb" : "none", paddingLeft: i > 0 ? "2.5rem" : "0" }}
            >
              <div className="font-bold text-gray-900 leading-none mb-1" style={{ fontFamily: "Arial, sans-serif", fontSize: "clamp(26px, 3.5vw, 40px)" }}>{num}</div>
              <div className="text-[12px] text-gray-500 font-normal whitespace-nowrap" style={{ fontFamily: "Arial, sans-serif" }}>{label}</div>
            </div>
          ))}
        </div>

        {/* Languages */}
        <Divider />
        <div className="max-w-5xl mx-auto px-6 sm:px-12 py-5 flex items-center flex-wrap">
          <span className="text-[11px] uppercase tracking-widest text-gray-400 font-medium mr-4" style={{ fontFamily: "Arial, sans-serif" }}>Available in</span>
          {LANGUAGES.map((lang, i) => (
            <span key={lang} className="flex items-center">
              <span className="text-[13px] text-gray-600" style={{ fontFamily: "Arial, sans-serif" }}>{lang}</span>
              {i < LANGUAGES.length - 1 && <span className="text-gray-300 mx-2 text-[11px]">·</span>}
            </span>
          ))}
        </div>

        {/* How it works */}
        <Divider />
        <div className="max-w-5xl mx-auto px-6 sm:px-12 py-14">
          <p className="text-[11px] sm:text-[12px] uppercase tracking-widest text-gray-400 font-medium mb-10" style={{ fontFamily: "Arial, sans-serif" }}>How it works</p>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-10">
            {HOW_IT_WORKS.map(([num, title, body]) => (
              <div key={num}>
                <div className="text-[11px] text-gray-400 font-medium mb-3" style={{ fontFamily: "Arial, sans-serif" }}>{num}</div>
                <div className="text-[15px] font-semibold text-gray-900 mb-2 leading-snug" style={{ fontFamily: "Arial, sans-serif" }}>{title}</div>
                <p className="text-[13px] text-gray-500 leading-relaxed" style={{ fontFamily: "Arial, sans-serif" }}>{body}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Sectors */}
        <Divider />
        <div className="max-w-5xl mx-auto px-6 sm:px-12 py-14">
          <p className="text-[11px] sm:text-[12px] uppercase tracking-widest text-gray-400 font-medium mb-8" style={{ fontFamily: "Arial, sans-serif" }}>Sectors covered</p>
          <div>
            {WORKER_CATEGORIES.map((cat) => (
              <Link
                key={cat.title}
                href={`/chat?topic=${encodeURIComponent(cat.title)}`}
                className="flex items-center justify-between py-4 px-2 border-b border-gray-200 group hover:bg-white/60 transition-colors duration-150"
              >
                <div className="flex items-baseline gap-6">
                  <span className="font-medium text-gray-900 text-[14px] sm:text-[15px] group-hover:text-gray-500 transition-colors min-w-[160px] sm:min-w-[210px]" style={{ fontFamily: "Arial, sans-serif" }}>{cat.title}</span>
                  <span className="text-[12px] sm:text-[13px] text-gray-400 hidden sm:block" style={{ fontFamily: "Arial, sans-serif" }}>{cat.desc}</span>
                </div>
                <span className="text-gray-300 group-hover:text-gray-500 group-hover:translate-x-0.5 transition-all duration-200 text-[16px] ml-4 shrink-0">→</span>
              </Link>
            ))}
          </div>
        </div>

        {/* Questions */}
        <Divider />
        <div className="max-w-5xl mx-auto px-6 sm:px-12 py-14">
          <p className="text-[11px] sm:text-[12px] uppercase tracking-widest text-gray-400 font-medium mb-8" style={{ fontFamily: "Arial, sans-serif" }}>Common questions</p>
          <div>
            {QUICK_QUESTIONS.map((q) => (
              <Link
                key={q}
                href={`/chat?q=${encodeURIComponent(q)}`}
                className="flex items-center justify-between py-4 px-2 border-b border-gray-200 group hover:bg-white/60 transition-colors duration-150"
              >
                <span className="text-[14px] sm:text-[15px] text-gray-800 group-hover:text-gray-500 transition-colors" style={{ fontFamily: "Arial, sans-serif" }}>{q}</span>
                <span className="text-gray-300 group-hover:text-gray-500 group-hover:translate-x-0.5 transition-all duration-200 text-[16px] ml-4 shrink-0">→</span>
              </Link>
            ))}
          </div>
          <div className="pt-10">
            <Link
              href="/chat"
              className="inline-flex items-center gap-2 font-medium text-gray-700 border border-gray-300 rounded-full bg-white hover:bg-gray-50 hover:border-gray-400 transition-all duration-200 group"
              style={{ fontFamily: "Arial, sans-serif", fontSize: "13px", padding: "10px 22px" }}
            >
              Ask your question free
              <span className="transition-transform duration-200 group-hover:translate-x-0.5">→</span>
            </Link>
          </div>
        </div>

        {/* Footer */}
        <Divider />
        <footer className="py-8 px-6 sm:px-12 max-w-5xl mx-auto flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
          <span className="text-[12px] text-gray-400" style={{ fontFamily: "Arial, sans-serif" }}>ShramMitra AI · Built for migrant workers of Bengaluru</span>
          <span className="text-[12px] text-gray-400" style={{ fontFamily: "Arial, sans-serif" }}>Not a substitute for legal advice</span>
        </footer>
      </div>
    </main>
  );
}
