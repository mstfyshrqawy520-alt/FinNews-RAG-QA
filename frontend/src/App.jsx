import React, { useState, useRef, useEffect } from "react";
import axios from "axios";
import {
  Send,
  Link as LinkIcon,
  Loader2,
  MessageSquare,
  AlertCircle,
  CheckCircle2,
  Copy,
  Download,
  RotateCcw,
  Upload,
} from "lucide-react";
import "./index.css";

const API_BASE_URL = "http://127.0.0.1:8000/api";

function App() {
  const [urls, setUrls] = useState("");
  const [isProcessing, setIsProcessing] = useState(false);
  const [status, setStatus] = useState(null);
  const [systemStatus, setSystemStatus] = useState(null);
  const [documentsCount, setDocumentsCount] = useState(0);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState(null);
  const fileInputRef = useRef(null);

  const [messages, setMessages] = useState([
    {
      id: 1,
      text: "Hello! I am your Financial News Assistant. Please paste some article URLs on the left, and then you can ask me questions about them.",
      isUser: false,
    },
  ]);
  const [inputMessage, setInputMessage] = useState("");
  const [isAsking, setIsAsking] = useState(false);

  const messagesEndRef = useRef(null);

  // Fetch system status on mount
  useEffect(() => {
    checkSystemStatus();
    const interval = setInterval(checkSystemStatus, 30000); // Check every 30 seconds
    return () => clearInterval(interval);
  }, []);

  const checkSystemStatus = async () => {
    try {
      const response = await axios.get(
        `${API_BASE_URL.replace("/api", "")}/health`,
      );
      setSystemStatus({ status: "healthy", connected: true });
    } catch (error) {
      setSystemStatus({
        status: "error",
        connected: false,
        message: "Backend is offline",
      });
    }
  };

  const checkDocumentsStatus = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/status`);
      setDocumentsCount(response.data.documents_count);
    } catch (error) {
      console.error("Error checking status:", error);
    }
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleIngest = async () => {
    if (!urls.trim()) return;

    const urlList = urls.split("\n").filter((url) => url.trim() !== "");
    if (urlList.length === 0) return;

    setIsProcessing(true);
    setStatus(null);

    try {
      const response = await axios.post(`${API_BASE_URL}/ingest`, {
        urls: urlList,
      });
      setStatus({
        type: "success",
        text: `Successfully processed ${response.data.documents_count} documents from ${urlList.length} URLs.`,
      });
      setUrls(""); // Clear input after success
      checkDocumentsStatus(); // Update documents count
    } catch (error) {
      console.error(error);
      const errorDetail = error.response?.data?.detail;
      const errorText =
        typeof errorDetail === "object"
          ? errorDetail.message || JSON.stringify(errorDetail)
          : errorDetail || "Failed to process URLs.";
      setStatus({ type: "error", text: errorText });
    } finally {
      setIsProcessing(false);
    }
  };

  const handleFileUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    const allowedTypes = [".pdf", ".txt"];
    const ext = file.name.substring(file.name.lastIndexOf(".")).toLowerCase();
    if (!allowedTypes.includes(ext)) {
      setUploadStatus({ type: "error", text: "Only PDF and TXT files are supported." });
      return;
    }

    setIsUploading(true);
    setUploadStatus(null);

    try {
      const formData = new FormData();
      formData.append("file", file);

      const response = await axios.post(`${API_BASE_URL}/upload`, formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      setUploadStatus({
        type: "success",
        text: `Successfully uploaded "${file.name}" (${response.data.documents_count} chunks).`,
      });
      checkDocumentsStatus();
    } catch (error) {
      console.error(error);
      const errorDetail = error.response?.data?.detail;
      const errorText =
        typeof errorDetail === "object"
          ? errorDetail.message || JSON.stringify(errorDetail)
          : errorDetail || "Failed to upload file.";
      setUploadStatus({ type: "error", text: errorText });
    } finally {
      setIsUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  };

  const handleSendMessage = async (e) => {
    if (e) e.preventDefault();
    if (!inputMessage.trim() || isAsking) return;

    const userQuestion = inputMessage.trim();
    setInputMessage("");

    const newMessages = [
      ...messages,
      { id: Date.now(), text: userQuestion, isUser: true },
    ];
    setMessages(newMessages);
    setIsAsking(true);

    try {
      const response = await axios.post(`${API_BASE_URL}/ask`, {
        question: userQuestion,
      });
      setMessages([
        ...newMessages,
        {
          id: Date.now(),
          text: response.data.answer,
          isUser: false,
          timestamp: new Date().toLocaleTimeString(),
        },
      ]);
    } catch (error) {
      console.error(error);
      const errorText =
        error.response?.data?.detail?.message ||
        "Error processing your question. Please try again.";
      setMessages([
        ...newMessages,
        {
          id: Date.now(),
          text: `⚠️ ${errorText}`,
          isUser: false,
        },
      ]);
    } finally {
      setIsAsking(false);
    }
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
    alert("Copied to clipboard!");
  };

  const downloadConversation = () => {
    const conversation = messages
      .map((msg) => `${msg.isUser ? "You" : "Assistant"}: ${msg.text}`)
      .join("\n\n");

    const element = document.createElement("a");
    element.setAttribute(
      "href",
      "data:text/plain;charset=utf-8," + encodeURIComponent(conversation),
    );
    element.setAttribute(
      "download",
      `conversation_${new Date().toISOString().slice(0, 10)}.txt`,
    );
    element.style.display = "none";
    document.body.appendChild(element);
    element.click();
    document.body.removeChild(element);
  };

  const clearConversation = () => {
    if (window.confirm("Clear conversation history?")) {
      setMessages([
        {
          id: 1,
          text: "Conversation cleared. Ready for new questions!",
          isUser: false,
        },
      ]);
    }
  };

  return (
    <div className="app-container">
      {/* Sidebar Panel */}
      <div className="sidebar glass-panel">
        <div className="sidebar-header">
          <MessageSquare size={24} color="#3b82f6" />
          <h1>FinNews Q&A</h1>
        </div>

        {/* System Status */}
        <div className="system-status">
          <div
            className={`status-indicator ${systemStatus?.connected ? "connected" : "disconnected"}`}
          >
            {systemStatus?.connected ? "🟢" : "🔴"}
            {systemStatus?.connected ? "Connected" : "Offline"}
          </div>
          {documentsCount > 0 && (
            <div className="documents-count">
              📄 {documentsCount} documents loaded
            </div>
          )}
        </div>

        <div className="url-section">
          <div className="url-input-container">
            <label htmlFor="url-input">Article URLs (One per line)</label>
            <textarea
              id="url-input"
              className="url-input"
              value={urls}
              onChange={(e) => setUrls(e.target.value)}
              placeholder="https://finance.yahoo.com/news/...&#10;https://reuters.com/..."
            />
          </div>

          <button
            className="primary-button"
            onClick={handleIngest}
            disabled={isProcessing || !urls.trim()}
          >
            {isProcessing ? (
              <>
                <Loader2 size={18} className="animate-spin" />
                Processing...
              </>
            ) : (
              <>
                <LinkIcon size={18} />
                Process URLs
              </>
            )}
          </button>

          {status && (
            <div className={`status-message ${status.type}`}>
              {status.type === "success" ? (
                <CheckCircle2 size={16} />
              ) : (
                <AlertCircle size={16} />
              )}
              {status.text}
            </div>
          )}

          {/* File Upload Section */}
          <div className="upload-divider">
            <span>or</span>
          </div>

          <input
            type="file"
            ref={fileInputRef}
            onChange={handleFileUpload}
            accept=".pdf,.txt"
            style={{ display: "none" }}
            id="file-upload"
          />
          <button
            className="upload-button"
            onClick={() => fileInputRef.current?.click()}
            disabled={isUploading}
          >
            {isUploading ? (
              <>
                <Loader2 size={18} className="animate-spin" />
                Uploading...
              </>
            ) : (
              <>
                <Upload size={18} />
                Upload PDF / TXT
              </>
            )}
          </button>

          {uploadStatus && (
            <div className={`status-message ${uploadStatus.type}`}>
              {uploadStatus.type === "success" ? (
                <CheckCircle2 size={16} />
              ) : (
                <AlertCircle size={16} />
              )}
              {uploadStatus.text}
            </div>
          )}
        </div>
      </div>

      {/* Main Chat Area */}
      <div className="chat-container glass-panel">
        <div className="chat-header">
          <h2>Chat</h2>
          <div className="chat-actions">
            <button
              className="chat-action-btn"
              onClick={downloadConversation}
              title="Download conversation"
            >
              <Download size={18} />
            </button>
            <button
              className="chat-action-btn"
              onClick={clearConversation}
              title="Clear conversation"
            >
              <RotateCcw size={18} />
            </button>
          </div>
        </div>

        <div className="chat-history">
          {messages.map((msg) => (
            <div
              key={msg.id}
              className={`message ${msg.isUser ? "user" : "ai"}`}
            >
              <div className="message-avatar">
                {msg.isUser ? (
                  <span style={{ fontSize: "14px" }}>U</span>
                ) : (
                  <MessageSquare size={18} color="white" />
                )}
              </div>
              <div className="message-content">
                <p>{msg.text}</p>
                {!msg.isUser && (
                  <button
                    className="copy-btn"
                    onClick={() => copyToClipboard(msg.text)}
                    title="Copy message"
                  >
                    <Copy size={14} />
                  </button>
                )}
              </div>
            </div>
          ))}

          {isAsking && (
            <div className="message ai">
              <div className="message-avatar">
                <MessageSquare size={18} color="white" />
              </div>
              <div className="message-content" style={{ padding: "1rem" }}>
                <div className="loading-dots">
                  <span></span>
                  <span></span>
                  <span></span>
                </div>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        <form onSubmit={handleSendMessage} className="chat-input-wrapper">
          <input
            type="text"
            className="chat-input"
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            placeholder="Ask a question about the news..."
            disabled={isAsking}
          />
          <button
            type="submit"
            className="icon-button send"
            disabled={isAsking || !inputMessage.trim()}
          >
            <Send size={18} />
          </button>
        </form>
      </div>
    </div>
  );
}

export default App;
