import React, { useState, useEffect } from 'react';
import { Calendar, Plus, Heart, Gift, Send, Users, Clock, AlertCircle, CheckCircle } from 'lucide-react';

interface Person {
  id: number;
  name: string;
  date: string;
  type: 'birthday' | 'anniversary';
  spouse_name?: string;
  phone?: string;
  email?: string;
  created_at?: string;
}

interface UpcomingEvent extends Person {
  days_until: number;
  next_occurrence?: string;
}

interface ApiResponse<T> {
  success: boolean;
  data?: T;
  message?: string;
  error?: string;
}

// interface MessageResponse {
//   message: string;
// }

// API Service
class ApiService {
  private baseUrl = 'http://localhost:5000/api';

  async get<T>(endpoint: string): Promise<ApiResponse<T>> {
    try {
      const response = await fetch(`${this.baseUrl}${endpoint}`);
      return await response.json();
    } catch (error) {
      return { success: false, error: 'Network error. Please check if the backend server is running.' };
    }
  }

  async post<T>(endpoint: string, data: any): Promise<ApiResponse<T>> {
    try {
      const response = await fetch(`${this.baseUrl}${endpoint}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
      });
      return await response.json();
    } catch (error) {
      return { success: false, error: 'Network error. Please check if the backend server is running.' };
    }
  }

  async delete<T>(endpoint: string): Promise<ApiResponse<T>> {
    try {
      const response = await fetch(`${this.baseUrl}${endpoint}`, {
        method: 'DELETE',
      });
      return await response.json();
    } catch (error) {
      return { success: false, error: 'Network error. Please check if the backend server is running.' };
    }
  }
}

const BirthdayApp = () => {
  const [people, setPeople] = useState<Person[]>([]);
  const [upcomingEvents, setUpcomingEvents] = useState<UpcomingEvent[]>([]);
  const [todaysEvents, setTodaysEvents] = useState<Person[]>([]);
  const [activeTab, setActiveTab] = useState<'dashboard' | 'add' | 'manage'>('dashboard');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const [formData, setFormData] = useState({
    name: '',
    date: '',
    type: 'birthday' as 'birthday' | 'anniversary',
    spouse_name: '',
    phone: '',
    email: ''
  });

  const apiService = new ApiService();

  // Clear messages after 5 seconds
  useEffect(() => {
    if (error || successMessage) {
      const timer = setTimeout(() => {
        setError(null);
        setSuccessMessage(null);
      }, 5000);
      return () => clearTimeout(timer);
    }
  }, [error, successMessage]);

  // Load data on component mount
  useEffect(() => {
    loadAllData();
  }, []);

  const loadAllData = async () => {
    setLoading(true);
    setError(null);

    try {
      await Promise.all([
        loadPeople(),
        loadUpcomingEvents(),
        loadTodaysEvents()
      ]);
    } catch (err) {
      setError('Failed to load data');
    } finally {
      setLoading(false);
    }
  };

  const loadPeople = async () => {
    const response = await apiService.get<Person[]>('/people');
    if (response.success && response.data) {
      setPeople(response.data);
    } else {
      setError(response.error || 'Failed to load people');
    }
  };

  const loadUpcomingEvents = async () => {
    const response = await apiService.get<UpcomingEvent[]>('/upcoming-celebrations?days=30');
    if (response.success && response.data) {
      setUpcomingEvents(response.data);
    } else {
      setError(response.error || 'Failed to load upcoming events');
    }
  };

  const loadTodaysEvents = async () => {
    const response = await apiService.get<Person[]>('/today-celebrations');
    if (response.success && response.data) {
      setTodaysEvents(response.data);
    } else {
      setError(response.error || 'Failed to load today\'s events');
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSubmit = async () => {
    if (!formData.name || !formData.date) {
      setError('Please fill in required fields');
      return;
    }

    setLoading(true);
    setError(null);

    const response = await apiService.post('/people', formData);

    if (response.success) {
      setSuccessMessage('Event added successfully!');
      setFormData({
        name: '',
        date: '',
        type: 'birthday',
        spouse_name: '',
        phone: '',
        email: ''
      });
      setActiveTab('dashboard');
      await loadAllData();
    } else {
      setError(response.error || 'Failed to add event');
    }

    setLoading(false);
  };

  const deletePerson = async (id: number) => {
    if (!confirm('Are you sure you want to delete this event?')) {
      return;
    }

    setLoading(true);
    setError(null);

    const response = await apiService.delete(`/people/${id}`);

    if (response.success) {
      setSuccessMessage('Event deleted successfully!');
      await loadAllData();
    } else {
      setError(response.error || 'Failed to delete event');
    }

    setLoading(false);
  };

  const sendWish = async (personId: number, personName: string) => {
    setLoading(true);
    setError(null);

    const response = await apiService.post(`/send-wish/${personId}`, {});

    if (response.success) {
      setSuccessMessage(`Wish sent to ${personName}!`);
    } else {
      setError(response.error || 'Failed to send wish');
    }

    setLoading(false);
  };

  const getMessagePreview = async (personId: number) => {
    const response = await apiService.get<{ message: string }>(`/message-preview/${personId}`);
    console.log("response", response);

    if (response.success && response?.message) {
      alert(response?.message);
    } else {
      setError(response.error || 'Failed to get message preview');
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      month: 'long',
      day: 'numeric',
      year: 'numeric'
    });
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-100 via-pink-50 to-blue-100">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="flex items-center justify-center gap-3 mb-4">
            <Gift className="w-10 h-10 text-purple-600" />
            <h1 className="text-4xl font-bold text-gray-800">Celebration Reminder</h1>
            <Heart className="w-10 h-10 text-pink-600" />
          </div>
          <p className="text-gray-600 text-lg">Never miss a special moment with your loved ones</p>
        </div>

        {/* Error/Success Messages */}
        {error && (
          <div className="mb-6 bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded-lg flex items-center gap-2">
            <AlertCircle className="w-5 h-5" />
            {error}
          </div>
        )}

        {successMessage && (
          <div className="mb-6 bg-green-100 border border-green-400 text-green-700 px-4 py-3 rounded-lg flex items-center gap-2">
            <CheckCircle className="w-5 h-5" />
            {successMessage}
          </div>
        )}

        {/* Loading Indicator */}
        {loading && (
          <div className="mb-6 bg-blue-100 border border-blue-400 text-blue-700 px-4 py-3 rounded-lg text-center">
            Loading...
          </div>
        )}

        {/* Navigation */}
        <div className="flex justify-center mb-8">
          <div className="bg-white rounded-full p-1 shadow-lg">
            <button
              onClick={() => setActiveTab('dashboard')}
              className={`px-6 py-3 rounded-full font-medium transition-all ${activeTab === 'dashboard'
                ? 'bg-purple-600 text-white shadow-md'
                : 'text-gray-600 hover:text-purple-600'
                }`}
            >
              Dashboard
            </button>
            <button
              onClick={() => setActiveTab('add')}
              className={`px-6 py-3 rounded-full font-medium transition-all ${activeTab === 'add'
                ? 'bg-purple-600 text-white shadow-md'
                : 'text-gray-600 hover:text-purple-600'
                }`}
            >
              Add Event
            </button>
            <button
              onClick={() => setActiveTab('manage')}
              className={`px-6 py-3 rounded-full font-medium transition-all ${activeTab === 'manage'
                ? 'bg-purple-600 text-white shadow-md'
                : 'text-gray-600 hover:text-purple-600'
                }`}
            >
              Manage
            </button>
          </div>
        </div>

        {/* Dashboard Tab */}
        {activeTab === 'dashboard' && (
          <div className="space-y-8">
            {/* Today's Events */}
            {todaysEvents.length > 0 && (
              <div className="bg-gradient-to-r from-yellow-400 to-orange-500 rounded-xl p-6 text-white shadow-xl">
                <div className="flex items-center gap-3 mb-4">
                  <Clock className="w-6 h-6" />
                  <h2 className="text-2xl font-bold">Today's Celebrations! 🎉</h2>
                </div>
                <div className="space-y-3">
                  {todaysEvents.map(event => (
                    <div key={event.id} className="bg-white bg-opacity-20 rounded-lg p-4">
                      <div className="flex items-center justify-between">
                        <div>
                          <h3 className="font-bold text-lg">
                            {event.type === 'birthday' ? '🎂' : '💕'} {event.name}
                            {event.spouse_name && ` & ${event.spouse_name}`}
                          </h3>
                          <p className="text-white text-opacity-90">
                            {event.type === 'birthday' ? 'Birthday' : 'Anniversary'} - {formatDate(event.date)}
                          </p>
                        </div>
                        <div className="flex gap-2">
                          <button
                            onClick={() => getMessagePreview(event.id)}
                            className="bg-white bg-opacity-20 text-white px-3 py-1 rounded text-sm hover:bg-opacity-30 transition-all"
                            disabled={loading}
                          >
                            Preview
                          </button>
                          <button
                            onClick={() => sendWish(event.id, event.name)}
                            className="bg-white text-orange-500 px-4 py-2 rounded-lg font-medium hover:bg-opacity-90 transition-all flex items-center gap-2"
                            disabled={loading}
                          >
                            <Send className="w-4 h-4" />
                            Send Wish
                          </button>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Upcoming Events */}
            <div className="bg-white rounded-xl shadow-xl p-6">
              <div className="flex items-center justify-between mb-6">
                <div className="flex items-center gap-3">
                  <Calendar className="w-6 h-6 text-purple-600" />
                  <h2 className="text-2xl font-bold text-gray-800">Upcoming Events</h2>
                </div>
                <button
                  onClick={loadAllData}
                  className="text-purple-600 hover:text-purple-800 font-medium"
                  disabled={loading}
                >
                  Refresh
                </button>
              </div>

              <div className="grid gap-4">
                {upcomingEvents.slice(0, 6).map(event => (
                  <div key={event.id} className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-all">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-4">
                        <div className={`w-12 h-12 rounded-full flex items-center justify-center text-2xl ${event.type === 'birthday' ? 'bg-blue-100' : 'bg-pink-100'
                          }`}>
                          {event.type === 'birthday' ? '🎂' : '💕'}
                        </div>
                        <div>
                          <h3 className="font-bold text-lg text-gray-800">
                            {event.name}
                            {event.spouse_name && ` & ${event.spouse_name}`}
                          </h3>
                          <p className="text-gray-600">
                            {event.type === 'birthday' ? 'Birthday' : 'Anniversary'} • {formatDate(event.date)}
                          </p>
                          <div className="text-sm text-gray-500 mt-1">
                            {event.phone && <span>📞 {event.phone}</span>}
                            {event.phone && event.email && <span> • </span>}
                            {event.email && <span>✉️ {event.email}</span>}
                          </div>
                        </div>
                      </div>
                      <div className="text-right">
                        <div className={`px-3 py-1 rounded-full text-sm font-medium mb-2 ${event.days_until === 0
                          ? 'bg-red-100 text-red-800'
                          : event.days_until <= 7
                            ? 'bg-yellow-100 text-yellow-800'
                            : 'bg-gray-100 text-gray-800'
                          }`}>
                          {event.days_until === 0 ? 'Today!' : `${event.days_until} days`}
                        </div>
                        <div className="flex gap-1">
                          <button
                            onClick={() => getMessagePreview(event.id)}
                            className="text-xs text-gray-600 hover:text-purple-600 px-2 py-1 rounded"
                            disabled={loading}
                          >
                            Preview
                          </button>
                          {event.days_until <= 7 && (
                            <button
                              onClick={() => sendWish(event.id, event.name)}
                              className="text-purple-600 hover:text-purple-800 text-sm font-medium flex items-center gap-1 px-2 py-1 rounded"
                              disabled={loading}
                            >
                              <Send className="w-3 h-3" />
                              Send
                            </button>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                ))}

                {upcomingEvents.length === 0 && !loading && (
                  <div className="text-center py-8 text-gray-500">
                    No upcoming events found
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Add Event Tab */}
        {activeTab === 'add' && (
          <div className="max-w-2xl mx-auto bg-white rounded-xl shadow-xl p-8">
            <div className="flex items-center gap-3 mb-6">
              <Plus className="w-6 h-6 text-purple-600" />
              <h2 className="text-2xl font-bold text-gray-800">Add New Event</h2>
            </div>

            <div className="space-y-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Event Type</label>
                <select
                  name="type"
                  value={formData.type}
                  onChange={handleInputChange}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                >
                  <option value="birthday">Birthday</option>
                  <option value="anniversary">Anniversary</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  {formData.type === 'birthday' ? 'Name' : 'Primary Name'} *
                </label>
                <input
                  type="text"
                  name="name"
                  value={formData.name}
                  onChange={handleInputChange}
                  placeholder={formData.type === 'birthday' ? 'Enter person name' : 'Enter first person name'}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                  required
                />
              </div>

              {formData.type === 'anniversary' && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Spouse Name</label>
                  <input
                    type="text"
                    name="spouse_name"
                    value={formData.spouse_name}
                    onChange={handleInputChange}
                    placeholder="Enter spouse name"
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                  />
                </div>
              )}

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Date *</label>
                <input
                  type="date"
                  name="date"
                  value={formData.date}
                  onChange={handleInputChange}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Phone (Optional)</label>
                <input
                  type="tel"
                  name="phone"
                  value={formData.phone}
                  onChange={handleInputChange}
                  placeholder="+91-9876543210"
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Email (Optional)</label>
                <input
                  type="email"
                  name="email"
                  value={formData.email}
                  onChange={handleInputChange}
                  placeholder="example@email.com"
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                />
              </div>

              <button
                onClick={handleSubmit}
                disabled={loading}
                className="w-full bg-gradient-to-r from-purple-600 to-pink-600 text-white py-3 px-6 rounded-lg font-medium hover:from-purple-700 hover:to-pink-700 transition-all shadow-lg disabled:opacity-50"
              >
                {loading ? 'Adding...' : 'Add Event'}
              </button>
            </div>
          </div>
        )}

        {/* Manage Tab */}
        {activeTab === 'manage' && (
          <div className="bg-white rounded-xl shadow-xl p-6">
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center gap-3">
                <Users className="w-6 h-6 text-purple-600" />
                <h2 className="text-2xl font-bold text-gray-800">Manage Events</h2>
              </div>
              <button
                onClick={loadPeople}
                className="text-purple-600 hover:text-purple-800 font-medium"
                disabled={loading}
              >
                Refresh
              </button>
            </div>

            <div className="space-y-4">
              {people.map(person => (
                <div key={person.id} className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-all">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-4">
                      <div className={`w-12 h-12 rounded-full flex items-center justify-center text-2xl ${person.type === 'birthday' ? 'bg-blue-100' : 'bg-pink-100'
                        }`}>
                        {person.type === 'birthday' ? '🎂' : '💕'}
                      </div>
                      <div>
                        <h3 className="font-bold text-lg text-gray-800">
                          {person.name}
                          {person.spouse_name && ` & ${person.spouse_name}`}
                        </h3>
                        <p className="text-gray-600">
                          {person.type === 'birthday' ? 'Birthday' : 'Anniversary'} • {formatDate(person.date)}
                        </p>
                        {person.phone && (
                          <p className="text-sm text-gray-500">📞 {person.phone}</p>
                        )}
                        {person.email && (
                          <p className="text-sm text-gray-500">✉️ {person.email}</p>
                        )}
                      </div>
                    </div>
                    <div className="flex gap-2">
                      <button
                        onClick={() => getMessagePreview(person.id)}
                        className="px-3 py-2 bg-blue-100 text-blue-600 rounded-lg hover:bg-blue-200 transition-all font-medium text-sm"
                        disabled={loading}
                      >
                        Preview
                      </button>
                      <button
                        onClick={() => deletePerson(person.id)}
                        disabled={loading}
                        className="px-4 py-2 bg-red-100 text-red-600 rounded-lg hover:bg-red-200 transition-all font-medium disabled:opacity-50"
                      >
                        Delete
                      </button>
                    </div>
                  </div>
                </div>
              ))}

              {people.length === 0 && !loading && (
                <div className="text-center py-12">
                  <div className="text-6xl mb-4">🎭</div>
                  <p className="text-gray-500 text-lg">No events added yet</p>
                  <button
                    onClick={() => setActiveTab('add')}
                    className="mt-4 bg-purple-600 text-white px-6 py-2 rounded-lg hover:bg-purple-700 transition-all"
                  >
                    Add Your First Event
                  </button>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default BirthdayApp;