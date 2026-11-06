# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import json
import os
import uuid
import datetime

# Cấu hình giao diện trang
st.set_page_config(page_title="Quản Lý Xuất Nhập & Tính Lãi", page_icon="📦", layout="wide")

DATA_FILE = "data_kho.json"

# Danh sách tài khoản đăng nhập (Bạn có thể đổi mật khẩu tại đây)
USERS = {
    "admin": "123456",
    "nhanvien": "abc@123"
}

def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "products": [
            {
                "name": "Lạp xưởng Mai Quế Lộ",
                "category": "Thực phẩm",
                "pack_unit": "Túi",
                "retail_unit": "Chiếc",
                "ratio": 8,
                "stock_retail": 40,
                "cost_pack": 80000,
                "price_pack": 100000,
                "price_retail": 15000
            }
        ],
        "history": []
    }

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# --- 1. MÀN HÌNH ĐĂNG NHẬP ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user = ""

if not st.session_state.logged_in:
    st.title("🔐 Đăng Nhập Hệ Thống Quản Lý Kho")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("login_form"):
            username = st.text_input("Tên đăng nhập")
            password = st.text_input("Mật khẩu", type="password")
            submit = st.form_submit_button("Đăng Nhập", use_container_width=True)
            
            if submit:
                if username in USERS and USERS[username] == password:
                    st.session_state.logged_in = True
                    st.session_state.user = username
                    st.success("Đăng nhập thành công!")
                    st.rerun()
                else:
                    st.error("Sai tên đăng nhập hoặc mật khẩu!")
    st.stop()

# --- 2. GIAO DIỆN CHÍNH SAU KHI ĐĂNG NHẬP ---
data = load_data()

# Thanh bên (Sidebar)
with st.sidebar:
    st.write(f"👤 Xin chào: **{st.session_state.user}**")
    if st.button("🚪 Đăng Xuất"):
        st.session_state.logged_in = False
        st.session_state.user = ""
        st.rerun()
    st.divider()
    menu = st.radio("Menu Chức Năng", [
        "📥 Nhập Hàng", 
        "📤 Xuất Hàng (Bán Lẻ/Sỉ)", 
        "⚙️ Quản Lý Kho & Hàng Hóa", 
        "📊 Thống Kê Ngày / Tháng / Năm", 
        "📜 Lịch Sử Giao Dịch"
    ])

# Báo cáo tổng thể trên đầu trang
tot_import = sum(h.get("qty_raw", 1) * h.get("price_raw", 0) for h in data["history"] if "Nhập" in h.get("type", ""))
tot_rev = sum(h.get("revenue", 0) for h in data["history"] if "Xuất" in h.get("type", ""))
tot_cost = sum(h.get("cogs", 0) for h in data["history"] if "Xuất" in h.get("type", ""))
tot_profit = tot_rev - tot_cost

col_m1, col_m2, col_m3, col_m4 = st.columns(4)
col_m1.metric("Tổng Tiền Nhập", f"{tot_import:,.0f} đ")
col_m2.metric("Tổng Doanh Thu", f"{tot_rev:,.0f} đ")
col_m3.metric("Tổng Vốn Xuất", f"{tot_cost:,.0f} đ")
col_m4.metric("Tổng Lãi Thực Tế", f"{tot_profit:,.0f} đ", delta=f"{(tot_profit/tot_rev*100) if tot_rev>0 else 0:.1f}%")

st.divider()

# TAB 1: NHẬP HÀNG
if menu == "📥 Nhập Hàng":
    st.subheader("📥 Thực Hiện Nhập Hàng Vào Kho")
    prod_names = [p["name"] for p in data["products"]]
    
    col1, col2 = st.columns(2)
    with col1:
        sel_prod_name = st.selectbox("Chọn mặt hàng", prod_names)
        prod = next(p for p in data["products"] if p["name"] == sel_prod_name)
        nhap_type = st.radio("Hình thức nhập", [f"Nhập sỉ (theo {prod['pack_unit']})", f"Nhập lẻ (theo {prod['retail_unit']})"])
        
    with col2:
        qty = st.number_input("Số lượng nhập", min_value=1, step=1, value=1)
        default_cost = prod["cost_pack"] if "sỉ" in nhap_type else (prod["cost_pack"] / prod["ratio"])
        price = st.number_input("Đơn giá nhập (VNĐ)", min_value=0.0, step=1000.0, value=float(default_cost))
        
    if st.button("Xác Nhận Nhập Hàng", use_container_width=True, type="primary"):
        if "sỉ" in nhap_type:
            prod["stock_retail"] += qty * prod["ratio"]
            prod["cost_pack"] = price
            qty_disp = f"{qty} {prod['pack_unit']}"
        else:
            prod["stock_retail"] += qty
            qty_disp = f"{qty} {prod['retail_unit']}"
            
        data["history"].append({
            "id": str(uuid.uuid4()),
            "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
            "type": "Nhập sỉ" if "sỉ" in nhap_type else "Nhập lẻ",
            "product": prod["name"],
            "qty_raw": qty,
            "price_raw": price,
            "qty_str": qty_disp,
            "revenue": 0,
            "cogs": 0,
            "profit": 0
        })
        save_data(data)
        st.success(f"Đã nhập kho thành công: {qty_disp} {prod['name']}")
        st.rerun()

# TAB 2: XUẤT HÀNG (BÁN HÀNG)
elif menu == "📤 Xuất Hàng (Bán Lẻ/Sỉ)":
    st.subheader("📤 Xuất Hàng Bán & Tính Lãi")
    prod_names = [p["name"] for p in data["products"]]
    
    col1, col2 = st.columns(2)
    with col1:
        sel_prod_name = st.selectbox("Chọn mặt hàng bán", prod_names)
        prod = next(p for p in data["products"] if p["name"] == sel_prod_name)
        cur_packs = prod["stock_retail"] // prod["ratio"]
        cur_rem = prod["stock_retail"] % prod["ratio"]
        st.info(f"Tồn kho hiện tại: **{prod['stock_retail']} {prod['retail_unit']}** ({cur_packs} {prod['pack_unit']} + {cur_rem} {prod['retail_unit']})")
        
        xuat_type = st.radio("Hình thức bán", [f"Bán lẻ (theo {prod['retail_unit']})", f"Bán sỉ (theo {prod['pack_unit']})"])
        
    with col2:
        qty = st.number_input("Số lượng xuất bán", min_value=1, step=1, value=1)
        default_price = prod["price_retail"] if "lẻ" in xuat_type else prod.get("price_pack", prod["cost_pack"] * 1.25)
        price = st.number_input("Giá bán (VNĐ)", min_value=0.0, step=1000.0, value=float(default_price))
        
    if st.button("Xác Nhận Xuất Hàng", use_container_width=True, type="primary"):
        unit_cost = prod["cost_pack"] / prod["ratio"]
        if "lẻ" in xuat_type:
            needed = qty
            if prod["stock_retail"] < needed:
                st.error("Kho không đủ hàng lẻ để bán!")
            else:
                prod["stock_retail"] -= needed
                rev = qty * price
                cogs = needed * unit_cost
                profit = rev - cogs
                data["history"].append({
                    "id": str(uuid.uuid4()),
                    "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "type": "Xuất lẻ",
                    "product": prod["name"],
                    "qty_raw": qty,
                    "price_raw": price,
                    "qty_str": f"{qty} {prod['retail_unit']}",
                    "revenue": rev,
                    "cogs": cogs,
                    "profit": profit
                })
                save_data(data)
                st.success(f"Bán thành công! Doanh thu: {rev:,.0f} đ | Tiền lãi: {profit:,.0f} đ")
                st.rerun()
        else:
            needed = qty * prod["ratio"]
            if prod["stock_retail"] < needed:
                st.error("Kho không đủ hàng sỉ để bán!")
            else:
                prod["stock_retail"] -= needed
                rev = qty * price
                cogs = needed * unit_cost
                profit = rev - cogs
                data["history"].append({
                    "id": str(uuid.uuid4()),
                    "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "type": "Xuất sỉ",
                    "product": prod["name"],
                    "qty_raw": qty,
                    "price_raw": price,
                    "qty_str": f"{qty} {prod['pack_unit']}",
                    "revenue": rev,
                    "cogs": cogs,
                    "profit": profit
                })
                save_data(data)
                st.success(f"Bán sỉ thành công! Doanh thu: {rev:,.0f} đ | Tiền lãi: {profit:,.0f} đ")
                st.rerun()

# TAB 3: QUẢN LÝ KHO & CHỈNH SỬA TỒN KHO
elif menu == "⚙️ Quản Lý Kho & Hàng Hóa":
    st.subheader("📦 Danh Sách Tồn Kho & Điều Chỉnh")
    
    rows = []
    for p in data["products"]:
        pk = p["stock_retail"] // p["ratio"]
        rm = p["stock_retail"] % p["ratio"]
        rows.append({
            "Tên Hàng": p["name"],
            "Loại Hàng": p["category"],
            "Tồn Kho": f"{p['stock_retail']} {p['retail_unit']} ({pk} {p['pack_unit']} + {rm} {p['retail_unit']})",
            "Giá Vốn Sỉ": f"{p['cost_pack']:,.0f} đ",
            "Giá Bán Sỉ": f"{p['price_pack']:,.0f} đ",
            "Giá Bán Lẻ": f"{p['price_retail']:,.0f} đ"
        })
    st.dataframe(pd.DataFrame(rows), use_container_width=True)
    
    st.divider()
    col_a, col_b = st.columns(2)
    
    with col_a:
        st.write("### ⚙️ Điều Chỉnh Nhanh Tồn Kho")
        sel_p = st.selectbox("Chọn mặt hàng cần sửa tồn", [p["name"] for p in data["products"]], key="adj_sel")
        target_p = next(p for p in data["products"] if p["name"] == sel_p)
        cur_pk = target_p["stock_retail"] // target_p["ratio"]
        cur_rm = target_p["stock_retail"] % target_p["ratio"]
        
        new_pk = st.number_input(f"Số {target_p['pack_unit']} mới", min_value=0, value=int(cur_pk))
        new_rm = st.number_input(f"Số {target_p['retail_unit']} lẻ mới", min_value=0, value=int(cur_rm))
        reason = st.text_input("Lý do điều chỉnh", "Kiểm kê định kỳ")
        
        if st.button("Cập Nhật Lại Kho"):
            new_total = new_pk * target_p["ratio"] + new_rm
            diff = new_total - target_p["stock_retail"]
            target_p["stock_retail"] = new_total
            sign = "+" if diff > 0 else ""
            data["history"].append({
                "id": str(uuid.uuid4()),
                "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
                "type": "Cân bằng kho",
                "product": target_p["name"],
                "qty_raw": abs(diff),
                "price_raw": 0,
                "qty_str": f"{sign}{diff} {target_p['retail_unit']} ({reason})",
                "revenue": 0,
                "cogs": 0,
                "profit": 0
            })
            save_data(data)
            st.success("Đã cập nhật số lượng tồn kho thành công!")
            st.rerun()

    with col_b:
        st.write("### ➕ Thêm Sản Phẩm Mới")
        with st.form("add_product"):
            p_name = st.text_input("Tên sản phẩm (*)")
            p_cat = st.text_input("Loại hàng", "Thực phẩm")
            col_u1, col_u2, col_u3 = st.columns(3)
            p_pack = col_u1.text_input("Đơn vị sỉ", "Túi")
            p_retail = col_u2.text_input("Đơn vị lẻ", "Chiếc")
            p_ratio = col_u3.number_input("Tỷ lệ quy đổi", min_value=1, value=8)
            
            p_cost = st.number_input("Giá vốn sỉ (VNĐ)", min_value=0.0, value=80000.0)
            p_ret_price = st.number_input("Giá bán lẻ (VNĐ)", min_value=0.0, value=15000.0)
            p_init_stock = st.number_input("Số lượng tồn ban đầu (ĐV Lẻ)", min_value=0, value=0)
            
            if st.form_submit_button("Lưu Sản Phẩm"):
                if not p_name:
                    st.error("Vui lòng nhập tên sản phẩm!")
                elif any(p["name"] == p_name for p in data["products"]):
                    st.error("Tên sản phẩm đã tồn tại!")
                else:
                    data["products"].append({
                        "name": p_name,
                        "category": p_cat,
                        "pack_unit": p_pack,
                        "retail_unit": p_retail,
                        "ratio": int(p_ratio),
                        "stock_retail": int(p_init_stock),
                        "cost_pack": p_cost,
                        "price_pack": p_cost * 1.25,
                        "price_retail": p_ret_price
                    })
                    save_data(data)
                    st.success(f"Đã thêm sản phẩm {p_name} thành công!")
                    st.rerun()

# TAB 4: THỐNG KÊ NGÀY / THÁNG / NĂM
elif menu == "📊 Thống Kê Ngày / Tháng / Năm":
    st.subheader("📊 Báo Cáo Thống Kê Chi Tiết Từng Ngày / Tháng / Năm")
    
    col_f1, col_f2, col_f3 = st.columns(3)
    days = ["Tất cả"] + [f"{d:02d}" for d in range(1, 32)]
    months = ["Tất cả"] + [f"{m:02d}" for m in range(1, 13)]
    now = datetime.datetime.now()
    
    years = ["Tất cả"] + sorted(list({h["time"][:4] for h in data["history"] if "time" in h} | {str(now.year)}), reverse=True)
    
    sel_d = col_f1.selectbox("Chọn Ngày", days, index=now.day)
    sel_m = col_f2.selectbox("Chọn Tháng", months, index=now.month)
    sel_y = col_f3.selectbox("Chọn Năm", years, index=years.index(str(now.year)) if str(now.year) in years else 0)
    
    # Lọc dữ liệu
    filtered = []
    for h in data["history"]:
        t = h.get("time", "")
        if len(t) < 10:
            continue
        if sel_y != "Tất cả" and t[0:4] != sel_y:
            continue
        if sel_m != "Tất cả" and t[5:7] != sel_m:
            continue
        if sel_d != "Tất cả" and t[8:10] != sel_d:
            continue
        filtered.append(h)
        
    f_import = sum(h.get("qty_raw", 1) * h.get("price_raw", 0) for h in filtered if "Nhập" in h.get("type", ""))
    f_rev = sum(h.get("revenue", 0) for h in filtered if "Xuất" in h.get("type", ""))
    f_cost = sum(h.get("cogs", 0) for h in filtered if "Xuất" in h.get("type", ""))
    f_profit = f_rev - f_cost
    
    st.markdown(f"#### 🎯 Kết Quả Kỳ Lọc: Ngày {sel_d} / Tháng {sel_m} / Năm {sel_y}")
    sc1, sc2, sc3, sc4, sc5 = st.columns(5)
    sc1.metric("Tiền Nhập", f"{f_import:,.0f} đ")
    sc2.metric("Doanh Thu Bán", f"{f_rev:,.0f} đ")
    sc3.metric("Tiền Vốn Bán", f"{f_cost:,.0f} đ")
    sc4.metric("Tiền Lãi", f"{f_profit:,.0f} đ")
    sc5.metric("Tỷ Suất Lãi", f"{(f_profit/f_rev*100) if f_rev>0 else 0:.1f}%")
    
    st.write("##### 📦 Chi Tiết Từng Mặt Hàng Trong Kỳ Đã Chọn:")
    prod_map = {p["name"]: p for p in data["products"]}
    prod_stats = {}
    
    for h in filtered:
        pname = h.get("product", "Khác")
        if pname not in prod_stats:
            pinfo = prod_map.get(pname, {"pack_unit": "Túi", "retail_unit": "Chiếc", "ratio": 1})
            prod_stats[pname] = {
                "name": pname,
                "pack_unit": pinfo.get("pack_unit", "Túi"),
                "retail_unit": pinfo.get("retail_unit", "Chiếc"),
                "ratio": pinfo.get("ratio", 1),
                "import_qty": 0,
                "import_money": 0,
                "export_qty": 0,
                "revenue": 0,
                "profit": 0
            }
        t_type = h.get("type", "")
        q = h.get("qty_raw", 0)
        p = h.get("price_raw", 0)
        rat = prod_stats[pname]["ratio"]
        
        if "Nhập sỉ" in t_type:
            prod_stats[pname]["import_qty"] += q * rat
            prod_stats[pname]["import_money"] += q * p
        elif "Nhập lẻ" in t_type:
            prod_stats[pname]["import_qty"] += q
            prod_stats[pname]["import_money"] += q * p
        elif "Xuất lẻ" in t_type:
            prod_stats[pname]["export_qty"] += q
            prod_stats[pname]["revenue"] += h.get("revenue", 0)
            prod_stats[pname]["profit"] += h.get("profit", 0)
        elif "Xuất sỉ" in t_type:
            prod_stats[pname]["export_qty"] += q * rat
            prod_stats[pname]["revenue"] += h.get("revenue", 0)
            prod_stats[pname]["profit"] += h.get("profit", 0)
            
    p_rows = []
    for pname, d in prod_stats.items():
        rat = d["ratio"]
        imp_s = f"{d['import_qty']} {d['retail_unit']} ({d['import_qty']//rat} {d['pack_unit']} {d['import_qty']%rat} {d['retail_unit']})" if d['import_qty']>0 else "0"
        exp_s = f"{d['export_qty']} {d['retail_unit']} ({d['export_qty']//rat} {d['pack_unit']} {d['export_qty']%rat} {d['retail_unit']})" if d['export_qty']>0 else "0"
        p_rows.append({
            "Mặt Hàng": pname,
            "Số Lượng Nhập": imp_s,
            "Tiền Nhập": f"{d['import_money']:,.0f} đ",
            "Số Lượng Bán": exp_s,
            "Doanh Thu Bán": f"{d['revenue']:,.0f} đ",
            "Tiền Lãi": f"{d['profit']:,.0f} đ"
        })
        
    if p_rows:
        st.dataframe(pd.DataFrame(p_rows), use_container_width=True)
    else:
        st.info("Không có giao dịch nào trong khoảng thời gian đã chọn.")

# TAB 5: LỊCH SỬ GIAO DỊCH
elif menu == "📜 Lịch Sử Giao Dịch":
    st.subheader("📜 Toàn Bộ Lịch Sử Giao Dịch")
    if data["history"]:
        h_df = pd.DataFrame(data["history"])[["time", "type", "product", "qty_str", "price_raw", "revenue", "cogs", "profit"]]
        h_df.columns = ["Thời Gian", "Loại GD", "Sản Phẩm", "Số Lượng", "Đơn Giá", "Doanh Thu", "Tiền Vốn", "Tiền Lãi"]
        st.dataframe(h_df.iloc[::-1], use_container_width=True)
    else:
        st.info("Chưa có giao dịch nào.")