import React, { useState } from 'react';
import { Eye, Download, Heart, Calendar, User } from 'lucide-react';

export default function GalleryPage() {
  const [filter, setFilter] = useState('all');
  
  // דוגמאות של עבודות - בהמשך יגיעו מהשרת
  const mockGalleryItems = [
    {
      id: 1,
      title: "Red Apple",
      originalImage: "https://images.unsplash.com/photo-1568702846914-96b305d2aaeb?w=300&h=300&fit=crop",
      creator: "John Doe",
      date: "2024-06-01",
      likes: 45,
      category: "fruit",
      stats: { vertices: "12.5K", faces: "25K" }
    },
    {
      id: 2,
      title: "Geometric Cube",
      originalImage: "https://images.unsplash.com/photo-1578662996442-48f60103fc96?w=300&h=300&fit=crop",
      creator: "Jane Smith",
      date: "2024-06-02",
      likes: 32,
      category: "geometric",
      stats: { vertices: "8.2K", faces: "16.4K" }
    },
    {
      id: 3,
      title: "Orange Fruit",
      originalImage: "https://images.unsplash.com/photo-1547036967-23d11aacaee0?w=300&h=300&fit=crop",
      creator: "Mike Johnson",
      date: "2024-06-03",
      likes: 67,
      category: "fruit",
      stats: { vertices: "15.1K", faces: "30.2K" }
    },
    {
      id: 4,
      title: "Coffee Cup",
      originalImage: "https://images.unsplash.com/photo-1559056199-641a0ac8b55e?w=300&h=300&fit=crop",
      creator: "Sarah Wilson",
      date: "2024-06-04",
      likes: 23,
      category: "organic",
      stats: { vertices: "18.7K", faces: "37.4K" }
    },
    {
      id: 5,
      title: "Toy Car",
      originalImage: "https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=300&h=300&fit=crop",
      creator: "David Brown",
      date: "2024-06-05",
      likes: 89,
      category: "geometric",
      stats: { vertices: "22.3K", faces: "44.6K" }
    },
    {
      id: 6,
      title: "Green Plant",
      originalImage: "https://images.unsplash.com/photo-1416879595882-3373a0480b5b?w=300&h=300&fit=crop",
      creator: "Emma Davis",
      date: "2024-06-06",
      likes: 56,
      category: "organic",
      stats: { vertices: "28.9K", faces: "57.8K" }
    }
  ];

  const categories = [
    { id: 'all', name: 'All Models', count: mockGalleryItems.length },
    { id: 'fruit', name: 'Fruits', count: mockGalleryItems.filter(item => item.category === 'fruit').length },
    { id: 'geometric', name: 'Geometric', count: mockGalleryItems.filter(item => item.category === 'geometric').length },
    { id: 'organic', name: 'Organic', count: mockGalleryItems.filter(item => item.category === 'organic').length }
  ];

  const filteredItems = filter === 'all' 
    ? mockGalleryItems 
    : mockGalleryItems.filter(item => item.category === filter);

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-purple-50 to-pink-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="text-center mb-12">
          <div className="flex justify-center mb-6">
            <div className="bg-gradient-to-r from-blue-600 via-purple-600 to-pink-600 p-4 rounded-full">
              <Eye className="h-12 w-12 text-white" />
            </div>
          </div>
          <h1 className="text-4xl font-bold text-gray-900 mb-4">
            3D Model Gallery
          </h1>
          <p className="text-xl text-gray-600 max-w-2xl mx-auto">
            Explore amazing 3D models created by our community using Depthify
          </p>
        </div>

        {/* Filter Tabs */}
        <div className="mb-8">
          <div className="flex flex-wrap justify-center gap-2">
            {categories.map((category) => (
              <button
                key={category.id}
                onClick={() => setFilter(category.id)}
                className={`px-6 py-3 rounded-full font-medium transition-all duration-200 ${
                  filter === category.id
                    ? 'bg-gradient-to-r from-blue-600 via-purple-600 to-pink-600 text-white shadow-lg transform scale-105'
                    : 'bg-white text-gray-700 hover:bg-gray-50 border border-gray-200'
                }`}
              >
                {category.name} ({category.count})
              </button>
            ))}
          </div>
        </div>

        {/* Gallery Grid */}
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
          {filteredItems.map((item) => (
            <div
              key={item.id}
              className="bg-white rounded-lg shadow-lg overflow-hidden hover:shadow-xl transition-all duration-300 transform hover:-translate-y-2"
            >
              {/* Image */}
              <div className="relative group">
                <img
                  src={item.originalImage}
                  alt={item.title}
                  className="w-full h-48 object-cover"
                />
                <div className="absolute inset-0 bg-black bg-opacity-0 group-hover:bg-opacity-50 transition-all duration-300 flex items-center justify-center">
                  <div className="opacity-0 group-hover:opacity-100 transition-opacity duration-300 flex space-x-2">
                    <button className="bg-white text-gray-900 p-2 rounded-full hover:bg-gray-100 transition-colors">
                      <Eye className="h-5 w-5" />
                    </button>
                    <button className="bg-white text-gray-900 p-2 rounded-full hover:bg-gray-100 transition-colors">
                      <Download className="h-5 w-5" />
                    </button>
                  </div>
                </div>
              </div>

              {/* Content */}
              <div className="p-6">
                <h3 className="text-xl font-bold text-gray-900 mb-2">
                  {item.title}
                </h3>
                
                {/* Creator & Date */}
                <div className="flex items-center text-gray-600 text-sm mb-4">
                  <User className="h-4 w-4 mr-1" />
                  <span className="mr-4">{item.creator}</span>
                  <Calendar className="h-4 w-4 mr-1" />
                  <span>{new Date(item.date).toLocaleDateString()}</span>
                </div>

                {/* Stats */}
                <div className="grid grid-cols-2 gap-4 mb-4">
                  <div className="text-center">
                    <div className="text-lg font-bold text-blue-600">{item.stats.vertices}</div>
                    <div className="text-xs text-gray-600">Vertices</div>
                  </div>
                  <div className="text-center">
                    <div className="text-lg font-bold text-purple-600">{item.stats.faces}</div>
                    <div className="text-xs text-gray-600">Faces</div>
                  </div>
                </div>

                {/* Actions */}
                <div className="flex items-center justify-between">
                  <button className="flex items-center space-x-1 text-gray-600 hover:text-red-500 transition-colors">
                    <Heart className="h-5 w-5" />
                    <span>{item.likes}</span>
                  </button>
                  
                  <div className="flex space-x-2">
                    <button className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors">
                      View 3D
                    </button>
                    <button className="bg-gray-200 hover:bg-gray-300 text-gray-700 px-4 py-2 rounded-lg text-sm font-medium transition-colors">
                      Download
                    </button>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Load More Button */}
        <div className="text-center mt-12">
          <button className="bg-gradient-to-r from-blue-600 via-purple-600 to-pink-600 hover:from-blue-700 hover:via-purple-700 hover:to-pink-700 text-white px-8 py-3 rounded-lg font-semibold transition-all duration-200 transform hover:scale-105">
            Load More Models
          </button>
        </div>

        {/* Stats Section */}
        <div className="mt-16 bg-white rounded-lg shadow-lg p-8">
          <div className="text-center mb-8">
            <h2 className="text-3xl font-bold text-gray-900 mb-2">
              Community Stats
            </h2>
            <p className="text-gray-600">
              See what our amazing community has created
            </p>
          </div>
          
          <div className="grid md:grid-cols-4 gap-8 text-center">
            <div>
              <div className="text-4xl font-bold text-blue-600 mb-2">{mockGalleryItems.length}</div>
              <div className="text-gray-600">Total Models</div>
            </div>
            <div>
              <div className="text-4xl font-bold text-purple-600 mb-2">
                {mockGalleryItems.reduce((sum, item) => sum + item.likes, 0)}
              </div>
              <div className="text-gray-600">Total Likes</div>
            </div>
            <div>
              <div className="text-4xl font-bold text-pink-600 mb-2">
                {new Set(mockGalleryItems.map(item => item.creator)).size}
              </div>
              <div className="text-gray-600">Active Creators</div>
            </div>
            <div>
              <div className="text-4xl font-bold text-green-600 mb-2">100%</div>
              <div className="text-gray-600">Success Rate</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}