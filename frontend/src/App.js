import React, { useState } from 'react';

function App() {
  const [question, setQuestion] = useState('');
  const [answer, setAnswer] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setAnswer('');
    try {
      const res = await fetch('http://localhost:5000/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question })
      });
      const data = await res.json();
      setAnswer(data.answer);
    } catch (err) {
      setAnswer('Có lỗi xảy ra!');
    }
    setLoading(false);
  };

  return (
    <div style={{ maxWidth: 500, margin: '40px auto', padding: 24, border: '1px solid #eee', borderRadius: 8 }}>
      <h2>Legal Chatbot</h2>
      <form onSubmit={handleSubmit}>
        <input
          type="text"
          value={question}
          onChange={e => setQuestion(e.target.value)}
          placeholder="Nhập câu hỏi về luật..."
          style={{ width: '100%', padding: 8, marginBottom: 12 }}
          required
        />
        <button type="submit" disabled={loading} style={{ width: '100%', padding: 8 }}>
          {loading ? 'Đang xử lý...' : 'Gửi câu hỏi'}
        </button>
      </form>
      {answer && (
        <div style={{ marginTop: 24, background: '#f9f9f9', padding: 12, borderRadius: 4 }}>
          <strong>Trả lời:</strong>
          <div>{answer}</div>
        </div>
      )}
    </div>
  );
}

export default App;
