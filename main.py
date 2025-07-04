from fastapi import FastAPI, Response
from pydantic import BaseModel
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.platypus import Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.utils import ImageReader
from io import BytesIO
import threading
import os

app = FastAPI()
lock = threading.Lock()
COUNTER_FILE = "counter.txt"

# ✅ Input model
class SalesContractData(BaseModel):
    contract_no: str
    date: str
    consignee: list[str]
    notify_party: list[str]
    product_name: str
    quantity: str
    price: str
    amount: str

# ✅ Counter logic
def get_next_counter():
    with lock:
        if not os.path.exists(COUNTER_FILE):
            with open(COUNTER_FILE, "w") as f:
                f.write("1")
            return 1
        with open(COUNTER_FILE, "r+") as f:
            count = int(f.read())
            f.seek(0)
            f.write(str(count + 1))
            f.truncate()
            return count

# ✅ PDF generator
@app.post("/generate-pdf/")
async def generate_pdf(data: SalesContractData):
    pdf_number = get_next_counter()
    filename = f"Sales_Contract_{pdf_number}.pdf"
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    # 🔷 Header Section (Website Left, Logo Center, Company Name Right)
    try:
        img_path = os.path.join(os.path.dirname(__file__), "saleslogo.jpg")
        header_img = ImageReader(img_path)

        img_width, img_height = 70, 60
        x_center = (width - img_width) / 2
        y_top = height - 65

        # 🔹 Website (Left)
        c.setFont("Helvetica-Bold", 9)
        c.setFillColor(colors.grey)
        c.drawString(40, height - 30, "Website: www.shraddhaimpex.in")

        # 🔹 Logo (Center)
        c.drawImage(header_img, x_center, y_top, width=img_width, height=img_height, mask='auto')

        # 🔹 Company Name + Tagline (Right)
        c.setFont("Helvetica-Bold", 12)
        c.setFillColor(colors.black)
        c.drawRightString(width - 40, height - 25, "SHRADDHA IMPEX")
        c.setFont("Helvetica", 8)
        c.drawRightString(width - 40, height - 38, "(A Government Recognized Export House)")
    except Exception as e:
        c.setFont("Helvetica-Bold", 10)
        c.drawCentredString(width / 2, height - 60, "[HEADER IMAGE MISSING]")

    # 🔷 Title
    start_y = height - 100
    c.setFont("Helvetica-Bold", 12)
    c.drawCentredString(width / 2, start_y, "SALES CONTRACT")
    c.setFont("Helvetica", 9)
    c.drawString(50, start_y - 20, f"Contract No: {data.contract_no}")
    c.drawRightString(width - 50, start_y - 20, f"Date: {data.date}")

    # 🔷 Seller Block
    y = start_y - 70
    c.setFont("Helvetica-Bold", 9)
    c.drawString(45, y, "SELLER")
    seller = [
        "SHRADDHA IMPEX",
        "308, THIRD FLOOR, FORTUNE BUSINESS CENTER",
        "165 R.N.T. MARG, INDORE-452001",
        "M.P., INDIA"
    ]
    c.setFont("Helvetica", 9)
    for i, line in enumerate(seller):
        c.drawString(50, y - ((i + 1) * 12), line)

    # 🔷 Consignee Block
    c.setFont("Helvetica-Bold", 9)
    c.drawString(230, y, "CONSIGNEE | NOTIFY PARTY 1")
    c.setFont("Helvetica", 9)
    for i, line in enumerate(data.consignee):
        c.drawString(230, y - ((i + 1) * 12), line)

    # 🔷 Notify Party 2
    c.setFont("Helvetica-Bold", 9)
    c.drawString(410, y, "NOTIFY PARTY 2")
    c.setFont("Helvetica", 9)
    for i, line in enumerate(data.notify_party):
        c.drawString(410, y - ((i + 1) * 12), line)

    # 🔷 Product Table
    table_data = [
        ["Product", "Quantity", "Price (CIF), Colombo", "Amount(CIF)"],
        [data.product_name, data.quantity, data.price, data.amount]
    ]
    table = Table(table_data, colWidths=[130, 180, 110, 90])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
    ]))
    table.wrapOn(c, width, height)
    table.drawOn(c, 40, y - 150)

    # 🔷 Static Details
    y -= 160
    details = [
        ("Packing", "50 KG Liner PP Bags"),
        ("Loading Port", "Any port in India"),
        ("Destination Port", "Colombo, Srilanka"),
        ("Shipment", "In lot of 5 containers, on or before 20 June, 2021"),
        ("Documents", "Invoice in quadruplicate, Packing List in triplicate, B/L 3 original and 2 copies, Phytosanitary Certificate, Certificate of Origin."),
        ("Payment Terms", "Payment against scanned documents through TT."),
        ("Seller’s Bank", "Bank Of Baroda, Annapurna Road Branch, Indore (M.P.), India"),
        ("Account No.", "31740200000041; Swift: BARBINBBIND; Account Name: Shraddha Impex"),
        ("Arbitration", "Disputes shall be settled by sole arbitration in Indore, M.P., under Indian laws."),
        ("Terms & Conditions", "1) No claim for port issues.\n2) Quality approved at load port is final.")
    ]
    for label, value in details:
        c.setFont("Helvetica-Bold", 8)
        c.drawString(50, y, f"{label} :")
        c.setFont("Helvetica", 8)
        for line in value.split("\n"):
            c.drawString(150, y, line)
            y -= 12
        y -= 6

    # 🔷 Acceptance and Signature
    c.setFont("Helvetica-Bold", 10)
    c.drawCentredString(width / 2, y, "Accepted")
    y -= 20
    c.setFont("Helvetica", 9)
    c.drawString(50, y, "For, Seller")
    c.drawString(230, y, "For, Consignee")
    c.drawString(400, y, "For, Notify Party")
    y -= 50
    c.drawString(50, y, "SHRADDHA IMPEX")
    c.drawString(230, y, "SMART DRAGON LANKA PVT LTD")
    c.drawString(400, y, "DEVI GLOBAL HK LTD")

    # 🔷 Footer Address
    c.setFont("Helvetica", 7)
    c.drawCentredString(width / 2, 30, "308, Third Floor, Fortune Business Center, 165 R.N.T. Marg, Indore 452001, M.P., India")
    c.drawCentredString(width / 2, 18, "Tel. : (+91) 731 2515151 • Fax : (+91) 731 4096348 • E-Mail : shraddhaimpex@yahoo.com")

    # ✅ Finalize
    c.save()
    buffer.seek(0)
    return Response(content=buffer.read(), media_type="application/pdf", headers={
        "Content-Disposition": f"attachment; filename={filename}"
    })

@app.get("/")
def home():
    return {"message": "Your Render App is Working!"}