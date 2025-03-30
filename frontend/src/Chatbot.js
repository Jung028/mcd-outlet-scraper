import { useState, useRef, useEffect } from "react";
import "./styles/App.css";

const Chatbot = () => {
  const [query, setQuery] = useState("");
  const [response, setResponse] = useState([]);
  const [isOpen, setIsOpen] = useState(false);
  const chatHistoryRef = useRef(null);

  const formatResponse = (text) => {
    return text
      .replace(/\*/g, "") // Remove markdown asterisks
      .replace(/McDonald's /g, "\n\n🔹 McDonald's ") // Ensure each outlet starts on a new line
      .replace(/,/g, "\n") // Ensure each feature appears on a new line
      .replace(/:/g, ":\n") // Add a newline after colons
      .replace(/Note that/g, "\n💡 *Note:*"); // Highlight important notes
  };

  const handleChat = async () => {
    if (!query) return;

    try {
      const res = await fetch(`http://localhost:8000/chat/${encodeURIComponent(query)}`);
      const data = await res.json();
      setResponse([...response, { query, answer: formatResponse(data.answer) }]);
      setQuery("");
    } catch (error) {
      setResponse([...response, { query, answer: "❌ Error: Unable to fetch response." }]);
    }
  };

  // Auto-scroll to the bottom of the chat history
  useEffect(() => {
    if (chatHistoryRef.current) {
      chatHistoryRef.current.scrollTop = chatHistoryRef.current.scrollHeight;
    }
  }, [response]);

  return (
    <>
      <button className="chat-toggle" onClick={() => setIsOpen(!isOpen)}>
        {isOpen ? "−" : "💬"}
      </button>

      {isOpen && (
        <div className="chatbot-container">
          <div className="chat-header">
            <h2>McDonald's Chatbot</h2>
            <button className="close-btn" onClick={() => setIsOpen(false)}>×</button>
          </div>

          <div className="chat-history" ref={chatHistoryRef}>
            {response.length > 0 ? (
              response.map((chat, index) => (
                <div key={index} className="chat-message">
                  <p className="chat-question"><strong>You:</strong> {chat.query}</p>
                  <p className="chat-answer"><strong>Bot:</strong> <br /> {chat.answer}</p>
                </div>
              ))
            ) : (
              <p className="chat-placeholder">Ask me anything about McDonald's outlets!</p>
            )}
          </div>

          <div className="chat-input">
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Ask about McDonald's outlets..."
            />
            <button onClick={handleChat}>Send</button>
          </div>
        </div>
      )}
    </>
  );
};

export default Chatbot;
