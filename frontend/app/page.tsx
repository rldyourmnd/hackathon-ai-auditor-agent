export default function Home() {
  return (
    <main className="min-h-screen bg-gray-50">
      <div className="container mx-auto px-4 py-8">
        <div className="text-center">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">
            Welcome to Curestry
          </h1>
          <p className="text-xl text-gray-600 mb-8">
            AI-powered prompt analysis and optimization platform
          </p>
          <div className="bg-white rounded-lg shadow-md p-6 max-w-2xl mx-auto">
            <h2 className="text-2xl font-semibold mb-4">Features</h2>
            <ul className="text-left space-y-2">
              <li className="flex items-center">
                <span className="text-green-500 mr-2">✓</span>
                Multi-dimensional prompt analysis
              </li>
              <li className="flex items-center">
                <span className="text-green-500 mr-2">✓</span>
                Smart patch generation
              </li>
              <li className="flex items-center">
                <span className="text-green-500 mr-2">✓</span>
                Interactive clarification system
              </li>
              <li className="flex items-center">
                <span className="text-green-500 mr-2">✓</span>
                Prompt base management
              </li>
              <li className="flex items-center">
                <span className="text-green-500 mr-2">✓</span>
                XML and Markdown support
              </li>
            </ul>
          </div>
          <div className="mt-8">
            <p className="text-sm text-gray-500">
              System Status: <span className="text-green-500 font-semibold">Ready</span>
            </p>
          </div>
        </div>
      </div>
    </main>
  )
}