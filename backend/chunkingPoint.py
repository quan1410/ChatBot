import pdfplumber
import json
import re
import os

#trích xuất Title của file 
def extract_title(text):
    # Tìm dòng có số hiệu
    so_match = re.search(r'Số:\s*([^\n]+)', text)
    so_text = so_match.group(0).strip() if so_match else ""

    # Tìm loại văn bản
    loai_vb_match = re.search(r'\n\s*(QUYẾT ĐỊNH|THÔNG TƯ|NGHỊ ĐỊNH|LUẬT|CHỈ THỊ|NGHỊ QUYẾT)\s*\n', text, re.IGNORECASE)
    loai_vb = loai_vb_match.group(1).strip().title() if loai_vb_match else ""

    # Tìm đoạn văn từ sau loại văn bản đến hết câu có "ban hành", "của Bộ", "do ... ban hành", ...
    start = loai_vb_match.end() if loai_vb_match else 0
    following_text = text[start:]

    # Cắt đoạn từ sau loại văn bản đến các từ khóa kết thúc tiêu đề
    # Dừng tại dòng bắt đầu bằng từ khóa legal basis
    legal_basis_keywords = ["Căn cứ", "Chiếu theo", "Xét đề nghị"]
    end_idx = len(following_text)

    for keyword in legal_basis_keywords:
        keyword_match = re.search(r'\n\s*' + re.escape(keyword), following_text)
        if keyword_match:
            end_idx = min(end_idx, keyword_match.start())

    # Lấy phần văn bản nghi là tiêu đề
    raw_title = following_text[:end_idx].strip()

    # Làm sạch đoạn đó thành một dòng
    lines = raw_title.split('\n')
    filtered_lines = []
    for line in lines:
        line = line.strip()
        if line:
            filtered_lines.append(line)
    joined_title = ' '.join(filtered_lines)

    # Gộp final title
    full_title = f"{loai_vb} {so_text} - {loai_vb.upper()} {joined_title}"
    return full_title.strip()



def remove_legal_basis(text):
    # Loại bỏ phần legal_basis đầu văn bản (từ đầu đến trước "Phần" hoặc "Chương")
    m = re.search(r'(Phần\s+\w+|Chương\s+[IVXLCDM])', text)
    if m:
        return text[m.start():]
    return text

def split_sections(text):
    # Tách dựa vào đầu dòng, lấy cả tiêu đề IN HOA sau "Chương X"
    pattern = r'(?m)^(Phần|Chương|Mục)[\s\.\:\-]*[\wIVXLCDM]+[^\n]*'
    matches = list(re.finditer(pattern, text))
    sections = []
    for i, m in enumerate(matches):
        start = m.start()
        end = matches[i+1].start() if i+1 < len(matches) else len(text)
        
        # Lấy phần đầu "Chương X" 
        header = m.group(0).strip()
        
        # Tìm dòng tiêu đề IN HOA sau "Chương X"
        remaining_text = text[m.end():end]
        lines = remaining_text.split('\n')
        
        # Tìm dòng đầu tiên không trống để lấy tiêu đề
        title_line = ""
        for line in lines:
            line = line.strip()
            if not line:  # Bỏ qua dòng trống
                continue
            if re.match(r'^Điều\s+\d+', line):  # Gặp điều - dừng lại
                break
            if re.match(r'^(Phần|Chương|Mục)', line):  # Gặp phần/chương/mục khác - dừng lại
                break
            # Nếu dòng này toàn chữ in hoa (có thể là tiêu đề chương)
            if line.isupper() or len([c for c in line if c.isupper()]) > len(line) * 0.7:
                title_line = line
                break
            # Hoặc nếu dòng này có vẻ là tiêu đề (không bắt đầu bằng số/ký tự đặc biệt)
            if not re.match(r'^[\d\.\-\(\)]', line):
                title_line = line
                break
        
        # Gộp header với tiêu đề
        if title_line:
            header = f"{header} {title_line}"
        
        section_text = text[start:end].strip()
        sections.append((header.strip(), section_text))
    return sections


def extract_context(section_text):
    # Bỏ header phần/chương/mục, chỉ lấy các điều/khoản
    lines = section_text.split('\n')
    if lines and (lines[0].startswith('Phần') or lines[0].startswith('Chương') or lines[0].startswith('Mục')):
        lines = lines[1:]
    context = '\n'.join(lines).strip()
    return context

def split_context_by_dieu(context, min_len=150, max_len=512):
    # Tách văn bản thành từng đoạn Điều, tránh bắt các từ "Điều x" không ở đầu dòng
    pattern = r'(?m)^\s*(Điều\s+\d+[^\n]*)'  # (?m): multiline mode
    matches = list(re.finditer(pattern, context))
    if not matches:
        return [context]
    
    chunks = []
    for i, m in enumerate(matches):
        start = m.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(context)
        dieu_text = context[start:end].strip()
        chunks.append(dieu_text)
    return chunks



# Hàm tách Điều, Khoản, Điểm từ văn bản
def parse_article_structure(dieu_text):
    # Tìm Điều
    article_match = re.match(r'^(Điều\s+\d+[^\n]*)', dieu_text)
    article = article_match.group(1).strip() if article_match else None

    # Tìm các khoản: Khoản x hoặc x. ở đầu dòng
    subclause_match = re.search(r'Khoản\s+\d+[^\n]*', dieu_text)
    if subclause_match:
        subclause = subclause_match.group(0).strip()
    else:
        subclause_match2 = re.search(r'(?m)^\s*(\d+)\.\s*([^\n]*)', dieu_text)
        subclause = f"Khoản {subclause_match2.group(1)}: {subclause_match2.group(2).strip()}" if subclause_match2 else None

    # Tìm các điểm: Điểm x hoặc x) ở đầu dòng
    clause_match = re.search(r'Điểm\s+[a-zA-Z][^\n]*', dieu_text)
    if clause_match:
        clause = clause_match.group(0).strip()
    else:
        clause_match2 = re.search(r'(?m)^\s*([a-zA-Z])\)\s*([^\n]*)', dieu_text)
        clause = f"Điểm {clause_match2.group(1)}: {clause_match2.group(2).strip()}" if clause_match2 else None

    return article, subclause, clause

def build_json_chunks(title, sections):
    json_chunks = []
    law_id = title
    current_part = None      # Phần
    current_chapter = None  # Chương
    current_section = None  # Mục
    current_subsection = None  # Tiểu mục

    for header, section_text in sections:
        context = extract_context(section_text)
        dieu_chunks = split_context_by_dieu(context)

        if header.startswith("Phần"):
            current_part = header
            current_chapter = None
            current_section = None
            current_subsection = None
        elif header.startswith("Chương"):
            current_chapter = header
            current_section = None
            current_subsection = None
        elif header.startswith("Mục"):
            current_section = header
            current_subsection = None
        elif header.startswith("Tiểu mục"):
            current_subsection = header

        for dieu_chunk in dieu_chunks:
            if dieu_chunk.strip():
                # Tách tiếp các khoản trong điều
                subclause_chunks = re.split(r'(?m)^\s*(?:Khoản\s+\d+|\d+\.)', dieu_chunk)
                subclause_headers = re.findall(r'(?m)^\s*(Khoản\s+\d+[^\n]*|\d+\.\s*[^\n]*)', dieu_chunk)
                if len(subclause_chunks) > 1:
                    for idx, subclause_text in enumerate(subclause_chunks[1:]):
                        subclause_header = subclause_headers[idx] if idx < len(subclause_headers) else None
                        # Tách tiếp các điểm trong khoản
                        clause_chunks = re.split(r'(?m)^\s*(?:Điểm\s+[a-zA-Z]|[a-zA-Z]\))', subclause_text)
                        clause_headers = re.findall(r'(?m)^\s*(Điểm\s+[a-zA-Z][^\n]*|[a-zA-Z]\)\s*[^\n]*)', subclause_text)
                        if len(clause_chunks) > 1:
                            for cidx, clause_text in enumerate(clause_chunks[1:]):
                                clause_header = clause_headers[cidx] if cidx < len(clause_headers) else None
                                json_chunks.append({
                                    "law_id": law_id,
                                    "section": current_part if current_part else None,
                                    "chapter": current_chapter if current_chapter else None,
                                    "subsection": current_section if current_section else None,
                                    "subsubsection": current_subsection if current_subsection else None,
                                    "article": re.match(r'^(Điều\s+\d+[^\n]*)', dieu_chunk).group(1).strip() if re.match(r'^(Điều\s+\d+[^\n]*)', dieu_chunk) else None,
                                    "Clause": clause_header if clause_header else None,
                                    "Subclause": subclause_header if subclause_header else None,
                                    "Context": clause_text.strip()
                                })
                        else:
                            json_chunks.append({
                                "law_id": law_id,
                                "section": current_part if current_part else None,
                                "chapter": current_chapter if current_chapter else None,
                                "subsection": current_section if current_section else None,
                                "subsubsection": current_subsection if current_subsection else None,
                                "article": re.match(r'^(Điều\s+\d+[^\n]*)', dieu_chunk).group(1).strip() if re.match(r'^(Điều\s+\d+[^\n]*)', dieu_chunk) else None,
                                "Clause": None,
                                "Subclause": subclause_header if subclause_header else None,
                                "Context": subclause_text.strip()
                            })
                else:
                    # Không có khoản, tách điểm trực tiếp trong điều
                    clause_chunks = re.split(r'(?m)^\s*(?:Điểm\s+[a-zA-Z]|[a-zA-Z]\))', dieu_chunk)
                    clause_headers = re.findall(r'(?m)^\s*(Điểm\s+[a-zA-Z][^\n]*|[a-zA-Z]\)\s*[^\n]*)', dieu_chunk)
                    if len(clause_chunks) > 1:
                        for cidx, clause_text in enumerate(clause_chunks[1:]):
                            clause_header = clause_headers[cidx] if cidx < len(clause_headers) else None
                            json_chunks.append({
                                "law_id": law_id,
                                "section": current_part if current_part else None,
                                "chapter": current_chapter if current_chapter else None,
                                "subsection": current_section if current_section else None,
                                "subsubsection": current_subsection if current_subsection else None,
                                "article": re.match(r'^(Điều\s+\d+[^\n]*)', dieu_chunk).group(1).strip() if re.match(r'^(Điều\s+\d+[^\n]*)', dieu_chunk) else None,
                                "Clause": clause_header if clause_header else None,
                                "Subclause": None,
                                "Context": clause_text.strip()
                            })
                    else:
                        # Không có khoản, không có điểm, context là điều
                        article, subclause, clause = parse_article_structure(dieu_chunk)
                        json_chunks.append({
                            "law_id": law_id,
                            "section": current_part if current_part else None,
                            "chapter": current_chapter if current_chapter else None,
                            "subsection": current_section if current_section else None,
                            "subsubsection": current_subsection if current_subsection else None,
                            "article": article if article else None,
                            "Clause": clause if clause else None,
                            "Subclause": subclause if subclause else None,
                            "Context": dieu_chunk.strip()
                        })
    return json_chunks


def main():
    pdf_path = "D:/Project/Đánh giá các cách chia văn bản/Data thử/pdf/23_2008_QH12_82203.pdf"
    json_path = "D:/Project/Đánh giá các cách chia văn bản/Data thử/json/Luatgiaothong.json"
    print(f"Bắt đầu xử lý file: {pdf_path}")
    if not os.path.exists(pdf_path):
        print(f"Không tìm thấy file {pdf_path}")
        return
    with pdfplumber.open(pdf_path) as pdf:
        full_text = ""
        for i, page in enumerate(pdf.pages):
            print(f"Đang đọc trang {i+1}/{len(pdf.pages)}...")
            page_text = page.extract_text()
            if page_text:
                full_text += page_text + "\n"
    print("Đã đọc xong toàn bộ file PDF.")
    # Lưu text ra file riêng
    text_output_path = "D:/Project/Đánh giá các cách chia văn bản/Data thử/json/output_text.txt"
    with open(text_output_path, "w", encoding="utf-8") as f:
        f.write(full_text)
    print(f"Đã lưu toàn bộ text vào: {text_output_path}")

    # Trích xuất title động
    title = extract_title(full_text)
    print(f"Đã trích xuất tiêu đề: {title}")

    full_text = remove_legal_basis(full_text)
    print("Đã loại bỏ phần legal_basis.")

    sections = split_sections(full_text)
    print(f"Tìm thấy {len(sections)} phần/chương/mục.")

    json_chunks = build_json_chunks(title, sections)
    print(f"Tạo {len(json_chunks)} chunk.")

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(json_chunks, f, ensure_ascii=False, indent=2)
    print(f"Đã lưu file JSON chunked: {json_path}")


if __name__ == "__main__":
    main()