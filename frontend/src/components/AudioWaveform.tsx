import React from 'react';
import { AgentState } from '../types';

interface WaveformProps {
  agentState: AgentState;
  isListening: boolean;
}

export const AudioWaveform: React.FC<WaveformProps> = ({ agentState, isListening }) => {
  const bars = [16, 24, 40, 28, 55, 32, 60, 45, 70, 38, 50, 20];

  return (
    <div className="flex flex-col items-center justify-center my-4">
      {/* Waveform Bar Container */}
      <div className="flex items-center gap-1.5 h-16 px-4 py-2 bg-stone-900/40 rounded-full border border-stone-800">
        {bars.map((baseHeight, idx) => {
          let height = '15%';
          let animationClass = '';

          if (isListening) {
            height = `${Math.min(100, Math.max(25, (baseHeight * 1.3)))}%`;
            animationClass = 'animate-pulse';
          } else if (agentState === 'speaking') {
            height = `${baseHeight}%`;
            animationClass = 'animate-bounce';
          } else if (agentState === 'thinking' || agentState === 'executing_tool') {
            height = '30%';
            animationClass = 'animate-pulse';
          }

          return (
            <div
              key={idx}
              className={`w-1.5 rounded-full transition-all duration-200 ${
                isListening
                  ? 'bg-rose-500 shadow-sm shadow-rose-500/50'
                  : agentState === 'speaking'
                  ? 'bg-amber-400 shadow-sm shadow-amber-400/50'
                  : agentState === 'thinking'
                  ? 'bg-indigo-400'
                  : 'bg-stone-700'
              } ${animationClass}`}
              style={{
                height: isListening || agentState === 'speaking' ? height : '20%',
                animationDelay: `${idx * 0.08}s`
              }}
            />
          );
        })}
      </div>

      {/* Decorative Notice: Transparently informs users per requirement */}
      <p className="text-[11px] text-stone-500 mt-1.5 tracking-wide">
        {isListening ? 'Live speech capture active' : 'Voice activity monitor'}
      </p>
    </div>
  );
};
