import sqlite3
import pandas as pd

# Điền tên file Excel của bạn vào đây (ví dụ: data_800mb.xlsx)
file_name = 'data_800mb.xlsx' 

print("Đang đọc file Excel (có thể mất một chút thời gian cho file lớn)...")
df = pd.read_excel(file_name)

conn = sqlite3.connect('quiz_app.db')
cursor = conn.cursor()

print("Đang lưu dữ liệu vào cơ sở dữ liệu...")
count = 0
for _, row in df.iterrows():
    cursor.execute("""
        INSERT INTO questions (subject, chapter, lesson, section, question_text, option_a, option_b, option_c, option_d, correct_answer, explanation)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        str(row.get('subject', 'Chung')),
        str(row.get('chapter', 'Chương 1')),
        str(row.get('lesson', 'Bài 1')),
        str(row.get('section', 'Phần 1')),
        str(row.get('question_text', '')),
        str(row.get('option_a', '')),
        str(row.get('option_b', '')),
        str(row.get('option_c', '')),
        str(row.get('option_d', '')),
        str(row.get('correct_answer', 'A')).strip().upper(),
        str(row.get('explanation', ''))
    ))
    count += 1

conn.commit()
conn.close()
print(f"Đã nạp thành công {count} câu hỏi vào hệ thống!")