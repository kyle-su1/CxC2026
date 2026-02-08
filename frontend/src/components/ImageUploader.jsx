import { useState, useRef, useEffect } from 'react'

const ImageUploader = ({ onImageSelected, initialImage, overlays = [] }) => {
    const [preview, setPreview] = useState(initialImage || null)
    const [isDragging, setIsDragging] = useState(false)
    const fileInputRef = useRef(null)

    useEffect(() => {
        if (initialImage) {
            setPreview(initialImage)
        }
    }, [initialImage])

    const handleFile = (file) => {
        if (file && file.type.startsWith('image/')) {
            const reader = new FileReader()
            reader.onload = (e) => {
                const img = new Image();
                img.onload = () => {
                    // Convert to JPEG using Canvas
                    const canvas = document.createElement('canvas');
                    canvas.width = img.width;
                    canvas.height = img.height;
                    const ctx = canvas.getContext('2d');
                    ctx.drawImage(img, 0, 0);

                    // Get JPEG Base64
                    const jpegBase64 = canvas.toDataURL('image/jpeg', 0.9);

                    setPreview(jpegBase64)
                    if (onImageSelected) {
                        // Pass original file for name/metadata, but NEW base64 for processing
                        onImageSelected(file, jpegBase64)
                    }
                };
                img.src = e.target.result;
            }
            reader.readAsDataURL(file)
        }
    }

    // ... (handlers remain the same) ...
    const handleDrop = (e) => {
        e.preventDefault()
        setIsDragging(false)
        if (e.dataTransfer.files && e.dataTransfer.files[0]) {
            handleFile(e.dataTransfer.files[0])
        }
    }

    const handleDragOver = (e) => {
        e.preventDefault()
        setIsDragging(true)
    }

    const handleDragLeave = (e) => {
        e.preventDefault()
        setIsDragging(false)
    }

    const handleClick = () => {
        fileInputRef.current.click()
    }

    const handleInputChange = (e) => {
        if (e.target.files && e.target.files[0]) {
            handleFile(e.target.files[0])
        }
    }

    return (
        <div className="w-full h-full">
            <div
                onClick={handleClick}
                onDrop={handleDrop}
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                className={`
          relative group cursor-pointer 
          border border-dashed rounded-xl
          transition-all duration-300 ease-in-out
          flex flex-col items-center justify-center
          h-full min-h-[400px] w-full overflow-hidden
          ${isDragging
                        ? 'border-emerald-500 bg-emerald-500/10 shadow-[0_0_30px_rgba(16,185,129,0.15)]'
                        : 'border-white/10 hover:border-white/20 hover:bg-white/5'
                    }
        `}
            >
                <input
                    type="file"
                    ref={fileInputRef}
                    onChange={handleInputChange}
                    className="hidden"
                    accept="image/*"
                />

                {preview ? (
                    <div className="relative w-full h-full flex items-center justify-center">
                        {/* Image Container with relative positioning for overlays */}
                        <div className="relative inline-flex max-h-full max-w-full">
                            <img
                                src={preview}
                                alt="Preview"
                                className="max-h-[calc(100vh-350px)] max-w-full w-auto h-auto rounded-lg shadow-2xl object-contain border border-white/10"
                            />

                            {/* Bounding Box Overlays */}
                            {overlays && overlays.map((obj, idx) => {
                                const vertices = obj.boundingPoly?.normalizedVertices;
                                if (!vertices || vertices.length < 4) return null;

                                const xs = vertices.map(v => v.x || 0);
                                const ys = vertices.map(v => v.y || 0);
                                const minX = Math.min(...xs) * 100;
                                const maxX = Math.max(...xs) * 100;
                                const minY = Math.min(...ys) * 100;
                                const maxY = Math.max(...ys) * 100;
                                const width = maxX - minX;
                                const height = maxY - minY;

                                return (
                                    <div
                                        key={idx}
                                        className="absolute border border-emerald-400/80 bg-emerald-500/10 hover:bg-emerald-500/20 transition-colors z-10"
                                        style={{
                                            left: `${minX}%`,
                                            top: `${minY}%`,
                                            width: `${width}%`,
                                            height: `${height}%`,
                                        }}
                                    >
                                        <span className="absolute -top-6 left-0 bg-emerald-600/90 backdrop-blur text-white text-[10px] font-medium px-2 py-0.5 rounded shadow-lg whitespace-nowrap border border-white/10">
                                            {obj.name} <span className="text-white/70">{(obj.score * 100).toFixed(0)}%</span>
                                        </span>
                                    </div>
                                );
                            })}

                            <div className={`absolute inset-0 bg-black/60 backdrop-blur-[2px] transition-opacity flex items-center justify-center rounded-lg opacity-0 group-hover/image:opacity-100 cursor-pointer`}>
                                <div className="flex items-center gap-2 text-white font-medium bg-black/50 px-4 py-2 rounded-full border border-white/10">
                                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12"></path></svg>
                                    Replace Image
                                </div>
                            </div>
                        </div>
                    </div>
                ) : (
                    <div className="text-center p-8">
                        <div className={`w-16 h-16 mx-auto mb-6 rounded-2xl flex items-center justify-center transition-all duration-300 ${isDragging ? 'bg-emerald-500/20 text-emerald-400' : 'bg-white/5 text-gray-500 group-hover:bg-white/10 group-hover:text-gray-300'}`}>
                            <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                            </svg>
                        </div>
                        <h3 className="text-lg font-medium text-white mb-2">
                            Drop image here
                        </h3>
                        <p className="text-sm text-gray-500 max-w-[200px] mx-auto">
                            Support for PNG, JPG, and WEBP. Max size 10MB.
                        </p>
                    </div>
                )}
            </div>
        </div>
    )
}

export default ImageUploader
