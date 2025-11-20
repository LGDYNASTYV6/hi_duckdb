import streamlit as st
import pandas as pd
import time
import duckdb

# DuckDB 연결
conn = duckdb.connect("madang.db")

def query_records(sql: str):
    df = conn.execute(sql).df()
    return df.to_dict(orient="records")

# -----------------------
# 1. 책 목록 (셀렉트박스용)
# -----------------------
books = [None]
book_rows = query_records("SELECT bookid, bookname FROM Book ORDER BY bookid;")
for row in book_rows:
    books.append(f"{row['bookid']},{row['bookname']}")

# -----------------------
# 2. 탭 구성
# -----------------------
tab1, tab2, tab3 = st.tabs(["고객조회", "거래 입력", "고객 등록"])

name = tab1.text_input("고객명")
custid = None

# -----------------------
# 3. 고객 조회 + 주문 내역 (tab1)
# -----------------------
if len(name) > 0:
    # (1) 고객 존재 여부 먼저 확인
    cust_rows = query_records(
        f"SELECT custid, name FROM Customer WHERE name = '{name}';"
    )

    if len(cust_rows) == 0:
        tab1.write("해당 이름의 고객이 없습니다.")
    else:
        custid = int(cust_rows[0]["custid"])

        # (2) 주문 내역 조회 (있으면 보여주고, 없어도 진행)
        order_sql = f"""
            SELECT 
                c.custid,
                c.name,
                b.bookname,
                o.orderdate,
                o.saleprice
            FROM Customer c
            JOIN Orders o ON c.custid = o.custid
            JOIN Book   b ON o.bookid = b.bookid
            WHERE c.custid = {custid}
            ORDER BY o.orderdate;
        """
        order_rows = query_records(order_sql)

        if len(order_rows) == 0:
            tab1.write("해당 고객의 주문 내역이 없습니다.")
        else:
            tab1.write(pd.DataFrame(order_rows))

        # -----------------------
        # 4. 거래 입력 (tab2)
        # -----------------------
        tab2.write(f"고객번호: {custid}")
        tab2.write(f"고객명: {name}")

        select_book = tab2.selectbox("구매 서적:", books)

        if select_book is not None:
            bookid = int(select_book.split(",")[0])

            dt = time.strftime("%Y-%m-%d", time.localtime())

            max_row = query_records("SELECT max(orderid) AS max_orderid FROM Orders;")
            current_max = max_row[0]["max_orderid"]
            orderid = 1 if current_max is None else int(current_max) + 1

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

# -----------------------
# 5. 고객 등록 (tab3) – 새 고객을 Customer 테이블에 INSERT
# -----------------------
with tab3:
    st.subheader("신규 고객 등록")

    new_name = st.text_input("고객명", key="new_name")
    new_addr = st.text_input("주소", key="new_addr")
    new_phone = st.text_input("전화번호", key="new_phone")

    if st.button("고객 등록"):
        if new_name.strip() == "":
            st.error("고객명을 입력하세요.")
        else:
            # 이미 있는지 확인
            exists = query_records(
                f"SELECT custid FROM Customer WHERE name = '{new_name}';"
            )
            if len(exists) > 0:
                st.warning("이미 존재하는 고객입니다.")
            else:
                # 새로운 custid = 최대값 + 1
                row = conn.execute(
                    "SELECT COALESCE(MAX(custid), 0) + 1 AS new_id FROM Customer;"
                ).fetchone()
                new_id = row[0]

                conn.execute(
                    """
                    INSERT INTO Customer (custid, name, address, phone)
                    VALUES (?, ?, ?, ?);
                    """,
                    [new_id, new_name, new_addr, new_phone],
                )

                st.success(f"신규 고객이 등록되었습니다! 고객번호: {new_id}")
                st.write("이제 '고객조회' 탭에서 방금 등록한 이름으로 조회해보세요.")
