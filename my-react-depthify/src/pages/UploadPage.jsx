import React, { useState, useRef } from 'react';
import { Upload, Image, Zap, Download, Settings, Eye, RotateCcw } from 'lucide-react';
import { projectAPI } from '../services/api';

export default function UploadPage() {
  const [uploadedImage, setUploadedImage] = useState(null);
  const [uploadedFile, setUploadedFile] = useState(null);
  const [projectId, setProjectId] = useState(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [processingStep, setProcessingStep] = useState(0);
  const [result3D, setResult3D] = useState(null);
  const [dragOver, setDragOver] = useState(false);
  const [objectType, setObjectType] = useState('auto');
  const [error, setError] = useState('');
  const handleDownload = async (format = 'ply') => {
    try {
      const response = await projectAPI.downloadProject(result3D.projectId);
      const blob = new Blob([response], { type: 'application/octet-stream' });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `model_${result3D.projectId}.${format}`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Download failed:', error);
      setError('Download failed. Please try again.');
    }
  };

  const fileInputRef = useRef(null);

  const processingSteps = [
    "Analyzing image...",
    "Removing background...",
    "Generating depth map...",
    "Creating 3D model...",
    "Optimizing mesh...",
    "Adding colors...",
    "Finalizing..."
  ];

  const handleFileSelect = (file) => {
    if (file && file.type.startsWith('image/')) {
      const reader = new FileReader();
      reader.onload = (e) => {
        setUploadedImage(e.target.result);
        setUploadedFile(file);
        setResult3D(null);
        setError('');
        setProjectId(null);
      };
      reader.readAsDataURL(file);
    } else {
      setError('Please select a valid image file');
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setDragOver(false);
    const file = e.dataTransfer.files[0];
    handleFileSelect(file);
  };

  const handleFileInputChange = (e) => {
    const file = e.target.files[0];
    handleFileSelect(file);
  };

  const startProcessing = async () => {
    if (!uploadedFile) return;

    setIsProcessing(true);
    setProcessingStep(0);
    setError('');

    try {
      // Step 1: Upload file to server
      console.log('Uploading file...');
      const uploadResponse = await projectAPI.uploadImage(
        uploadedFile,
        `Project_${Date.now()}`,
        objectType
      );

      const newProjectId = uploadResponse.project_id;
      setProjectId(newProjectId);

      // Step 2: Start processing
      setProcessingStep(1);
      console.log('Starting processing...');

      // Simulate processing steps
      for (let i = 1; i < processingSteps.length; i++) {
        setProcessingStep(i);
        await new Promise(resolve => setTimeout(resolve, 1000));
      }

      // Step 3: Trigger actual processing on server
      const processResponse = await projectAPI.processProject(newProjectId);

      // Set results
      setResult3D({
        projectId: newProjectId,
        plyFile: `/api/projects/${newProjectId}/download`,
        stlFile: `/api/projects/${newProjectId}/download`,
        previewImage: uploadedImage,
        stats: {
          vertices: processResponse.project.vertices_count || 15420,
          faces: processResponse.project.faces_count || 30840,
          processingTime: `${processResponse.project.processing_time || 2.3}s`
        }
      });

      console.log('Processing completed!', processResponse);

    } catch (error) {
      console.error('Processing failed:', error);
      setError(error.error || 'Processing failed. Please try again.');
    } finally {
      setIsProcessing(false);
    }
  };

  const resetUpload = () => {
    setUploadedImage(null);
    setUploadedFile(null);
    setResult3D(null);
    setIsProcessing(false);
    setProcessingStep(0);
    setError('');
    setProjectId(null);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-purple-50 to-pink-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-6xl mx-auto">
        {/* Error Display */}
        {error && (
          <div className="mb-6 p-4 bg-red-100 border border-red-400 text-red-700 rounded-lg">
            <strong>Error:</strong> {error}
          </div>
        )}
        {/* Header */}
        <div className="text-center mb-12">
          <div className="flex justify-center mb-6">
            <div className="bg-gradient-to-r from-blue-600 via-purple-600 to-pink-600 p-4 rounded-full">
              <Upload className="h-12 w-12 text-white" />
            </div>
          </div>
          <h1 className="text-4xl font-bold text-gray-900 mb-4">
            Upload Your Image
          </h1>
          <p className="text-xl text-gray-600 max-w-2xl mx-auto">
            Transform any 2D image into a stunning 3D model using our AI-powered technology
          </p>
        </div>

        <div className="grid lg:grid-cols-2 gap-8">
          {/* Upload Section */}
          <div className="space-y-6">
            {!uploadedImage ? (
              <div
                className={`border-2 border-dashed rounded-lg p-8 text-center transition-all duration-200 ${dragOver
                  ? 'border-blue-500 bg-blue-50'
                  : 'border-gray-300 hover:border-blue-400 hover:bg-gray-50'
                  }`}
                onDrop={handleDrop}
                onDragOver={(e) => {
                  e.preventDefault();
                  setDragOver(true);
                }}
                onDragLeave={() => setDragOver(false)}
              >
                <div className="space-y-4">
                  <div className="flex justify-center">
                    <Image className="h-16 w-16 text-gray-400" />
                  </div>
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900 mb-2">
                      Drag and drop your image here
                    </h3>
                    <p className="text-gray-600 mb-4">
                      or click to browse your files
                    </p>
                    <button
                      onClick={() => fileInputRef.current?.click()}
                      className="bg-gradient-to-r from-blue-600 via-purple-600 to-pink-600 hover:from-blue-700 hover:via-purple-700 hover:to-pink-700 text-white px-6 py-3 rounded-lg font-semibold transition-all duration-200 transform hover:scale-105"
                    >
                      Choose File
                    </button>
                    <input
                      ref={fileInputRef}
                      type="file"
                      accept="image/*"
                      onChange={handleFileInputChange}
                      className="hidden"
                    />
                  </div>
                  <p className="text-sm text-gray-500">
                    Supports: JPG, PNG, WEBP, BMP (Max: 10MB)
                  </p>
                </div>
              </div>
            ) : (
              <div className="bg-white rounded-lg shadow-lg p-6">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-semibold text-gray-900">Uploaded Image</h3>
                  <button
                    onClick={resetUpload}
                    className="text-gray-500 hover:text-red-600 transition-colors"
                  >
                    <RotateCcw className="h-5 w-5" />
                  </button>
                </div>
                <div className="mb-4">
                  <img
                    src={uploadedImage}
                    alt="Uploaded"
                    className="w-full h-64 object-cover rounded-lg"
                  />
                </div>

                {/* Object Type Selection */}
                <div className="mb-6">
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Object Type (Optional)
                  </label>
                  <select
                    value={objectType}
                    onChange={(e) => setObjectType(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="auto">Auto Detect</option>
                    <option value="fruit">Fruit</option>
                    <option value="geometric">Geometric Object</option>
                    <option value="organic">Organic Shape</option>
                    <option value="flat">Flat Object</option>
                  </select>
                </div>

                {!isProcessing && !result3D && (
                  <button
                    onClick={startProcessing}
                    className="w-full bg-gradient-to-r from-blue-600 via-purple-600 to-pink-600 hover:from-blue-700 hover:via-purple-700 hover:to-pink-700 text-white py-3 px-4 rounded-lg font-semibold transition-all duration-200 transform hover:scale-105 flex items-center justify-center space-x-2"
                  >
                    <Zap className="h-5 w-5" />
                    <span>Generate 3D Model</span>
                  </button>
                )}
              </div>
            )}
          </div>

          {/* Processing/Results Section */}
          <div className="space-y-6">
            {isProcessing && (
              <div className="bg-white rounded-lg shadow-lg p-6">
                <div className="text-center">
                  <div className="flex justify-center mb-4">
                    <div className="bg-gradient-to-r from-blue-600 via-purple-600 to-pink-600 p-3 rounded-full">
                      <Zap className="h-8 w-8 text-white animate-pulse" />
                    </div>
                  </div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">
                    Processing Your Image
                  </h3>

                  {/* Progress Bar */}
                  <div className="w-full bg-gray-200 rounded-full h-2 mb-4">
                    <div
                      className="bg-gradient-to-r from-blue-600 via-purple-600 to-pink-600 h-2 rounded-full transition-all duration-300"
                      style={{ width: `${((processingStep + 1) / processingSteps.length) * 100}%` }}
                    ></div>
                  </div>

                  <p className="text-gray-600 mb-6">
                    {processingSteps[processingStep]}
                  </p>

                  {/* Processing Steps */}
                  <div className="space-y-2">
                    {processingSteps.map((step, index) => (
                      <div
                        key={index}
                        className={`flex items-center space-x-2 text-sm ${index <= processingStep
                          ? 'text-blue-600'
                          : 'text-gray-400'
                          }`}
                      >
                        <div
                          className={`w-2 h-2 rounded-full ${index <= processingStep
                            ? 'bg-blue-600'
                            : 'bg-gray-300'
                            }`}
                        ></div>
                        <span>{step}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}

            {result3D && (
              <div className="bg-white rounded-lg shadow-lg p-6">
                <div className="text-center mb-6">
                  <div className="flex justify-center mb-4">
                    <div className="bg-green-100 p-3 rounded-full">
                      <Eye className="h-8 w-8 text-green-600" />
                    </div>
                  </div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-2">
                    3D Model Ready!
                  </h3>
                  <p className="text-gray-600">
                    Your 3D model has been generated successfully
                  </p>
                </div>

                {/* 3D Preview */}
                <div className="mb-6">
                  <div className="w-full h-48 bg-gray-100 rounded-lg flex items-center justify-center">
                    <div className="text-center">
                      <Settings className="h-12 w-12 text-gray-400 mx-auto mb-2" />
                      <p className="text-gray-600">3D Preview</p>
                      <p className="text-sm text-gray-500">(Interactive viewer coming soon)</p>
                    </div>
                  </div>
                </div>

                {/* Model Stats */}
                <div className="grid grid-cols-3 gap-4 mb-6 text-center">
                  <div>
                    <div className="text-2xl font-bold text-blue-600">{result3D.stats.vertices.toLocaleString()}</div>
                    <div className="text-sm text-gray-600">Vertices</div>
                  </div>
                  <div>
                    <div className="text-2xl font-bold text-purple-600">{result3D.stats.faces.toLocaleString()}</div>
                    <div className="text-sm text-gray-600">Faces</div>
                  </div>
                  <div>
                    <div className="text-2xl font-bold text-pink-600">{result3D.stats.processingTime}</div>
                    <div className="text-sm text-gray-600">Time</div>
                  </div>
                </div>

                {/* Download Buttons */}
                <div className="space-y-3">
                  <button onClick={() => handleDownload('ply')} className="w-full bg-blue-600 hover:bg-blue-700 text-white py-3 px-4 rounded-lg font-semibold transition-colors flex items-center justify-center space-x-2">                    <Download className="h-5 w-5" />
                    <span>Download PLY (Colored)</span>
                  </button>
                  <button onClick={() => handleDownload('stl')} className="w-full bg-gray-600 hover:bg-gray-700 text-white py-3 px-4 rounded-lg font-semibold transition-colors flex items-center justify-center space-x-2">                    <Download className="h-5 w-5" />
                    <span>Download STL (3D Printing)</span>
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}