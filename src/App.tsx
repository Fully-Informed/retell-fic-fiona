import React, { useEffect, useState, useRef } from "react";
import "./App.css";
import { RetellWebClient } from "retell-client-js-sdk";

const agentId = process.env.REACT_APP_RETELL_AGENTID;

interface RegisterCallResponse {
  call_id: string;
  access_token: string;
  transport?: "livekit" | "gateway";
  ice_servers?: RTCIceServer[];
}

// Agent audio level (RMS) above which Fiona counts as speaking. v3 web calls
// no longer send agent_start_talking / agent_stop_talking, so the halo is
// driven by the agent's audio level instead.
const AGENT_SPEAKING_VOLUME_THRESHOLD = 0.02;

const retellWebClient = new RetellWebClient();

const App = () => {
  const [isCalling, setIsCalling] = useState(false);
  const [isAgentSpeaking, setIsAgentSpeaking] = useState(false);
  const [instructionsVisible, setInstructionsVisible] = useState(true);
  const speakingTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    retellWebClient.on("call_started", () => {
      console.log("call started");
      setIsCalling(true);
      setInstructionsVisible(false);
    });

    retellWebClient.on("call_ended", () => {
      console.log("call ended");
      // Clear any pending speaking timeout
      if (speakingTimeoutRef.current) {
        clearTimeout(speakingTimeoutRef.current);
        speakingTimeoutRef.current = null;
      }
      setIsCalling(false);
      setIsAgentSpeaking(false);
      setInstructionsVisible(true);
    });

    // Fires every animation frame with a snapshot of the agent's audio
    // (requires emitRawAudioSamples: true in startCall).
    retellWebClient.on("audio", (audio: Float32Array) => {
      let sum = 0;
      for (let i = 0; i < audio.length; i++) sum += audio[i] * audio[i];
      const volume = Math.sqrt(sum / audio.length);

      if (volume > AGENT_SPEAKING_VOLUME_THRESHOLD) {
        // Agent is speaking: clear any pending timeout to stop speaking
        if (speakingTimeoutRef.current) {
          clearTimeout(speakingTimeoutRef.current);
          speakingTimeoutRef.current = null;
        }
        setIsAgentSpeaking(true);
      } else if (!speakingTimeoutRef.current) {
        // Debounce: wait 400ms before hiding green halo
        // This prevents flickering on short pauses between words
        speakingTimeoutRef.current = setTimeout(() => {
          setIsAgentSpeaking(false);
          speakingTimeoutRef.current = null;
        }, 400);
      }
    });

    retellWebClient.on("update", (update) => {
      console.log("Received update", update);
    });

    retellWebClient.on("metadata", (metadata) => {
      console.log("Received metadata", metadata);
    });

    retellWebClient.on("error", (error) => {
      console.error("An error occurred:", error);
      retellWebClient.stopCall();
      setIsCalling(false);
      setIsAgentSpeaking(false);
    });

    // Cleanup function
    return () => {
      if (speakingTimeoutRef.current) {
        clearTimeout(speakingTimeoutRef.current);
      }
    };
  }, []);

async function requestMicrophonePermission() {
  try {
    await navigator.mediaDevices.getUserMedia({ audio: true });
    console.log("Microphone permission granted");
  } catch (err) {
    console.error("Error requesting microphone permission:", err);
  }
}

  const toggleConversation = async () => {
    if (isCalling) {
      retellWebClient.stopCall();
    } else {
      setInstructionsVisible(false);
      try {
        await requestMicrophonePermission();
        const registerCallResponse = await registerCall(agentId);
        if (registerCallResponse.access_token) {
          await retellWebClient.startCall({
            callId: registerCallResponse.call_id,
            accessToken: registerCallResponse.access_token,
            transport: registerCallResponse.transport,
            iceServers: registerCallResponse.ice_servers,
            emitRawAudioSamples: true,
          });
        } else {
          console.error("No access token received");
          setInstructionsVisible(true);
        }
      } catch (error) {
        console.error("Error starting call:", error);
        setInstructionsVisible(true);
      }
    }
  };

  async function registerCall(agentId: string): Promise<RegisterCallResponse> {
    console.log("Registering call for agent ID:", agentId);
    try {
      const response = await fetch("/api/create-web-call", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          agent_id: agentId,
        }),
      });

      if (!response.ok) {
        throw new Error(`Error: ${response.status}`);
      }

      const data: RegisterCallResponse = await response.json();
      return data;
    } catch (err) {
      console.error("Error registering call:", err);
      throw err;
    }
  }

  const handleTouchStart = (e: React.TouchEvent) => {
    e.preventDefault();
    e.currentTarget.classList.add('active');
  };

  const handleTouchEnd = (e: React.TouchEvent) => {
    e.preventDefault();
    e.currentTarget.classList.remove('active');
    toggleConversation();
  }; 

  return (
    <div className="App">
      <header className="App-header">
        <div className="portrait-wrapper">
          <div
            className={`portrait-container ${isCalling ? 'active' : 'inactive'} ${isAgentSpeaking ? 'agent-speaking' : ''}`}
            onClick={toggleConversation}
            onTouchStart={handleTouchStart}
            onTouchEnd={handleTouchEnd}
          >
            <div className={`halo ${isCalling ? 'active' : 'inactive'} ${isAgentSpeaking ? 'speaking' : 'not-speaking'}`}></div>
            <img
              src="/Fiona_Round.png"
              alt="Fiona"
              className="agent-portrait"
            />
          </div>
          <div className={`instructions ${instructionsVisible ? 'visible' : 'hidden'}`}>
            <p><strong>Click</strong> or <strong>Tap</strong></p>
          </div>
        </div>
      </header>
    </div>
  );
};

export default App;