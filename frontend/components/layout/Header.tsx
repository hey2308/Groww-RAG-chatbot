export function Header() {
  return (
    <header className="bg-white shadow-sm border-b border-gray-200">
      <div className="max-w-4xl mx-auto px-4 py-4 flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Mutual Fund FAQ Assistant</h1>
        <span className="text-sm text-gray-600 bg-yellow-100 px-3 py-1 rounded-full">
          Facts-only. No investment advice.
        </span>
      </div>
    </header>
  );
}

