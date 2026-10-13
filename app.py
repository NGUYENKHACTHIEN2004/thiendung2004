import hashlib
import random
import sqlite3
import pandas as pd
import streamlit as st

# --- CẤU HÌNH CƠ SỞ DỮ LIỆU ---


def init_db():
  conn = sqlite3.connect("quiz_app.db", check_same_thread=False)
  cursor = conn.cursor()
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT,
            role TEXT
        )
    """)
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject TEXT,
            chapter TEXT,
            lesson TEXT,
            section TEXT,
            question_text TEXT,
            option_a TEXT,
            option_b TEXT,
            option_c TEXT,
            option_d TEXT,
            correct_answer TEXT,
            explanation TEXT
        )
    """)
  # Tạo tài khoản admin mặc định (admin / 123456)
  cursor.execute("SELECT * FROM users WHERE username = 'admin'")
  if not cursor.fetchone():
    hashed_pw = hashlib.sha256("123456".encode()).hexdigest()
    cursor.execute(
        "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
        ("admin", hashed_pw, "admin"),
    )
  conn.commit()
  return conn


conn = init_db()
cursor = conn.cursor()


def hash_password(password):
  return hashlib.sha256(password.encode()).hexdigest()


# --- GIAO DIỆN ĐĂNG NHẬP / ĐĂNG KÝ ---
st.set_page_config(
    page_title="Hệ thống Ôn tập Trắc nghiệm", page_icon="📚", layout="wide"
)

if "logged_in" not in st.session_state:
  st.session_state["logged_in"] = False
  st.session_state["username"] = ""
  st.session_state["role"] = ""

if not st.session_state["logged_in"]:
  st.title("🔐 Đăng nhập hệ thống ôn tập")
  tab1, tab2 = st.tabs(["Đăng nhập", "Đăng ký tài khoản"])

  with tab1:
    with st.form("login_form"):
      username = st.text_input("Tên đăng nhập")
      password = st.text_input("Mật khẩu", type="password")
      submit = st.form_submit_button("Đăng nhập")
      if submit:
        hashed_pw = hash_password(password)
        cursor.execute(
            "SELECT role FROM users WHERE username = ? AND password = ?",
            (username, hashed_pw),
        )
        user = cursor.fetchone()
        if user:
          st.session_state["logged_in"] = True
          st.session_state["username"] = username
          st.session_state["role"] = user[0]
          st.success("Đăng nhập thành công!")
          st.rerun()
        else:
          st.error("Sai tên đăng nhập hoặc mật khẩu!")

  with tab2:
    with st.form("register_form"):
      new_user = st.text_input("Tên đăng nhập mới")
      new_pass = st.text_input("Mật khẩu mới", type="password")
      reg_submit = st.form_submit_button("Đăng ký")
      if reg_submit:
        if new_user and new_pass:
          try:
            hashed_pw = hash_password(new_pass)
            cursor.execute(
                "INSERT INTO users (username, password, role) VALUES (?, ?,"
                " ?)",
                (new_user, hashed_pw, "student"),
            )
            conn.commit()
            st.success("Đăng ký thành công! Hãy chuyển sang tab Đăng nhập.")
          except sqlite3.IntegrityError:
            st.error("Tên đăng nhập đã tồn tại!")
        else:
          st.warning("Vui lòng điền đầy đủ thông tin.")
  st.stop()

# --- THANH ĐIỀU HƯỚNG ---
st.sidebar.markdown(
    f"👤 Xin chào: **{st.session_state['username']}**"
    f" ({st.session_state['role']})"
)
menu = ["Ôn tập trắc nghiệm", "Thêm câu hỏi", "Import file câu hỏi riêng"]
if st.session_state["role"] == "admin":
  menu.append("Quản lý câu hỏi")
menu.append("Đăng xuất")

choice = st.sidebar.selectbox("Menu chính", menu)

if choice == "Đăng xuất":
  st.session_state["logged_in"] = False
  st.rerun()

# --- CHỨC NĂNG 1: ÔN TẬP TRẮC NGHIỆM ---
if choice == "Ôn tập trắc nghiệm":
  st.header("📝 Chương trình Ôn tập Trắc nghiệm")

  cursor.execute("SELECT DISTINCT subject FROM questions")
  subjects = [row[0] for row in cursor.fetchall() if row[0]]

  if not subjects:
    st.info(
        "Chưa có câu hỏi nào trong hệ thống. Vui lòng thêm câu hỏi hoặc import"
        " file câu hỏi riêng của bạn ở menu bên cạnh."
    )
  else:
    selected_subject = st.selectbox("Chọn Môn", subjects)

    cursor.execute(
        "SELECT DISTINCT chapter FROM questions WHERE subject = ?",
        (selected_subject,),
    )
    chapters = [row[0] for row in cursor.fetchall() if row[0]]
    selected_chapter = st.selectbox("Chọn Chương", chapters)

    cursor.execute(
        "SELECT DISTINCT lesson FROM questions WHERE subject = ? AND chapter ="
        " ?",
        (selected_subject, selected_chapter),
    )
    lessons = [row[0] for row in cursor.fetchall() if row[0]]
    selected_lesson = st.selectbox("Chọn Bài", lessons)

    cursor.execute(
        "SELECT DISTINCT section FROM questions WHERE subject = ? AND chapter ="
        " ? AND lesson = ?",
        (selected_subject, selected_chapter, selected_lesson),
    )
    sections = [row[0] for row in cursor.fetchall() if row[0]]
    selected_section = st.selectbox("Chọn Phần", sections)

    if st.button("Bắt đầu ôn tập"):
      cursor.execute(
          """
                SELECT id, question_text, option_a, option_b, option_c, option_d, correct_answer, explanation 
                FROM questions 
                WHERE subject = ? AND chapter = ? AND lesson = ? AND section = ?
            """,
          (
              selected_subject,
              selected_chapter,
              selected_lesson,
              selected_section,
          ),
      )
      questions = cursor.fetchall()

      # ĐẢO CÂU HỎI
      random.shuffle(questions)
      st.session_state["current_questions"] = questions
      st.session_state["quiz_started"] = True

    if st.session_state.get("quiz_started", False):
      questions = st.session_state["current_questions"]
      st.write(f"--- Tổng số câu hỏi trong phần này: **{len(questions)}** ---")

      for idx, q in enumerate(questions):
        (
            q_id,
            q_text,
            opt_a,
            opt_b,
            opt_c,
            opt_d,
            correct_ans,
            explanation,
        ) = q

        st.subheader(f"Câu {idx + 1}: {q_text}")

        # ĐẢO ĐÁP ÁN CHO TỪNG CÂU
        options = {"A": opt_a, "B": opt_b, "C": opt_c, "D": opt_d}
        options = {k: v for k, v in options.items() if v and str(v).strip() != ""}

        opt_keys = list(options.keys())
        random.shuffle(opt_keys)  # Đảo thứ tự hiển thị đáp án

        shuffled_options = [options[k] for k in opt_keys]

        user_choice = st.radio(
            f"Chọn đáp án câu {idx + 1}:",
            shuffled_options,
            key=f"q_{q_id}_{idx}",
            index=None,
        )

        # HIỂN THỊ ĐÁP ÁN VÀ GIẢI THÍCH NGAY KHI CHỌN
        if user_choice is not None:
          selected_original_key = [
              k for k, v in options.items() if v == user_choice
          ][0]

          if selected_original_key == correct_ans:
            st.success(
                f"Chính xác! Đáp án đúng là: {correct_ans}."
                f" {options[correct_ans]}"
            )
          else:
            st.error(
                f"Chưa chính xác. Bạn đã chọn {selected_original_key}. Đáp án"
                f" đúng là: {correct_ans}. {options[correct_ans]}"
            )

          if explanation and str(explanation).strip() != "nan":
            st.info(f"💡 **Giải thích:** {explanation}")
        st.markdown("---")

# --- CHỨC NĂNG 2: IMPORT FILE CÂU HỎI RIÊNG ---
elif choice == "Import file câu hỏi riêng":
  st.header("📂 Tải lên file câu hỏi của bạn (Excel / CSV)")
  st.markdown(
      "File tải lên cần có các cột tiêu đề tiếng Anh: `subject`, `chapter`,"
      " `lesson`, `section`, `question_text`, `option_a`, `option_b`,"
      " `option_c`, `option_d`, `correct_answer`, `explanation`."
  )

  uploaded_file = st.file_uploader("Chọn file Excel hoặc CSV", type=["xlsx", "csv"])
  if uploaded_file is not None:
    try:
      # SỬA LẠI PHẦN ĐỌC FILE Ở ĐÂY ĐỂ TRÁNH LỖI OPENPYXL
      file_extension = uploaded_file.name.split(".")[-1].lower()
      if file_extension == "xlsx":
        df = pd.read_excel(uploaded_file, engine="openpyxl")
      elif file_extension == "csv":
        df = pd.read_csv(uploaded_file)
      else:
        st.error("Định dạng file không hỗ trợ! Vui lòng tải lên file .xlsx hoặc .csv")
        st.stop()

      st.write("Xem trước dữ liệu từ file:", df.head())

      if st.button("Xác nhận đưa vào cơ sở dữ liệu"):
        count = 0
        for _, row in df.iterrows():
          cursor.execute(
              """
                        INSERT INTO questions (subject, chapter, lesson, section, question_text, option_a, option_b, option_c, option_d, correct_answer, explanation)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
              (
                  str(row.get("subject", "Chung")),
                  str(row.get("chapter", "Chương")),
                  str(row.get("lesson", "Bài")),
                  str(row.get("section", "Phần ")),
                  str(row.get("question_text", "")),
                  str(row.get("option_a", "")),
                  str(row.get("option_b", "")),
                  str(row.get("option_c", "")),
                  str(row.get("option_d", "")),
                  str(row.get("correct_answer", "A")).strip().upper(),
                  str(row.get("explanation", "")),
              ),
          )
          count += 1
        conn.commit()
        st.success(f"Đã import thành công {count} câu hỏi vào hệ thống!")
    except Exception as e:
      st.error(f"Lỗi khi đọc file: {e}")

# --- CHỨC NĂNG 3: THÊM CÂU HỎI THỦ CÔNG ---
elif choice == "Thêm câu hỏi":
  st.header("➕ Thêm câu hỏi thủ công")
  with st.form("add_question_form"):
    col1, col2 = st.columns(2)
    with col1:
      subject = st.text_input("Tên Môn")
      chapter = st.text_input("Tên Chương")
    with col2:
      lesson = st.text_input("Tên Bài")
      section = st.text_input("Tên Phần")

    question_text = st.text_area("Nội dung câu hỏi")

    col_a, col_b = st.columns(2)
    with col_a:
      opt_a = st.text_input("Đáp án A")
      opt_c = st.text_input("Đáp án C")
    with col_b:
      opt_b = st.text_input("Đáp án B")
      opt_d = st.text_input("Đáp án D")

    correct_answer = st.selectbox("Đáp án đúng", ["A", "B", "C", "D"])
    explanation = st.text_area("Giải thích chi tiết")

    submitted = st.form_submit_button("Lưu câu hỏi")
    if submitted:
      if subject and question_text and opt_a and opt_b:
        cursor.execute(
            """
                    INSERT INTO questions (subject, chapter, lesson, section, question_text, option_a, option_b, option_c, option_d, correct_answer, explanation)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
            (
                subject,
                chapter,
                lesson,
                section,
                question_text,
                opt_a,
                opt_b,
                opt_c,
                opt_d,
                correct_answer,
                explanation,
            ),
        )
        conn.commit()
        st.success("Đã thêm câu hỏi thành công!")
      else:
        st.warning(
            "Vui lòng điền tối thiểu Môn, Nội dung câu hỏi và ít nhất 2 đáp án A,"
            " B."
        )

# --- CHỨC NĂNG 4: QUẢN LÝ (Dành cho Admin) ---
elif choice == "Quản lý câu hỏi" and st.session_state["role"] == "admin":
  st.header("⚙️ Quản lý danh sách câu hỏi")
  cursor.execute(
      "SELECT id, subject, chapter, question_text, correct_answer FROM questions"
  )
  rows = cursor.fetchall()

  if rows:
    df_manage = pd.DataFrame(
        rows, columns=["ID", "Môn", "Chương", "Nội dung", "Đáp án đúng"]
    )
    st.dataframe(df_manage, use_container_width=True)

    del_id = st.number_input("Nhập ID câu hỏi muốn xóa", min_value=1, step=1)
    if st.button("Xóa câu hỏi"):
      cursor.execute("DELETE FROM questions WHERE id = ?", (del_id,))
      conn.commit()
      st.success(f"Đã xóa câu hỏi ID: {del_id}")
      st.rerun()
  else:
    st.info("Chưa có dữ liệu câu hỏi.")