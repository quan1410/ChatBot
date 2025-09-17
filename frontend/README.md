# Legal Chatbot Frontend

## Cách chạy

1. Cài đặt Node.js nếu chưa có.
2. Mở terminal tại thư mục `frontend` và chạy:
   ```powershell
   npm install
   npm start
   ```
3. Truy cập http://localhost:3000 để sử dụng giao diện chatbot.

---

# Legal Chatbot Backend

## Cách chạy

1. Cài đặt Python và pip nếu chưa có.
2. Mở terminal tại thư mục `backend` và chạy:
   ```powershell
   pip install -r requirements.txt
   python app.py
   ```
3. API sẽ chạy ở http://localhost:5000

---

## Kết nối FE và BE

FE sẽ gửi câu hỏi tới BE qua API `/api/chat` và nhận lại câu trả lời mẫu về luật.
