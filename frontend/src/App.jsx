import { useState, useEffect } from 'react'
import ImageUploader from './components/ImageUploader'
import LoginButton from './components/LoginButton'
import LogoutButton from './components/LogoutButton'
import { useAuth0 } from '@auth0/auth0-react'
import { analyzeImage } from './lib/api'
import './App.css'

function App() {
  const { user, isAuthenticated, isLoading, getAccessTokenSilently } = useAuth0()
  const [imageFile, setImageFile] = useState(null)
  const [imageBase64, setImageBase64] = useState(null)
  const [analysisResult, setAnalysisResult] = useState(null)
  const [isAnalyzing, setIsAnalyzing] = useState(false)

  const handleImageSelected = (file, base64) => {
    setImageFile(file)
    setImageBase64(base64)
    setAnalysisResult(null)
  }

  const handleAnalyze = async () => {
    if (!imageFile) return;
    setIsAnalyzing(true);
    try {
      const token = await getAccessTokenSilently();
      const result = await analyzeImage(imageFile, token);
      setAnalysisResult(result);
    } catch (error) {
      console.error("Analysis failed:", error);
      alert("Failed to analyze image. Ensure you are logged in.");
    } finally {
      setIsAnalyzing(false);
    }
  };

  if (isLoading) {
    return <div className="min-h-screen flex items-center justify-center text-white">Loading...</div>
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-black text-white p-4 md:p-8">
      <div className="w-full h-full max-w-7xl mx-auto">
        <header className="mb-8 flex items-center justify-between">
          <div>
            <h1 className="text-4xl md:text-5xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-emerald-400">
              Shopping Suggester
            </h1>
            <p className="text-gray-400 mt-2 text-lg">
              Upload an image to process with our Agentic Workflow.
            </p>
          </div>
          <div className="flex items-center gap-4">
            {isAuthenticated ? (
              <div className="flex items-center gap-4">
                <span className="text-sm text-gray-300">Welcome, {user.name}</span>
                <LogoutButton />
              </div>
            ) : (
              <LoginButton />
            )}
          </div>
        </header>

        {isAuthenticated ? (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            <div className="bg-white/10 backdrop-blur-lg rounded-3xl p-6 border border-white/20 shadow-2xl flex flex-col">
              <h2 className="text-2xl font-semibold mb-4 text-white/90">Input Image</h2>
              <div className="flex-1 flex flex-col">
                <ImageUploader onImageSelected={handleImageSelected} />
                {imageFile && (
                  <button
                    onClick={handleAnalyze}
                    disabled={isAnalyzing}
                    className="mt-4 py-3 px-6 bg-blue-600 hover:bg-blue-700 rounded-xl font-semibold transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {isAnalyzing ? "Analyzing..." : "Analyze Image"}
                  </button>
                )}
              </div>
            </div>

            <div className="bg-white/5 backdrop-blur-lg rounded-3xl p-6 border border-white/10 shadow-xl flex flex-col">
              <h2 className="text-2xl font-semibold mb-4 text-white/90">Processing Results</h2>
              {analysisResult ? (
                <div className="p-4 bg-black/30 rounded-xl border border-white/10">
                  <h3 className="text-xl font-semibold mb-2 text-green-400">Analysis Complete</h3>
                  <div className="space-y-2">
                    <p><span className="text-gray-400">Item:</span> <span className="font-medium">{analysisResult.item_name}</span></p>
                    <p className="text-gray-300">{analysisResult.description}</p>
                    <div className="flex flex-wrap gap-2 mt-2">
                      {analysisResult.detected_keywords?.map((kw, i) => (
                        <span key={i} className="px-3 py-1 bg-gray-700 rounded-full text-sm text-gray-300">#{kw}</span>
                      ))}
                    </div>
                  </div>
                </div>
              ) : imageFile ? (
                <div className="flex-1 space-y-6 overflow-y-auto">
                  <div className="p-4 bg-black/30 rounded-xl border border-white/10">
                    <h3 className="text-xl font-semibold mb-2 text-blue-300">Ready to Analyze</h3>
                    <p className="text-gray-400">Click "Analyze Image" to start the workflow.</p>
                  </div>
                </div>
              ) : (
                <div className="flex-1 flex items-center justify-center text-gray-500">
                  <p>Upload an image to see details and processing options.</p>
                </div>
              )}
            </div>
          </div>
        ) : (
          <div className="flex flex-col items-center justify-center h-96 bg-white/5 rounded-3xl border border-white/10 p-8 text-center">
            <h2 className="text-3xl font-bold mb-4">Please Log In</h2>
            <p className="text-gray-400 mb-8 max-w-md">
              You need to be authenticated to use the Shopping Suggester features.
            </p>
            <LoginButton />
          </div>
        )}
      </div>
    </div>
  )
}

export default App
