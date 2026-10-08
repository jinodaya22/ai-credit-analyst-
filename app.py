import streamlit as st
from google import genai
from google.genai import types
import json
import os
import tempfile
import time
from pypdf import PdfReader, PdfWriter

# ==========================================
# 1. การตั้งค่าหน้าจอหลัก
# ==========================================
st.set_page_config(page_title="AI Mortgage Credit & Financial Analysis System", layout="wide")

st.title("🏡 ระบบวิเคราะห์สินเชื่อและประเมินศักยภาพลูกค้าอัจฉริยะ (AI-Agent Architecture)")

# ==========================================
# 2. จัดการ Session State (หน่วยความจำของแอป)
# ==========================================
if "property_price" not in st.session_state:
    st.session_state.property_price = 0.0
if "requested_loan" not in st.session_state:
    st.session_state.requested_loan = 0.0
if "customer_name" not in st.session_state:
    st.session_state.customer_name = ""
if "business_context" not in st.session_state:
    st.session_state.business_context = ""
if "interview_notes" not in st.session_state:
    st.session_state.interview_notes = ""

# 1. ระเบียบถาวร (Static Regulations)
default_regulations = """คุณคือนักวิเคราะห์สินเชื่อเพื่อที่อยู่อาศัยระดับอาวุโส, ที่ปรึกษาทางการเงินส่วนบุคคล และผู้เชี่ยวชาญด้านการประเมินสินเชื่อเชิงสถาบันการเงิน (Senior Mortgage Credit Analyst & Financial Strategist)
หน้าที่: วิเคราะห์เอกสารทางการเงิน (Hard Data) ควบคู่กับข้อมูลสัมภาษณ์เชิงลึก (Soft Data) และประเมินศักยภาพการกู้ตาม "หลักเกณฑ์จริงของธนาคารพาณิชย์และมาตรการภาครัฐ" อย่างละเอียดรอบคอบที่สุด

--- กฎเหล็กและระเบียบการวิเคราะห์ (Core Regulations) ---

1. การประเมินรายได้ (Income Assessment):
   - คัดกรองยอดโอนเข้าออกที่ผิดปกติ หรือการโอนกลับไปมา (Flipping) ตัดออก
   - ตัดรายได้จากการเทรด (เช่น ฮั่วเซ่งเฮง, คริปโตเก็งกำไร) ออกจากการคำนวณรายได้ประจำ
   - นำรายได้จาก 50 ทวิ, ค่าเช่า, หรือรายได้เสริม มาคำนวณตามเกณฑ์ความเสี่ยง
   - [กฎสำคัญกรณีสลิปออกครึ่งเดือน]: หากพบว่าสลิปเงินเดือนออกเป็นงวดละ 2 ครั้งต่อเดือน (Semi-monthly เช่น งวดกลางเดือน และงวดสิ้นเดือน) ให้ทำการรวมยอดเงินได้ทั้ง 2 งวดของเดือนนั้น ๆ เข้าด้วยกันเพื่อให้ได้ "รายได้รวมประจำต่อเดือนที่แท้จริง" ห้ามนำยอดต่อครึ่งเดือนมานับเป็นรายได้ต่อเดือนโดยเด็ดขาด

2. การประเมินภาระหนี้และเครดิตบูโร (Debt & NCB Scoring Assessment):
   - ดึงภาระหนี้จาก NCB ผสานกับหนี้จากการสัมภาษณ์
   - เกณฑ์การคำนวณภาระหนี้บัตรเครดิต/สินเชื่อส่วนบุคคล: คำนวณขั้นต่ำตามยอดเรียกเก็บจริง หรือ 5-10% ของวงเงินอนุมัติ

3. คณิตศาสตร์การเงินและโครงสร้างอัตราดอกเบี้ย (Financial Metrics & Interest Rate Logic):
   - การคำนวณค่างวดเพื่อทดสอบความสามารถในการผ่อน (Affordability & Stress Test):
     * พิจารณาอัตราดอกเบี้ยพิเศษช่วง 3 ปีแรก ควบคู่กับการทำ Stress Test ที่อัตราดอกเบี้ยกลาง-ยาว (ประมาณ 6.5%)
   - เกณฑ์พิจารณา DSR (Debt Service Ratio):
     * กลุ่มรายได้ปานกลาง: DSR สูงสุด 50-60%
     * กลุ่มลูกค้าเกรดพรีเมียม / พนักงานรายได้สูง / ข้าราชการ: สามารถพิจารณา DSR ขยับขึ้นไปได้ถึง 70-80% หากมีประวัติการเงินดีเยี่ยม

4. การคัดกรองและเปรียบเทียบธนาคาร (Bank Matrix Matching):
   - วิเคราะห์และแนะนำธนาคารที่เหมาะสม พร้อมระบุเหตุผลทางเทคนิคและเอกสารที่ต้องเตรียม

--- รูปแบบผลลัพธ์ที่ต้องการ (Output Format) ---
โปรดประมวลผลและส่งกลับมาในรูปแบบ JSON ที่มีโครงสร้างสมบูรณ์ พร้อมข้อความบรรยายเชิงกลยุทธ์ตามโครงสร้างนี้:

{
  "verified_income": 0,
  "verified_debt": 0,
  "dsr_percentage": 0,
  "max_loan_amount": 0,
  "ltv_percentage": 0,
  "business_type": "",
  "key_findings": [
    "วิเคราะห์รายได้ที่แท้จริง (รวมสลิปครึ่งเดือน / หักลบรายการผิดปกติ)",
    "วิเคราะห์ภาระหนี้บูโรและผลกระทบต่อ DSR",
    "วิเคราะห์เปรียบเทียบอัตราดอกเบี้ยพิเศษ 3 ปีแรก vs Stress Test 6.5% และสิทธิประโยชน์ตามมาตรการภาครัฐปัจจุบัน"
  ],
  "recommended_banks": [
    {
      "bank": "ชื่อธนาคาร",
      "reason": "เหตุผลเชิงลึก",
      "required_docs": ["เอกสารที่ต้องเตรียมเพิ่มเติม"]
    }
  ]
}"""

# 2. ไคเทเรียและมาตรการที่ปรับเปลี่ยนได้ (Dynamic Criteria Buffer - ค่าเริ่มต้นใส่ LTV ถึง มิ.ย. 2570 ไว้ให้)
default_criteria = """- มาตรการ LTV (ปรับปรุงล่าสุด): ธนาคารแห่งประเทศไทยผ่อนคลายเกณฑ์ LTV โดยกำหนดเพดานอัตราส่วนเงินให้สินเชื่อต่อมูลค่าหลักประกัน (LTV) เป็น 100% สำหรับสินเชื่อเพื่อที่อยู่อาศัย (กรณีมูลค่าหลักประกันต่ำกว่า 10 ล้านบาท ตั้งแต่สัญญาที่ 2 เป็นต้นไป หรือมูลค่าตั้งแต่ 10 ล้านบาทขึ้นไป สัญญาที่ 1 เป็นต้นไป) โดยมาตรการนี้มีผลผ่อนคลายชั่วคราวถึงวันที่ 30 มิถุนายน 2570"""

if "system_regulations" not in st.session_state:
    st.session_state.system_regulations = default_regulations
if "dynamic_criteria" not in st.session_state:
    st.session_state.dynamic_criteria = default_criteria

# ==========================================
# 3. แถบด้านข้าง (Sidebar): แยกส่วนระเบียบถาวร และ ไคเทเรียปรับเปลี่ยน
# ==========================================
st.sidebar.header("🔑 ตั้งค่าระบบ API & จัดการเคส")
api_key_input = st.sidebar.text_input("Gemini API Key", type="password", value="", placeholder="วางรหัส API (รองรับคีย์ AQ...) ที่นี่")

if st.sidebar.button("🔄 ล้างข้อมูลและเริ่มเคสใหม่", type="primary"):
    st.session_state.property_price = 0.0
    st.session_state.requested_loan = 0.0
    st.session_state.customer_name = ""
    st.session_state.business_context = ""
    st.session_state.interview_notes = ""
    st.success("ล้างข้อมูลเรียบร้อย พร้อมเริ่มเคสใหม่ครับ!")
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.header("⚙️ จัดการคู่มือความรู้ (Architecture Separation)")

st.sidebar.markdown("##### 📌 1. ไคเทเรียและมาตรการที่ปรับเปลี่ยนบ่อย (Dynamic Criteria)")
st.sidebar.write("💡 แก้ไขตัวเลขหรือเงื่อนไขเฉพาะกิจตรงนี้ได้ทันที (เช่น LTV, DSR, โปรโมชั่นแบงก์)")
dynamic_criteria = st.sidebar.text_area("เงื่อนไขเฉพาะกิจ / มาตรการรัฐ:", value=st.session_state.dynamic_criteria, height=120)
st.session_state.dynamic_criteria = dynamic_criteria

st.sidebar.markdown("##### 📌 2. ระเบียบพื้นฐานถาวร (Static Regulations)")
system_regulations = st.sidebar.text_area("ระเบียบหลัก:", value=st.session_state.system_regulations, height=250)
st.session_state.system_regulations = system_regulations

# ==========================================
# 4. โครงสร้างหน้าจอหลัก (Tabs)
# ==========================================
tab1, tab2 = st.tabs(["📝 ข้อมูลคำขอสินเชื่อ & สัมภาษณ์ (Soft Data)", "📂 ระบบจัดระเบียบและรวมเล่มเอกสารอัจฉริยะ (Hard Data Agent)"])

with tab1:
    st.header("ข้อมูลคำขอสินเชื่อและรายละเอียดทรัพย์สิน")
    col1, col2 = st.columns(2)
    with col1:
        property_price = st.number_input("ราคารับซื้อ / ราคาซื้อขายทรัพย์สิน (บาท)", value=st.session_state.property_price, step=100000.0, format="%.2f", key="inp_property_price")
        requested_loan = st.number_input("วงเงินกู้ที่ลูกค้าต้องการ (บาท)", value=st.session_state.requested_loan, step=100000.0, format="%.2f", key="inp_requested_loan")
    with col2:
        customer_name = st.text_input("ชื่อ-นามสกุล ลูกค้า", value=st.session_state.customer_name, key="inp_customer_name")
        business_context = st.text_input("ประเภทธุรกิจ / แหล่งที่มาของรายได้หลัก", value=st.session_state.business_context, key="inp_business_context")

    st.markdown("---")
    st.subheader("💬 บันทึกข้อมูลเชิงลึกจากการสัมภาษณ์ (Interview / Soft Data)")
    interview_notes = st.text_area("รายละเอียดเพิ่มเติมที่ได้จากการพูดคุย (เช่น รายได้เสริม, หนี้สินที่ยังไม่ปรากฏในบูโร, แผนการเงิน, การกู้ร่วม ฯลฯ)", 
    value=st.session_state.interview_notes, height=150, key="inp_interview_notes")

with tab2:
    st.header("🗂️ ระบบจัดระเบียบและรวมเล่มเอกสารอัตโนมัติ")
    st.write("💡 **โยนกองเอกสารมาได้เลยครับ!** ระบบจะผสาน 'ระเบียบถาวร' และ 'ไคเทเรียล่าสุด' เข้าด้วยกันเพื่อวิเคราะห์เคสอย่างแม่นยำ")
    
    uploaded_files = st.file_uploader("ลากไฟล์เอกสารทั้งหมดของลูกค้ามาวางที่นี่", accept_multiple_files=True, type=['pdf', 'png', 'jpg', 'jpeg'])

    st.markdown("---")
    if st.button("🚀 เริ่มรวมเล่มและวิเคราะห์สินเชื่อเชิงลึก", type="primary"):
        if not api_key_input:
            st.error("⚠️ กรุณากรอก Gemini API Key (คีย์ขึ้นต้นด้วย AQ...) ที่ช่องด้านซ้าย (Sidebar) ก่อนเริ่มใช้งาน")
        elif not uploaded_files:
            st.warning("⚠️ กรุณาอัปโหลดเอกสารทางการเงินอย่างน้อย 1 ไฟล์")
        else:
           # แก้ไขจุดที่ 1: เปลี่ยนมาใช้ api_key_input จาก Sidebar
            client = genai.Client(api_key=api_key_input)
            
            with st.spinner("🤖 ระบบกำลังจัดหมวดหมู่และรวมเล่มเอกสารด้วย Python..."):
                try:
                    def classify_by_filename(filename):
                        name_lower = filename.lower()
                        if any(k in name_lower for k in ['stm', 'statement', 'book', 'บัญชี']):
                            return "STATEMENT"
                        elif any(k in name_lower for k in ['ncb', 'บูโร', 'เครดิตบูโร']):
                            return "NCB"
                        elif any(k in name_lower for k in ['ภพ', '50', 'งบ', 'ภาษี', 'สลิป', 'รับรอง', 'รายได้', 'เงินเดือน', 'ซ้าย', 'ขวา']):
                            return "INCOME"
                        elif any(k in name_lower for k in ['โฉนด', 'ที่ดิน', 'กรรมสิทธิ์']):
                            return "ASSET"
                        else:
                            return "BUSINESS_BILL"

                    file_categorized_summary = []
                    master_gemini_files = []
                    
                    with tempfile.TemporaryDirectory() as temp_dir:
                        pdf_writer_dict = {
                            "STATEMENT": PdfWriter(),
                            "INCOME": PdfWriter(),
                            "NCB": PdfWriter(),
                            "ASSET": PdfWriter(),
                            "BUSINESS_BILL": PdfWriter()
                        }
                        category_has_pages = {k: False for k in pdf_writer_dict.keys()}

                        for uploaded_file in uploaded_files:
                            temp_path = os.path.join(temp_dir, uploaded_file.name)
                            with open(temp_path, "wb") as f:
                                f.write(uploaded_file.getvalue())

                            cat_tag = classify_by_filename(uploaded_file.name)
                            file_categorized_summary.append(f"- {uploaded_file.name} ➡️ หมวด: **{cat_tag}**")

                            if uploaded_file.name.lower().endswith('.pdf'):
                                try:
                                    reader = PdfReader(temp_path)
                                    for page in reader.pages:
                                        pdf_writer_dict[cat_tag].add_page(page)
                                    category_has_pages[cat_tag] = True
                                except:
                                    pass

                        for cat_key, writer in pdf_writer_dict.items():
                            if category_has_pages[cat_key]:
                                master_pdf_path = os.path.join(temp_dir, f"Master_{cat_key}.pdf")
                                with open(master_pdf_path, "wb") as mf:
                                    writer.write(mf)
                                
                                m_g_file = client.files.upload(file=master_pdf_path)
                                master_gemini_files.append(m_g_file)

                        for uploaded_file in uploaded_files:
                            if not uploaded_file.name.lower().endswith('.pdf'):
                                temp_path = os.path.join(temp_dir, uploaded_file.name)
                                raw_g = client.files.upload(file=temp_path)
                                master_gemini_files.append(raw_g)

                        st.info("📋 **รายงานการจัดหมวดหมู่เอกสารอัตโนมัติ (Rule-based Sorting Report):**\n" + "\n".join(file_categorized_summary))

                    # 🌟 รวมร่างระเบียบหลัก เข้ากับ ไคเทเรียเฉพาะกิจ ส่งให้ AI ประมวลผลแบบฉลาดไร้รอยต่อ
                    combined_system_prompt = f"""
                    {st.session_state.system_regulations}
                    
                    --- ⚠️ [เกณฑ์เฉพาะกิจและมาตรการภาครัฐปัจจุบันที่ต้องยึดถือเคร่งครัด] ---
                    {st.session_state.dynamic_criteria}
                    """

                    full_prompt = f"""
                    {combined_system_prompt}
                    
                    --- ข้อมูลคำขอสินเชื่อและข้อมูลสัมภาษณ์ (Soft Data) จากเจ้าหน้าที่ ---
                    - ชื่อลูกค้า: {customer_name}
                    - ราคารับซื้อทรัพย์สิน: {property_price:,.2f} บาท
                    - วงเงินกู้ที่ลูกค้าต้องการ: {requested_loan:,.2f} บาท
                    - ลักษณะธุรกิจ: {business_context}
                    - บันทึกการสัมภาษณ์เพิ่มเติม: {interview_notes}
                    
                    โปรดอ่านและวิเคราะห์ไฟล์เอกสาร Master ที่จัดหมวดหมู่แล้วทั้งหมดร่วมกับข้อมูลด้านบน โดยต้องปฏิบัติตามทั้งระเบียบถาวรและเกณฑ์เฉพาะกิจ/มาตรการ LTV ล่าสุดที่ระบุไว้ข้างต้นอย่างเคร่งครัด คำนวณตัวเลขทางการเงินให้ออกมาถูกต้อง และส่งผลลัพธ์กลับมาเป็นโครงสร้าง JSON เท่านั้น
                    """

                    prompt_contents = [full_prompt] + master_gemini_files
                    
                    max_retries = 5
                    response = None
                    status_placeholder = st.empty()
                    
                    for attempt in range(max_retries):
                        try:
                            status_placeholder.info(f"🔄 กำลังส่งข้อมูลวิเคราะห์ไปยัง Google (ความพยายามครั้งที่ {attempt + 1}/{max_retries})...")
                            response = client.models.generate_content(
                                model='gemini-3.8-flash',
                                contents=prompt_contents,
                                config=types.GenerateContentConfig(
                                    response_mime_type="application/json"
                                )
                            )
                            status_placeholder.empty()
                            break
                        except Exception as api_err:
                            err_str = str(api_err)
                            if "503" in err_str or "UNAVAILABLE" in err_str or "high demand" in err_str:
                                if attempt < max_retries - 1:
                                    wait_time = (attempt + 1) * 8
                                    status_placeholder.warning(f"⚠️ เซิร์ฟเวอร์ Google หนาแน่นชั่วคราว ระบบกำลังรอคิวและลองใหม่ในอีก {wait_time} วินาที...")
                                    time.sleep(wait_time)
                                    continue
                            status_placeholder.empty()
                            raise api_err

                    for m_file in master_gemini_files:
                        try:
                            client.files.delete(name=m_file.name)
                        except:
                            pass

                    response_text = response.text.strip()
                    # แก้ไขจุดที่ 3: ลบสัญลักษณ์โค้ดบล็อกออก ป้องกัน JSON Decode Error
                    if response_text.startswith("```"):
                        response_text = response_text.replace("```json", "").replace("```", "").strip()
                        
                    analysis_data = json.loads(response_text)

                    st.success("✨ วิเคราะห์ข้อมูลสำเร็จ! สรุปผลการประเมินศักยภาพสินเชื่อ:")
                    
                    col1, col2, col3, col4 = st.columns(4)
                    col1.metric("รายได้สุทธิที่ตรวจสอบได้", f"฿{analysis_data.get('verified_income', 0):,.2f}")
                    col2.metric("ภาระหนี้สินรวม", f"฿{analysis_data.get('verified_debt', 0):,.2f}")
                    col3.metric("อัตราส่วนภาระหนี้ (DSR)", f"{analysis_data.get('dsr_percentage', 0)}%")
                    col4.metric("วงเงินกู้สูงสุดที่อนุมัติได้", f"฿{analysis_data.get('max_loan_amount', 0):,.2f}")

                    st.markdown("---")
                    st.subheader("📊 การวิเคราะห์เจาะลึกและตรรกะทางสินเชื่อ (Key Findings)")
                    for finding in analysis_data.get('key_findings', []):
                        st.write(f"👉 {finding}")

                    st.markdown("---")
                    st.subheader("🏦 ผลการคัดกรองธนาคารและแนวทางเตรียมเอกสาร")
                    for bank in analysis_data.get('recommended_banks', []):
                        with st.expander(f"🏦 {bank.get('bank', '')}"):
                            st.write(f"**เหตุผลในการแนะนำ:** {bank.get('reason', '')}")
                            st.write("**เอกสารและแนวทางที่ต้องเตรียมเพิ่ม:**")
                            for doc in bank.get('required_docs', []):
                                st.write(f"- {doc}")

                except Exception as e:
                    st.error(f"เกิดข้อผิดพลาดในการประมวลผล: {e}")
