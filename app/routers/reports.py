from datetime import date
from calendar import monthrange
from io import BytesIO
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import select
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from app.database import get_db
from app.deps import get_current_user
from app.models import Transaction, User

router = APIRouter(prefix="/api/reports", tags=["Reports"])

@router.get("/monthly.pdf")
def monthly_pdf(month: str | None = None, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    month = month or date.today().strftime("%Y-%m")
    start = date.fromisoformat(month + "-01")
    end = date(start.year, start.month, monthrange(start.year, start.month)[1])
    rows = db.scalars(select(Transaction).where(Transaction.user_id == user.id,
        Transaction.transaction_date.between(start, end)).order_by(Transaction.transaction_date)).all()
    income = sum(x.amount for x in rows if x.kind == "income")
    expenses = sum(x.amount for x in rows if x.kind == "expense")
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    story = [Paragraph(f"Financial report — {month}", styles["Title"]),
             Paragraph(f"Prepared for {user.name}", styles["Normal"]), Spacer(1, 14),
             Paragraph(f"Income: {income:,.2f} | Expenses: {expenses:,.2f} | Net: {income-expenses:,.2f}", styles["Heading2"]),
             Spacer(1, 12)]
    data = [["Date", "Type", "Description", "Amount"]]
    data += [[str(x.transaction_date), x.kind.title(), x.description[:35], f"{x.amount:,.2f}"] for x in rows]
    table = Table(data, repeatRows=1, colWidths=[75, 65, 245, 85])
    table.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),colors.HexColor("#172554")),
        ("TEXTCOLOR",(0,0),(-1,0),colors.white),("GRID",(0,0),(-1,-1),.35,colors.lightgrey),
        ("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white,colors.HexColor("#f1f5f9")]),
        ("PADDING",(0,0),(-1,-1),6)]))
    story.append(table)
    doc.build(story)
    buffer.seek(0)
    return StreamingResponse(buffer, media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="financial-report-{month}.pdf"'})
