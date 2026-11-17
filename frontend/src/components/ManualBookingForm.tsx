import React, { useState } from 'react';
import { CheckCircle, AlertCircle, Sparkles } from 'lucide-react';
import { ReservationResponse } from '../types';

export const ManualBookingForm: React.FC = () => {
  const tomorrow = new Date(Date.now() + 86400000).toISOString().split('T')[0];
  
  const [date, setDate] = useState(tomorrow);
  const [time, setTime] = useState('19:00');
  const [partySize, setPartySize] = useState(2);
  const [seatingArea, setSeatingArea] = useState('indoor');
  const [name, setName] = useState('');
  const [phone, setPhone] = useState('');
  const [specialRequests, setSpecialRequests] = useState('');

  const [loading, setLoading] = useState(false);
  const [availabilityResult, setAvailabilityResult] = useState<any>(null);
  const [reservationResult, setReservationResult] = useState<ReservationResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleCheckAvailability = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setReservationResult(null);

    try {
      const res = await fetch(`http://localhost:8005/api/availability?date=${date}&time=${time}&party_size=${partySize}&seating_area=${seatingArea}`);
      const data = await res.json();
      setAvailabilityResult(data);
    } catch (err: any) {
      setError("Failed to query availability: " + err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleConfirmBooking = async () => {
    if (!name || !phone) {
      setError("Please provide your full name and phone number to complete the booking.");
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const res = await fetch(`http://localhost:8005/api/reservations`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          customer_name: name,
          customer_phone: phone,
          date,
          time,
          party_size: partySize,
          seating_area: seatingArea,
          special_requests: specialRequests
        })
      });

      const data = await res.json();
      if (!res.ok) {
        setError(data.detail || "Booking failed");
      } else {
        setReservationResult(data);
        setAvailabilityResult(null);
      }
    } catch (err: any) {
      setError("Error creating reservation: " + err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-stone-900 border border-stone-800 rounded-2xl p-6 shadow-xl">
      <div className="flex items-center gap-2 mb-4">
        <Sparkles className="w-5 h-5 text-rose-500" />
        <h3 className="text-lg font-semibold text-white">Direct Table Reservation Engine</h3>
      </div>
      <p className="text-xs text-stone-400 mb-6">
        Verified real-time PostgreSQL availability check with transaction concurrency protection.
      </p>

      {error && (
        <div className="p-3 mb-4 rounded-xl bg-rose-950/60 border border-rose-800 text-xs text-rose-300 flex items-center gap-2">
          <AlertCircle className="w-4 h-4 text-rose-400 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {reservationResult?.success ? (
        <div className="p-6 bg-emerald-950/40 border border-emerald-800/80 rounded-xl text-center space-y-3">
          <CheckCircle className="w-10 h-10 text-emerald-400 mx-auto" />
          <h4 className="text-lg font-semibold text-emerald-200">Table Successfully Reserved!</h4>
          <p className="text-sm text-stone-300">
            Booking Code: <span className="font-mono font-bold text-amber-300 text-base">{reservationResult.booking_code}</span>
          </p>
          <div className="text-xs text-stone-400 space-y-1">
            <p>Table: <strong className="text-white">{reservationResult.table_number}</strong> ({reservationResult.seating_area})</p>
            <p>Date & Time: <strong className="text-white">{reservationResult.date} at {reservationResult.time}</strong></p>
            <p>Party of: <strong className="text-white">{reservationResult.party_size} guests</strong></p>
          </div>
          <button
            onClick={() => setReservationResult(null)}
            className="mt-3 px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg text-xs font-medium transition"
          >
            Make Another Booking
          </button>
        </div>
      ) : (
        <form onSubmit={handleCheckAvailability} className="space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <div>
              <label className="block text-xs font-medium text-stone-300 mb-1">Date</label>
              <div className="relative">
                <input
                  type="date"
                  value={date}
                  onChange={(e) => setDate(e.target.value)}
                  className="w-full px-3 py-2 bg-stone-950 border border-stone-800 rounded-lg text-xs text-white focus:outline-none focus:border-rose-500"
                  required
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-medium text-stone-300 mb-1">Time</label>
              <input
                type="time"
                value={time}
                onChange={(e) => setTime(e.target.value)}
                className="w-full px-3 py-2 bg-stone-950 border border-stone-800 rounded-lg text-xs text-white focus:outline-none focus:border-rose-500"
                required
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-stone-300 mb-1">Guests</label>
              <select
                value={partySize}
                onChange={(e) => setPartySize(Number(e.target.value))}
                className="w-full px-3 py-2 bg-stone-950 border border-stone-800 rounded-lg text-xs text-white focus:outline-none focus:border-rose-500"
              >
                {[1, 2, 3, 4, 5, 6, 8, 10].map((n) => (
                  <option key={n} value={n}>{n} {n === 1 ? 'Guest' : 'Guests'}</option>
                ))}
              </select>
            </div>
          </div>

          <div>
            <label className="block text-xs font-medium text-stone-300 mb-1">Preferred Seating Area</label>
            <select
              value={seatingArea}
              onChange={(e) => setSeatingArea(e.target.value)}
              className="w-full px-3 py-2 bg-stone-950 border border-stone-800 rounded-lg text-xs text-white focus:outline-none focus:border-rose-500"
            >
              <option value="indoor">Main Dining Hall (Indoor)</option>
              <option value="booth">Cozy Leather Booth</option>
              <option value="outdoor_patio">Heated Garden Patio</option>
              <option value="bar">Bar Counter Seating</option>
              <option value="private_dining">Private Dining Room (Large Parties)</option>
            </select>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full py-2.5 bg-stone-800 hover:bg-stone-700 text-stone-200 border border-stone-700 rounded-xl text-xs font-medium transition"
          >
            {loading ? "Checking Database..." : "Verify Table Availability"}
          </button>

          {/* Availability Status Display */}
          {availabilityResult && (
            <div className="p-4 bg-stone-950 rounded-xl border border-stone-800 mt-4 space-y-3">
              {availabilityResult.available ? (
                <>
                  <div className="flex items-center gap-2 text-emerald-400 text-xs font-semibold">
                    <CheckCircle className="w-4 h-4" />
                    <span>Verified Available! ({availabilityResult.available_tables_count} suitable tables)</span>
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-2">
                    <div>
                      <label className="block text-[11px] text-stone-400 mb-1">Full Name *</label>
                      <input
                        type="text"
                        placeholder="e.g. Marcus Miller"
                        value={name}
                        onChange={(e) => setName(e.target.value)}
                        className="w-full px-3 py-1.5 bg-stone-900 border border-stone-800 rounded-lg text-xs text-white"
                        required
                      />
                    </div>
                    <div>
                      <label className="block text-[11px] text-stone-400 mb-1">Contact Phone *</label>
                      <input
                        type="tel"
                        placeholder="e.g. +1 (555) 987-6543"
                        value={phone}
                        onChange={(e) => setPhone(e.target.value)}
                        className="w-full px-3 py-1.5 bg-stone-900 border border-stone-800 rounded-lg text-xs text-white"
                        required
                      />
                    </div>
                  </div>

                  <div>
                    <label className="block text-[11px] text-stone-400 mb-1">Special Requests (Optional)</label>
                    <input
                      type="text"
                      placeholder="e.g. Dietary allergies, anniversary, high chair"
                      value={specialRequests}
                      onChange={(e) => setSpecialRequests(e.target.value)}
                      className="w-full px-3 py-1.5 bg-stone-900 border border-stone-800 rounded-lg text-xs text-white"
                    />
                  </div>

                  <button
                    type="button"
                    onClick={handleConfirmBooking}
                    disabled={loading}
                    className="w-full py-2.5 bg-rose-600 hover:bg-rose-500 text-white rounded-xl text-xs font-semibold transition shadow-md"
                  >
                    Confirm & Complete Reservation
                  </button>
                </>
              ) : (
                <div className="text-xs text-amber-400 space-y-2">
                  <p>{availabilityResult.reason || "No tables available for this time."}</p>
                  {availabilityResult.alternative_slots?.length > 0 && (
                    <div>
                      <p className="text-stone-400">Alternative times on this date:</p>
                      <div className="flex gap-2 mt-1">
                        {availabilityResult.alternative_slots.map((alt: string) => (
                          <button
                            key={alt}
                            type="button"
                            onClick={() => setTime(alt)}
                            className="px-2.5 py-1 bg-stone-800 hover:bg-stone-700 text-stone-200 border border-stone-700 rounded text-xs"
                          >
                            {alt}
                          </button>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          )}
        </form>
      )}
    </div>
  );
};
