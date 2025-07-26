import { useState, useEffect } from 'react'

function App() {
  const [ticker, setTicker] = useState('')
  const [filings, setFilings] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const tickers = ['TSLA', 'AAPL', 'MSFT', 'DVLT', 'RANI']

  useEffect(() => {
    if (ticker) {
      setLoading(true)
      setError(null)
      fetch(`http://localhost:8000/filings/${ticker}`)
        .then(response => {
          if (!response.ok) {
            throw new Error('No filings found')
          }
          return response.json()
        })
        .then(data => {
          setFilings(data)
          setLoading(false)
        })
        .catch(err => {
          setError(err.message)
          setFilings([])
          setLoading(false)
        })
    }
  }, [ticker])

  const handleDownload = (format) => {
    window.location.href = `http://localhost:8000/download/${ticker}?format=${format}`
  }

  return (
    <div className="min-h-screen bg-gray-100 flex flex-col items-center p-4">
      <h1 className="text-3xl font-bold mb-6">SECChronicle</h1>
      <select 
        className="mb-4 p-2 border border-gray-300 rounded"
        value={ticker}
        onChange={(e) => setTicker(e.target.value)}
      >
        <option value="">Select Ticker</option>
        {tickers.map(t => (
          <option key={t} value={t}>{t}</option>
        ))}
      </select>
      {loading && <p>Loading...</p>}
      {error && <p className="text-red-500">{error}</p>}
      {filings.length === 0 && !loading && ticker && <p>No Filings Found</p>}
      <div className="w-full max-w-2xl">
        {filings.map((filing, index) => (
          <div key={index} className="mb-6 p-4 bg-white rounded shadow">
            <h2 className="text-xl font-semibold">{filing.date} - {filing.type}</h2>
            <p>{filing.summary}</p>
          </div>
        ))}
      </div>
      {filings.length > 0 && (
        <div className="mt-4">
          <button 
            className="mr-2 px-4 py-2 bg-blue-500 text-white rounded"
            onClick={() => handleDownload('markdown')}
          >
            Download Markdown
          </button>
          <button 
            className="px-4 py-2 bg-green-500 text-white rounded"
            onClick={() => handleDownload('pdf')}
          >
            Download PDF
          </button>
        </div>
      )}
    </div>
  )
}

export default App
