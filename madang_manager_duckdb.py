import streamlit as st
import pandas as pd
import time
import duckdb

# DuckDB 파일(madang.db)에 연결
conn = duckdb.connect("madang.db")

# MySQL DictCursor처럼 list[dict] 형태로 돌려주는 헬퍼 함수
def query(sql: str):
    df = conn.execute(sql).df()
    return df.to_dict(orient="records")


# -----------------------
# 1. 책 목록(셀렉트박스용)
# -----------------------
books = [None]

book_rows = query("SELECT CONCAT(bookid, ',', bookname) AS label FROM Book;")
for row in book_rows:
    books.append(row["label"])


# -----------------------
# 2. 화면 탭 구성
# -----------------------
tab1, tab2 = st.tabs(["고객조회", "거래 입력"])

name = ""
custid = None
result_df = pd.DataFrame()
select_book = ""

# -----------------------
# 3. 고객 주문 조회(tab1)
# -----------------------
name = tab1.text_input("고객명")

if len(name) > 0:
    sql = f"""
        SELECT 
            c.custid,
            c.name,
            b.bookname,
            o.orderdate,
            o.saleprice
        FROM Customer c
        JOIN Orders o ON c.custid = o.custid
        JOIN Book   b ON o.bookid = b.bookid
        WHERE c.name = '{name}';
    """

    rows = query(sql)

    if len(rows) == 0:
        tab1.write("해당 고객의 주문 내역이 없습니다.")
    else:
        result_df = pd.DataFrame(rows)
        tab1.write(result_df)

        # 첫 행의 고객번호 사용
        custid = int(result_df["custid"][0])

        # -----------------------
        # 4. 거래 입력(tab2)
        # -----------------------
        tab2.write("고객번호: " + str(custid))
        tab2.write("고객명: " + name)

        select_book = tab2.selectbox("구매 서적:", books)

        if select_book is not None:
            bookid = int(select_book.split(",")[0])

            # 오늘 날짜 (YYYY-MM-DD)
            dt = time.localtime()
            dt = time.strftime("%Y-%m-%d", dt)

            # 다음 orderid 구하기
            max_row = query("SELECT max(orderid) AS max_orderid FROM Orders;")
            current_max = max_row[0]["max_orderid"]
            if current_max is None:
                orderid = 1
            else:
                orderid = int(current_max) + 1

            price = tab2.text_input("금액")

            if tab2.button("거래 입력"):
                if price.strip() == "":
                    tab2.error("금액을 입력하세요.")
                else:
                    try:
                        price_int = int(price)

                        insert_sql = f"""
                            INSERT INTO Orders (orderid, custid, bookid, saleprice, orderdate)
                            VALUES ({orderid}, {custid}, {bookid}, {price_int}, '{dt}');
                        """
                        conn.execute(insert_sql)

                        tab2.success("거래가 입력되었습니다.")
                    except ValueError:
                        tab2.error("금액에는 숫자만 입력하세요.")
###streamlit run madang_manager_duckdb.py
