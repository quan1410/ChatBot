from sentence_transformers import SentenceTransformer

model = SentenceTransformer("huyydangg/DEk21_hcmute_embedding")

sentences = [
    "Điều 2 Quyết định 185/QĐ-UB năm 1998 Bảng giá đất tỉnh Bến Tre có nội dung như sau:\n\nĐiều 2. Giá đất trên được áp dụng cho những trường hợp: Tính thuế chuyển quyền sử dụng cho những trường hợp: Tính thuế chuyển quyền sử dụng đất, thu lệ phí trước bạ, thu tiền sử dụng đất khi giao đất, cho thuê đất, tính giá trị tài sản khi giao đất, bồi thường thiệt hại về đất khi Nhà nước thu hồi.\nTrường hợp giao đất theo hình thức đấu giá, thì giá đất sẽ do Uỷ ban nhân dân tỉnh cho trường hợp cụ thể.\nGiá cho thuê đất đối với các tổ chức, cá nhân nước ngoài hoặc xí nghiệp có vốn đầu tư nước ngoài được áp dụng theo quy định của Chính phủ.",
    "Điều 2 Quyết định 55/2012/QĐ-UBND dự toán ngân sách phân bổ dự toán ngân sách 2013 Bình Dương",
    "Điều 2 Quyết định 185/QĐ-UB năm 1998 Bảng giá đất tỉnh Bến Tre",
    "Điều 3 Quyết định 79/2019/QĐ-UBND mức thu học phí quản lý và sử dụng học phí giáo dục mầm non Huế"
]
embeddings = model.encode(sentences)

similarities = model.similarity(embeddings, embeddings)
print(similarities.shape)
# [4, 4]
