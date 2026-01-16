import re
import pandas as pd
import streamlit as st
import altair as alt


def format_phone(x) -> str:
    if x is None:
        return ""
    digits = re.sub(r"\D", "", str(x))
    if digits == "" or digits == "00000000":
        return ""
    if len(digits) == 8:
        return f"{digits[:4]}-{digits[4:]}"
    if digits.startswith("02") and len(digits) >= 9:
        return f"{digits[:2]}-{digits[2:-4]}-{digits[-4:]}"
    if len(digits) >= 10:
        return f"{digits[:3]}-{digits[3:-4]}-{digits[-4:]}"
    return digits


@st.cache_data(show_spinner=False)
def load(_conn) -> pd.DataFrame:
    sql = """
        SELECT companyName, coPhoneNo, averageFee
        FROM charge_fee
    """
    df = pd.read_sql(sql, _conn)
    df = df.rename(columns={
        "companyName": "업체명",
        "coPhoneNo": "업체 전화번호",
        "averageFee": "평균 충전요금(원)",
    })
    df["업체 전화번호"] = df["업체 전화번호"].apply(format_phone)
    df["평균 충전요금(원)"] = pd.to_numeric(df["평균 충전요금(원)"], errors="coerce")
    return df


def render_charge_fee_page(conn):
    st.title("⚡ 충전소 업체별 요금")
    st.caption("차지인포 - 통계정보 - 충전 사업자별 충전요금 (2026년 1월 15일 기준)")

    df = load(conn).copy()
    if df.empty:
        st.warning("데이터가 없습니다.")
        return

    fee_col = "평균 충전요금(원)"

    # =======================
    # TOP 15 차트
    # =======================
    st.subheader("📊 평균 충전요금 TOP 15 (업체 기준)")

    top15 = (
        df.dropna(subset=[fee_col])
          .sort_values(by=fee_col, ascending=False)
          .head(15)
    )

    chart = (
        alt.Chart(top15)
        .mark_bar()
        .encode(
            x=alt.X("업체명:N", sort="-y", axis=alt.Axis(labelAngle=-45, title=None)),
            y=alt.Y(f"{fee_col}:Q", title="평균가(원)"),  # ✅ y축 0부터 자동 시작
            tooltip=["업체명", alt.Tooltip(f"{fee_col}:Q", format=",.2f")],
        )
        .properties(height=350)
    )

    st.altair_chart(chart, use_container_width=True)
    st.divider()

    # =======================
    # 표 + 필터
    # =======================
    st.subheader("📋 업체별 평균 충전요금 목록")
    show_filter = st.checkbox("필터 표시", value=True)

    keyword = ""
    sort_option = "평균가 높은 순"

    if show_filter:
        c1, c2 = st.columns([2, 1])
        keyword = c1.text_input("업체명 검색(부분일치)")
        sort_option = c2.selectbox("정렬 기준", ["평균가 높은 순", "평균가 낮은 순", "업체명 가나다 순"])

    filtered = df.copy()

    if keyword.strip():
        filtered = filtered[filtered["업체명"].astype(str).str.contains(keyword.strip(), case=False, na=False)]

    if sort_option == "평균가 높은 순":
        filtered = filtered.sort_values(by=fee_col, ascending=False)
    elif sort_option == "평균가 낮은 순":
        filtered = filtered.sort_values(by=fee_col, ascending=True)
    else:
        filtered = filtered.sort_values(by="업체명")

    # 표 표시
    st.dataframe(filtered, width="stretch", hide_index=True)
