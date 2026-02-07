import { useState } from 'react'
import ImageUploader from './components/ImageUploader'
import './App.css'

function App() {
  const [imageFile, setImageFile] = useState(null)
  const [imageBase64, setImageBase64] = useState(null)

  const handleImageSelected = (file, base64) => {
    setImageFile(file)
    setImageBase64(base64)
    console.log("File selected:", file)
    console.log("Base64 available (truncated):", base64.substring(0, 50) + "...")
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-black text-white p-4 md:p-8">
      <div className="w-full h-full">
        <header className="mb-8 flex items-center justify-between">
          <div>
            <h1 className="text-4xl md:text-5xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-emerald-400">
              AI Vision Uploader
            </h1>
            <p className="text-gray-400 mt-2 text-lg">
              Upload an image to process with Google Cloud Vision or OpenAI Vision.
            </p>
          </div>
        </header>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 h-[calc(100vh-180px)]">
          <div className="bg-white/10 backdrop-blur-lg rounded-3xl p-6 border border-white/20 shadow-2xl flex flex-col">
            <h2 className="text-2xl font-semibold mb-4 text-white/90">Input Image</h2>
            <div className="flex-1 flex flex-col">
              <ImageUploader onImageSelected={handleImageSelected} />
            </div>
          </div>

          <div className="bg-white/5 backdrop-blur-lg rounded-3xl p-6 border border-white/10 shadow-xl flex flex-col">
            <h2 className="text-2xl font-semibold mb-4 text-white/90">Processing Results</h2>
            {imageFile ? (
              <div className="flex-1 space-y-6 overflow-y-auto">
                <div className="p-4 bg-black/30 rounded-xl border border-white/10">
                  <h3 className="text-xl font-semibold mb-2 text-blue-300">Image Details</h3>
                  <div className="grid grid-cols-2 gap-4 text-sm text-gray-300">
                    <div>
                      <span className="block text-gray-500 text-xs uppercase tracking-wider">Name</span>
                      {imageFile.name}
                    </div>
                    <div>
                      <span className="block text-gray-500 text-xs uppercase tracking-wider">Size</span>
                      {(imageFile.size / 1024).toFixed(2)} KB
                    </div>
                    <div>
                      <span className="block text-gray-500 text-xs uppercase tracking-wider">Type</span>
                      {imageFile.type}
                    </div>
                  </div>
                </div>

                <div className="p-4 bg-black/30 rounded-xl border border-white/10 flex-1">
                  <h3 className="text-xl font-semibold mb-2 text-purple-300">Next Steps</h3>
                  <p className="text-gray-400 mb-4">
                    The image is ready to be sent to Cloud Vision or OpenAI.
                  </p>
                  {/* Placeholder for future sub-image results */}
                  <div className="h-32 border-2 border-dashed border-gray-700 rounded-lg flex items-center justify-center text-gray-600">
                    Results will appear here...
                  </div>
                </div>
              </div>
            ) : (
              <div className="flex-1 flex items-center justify-center text-gray-500">
                <p>Upload an image to see details and processing options.</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

export default App
