from __future__ import annotations

from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile
from xml.sax.saxutils import escape


OUTPUT = Path(__file__).with_name("Correspondence_Agent_Presentation.pptx")

SLIDES = [
    (
        "Correspondence Agent",
        [
            "Vendor clarification drafts for invoice exceptions",
            "Current implementation: FastAPI + Streamlit + structured AI output",
            "Draft-only communication with human review",
        ],
    ),
    (
        "Purpose",
        [
            "Creates a professional vendor email when an invoice needs clarification",
            "Uses verified invoice and exception facts",
            "Never sends an email automatically",
            "Never makes the payment approval or rejection decision",
        ],
    ),
    (
        "When It Runs",
        [
            "The pipeline receives uploaded documents",
            "An invoice is successfully extracted",
            "At least one exception is detected",
            "The HITL router sends the invoice to human_review",
            "pipeline.py calls correspondence.draft(record, issues)",
        ],
    ),
    (
        "Safe Value Formatting",
        [
            "_value() converts available values to text",
            "Missing values use a clear fallback instead of invented data",
            "_money() formats numeric values as dollars",
            "Example: 5900 becomes $5,900.00",
            "Invalid values are displayed safely instead of crashing",
        ],
    ),
    (
        "Issue Details",
        [
            "_issue_details() converts exception codes into readable email lines",
            "AMOUNT_MISMATCH shows PO amount, invoice amount, and difference",
            "VENDOR_MISMATCH shows both vendor values",
            "PO_NOT_FOUND and RECEIPT_NOT_FOUND explain missing records",
            "Duplicate, threshold, and outlier issues have dedicated details",
        ],
    ),
    (
        "Verified Facts Sent to AI",
        [
            "_facts() prepares a small structured dictionary",
            "Includes vendor name, invoice number, PO number, and exceptions",
            "Includes severity, expected value, found value, and amount at risk",
            "The AI receives verified facts rather than inventing document values",
        ],
    ),
    (
        "AI Draft Generation",
        [
            "OpenAI is used only when OPENAI_API_KEY is configured",
            "temperature=0.2 keeps wording consistent and professional",
            "VendorEmailDraft requires subject, body, and human approval status",
            "The prompt forbids changing amounts, references, or exception details",
            "The email must state that human approval is required",
        ],
    ),
    (
        "Validation and Fallback",
        [
            "Reject the AI response if it is missing or does not require approval",
            "Reject it if the invoice number or PO number is missing",
            "Any API, network, or parsing failure returns None",
            "The deterministic template then creates a reliable backup draft",
        ],
    ),
    (
        "Human Review Workflow",
        [
            "Streamlit displays the exception evidence and vendor draft",
            "Reviewer can Approve case, Reject case, or Request clarification",
            "The decision is recorded through POST /review",
            "Approval of a case is separate from sending an email",
            "The current review store is in memory for the running session",
        ],
    ),
    (
        "Example and Key Message",
        [
            "Invoice INV-1001, PO-5001, amount at risk $5,900",
            "Exception: receipt or proof of delivery was not found",
            "Correspondence creates a clarification draft for the vendor",
            "Human review remains the final control",
            "Key message: AI assists communication, but does not decide or send",
        ],
    ),
]


def paragraph(text: str, size: int, bold: bool = False) -> str:
    text = escape(text)
    weight = " b=\"1\"" if bold else ""
    return (
        "<a:p><a:pPr marL=\"0\" algn=\"l\"/>"
        f"<a:r><a:rPr lang=\"en-US\" sz=\"{size}\"{weight}/>"
        f"<a:t>{text}</a:t></a:r><a:endParaRPr lang=\"en-US\" sz=\"{size}\"/></a:p>"
    )


def shape_xml(shape_id: int, name: str, x: int, y: int, width: int, height: int, body: str) -> str:
    return (
        f"<p:sp><p:nvSpPr><p:cNvPr id=\"{shape_id}\" name=\"{name}\"/>"
        f"<p:cNvSpPr/><p:nvPr/></p:nvSpPr><p:spPr><a:xfrm><a:off x=\"{x}\" y=\"{y}\"/>"
        f"<a:ext cx=\"{width}\" cy=\"{height}\"/></a:xfrm><a:prstGeom prst=\"rect\"><a:avLst/></a:prstGeom>"
        "</p:spPr><p:txBody><a:bodyPr/><a:lstStyle/>"
        f"{body}</p:txBody></p:sp>"
    )


def slide_xml(title: str, bullets: list[str]) -> str:
    title_body = paragraph(title, 3000, True)
    bullet_body = "".join(
        "<a:p><a:pPr marL=\"360000\" indent=\"-180000\"><a:buChar char=\"•\"/></a:pPr>"
        f"<a:r><a:rPr lang=\"en-US\" sz=\"2100\"/><a:t>{escape(item)}</a:t></a:r>"
        "<a:endParaRPr lang=\"en-US\" sz=\"2100\"/></a:p>"
        for item in bullets
    )
    shapes = shape_xml(2, "Title", 700000, 380000, 8500000, 800000, title_body)
    shapes += shape_xml(3, "Content", 900000, 1450000, 8200000, 5000000, bullet_body)
    return (
        "<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\"?>"
        "<p:sld xmlns:a=\"http://schemas.openxmlformats.org/drawingml/2006/main\" "
        "xmlns:r=\"http://schemas.openxmlformats.org/officeDocument/2006/relationships\" "
        "xmlns:p=\"http://schemas.openxmlformats.org/presentationml/2006/main\">"
        "<p:cSld><p:spTree><p:nvGrpSpPr><p:cNvPr id=\"1\" name=\"\"/><p:cNvGrpSpPr/>"
        "<p:nvPr/></p:nvGrpSpPr><p:grpSpPr/>"
        f"{shapes}</p:spTree></p:cSld><p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr></p:sld>"
    )


CONTENT_TYPES = """<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\"?>
<Types xmlns=\"http://schemas.openxmlformats.org/package/2006/content-types\">
<Default Extension=\"rels\" ContentType=\"application/vnd.openxmlformats-package.relationships+xml\"/>
<Default Extension=\"xml\" ContentType=\"application/xml\"/>
<Override PartName=\"/ppt/presentation.xml\" ContentType=\"application/vnd.openxmlformats-officedocument.presentationml.presentation.main+xml\"/>
<Override PartName=\"/ppt/slideMasters/slideMaster1.xml\" ContentType=\"application/vnd.openxmlformats-officedocument.presentationml.slideMaster+xml\"/>
<Override PartName=\"/ppt/slideLayouts/slideLayout1.xml\" ContentType=\"application/vnd.openxmlformats-officedocument.presentationml.slideLayout+xml\"/>
<Override PartName=\"/ppt/theme/theme1.xml\" ContentType=\"application/vnd.openxmlformats-officedocument.theme+xml\"/>
""" + "".join(
    f"<Override PartName=\"/ppt/slides/slide{i}.xml\" ContentType=\"application/vnd.openxmlformats-officedocument.presentationml.slide+xml\"/>\n"
    for i in range(1, len(SLIDES) + 1)
) + "</Types>"

RELS = """<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\"?>
<Relationships xmlns=\"http://schemas.openxmlformats.org/package/2006/relationships\">
<Relationship Id=\"rId1\" Type=\"http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument\" Target=\"ppt/presentation.xml\"/>
</Relationships>"""

PRESENTATION = """<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\"?>
<p:presentation xmlns:a=\"http://schemas.openxmlformats.org/drawingml/2006/main\" xmlns:r=\"http://schemas.openxmlformats.org/officeDocument/2006/relationships\" xmlns:p=\"http://schemas.openxmlformats.org/presentationml/2006/main\" saveSubsetFonts=\"1\"><p:sldMasterIdLst><p:sldMasterId id=\"2147483648\" r:id=\"rId1\"/></p:sldMasterIdLst><p:sldIdLst>
""" + "".join(
    f"<p:sldId id=\"{255 + i}\" r:id=\"rId{i + 1}\"/>" for i in range(1, len(SLIDES) + 1)
) + """</p:sldIdLst><p:sldSz cx=\"12192000\" cy=\"6858000\" type=\"screen16x9\"/><p:notesSz cx=\"6858000\" cy=\"9144000\"/></p:presentation>"""

PRESENTATION_RELS = """<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\"?>
<Relationships xmlns=\"http://schemas.openxmlformats.org/package/2006/relationships\">
<Relationship Id=\"rId1\" Type=\"http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideMaster\" Target=\"slideMasters/slideMaster1.xml\"/>
""" + "".join(
    f"<Relationship Id=\"rId{i + 1}\" Type=\"http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide\" Target=\"slides/slide{i}.xml\"/>"
    for i in range(1, len(SLIDES) + 1)
) + "</Relationships>"

MASTER = """<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\"?>
<p:sldMaster xmlns:a=\"http://schemas.openxmlformats.org/drawingml/2006/main\" xmlns:r=\"http://schemas.openxmlformats.org/officeDocument/2006/relationships\" xmlns:p=\"http://schemas.openxmlformats.org/presentationml/2006/main\"><p:cSld><p:spTree><p:nvGrpSpPr><p:cNvPr id=\"1\" name=\"\"/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr><p:grpSpPr/></p:spTree></p:cSld><p:sldLayoutIdLst><p:sldLayoutId id=\"1\" r:id=\"rId1\"/></p:sldLayoutIdLst><p:clrMap accent1=\"accent1\" accent2=\"accent2\" bg1=\"lt1\" bg2=\"lt2\" tx1=\"dk1\" tx2=\"dk2\"/></p:sldMaster>"""

MASTER_RELS = """<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\"?>
<Relationships xmlns=\"http://schemas.openxmlformats.org/package/2006/relationships\"><Relationship Id=\"rId1\" Type=\"http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout\" Target=\"../slideLayouts/slideLayout1.xml\"/><Relationship Id=\"rId2\" Type=\"http://schemas.openxmlformats.org/officeDocument/2006/relationships/theme\" Target=\"../theme/theme1.xml\"/></Relationships>"""

LAYOUT = """<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\"?>
<p:sldLayout xmlns:a=\"http://schemas.openxmlformats.org/drawingml/2006/main\" xmlns:r=\"http://schemas.openxmlformats.org/officeDocument/2006/relationships\" xmlns:p=\"http://schemas.openxmlformats.org/presentationml/2006/main\" type=\"blank\"><p:cSld name=\"Blank\"><p:spTree><p:nvGrpSpPr><p:cNvPr id=\"1\" name=\"\"/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr><p:grpSpPr/></p:spTree></p:cSld><p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr></p:sldLayout>"""

LAYOUT_RELS = """<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\"?>
<Relationships xmlns=\"http://schemas.openxmlformats.org/package/2006/relationships\"><Relationship Id=\"rId1\" Type=\"http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideMaster\" Target=\"../slideMasters/slideMaster1.xml\"/></Relationships>"""

THEME = """<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\"?><a:theme xmlns:a=\"http://schemas.openxmlformats.org/drawingml/2006/main\" name=\"Office Theme\"><a:themeElements><a:clrScheme name=\"Office\"><a:dk1><a:sysClr val=\"windowText\" lastClr=\"000000\"/></a:dk1><a:lt1><a:sysClr val=\"window\" lastClr=\"FFFFFF\"/></a:lt1><a:dk2><a:srgbClr val=\"1F2937\"/></a:dk2><a:lt2><a:srgbClr val=\"F8FAFC\"/></a:lt2><a:accent1><a:srgbClr val=\"0F766E\"/></a:accent1><a:accent2><a:srgbClr val=\"F59E0B\"/></a:accent2><a:accent3><a:srgbClr val=\"2563EB\"/></a:accent3><a:accent4><a:srgbClr val=\"DC2626\"/></a:accent4><a:accent5><a:srgbClr val=\"7C3AED\"/></a:accent5><a:accent6><a:srgbClr val=\"0891B2\"/></a:accent6><a:hlink><a:srgbClr val=\"0563C1\"/></a:hlink><a:folHlink><a:srgbClr val=\"954F72\"/></a:folHlink></a:clrScheme><a:fontScheme name=\"Office\"><a:majorFont><a:latin typeface=\"Aptos Display\"/></a:majorFont><a:minorFont><a:latin typeface=\"Aptos\"/></a:minorFont></a:fontScheme><a:fmtScheme name=\"Office\"><a:fillStyleLst/><a:lnStyleLst/><a:effectStyleLst/><a:bgFillStyleLst/></a:fmtScheme></a:themeElements></a:theme>"""


def main() -> None:
    with ZipFile(OUTPUT, "w", ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", CONTENT_TYPES)
        archive.writestr("_rels/.rels", RELS)
        archive.writestr("ppt/presentation.xml", PRESENTATION)
        archive.writestr("ppt/_rels/presentation.xml.rels", PRESENTATION_RELS)
        archive.writestr("ppt/slideMasters/slideMaster1.xml", MASTER)
        archive.writestr("ppt/slideMasters/_rels/slideMaster1.xml.rels", MASTER_RELS)
        archive.writestr("ppt/slideLayouts/slideLayout1.xml", LAYOUT)
        archive.writestr("ppt/slideLayouts/_rels/slideLayout1.xml.rels", LAYOUT_RELS)
        archive.writestr("ppt/theme/theme1.xml", THEME)
        for index, (title, bullets) in enumerate(SLIDES, start=1):
            archive.writestr(f"ppt/slides/slide{index}.xml", slide_xml(title, bullets))
            archive.writestr(
                f"ppt/slides/_rels/slide{index}.xml.rels",
                "<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\"?>"
                "<Relationships xmlns=\"http://schemas.openxmlformats.org/package/2006/relationships\">"
                "<Relationship Id=\"rId1\" Type=\"http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout\" Target=\"../slideLayouts/slideLayout1.xml\"/>"
                "</Relationships>",
            )
    print(OUTPUT)


if __name__ == "__main__":
    main()
