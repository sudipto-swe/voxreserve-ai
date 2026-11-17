/**
 * VoiceAdapter handles Browser SpeechRecognition (STT) and SpeechSynthesis (TTS).
 * Supports user-gesture unlock, continuous speech, manual voice trigger,
 * and reliable speech playback across Chrome, Chromium, Edge, and Safari.
 */

interface IWindow extends Window {
  webkitSpeechRecognition?: any;
  SpeechRecognition?: any;
}

export class VoiceAdapter {
  private recognition: any = null;
  private synthesis: SpeechSynthesis | null = null;
  public isSpeechSupported: boolean = false;
  public isSynthesisSupported: boolean = false;
  private selectedVoice: SpeechSynthesisVoice | null = null;

  constructor(
    private onTranscript: (text: string, isFinal: boolean) => void,
    private onError: (errorMsg: string) => void,
    private onEnd: () => void
  ) {
    const win = window as unknown as IWindow;
    const SpeechRec = win.SpeechRecognition || win.webkitSpeechRecognition;

    if (SpeechRec) {
      try {
        this.recognition = new SpeechRec();
        this.recognition.continuous = false; // continuous=false is far more reliable on Linux/Chrome for emitting onresult
        this.recognition.interimResults = true;
        this.recognition.maxAlternatives = 1;
        this.recognition.lang = navigator.language || 'en-US';

        this.recognition.onresult = (event: any) => {
          let interim = '';
          let final = '';

          for (let i = event.resultIndex; i < event.results.length; ++i) {
            if (event.results[i].isFinal) {
              final += event.results[i][0].transcript;
            } else {
              interim += event.results[i][0].transcript;
            }
          }

          if (final) {
            this.onTranscript(final.trim(), true);
          } else if (interim) {
            this.onTranscript(interim.trim(), false);
          }
        };

        this.recognition.onerror = (event: any) => {
          const err = event.error || 'Speech recognition error';
          if (err === 'not-allowed') {
            this.onError('Microphone access was denied. Please allow microphone permissions in your browser address bar.');
          } else if (err === 'no-speech') {
            // User paused or remained silent
            this.onEnd();
          } else {
            console.warn(`Speech recognition notification: ${err}`);
            this.onEnd();
          }
        };

        this.recognition.onend = () => {
          this.onEnd();
        };

        this.isSpeechSupported = true;
      } catch (e) {
        this.isSpeechSupported = false;
      }
    }

    if ('speechSynthesis' in window) {
      this.synthesis = window.speechSynthesis;
      this.isSynthesisSupported = true;

      // Ensure voices are loaded (Chrome loads voices asynchronously)
      const loadVoices = () => {
        if (!this.synthesis) return;
        const voices = this.synthesis.getVoices();
        if (voices.length > 0) {
          this.selectedVoice = voices.find(v => v.lang.startsWith('en') && (v.name.includes('Google') || v.name.includes('Natural') || v.name.includes('Samantha') || v.name.includes('Daniel') || v.name.includes('English'))) || voices[0] || null;
        }
      };

      loadVoices();
      if (this.synthesis.onvoiceschanged !== undefined) {
        this.synthesis.onvoiceschanged = loadVoices;
      }
    }
  }

  public startListening() {
    if (!this.recognition) {
      this.onError('Browser speech recognition is not supported on this browser. Please type your message.');
      return;
    }

    // Wake up speech synthesis audio context with a silent unlock if needed
    if (this.synthesis && !this.synthesis.speaking) {
      try {
        this.synthesis.resume();
      } catch (e) {}
    }

    try {
      this.recognition.start();
    } catch (e: any) {
      if (e.name !== 'InvalidStateError') {
        this.onError(`Microphone notice: ${e.message}`);
      }
    }
  }

  public stopListening() {
    if (this.recognition) {
      try {
        this.recognition.stop();
      } catch (e) {}
    }
  }

  public speak(text: string, onStart?: () => void, onComplete?: () => void) {
    if (!this.synthesis || !this.isSynthesisSupported) {
      if (onComplete) onComplete();
      return;
    }

    try {
      // Unstick Chrome speech synthesis if paused
      if (this.synthesis.paused) {
        this.synthesis.resume();
      }
      this.synthesis.cancel();

      // Clean markdown, symbols, hashtags, asterisks
      const cleanText = text
        .replace(/[*_#`[\]()]/g, ' ')
        .replace(/\bVR-[A-Z0-9]+\b/g, (match) => `booking code ${match.split('').join(' ')}`)
        .replace(/\s+/g, ' ')
        .trim();

      if (!cleanText) {
        if (onComplete) onComplete();
        return;
      }

      const utterance = new SpeechSynthesisUtterance(cleanText);
      utterance.rate = 1.0;
      utterance.pitch = 1.0;
      utterance.volume = 1.0;

      const isBengali = /[\u0980-\u09FF]/.test(cleanText);
      const voices = this.synthesis.getVoices();

      if (isBengali) {
        utterance.lang = 'bn-BD';
        const bnVoice = voices.find(v => v.lang.startsWith('bn'));
        if (bnVoice) utterance.voice = bnVoice;
      } else {
        utterance.lang = 'en-US';
        if (this.selectedVoice) {
          utterance.voice = this.selectedVoice;
        } else {
          const defaultEn = voices.find(v => v.lang.startsWith('en'));
          if (defaultEn) utterance.voice = defaultEn;
        }
      }

      let started = false;
      utterance.onstart = () => {
        started = true;
        if (onStart) onStart();
      };

      utterance.onend = () => {
        if (onComplete) onComplete();
      };

      utterance.onerror = (err) => {
        console.warn('SpeechSynthesis utterance event:', err);
        if (onComplete) onComplete();
      };

      // Safeguard against Chrome garbage-collecting active utterance
      (window as any).__currentUtterance = utterance;

      this.synthesis.speak(utterance);

      // Chrome sometimes requires resume() after speak()
      if (this.synthesis.paused) {
        this.synthesis.resume();
      }

      // Safety fallback: if onstart hasn't fired in 4 seconds due to background tab restrictions
      setTimeout(() => {
        if (!started && this.synthesis && !this.synthesis.speaking) {
          if (onComplete) onComplete();
        }
      }, 4000);

    } catch (e) {
      console.error('Error invoking speak:', e);
      if (onComplete) onComplete();
    }
  }

  public stopSpeaking() {
    if (this.synthesis) {
      try {
        this.synthesis.cancel();
      } catch (e) {}
    }
  }
}
