import os
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors


def generar_pdf_ticket(id_venta, mesa_input, tipo_pedido, metodo_pago, total, pago_con, cambio, items, nombre_mesero="N/A"):
    os.makedirs("tickets", exist_ok=True)
    filepath = f"tickets/ticket_{id_venta}.pdf"

    PAGE_WIDTH = 80 * mm
    PAGE_HEIGHT = 180 * mm

    doc = SimpleDocTemplate(
        filepath,
        pagesize=(PAGE_WIDTH, PAGE_HEIGHT),
        rightMargin=4 * mm, leftMargin=4 * mm, topMargin=6 * mm, bottomMargin=6 * mm
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle('ReceiptTitle', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=12, alignment=1, spaceAfter=2)
    subtitle_style = ParagraphStyle('ReceiptSubtitle', parent=styles['Normal'], fontName='Helvetica', fontSize=8, alignment=1, spaceAfter=6)
    body_style = ParagraphStyle('ReceiptBody', parent=styles['Normal'], fontName='Helvetica', fontSize=8, leading=10)
    bold_style = ParagraphStyle('ReceiptBold', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=8, leading=10)
    right_bold = ParagraphStyle('ReceiptRightBold', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=9, alignment=2)

    story = []

    story.append(Paragraph("DANNY'S BURGER 🍔", title_style))
    story.append(Paragraph("¡Las mejores hamburguesas!", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.black, spaceBefore=2, spaceAfter=4))

    story.append(Paragraph(f"<b>Folio #:</b> {id_venta}", body_style))
    story.append(Paragraph(f"<b>Mesa/Servicio:</b> {mesa_input} ({tipo_pedido})", body_style))
    story.append(Paragraph(f"<b>Mesero:</b> {nombre_mesero}", body_style))
    story.append(Paragraph(f"<b>Método Pago:</b> {metodo_pago}", body_style))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.gray, spaceBefore=4, spaceAfter=4))

    table_data = [[Paragraph("<b>Cant / Prod</b>", bold_style), Paragraph("<b>Subtotal</b>", right_bold)]]
    for item in items:
        cant_nom = f"{item['cantidad']}x {item['nombre']}"
        sub = f"${item['subtotal']:.2f}"
        table_data.append([Paragraph(cant_nom, body_style), Paragraph(sub, body_style)])

    t = Table(table_data, colWidths=[48*mm, 24*mm])
    t.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 1),
        ('TOPPADDING', (0, 0), (-1, -1), 1),
    ]))
    story.append(t)
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.gray, spaceBefore=4, spaceAfter=4))

    story.append(Paragraph(f"TOTAL: ${total:.2f} MXN", right_bold))
    if metodo_pago == "Efectivo":
        story.append(Paragraph(f"Efectivo Recibido: ${pago_con:.2f}", body_style))
        story.append(Paragraph(f"Cambio Entregado: ${cambio:.2f}", body_style))

    story.append(HRFlowable(width="100%", thickness=1, color=colors.black, spaceBefore=6, spaceAfter=6))
    story.append(Paragraph("¡Gracias por su compra!", subtitle_style))

    doc.build(story)

    with open(filepath, "rb") as f:
        pdf_bytes = f.read()

    return filepath, pdf_bytes