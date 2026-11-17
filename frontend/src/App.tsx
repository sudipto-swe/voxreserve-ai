import React, { useState } from 'react';
import { Mic, BookOpen, Calendar, LayoutDashboard, ShieldCheck, Flame } from 'lucide-react';
import { VoiceAssistant } from './components/VoiceAssistant';
import { ManualBookingForm } from './components/ManualBookingForm';
import { RestaurantMenu } from './components/RestaurantMenu';
import { AdminDashboard } from './components/AdminDashboard';

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'voice' | 'menu' | 'booking' | 'admin'>('voice');

  return (
    <div className="min-h-screen bg-stone-950 text-stone-100 flex flex-col font-sans selection:bg-rose-500 selection:text-white">
      {/* Top Navbar */}
      <header className="border-b border-stone-800/80 bg-stone-900/40 backdrop-blur-md sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-rose-600 to-amber-500 flex items-center justify-center shadow-lg shadow-rose-900/30">
              <Flame className="w-5 h-5 text-white" />
            </div>
            <div>
              <span className="font-bold tracking-tight text-white text-base">VOXRESERVE</span>
              <span className="text-[10px] text-stone-400 block -mt-1 font-mono">Aura & Embers Bistro</span>
            </div>
          </div>

          {/* Navigation Tabs */}
          <nav className="flex items-center gap-1 sm:gap-2">
            <button
              onClick={() => setActiveTab('voice')}
              className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-medium transition ${
                activeTab === 'voice'
                  ? 'bg-rose-600 text-white shadow-sm'
                  : 'text-stone-400 hover:text-stone-200 hover:bg-stone-800/60'
              }`}
            >
              <Mic className="w-4 h-4" />
              <span>Voice Concierge</span>
            </button>

            <button
              onClick={() => setActiveTab('menu')}
              className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-medium transition ${
                activeTab === 'menu'
                  ? 'bg-rose-600 text-white shadow-sm'
                  : 'text-stone-400 hover:text-stone-200 hover:bg-stone-800/60'
              }`}
            >
              <BookOpen className="w-4 h-4" />
              <span>Menu & Allergens</span>
            </button>

            <button
              onClick={() => setActiveTab('booking')}
              className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-medium transition ${
                activeTab === 'booking'
                  ? 'bg-rose-600 text-white shadow-sm'
                  : 'text-stone-400 hover:text-stone-200 hover:bg-stone-800/60'
              }`}
            >
              <Calendar className="w-4 h-4" />
              <span>Direct Booking</span>
            </button>

            <button
              onClick={() => setActiveTab('admin')}
              className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-medium transition ${
                activeTab === 'admin'
                  ? 'bg-rose-600 text-white shadow-sm'
                  : 'text-stone-400 hover:text-stone-200 hover:bg-stone-800/60'
              }`}
            >
              <LayoutDashboard className="w-4 h-4" />
              <span>Admin & Analytics</span>
            </button>
          </nav>
        </div>
      </header>

      {/* Main Container */}
      <main className="flex-1 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 w-full">
        {activeTab === 'voice' && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            <div className="lg:col-span-2">
              <VoiceAssistant />
            </div>

            {/* Right Column: Restaurant Highlights */}
            <div className="space-y-6">
              <div className="bg-stone-900 border border-stone-800 rounded-2xl p-6 shadow-xl">
                <h3 className="text-sm font-semibold text-white tracking-wide mb-3 flex items-center gap-2">
                  <Flame className="w-4 h-4 text-amber-500" />
                  About Aura & Embers
                </h3>
                <p className="text-xs text-stone-400 leading-relaxed">
                  450 Lumina Blvd, Waterfront District, San Francisco. Open daily 5:00 PM – 11:00 PM (open until midnight Fri & Sat).
                </p>
                <div className="mt-4 pt-4 border-t border-stone-800 text-xs text-stone-400 space-y-2">
                  <div className="flex justify-between">
                    <span>Dining Duration:</span>
                    <span className="text-stone-200 font-medium">90 mins standard</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Grace Period:</span>
                    <span className="text-stone-200 font-medium">15 mins</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Direct Telephone:</span>
                    <span className="text-stone-200 font-mono">+1 (415) 890-4422</span>
                  </div>
                </div>
              </div>

              <div className="bg-gradient-to-br from-stone-900 to-stone-950 border border-stone-800 rounded-2xl p-6 shadow-xl">
                <h3 className="text-sm font-semibold text-white tracking-wide mb-2 flex items-center gap-2">
                  <ShieldCheck className="w-4 h-4 text-emerald-400" />
                  Safety & Verified Booking Guarantee
                </h3>
                <p className="text-xs text-stone-400 leading-relaxed">
                  Every table confirmed by VOX is verified through real-time database transactions with row-level locks, guaranteeing zero double-bookings.
                </p>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'menu' && <RestaurantMenu />}
        {activeTab === 'booking' && <ManualBookingForm />}
        {activeTab === 'admin' && <AdminDashboard />}
      </main>

      {/* Footer */}
      <footer className="border-t border-stone-800/60 py-6 text-center text-xs text-stone-500 bg-stone-950">
        <p>VOXRESERVE &copy; 2026. Production AI Restaurant Voice Reservation Platform. Powered by Open-Source & Local Intelligence.</p>
      </footer>
    </div>
  );
};

export default App;
