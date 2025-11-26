'use client';

import { useState, useRef, useEffect } from 'react';
import { Send, Key, Loader2, Code, MapPin, Star, Calendar, DollarSign, Globe, Sparkles, Clock, Navigation, Layout, Github, StopCircle, Plane } from 'lucide-react';

// --- Complex Data Structures ---

interface Location {
  lat?: number;
  lng?: number;
  address?: string;
}

interface Review {
  author?: string;
  rating?: number;
  comment?: string;
}

interface Attraction {
  name?: string;
  type?: string;
  description?: string;
  price_range?: string;
  location?: Location;
  reviews?: Review[];
}

interface DayItinerary {
  day?: number;
  title?: string;
  activities?: Attraction[];
  summary?: string;
}

interface CityGuide {
  city_name?: string;
  country?: string;
  description?: string;
  best_time_to_visit?: string;
  currency?: string;
  languages?: string[];
  itinerary?: DayItinerary[];
  top_tips?: string[];
}

// -------------------------------

export default function Home() {
  const [apiKey, setApiKey] = useState('');
  const [prompt, setPrompt] = useState('Create a comprehensive 3-day travel guide for Shanghai, China, including hidden gems and local food spots.');
  const [provider, setProvider] = useState('anthropic');
  const [model, setModel] = useState('claude-sonnet-4-5-20250929');
  const [isLoading, setIsLoading] = useState(false);
  const [output, setOutput] = useState<CityGuide | null>(null);
  const [rawJson, setRawJson] = useState<string>('');
  const [error, setError] = useState<string | null>(null);
  const outputRef = useRef<HTMLDivElement>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  // Load API key from local storage on mount
  useEffect(() => {
    const storedKey = localStorage.getItem('llm_json_streaming_api_key');
    if (storedKey) setApiKey(storedKey);
  }, []);

  // Save API key when it changes
  useEffect(() => {
    if (apiKey) {
      localStorage.setItem('llm_json_streaming_api_key', apiKey);
    } else {
      localStorage.removeItem('llm_json_streaming_api_key');
    }
  }, [apiKey]);

  // Update model when provider changes
  useEffect(() => {
    if (provider === 'anthropic') setModel('claude-sonnet-4-5-20250929');
    else if (provider === 'openai') setModel('gpt-4o');
    else if (provider === 'google') setModel('gemini-1.5-pro');
  }, [provider]);

  // Auto-scroll to bottom of output
  useEffect(() => {
    if (outputRef.current) {
      outputRef.current.scrollTop = outputRef.current.scrollHeight;
    }
  }, [rawJson]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    // Handle stop streaming
    if (isLoading) {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
        abortControllerRef.current = null;
      }
      setIsLoading(false);
      return;
    }

    if (!apiKey) {
      setError('Please enter an API key');
      return;
    }

    setIsLoading(true);
    setError(null);
    setOutput(null);
    setRawJson('');
    
    // Initialize new AbortController
    abortControllerRef.current = new AbortController();

    try {
      const response = await fetch('http://localhost:8000/stream', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          prompt,
          api_key: apiKey,
          provider,
          model,
        }),
        signal: abortControllerRef.current.signal,
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to start stream');
      }

      if (!response.body) {
        throw new Error('No response body');
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value, { stream: true });
        buffer += chunk;
        
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (!line.trim()) continue;
          
          try {
            const data = JSON.parse(line);
            
            if (data.error) {
              throw new Error(data.error);
            }

            if (data.partial_object) {
               setRawJson(JSON.stringify(data.partial_object, null, 2));
               setOutput(data.partial_object);
            }
            
            if (data.final_object) {
              setOutput(data.final_object);
              setRawJson(JSON.stringify(data.final_object, null, 2));
            }
          } catch (e) {
            console.error('Error parsing line:', line, e);
          }
        }
      }

    } catch (err: any) {
      if (err.name === 'AbortError') {
        console.log('Stream aborted by user');
      } else {
        setError(err.message || 'An error occurred');
      }
    } finally {
      setIsLoading(false);
      abortControllerRef.current = null;
    }
  };

  return (
    <main className="min-h-screen bg-slate-50 text-slate-900">
      {/* Hero Header */}
      <div className="bg-white border-b border-slate-200 sticky top-0 z-10 bg-opacity-90 backdrop-blur-md">
        <div className="container mx-auto px-4 h-16 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 bg-indigo-600 rounded-lg flex items-center justify-center text-white shadow-lg shadow-indigo-200">
              <Sparkles size={18} />
            </div>
            <h1 className="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-indigo-600 to-violet-600">
              LLM Stream Explorer
            </h1>
          </div>
          <div className="text-sm text-slate-500 flex items-center gap-4">
            <a 
              href="https://github.com/daniel-style/llm-json-streaming" 
              target="_blank" 
              rel="noopener noreferrer" 
              className="hover:text-indigo-600 transition-colors"
              title="View on GitHub"
            >
              <Github size={24} />
            </a>
          </div>
        </div>
      </div>

      <div className="container mx-auto px-4 py-8 max-w-7xl">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
          
          {/* Left Sidebar: Configuration & Raw Data */}
          <div className="lg:col-span-4 xl:col-span-3 space-y-6">
            
            {/* Config Card */}
            <div className="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden">
              <div className="p-4 border-b border-slate-100 bg-slate-50/50 flex items-center gap-2">
                <Key size={16} className="text-indigo-600" />
                <h2 className="font-semibold text-slate-700">Settings</h2>
              </div>
              
              <div className="p-4 space-y-4">
                <div className="space-y-1.5">
                  <label className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Provider</label>
                  <div className="relative">
                    <select 
                      value={provider}
                      onChange={(e) => setProvider(e.target.value)}
                      className="w-full pl-3 pr-10 py-2.5 bg-slate-50 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent appearance-none transition-shadow"
                    >
                      <option value="anthropic">Anthropic (Claude)</option>
                      <option value="openai">OpenAI (GPT)</option>
                      <option value="google">Google (Gemini)</option>
                    </select>
                    <Layout className="absolute right-3 top-3 text-slate-400 pointer-events-none" size={14} />
                  </div>
                </div>

                <div className="space-y-1.5">
                  <label className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Model ID</label>
                  <input
                    type="text"
                    value={model}
                    onChange={(e) => setModel(e.target.value)}
                    className="w-full px-3 py-2.5 bg-slate-50 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-shadow font-mono text-slate-600"
                  />
                </div>

                <div className="space-y-1.5">
                  <label className="text-xs font-semibold text-slate-500 uppercase tracking-wider">API Key</label>
                  <input
                    type="password"
                    value={apiKey}
                    onChange={(e) => setApiKey(e.target.value)}
                    placeholder="sk-..."
                    className="w-full px-3 py-2.5 bg-slate-50 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-shadow"
                  />
                </div>
              </div>
            </div>

            {/* Prompt Card */}
            <div className="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden">
              <div className="p-4 border-b border-slate-100 bg-slate-50/50 flex items-center gap-2">
                <Navigation size={16} className="text-indigo-600" />
                <h2 className="font-semibold text-slate-700">Input</h2>
              </div>
              <div className="p-4 space-y-3">
                <textarea
                  value={prompt}
                  onChange={(e) => setPrompt(e.target.value)}
                  rows={6}
                  className="w-full px-3 py-3 bg-slate-50 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent resize-none transition-shadow"
                  placeholder="What would you like to generate?"
                />
                <button
                  onClick={handleSubmit}
                  className={`w-full flex items-center justify-center gap-2 text-white px-4 py-3 rounded-xl font-medium transition-all shadow-md disabled:opacity-70 disabled:cursor-not-allowed active:scale-[0.98] ${
                    isLoading 
                      ? 'bg-red-500 hover:bg-red-600 shadow-red-200' 
                      : 'bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-700 hover:to-violet-700 shadow-indigo-200'
                  }`}
                >
                  {isLoading ? (
                    <>
                      <StopCircle size={18} className="animate-pulse" />
                      Stop Streaming
                    </>
                  ) : (
                    <>
                      <Send size={18} />
                      Start Streaming
                    </>
                  )}
                </button>
              </div>
            </div>

            {/* Raw Data Panel */}
            <div className="bg-slate-900 rounded-2xl shadow-lg overflow-hidden border border-slate-800 flex flex-col h-[300px]">
              <div className="bg-slate-950/50 px-4 py-3 border-b border-slate-800 flex items-center justify-between">
                <div className="flex items-center gap-2 text-slate-400 text-xs font-mono font-medium uppercase tracking-wider">
                  <Code size={14} /> Live JSON Stream
                </div>
                <div className="flex gap-1.5">
                    <div className="w-2.5 h-2.5 rounded-full bg-red-500/20 border border-red-500/50"></div>
                    <div className="w-2.5 h-2.5 rounded-full bg-yellow-500/20 border border-yellow-500/50"></div>
                    <div className="w-2.5 h-2.5 rounded-full bg-green-500/20 border border-green-500/50"></div>
                </div>
              </div>
              <div 
                ref={outputRef}
                className="p-4 overflow-y-auto font-mono text-[11px] leading-relaxed text-emerald-400 whitespace-pre-wrap grow custom-scrollbar"
              >
                {rawJson || <span className="text-slate-600 italic">Waiting for data stream...</span>}
              </div>
            </div>

          </div>

          {/* Right Main Content: Renderer */}
          <div className="lg:col-span-8 xl:col-span-9">
            {error && (
              <div className="mb-6 bg-red-50 text-red-600 p-4 rounded-xl border border-red-100 flex items-center gap-3 shadow-sm">
                <div className="w-2 h-2 rounded-full bg-red-500 animate-pulse"></div>
                {error}
              </div>
            )}

            {isLoading && !output ? (
              <div className="h-[600px] flex flex-col items-center justify-center bg-white rounded-3xl border border-slate-100 shadow-xl relative overflow-hidden">
                {/* Background Animation */}
                <div className="absolute inset-0 overflow-hidden opacity-30">
                  <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[500px] h-[500px] bg-indigo-500/10 rounded-full blur-3xl animate-pulse"></div>
                  <div className="absolute top-0 right-0 w-[300px] h-[300px] bg-violet-500/10 rounded-full blur-3xl animate-bounce delay-700"></div>
                  <div className="absolute bottom-0 left-0 w-[300px] h-[300px] bg-blue-500/10 rounded-full blur-3xl animate-bounce delay-1000"></div>
                </div>

                <div className="relative z-10 flex flex-col items-center">
                  {/* Spinning Globe & Orbiting Plane */}
                  <div className="relative w-32 h-32 mb-8">
                    <div className="absolute inset-0 border-4 border-indigo-100 rounded-full"></div>
                    <div className="absolute inset-0 border-t-4 border-indigo-500 rounded-full animate-spin"></div>
                    <div className="absolute inset-4 bg-indigo-50 rounded-full flex items-center justify-center shadow-inner">
                      <Globe size={48} className="text-indigo-600 animate-pulse" />
                    </div>
                    
                    {/* Orbiting Plane */}
                    <div className="absolute inset-0 animate-spin [animation-duration:3s]">
                      <div className="absolute -top-3 left-1/2 -translate-x-1/2 bg-white p-1.5 rounded-full shadow-md border border-indigo-100">
                        <Plane size={20} className="text-indigo-600 rotate-45" />
                      </div>
                    </div>
                  </div>

                  <h3 className="text-2xl font-bold text-slate-800 mb-2 bg-clip-text text-transparent bg-gradient-to-r from-indigo-600 to-violet-600 animate-pulse">
                    Design your journey...
                  </h3>
                  <div className="flex flex-col items-center gap-2 text-slate-500 text-sm">
                    <p className="animate-slide-up">Analyzing destination...</p>
                    <p className="animate-slide-up [animation-delay:1s] opacity-0 fill-mode-forwards">Finding hidden gems...</p>
                    <p className="animate-slide-up [animation-delay:2s] opacity-0 fill-mode-forwards">Structuring itinerary...</p>
                  </div>
                </div>
              </div>
            ) : output ? (
              <div className="bg-white rounded-3xl shadow-xl shadow-slate-200/50 border border-slate-100 overflow-hidden min-h-[600px] animate-in slide-in-from-bottom-4 duration-700">
                
                {/* Hero Section */}
                <div className="relative h-48 bg-gradient-to-br from-slate-900 via-indigo-950 to-slate-900 text-white p-8 flex flex-col justify-end">
                    <div className="absolute top-0 right-0 p-8 opacity-10">
                        <Globe size={200} />
                    </div>
                    <div className="relative z-10">
                        <div className="flex items-center gap-3 text-indigo-200 mb-2 font-medium">
                            <MapPin size={18} />
                            <span className="uppercase tracking-widest text-sm">{output.country}</span>
                        </div>
                        <h1 className="text-5xl font-bold tracking-tight mb-2">
                            {output.city_name || <span className="opacity-50">Loading...</span>}
                        </h1>
                    </div>
                </div>

                <div className="p-8 space-y-10">
                    
                    {/* Description & Meta */}
                    <div className="grid md:grid-cols-3 gap-8">
                        <div className="md:col-span-2">
                            <h3 className="text-lg font-semibold text-slate-900 mb-3">About the Destination</h3>
                            <p className="text-slate-600 leading-relaxed text-lg">
                                {output.description || <span className="text-slate-300 italic">Generating overview...</span>}
                            </p>
                        </div>
                        <div className="bg-slate-50 p-6 rounded-2xl border border-slate-100 space-y-4 h-fit">
                            <div>
                                <div className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-1 flex items-center gap-1"><Calendar size={12}/> Best Time</div>
                                <div className="font-medium text-slate-700">{output.best_time_to_visit || "..."}</div>
                            </div>
                            <div>
                                <div className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-1 flex items-center gap-1"><DollarSign size={12}/> Currency</div>
                                <div className="font-medium text-slate-700">{output.currency || "..."}</div>
                            </div>
                            <div>
                                <div className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-1 flex items-center gap-1"><Globe size={12}/> Languages</div>
                                <div className="font-medium text-slate-700">
                                    {output.languages?.join(", ") || "..."}
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* Itinerary */}
                    <div>
                        <div className="flex items-center gap-3 mb-6">
                            <div className="h-8 w-1 bg-indigo-500 rounded-full"></div>
                            <h2 className="text-2xl font-bold text-slate-900">Travel Itinerary</h2>
                        </div>

                        <div className="space-y-12">
                            {output.itinerary && output.itinerary.length > 0 ? (
                                output.itinerary.map((day, idx) => (
                                    <div key={idx} className="relative pl-8 md:pl-12 border-l-2 border-indigo-100/50 animate-slide-up">
                                        {/* Day Marker */}
                                        <div className="absolute -left-[11px] top-0 w-6 h-6 rounded-full bg-indigo-600 text-white flex items-center justify-center text-xs font-bold shadow-md shadow-indigo-200 ring-4 ring-white">
                                            {day.day}
                                        </div>
                                        
                                        <div className="mb-6">
                                            <h3 className="text-xl font-bold text-slate-900 flex items-center gap-3">
                                                {day.title || <span className="text-slate-300">Planning day...</span>}
                                                <span className="text-xs font-normal px-2 py-1 bg-slate-100 rounded-full text-slate-500">Day {day.day}</span>
                                            </h3>
                                            <p className="text-slate-500 mt-1 italic">{day.summary}</p>
                                        </div>

                                        <div className="grid gap-5 md:grid-cols-2">
                                            {day.activities && day.activities.map((activity, actIdx) => (
                                                <div key={actIdx} className="group bg-white rounded-xl border border-slate-100 p-5 hover:shadow-xl hover:shadow-indigo-100/50 hover:border-indigo-100 transition-all duration-300 cursor-default relative overflow-hidden animate-scale-up">
                                                    <div className="absolute top-0 right-0 w-16 h-16 bg-gradient-to-br from-indigo-500/5 to-transparent rounded-bl-full -mr-8 -mt-8 group-hover:scale-150 transition-transform duration-500"></div>
                                                    
                                                    <div className="flex justify-between items-start mb-3">
                                                        <div className="bg-indigo-50 text-indigo-700 text-[10px] font-bold uppercase tracking-wider px-2 py-1 rounded-md">
                                                            {activity.type}
                                                        </div>
                                                        <div className="flex items-center gap-1 text-amber-400 text-xs font-bold bg-amber-50 px-2 py-1 rounded-full border border-amber-100">
                                                            <Star size={10} className="fill-amber-400" />
                                                            {activity.reviews?.[0]?.rating || "New"}
                                                        </div>
                                                    </div>
                                                    
                                                    <h4 className="font-bold text-slate-800 mb-2 text-lg group-hover:text-indigo-700 transition-colors">{activity.name}</h4>
                                                    <p className="text-sm text-slate-500 mb-4 line-clamp-3 leading-relaxed">
                                                        {activity.description}
                                                    </p>
                                                    
                                                    <div className="flex items-center justify-between pt-4 border-t border-slate-50 text-xs text-slate-400">
                                                        <div className="flex items-center gap-1">
                                                            <MapPin size={12} />
                                                            <span className="truncate max-w-[120px]">{activity.location?.address || "Location"}</span>
                                                        </div>
                                                        <div className="font-medium text-emerald-600 bg-emerald-50 px-2 py-0.5 rounded">
                                                            {activity.price_range}
                                                        </div>
                                                    </div>
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                ))
                            ) : (
                                <div className="flex flex-col items-center justify-center py-12 text-slate-400 animate-pulse">
                                    <Clock size={32} className="mb-3 opacity-50" />
                                    <p>Curating the perfect itinerary for you...</p>
                                </div>
                            )}
                        </div>
                    </div>

                    {/* Local Tips */}
                    {output.top_tips && output.top_tips.length > 0 && (
                        <div className="mt-8 bg-gradient-to-r from-amber-50 to-orange-50 p-8 rounded-2xl border border-orange-100/50">
                            <h2 className="text-lg font-bold text-orange-900 mb-4 flex items-center gap-2">
                                <span className="text-xl">💡</span> Local Insider Tips
                            </h2>
                            <div className="grid md:grid-cols-2 gap-4">
                                {output.top_tips.map((tip, i) => (
                                    <div key={i} className="flex items-start gap-3 bg-white/60 p-3 rounded-lg border border-orange-100/50 shadow-sm animate-fade-in">
                                        <span className="mt-1.5 w-1.5 h-1.5 rounded-full bg-orange-400 shrink-0 shadow-sm shadow-orange-200"></span>
                                        <span className="text-orange-900/80 text-sm leading-relaxed">{tip}</span>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}
                </div>
              </div>
            ) : (
              <div className="h-[600px] flex flex-col items-center justify-center text-slate-400 bg-white rounded-3xl border border-dashed border-slate-200 shadow-sm">
                <div className="w-24 h-24 bg-slate-50 rounded-full flex items-center justify-center mb-6 shadow-inner">
                    <Globe size={48} className="text-indigo-200" />
                </div>
                <h3 className="text-xl font-semibold text-slate-700 mb-2">Ready to Explore?</h3>
                <p className="text-slate-500 max-w-sm text-center leading-relaxed">
                    Enter your API key on the left and click "Start Streaming" to generate a personalized travel guide in real-time.
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    </main>
  );
}
