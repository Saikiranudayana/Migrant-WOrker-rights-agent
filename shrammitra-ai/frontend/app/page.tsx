import Link from "next/link";

export default function HomePage() {
  return (
    <main className="min-h-screen flex flex-col items-center justify-center gap-8 p-8">
      <div className="text-center">
        <h1 className="text-4xl font-bold text-brand">ShramMitra AI</h1>
        <p className="mt-2 text-gray-600">
          Multilingual AI Assistant for Migrant Worker Rights — Admin Dashboard
        </p>
      </div>
      <nav className="flex flex-col sm:flex-row gap-4">
        <Link
          href="/admin/analytics"
          className="px-6 py-3 bg-brand text-white rounded-lg hover:bg-brand-dark transition"
        >
          Analytics
        </Link>
        <Link
          href="/admin/conversations"
          className="px-6 py-3 bg-white border border-brand text-brand rounded-lg hover:bg-gray-50 transition"
        >
          Conversations
        </Link>
        <Link
          href="/admin/sources"
          className="px-6 py-3 bg-white border border-brand text-brand rounded-lg hover:bg-gray-50 transition"
        >
          Document Sources
        </Link>
      </nav>
    </main>
  );
}
