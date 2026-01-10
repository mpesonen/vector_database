import { useState } from 'react'
import './style.css'

interface SearchResult {
  id: string
  title: string
  categories: string
  distance: number
}

const EXAMPLE_CATEGORIES = [
  { label: 'Computer Science', query: 'machine learning neural networks' },
  { label: 'Mathematics', query: 'algebraic geometry topology' },
  { label: 'Physics', query: 'quantum mechanics particle physics' },
  { label: 'Statistics', query: 'statistical inference bayesian methods' },
  { label: 'Economics', query: 'game theory market equilibrium' },
  { label: 'Biology', query: 'genomics protein structure' },
]

function App() {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState<SearchResult[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [hasSearched, setHasSearched] = useState(false)

  const performSearch = async (searchQuery: string) => {
    if (!searchQuery.trim()) return

    setLoading(true)
    setError(null)
    setHasSearched(true)

    try {
      const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000'
      const response = await fetch(`${apiUrl}/search`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: searchQuery, n_results: 20 }),
      })

      if (!response.ok) {
        throw new Error('Search failed')
      }

      const data = await response.json()
      setResults(data.results)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred')
    } finally {
      setLoading(false)
    }
  }

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault()
    performSearch(query)
  }

  const handleCategoryClick = (categoryQuery: string) => {
    setQuery(categoryQuery)
    performSearch(categoryQuery)
  }

  return (
    <>
      <div className="hero">
        <h1>arXiv Paper Search</h1>
        <p className="subtitle">
          Semantic search across <a href="https://arxiv.org/" target="_blank" rel="noopener noreferrer">arXiv</a> research papers (2016&ndash;present)
        </p>
        <p className="tech-stack">
          <a href="https://www.trychroma.com/" target="_blank" rel="noopener noreferrer">ChromaDB</a>
          {' + '}
          <a href="https://fastapi.tiangolo.com/" target="_blank" rel="noopener noreferrer">FastAPI</a>
          {' + '}
          <a href="https://react.dev/" target="_blank" rel="noopener noreferrer">React</a>
        </p>

        <div className="search-container">
          <form onSubmit={handleSearch} className="search-form">
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search for papers..."
              className="search-input"
            />
            <button type="submit" disabled={loading} className="search-button">
              {loading ? 'Searching...' : 'Search'}
            </button>
          </form>

          <div className="categories-section">
            <p className="categories-label">Try example search terms by field:</p>
            <div className="category-chips">
              {EXAMPLE_CATEGORIES.map((cat) => (
                <span
                  key={cat.label}
                  className="category-chip"
                  onClick={() => handleCategoryClick(cat.query)}
                >
                  {cat.label}
                </span>
              ))}
            </div>
          </div>
        </div>
      </div>

      <div className="results-section">
        <div className="results-container">
          {error && <p className="error">{error}</p>}

          {loading && <p className="loading">Searching...</p>}

          {!loading && results.length > 0 && (
            <>
              <p className="results-header">{results.length} results found</p>
              <div className="results">
                {results.map((result) => (
                  <div key={result.id} className="result-card">
                    <h3 className="result-title">
                      <a
                        href={`https://arxiv.org/abs/${result.id}`}
                        target="_blank"
                        rel="noopener noreferrer"
                      >
                        {result.title}
                      </a>
                    </h3>
                    <div className="result-meta">
                      <div className="result-categories">
                        {result.categories.split(' ').map((cat) => (
                          <span key={cat} className="result-category">{cat}</span>
                        ))}
                      </div>
                      <span className="result-distance">
                        {(1 - result.distance).toFixed(3)}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </>
          )}

          {!loading && !hasSearched && (
            <div className="empty-state">
              <p>Enter a search term or click a category above to find papers.</p>
            </div>
          )}

          {!loading && hasSearched && results.length === 0 && !error && (
            <div className="empty-state">
              <p>No results found. Try a different search term.</p>
            </div>
          )}
        </div>
      </div>
    </>
  )
}

export default App
