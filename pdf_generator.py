from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import io


def generate_semester_pdf(rows, sem):

    buffer = io.BytesIO()

    pdf = canvas.Canvas(buffer, pagesize=letter)

    y = 750

    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(200, 800, f"Semester {sem} Report")

    pdf.setFont("Helvetica", 12)

    for r in rows:

        text = f"{r['name']} - {r['subject']} : {r['marks']}"

        pdf.drawString(50, y, text)

        y -= 20

        if y < 50:
            pdf.showPage()
            y = 750

    pdf.save()

    buffer.seek(0)

    return buffer