/**
 * Browser speech-to-text via the open Web Speech API
 * (SpeechRecognition / webkitSpeechRecognition).
 * No API key; works in Chromium, Edge, and Safari.
 */

import { useCallback, useEffect, useRef, useState } from "react";

type SpeechRecognitionConstructor = new () => SpeechRecognition;

function getSpeechRecognitionCtor(): SpeechRecognitionConstructor | null {
  if (typeof window === "undefined") return null;
  const w = window as Window & {
    SpeechRecognition?: SpeechRecognitionConstructor;
    webkitSpeechRecognition?: SpeechRecognitionConstructor;
  };
  return w.SpeechRecognition ?? w.webkitSpeechRecognition ?? null;
}

export function isSpeechToTextSupported(): boolean {
  return getSpeechRecognitionCtor() !== null;
}

export function useSpeechToText(options?: {
  lang?: string;
  continuous?: boolean;
  onResult?: (transcript: string, isFinal: boolean) => void;
}) {
  const [listening, setListening] = useState(false);
  const [supported] = useState(() => isSpeechToTextSupported());
  const [error, setError] = useState<string | null>(null);
  const recognitionRef = useRef<SpeechRecognition | null>(null);
  const onResultRef = useRef(options?.onResult);
  onResultRef.current = options?.onResult;

  useEffect(() => {
    const Ctor = getSpeechRecognitionCtor();
    if (!Ctor) return;

    const recognition = new Ctor();
    recognition.lang = options?.lang ?? "en-US";
    recognition.continuous = options?.continuous ?? false;
    recognition.interimResults = true;
    recognition.maxAlternatives = 1;

    recognition.onstart = () => {
      setListening(true);
      setError(null);
    };
    recognition.onend = () => {
      setListening(false);
    };
    recognition.onerror = (event) => {
      setListening(false);
      if (event.error === "aborted" || event.error === "no-speech") return;
      if (event.error === "not-allowed") {
        setError("Microphone permission denied.");
        return;
      }
      setError("Could not capture speech. Try again.");
    };
    recognition.onresult = (event) => {
      let interim = "";
      let finalText = "";
      for (let i = event.resultIndex; i < event.results.length; i++) {
        const result = event.results[i];
        if (!result) continue;
        const chunk = result[0]?.transcript ?? "";
        if (result.isFinal) finalText += chunk;
        else interim += chunk;
      }
      const text = (finalText || interim).trim();
      if (text) onResultRef.current?.(text, Boolean(finalText));
    };

    recognitionRef.current = recognition;
    return () => {
      recognition.onstart = null;
      recognition.onend = null;
      recognition.onerror = null;
      recognition.onresult = null;
      try {
        recognition.abort();
      } catch {
        /* ignore */
      }
      recognitionRef.current = null;
    };
    // lang/continuous are init-time only for this instance
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const stop = useCallback(() => {
    const recognition = recognitionRef.current;
    if (!recognition) return;
    try {
      recognition.stop();
    } catch {
      /* ignore */
    }
    setListening(false);
  }, []);

  const start = useCallback(() => {
    const recognition = recognitionRef.current;
    if (!recognition) {
      setError("Speech recognition is not supported in this browser.");
      return;
    }
    setError(null);
    try {
      recognition.start();
    } catch {
      // Already started — restart cleanly
      try {
        recognition.abort();
        recognition.start();
      } catch {
        setError("Could not start the microphone.");
      }
    }
  }, []);

  const toggle = useCallback(() => {
    if (listening) stop();
    else start();
  }, [listening, start, stop]);

  return { supported, listening, error, start, stop, toggle };
}
