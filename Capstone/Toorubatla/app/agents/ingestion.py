from __future__ import annotations
import io, logging, uuid
from pathlib import Path
import pandas as pd
import pymupdf
import pytesseract
from PIL import Image, ImageOps
from app.core.config import settings
from app.models.schemas import IngestedDocument, ExtractionMethod, ProcessingStatus
from app.services.file_utils import sha256_file, mime_type, validate_path
from app.services.classifier import classify
log=logging.getLogger("ingestion")

class IngestionAgent:
    def __init__(self):
        if settings.tesseract_cmd: pytesseract.pytesseract.tesseract_cmd=settings.tesseract_cmd

    def ingest_folder(self, folder: Path) -> list[IngestedDocument]:
        return [self.ingest(p) for p in sorted(folder.iterdir()) if p.is_file()]

    def ingest(self, path: Path) -> IngestedDocument:
        doc_id=str(uuid.uuid4()); digest=sha256_file(path) if path.exists() else ""
        try:
            validate_path(path)
            ext=path.suffix.lower()
            if ext==".pdf": text,tables,method,pages,quality=self._pdf(path)
            elif ext==".csv": text,tables,method,pages,quality=self._csv(path)
            else: text,tables,method,pages,quality=self._image(path)
            doc_type,class_conf=classify(text,path.name,ext==".csv")
            confidence=round(min(1.0,.7*quality+.3*class_conf),3)
            result=IngestedDocument(document_id=doc_id,file_name=path.name,mime_type=mime_type(path),document_type=doc_type,extraction_method=method,raw_text=text,tables=tables,confidence=confidence,sha256=digest,page_count=pages,metadata={"size_bytes":path.stat().st_size})
            log.info("file=%s method=%s type=%s confidence=%s",path.name,method,doc_type,confidence)
            return result
        except Exception as e:
            log.exception("Ingestion failed for %s",path)
            return IngestedDocument(document_id=doc_id,file_name=path.name,mime_type=mime_type(path),document_type="unknown",extraction_method="csv" if path.suffix.lower()==".csv" else "image_ocr",confidence=0,sha256=digest,status=ProcessingStatus.failed,error=str(e))

    def _pdf(self,path:Path):
        doc=pymupdf.open(path); texts=[]; tables=[]; used_ocr=False
        scale=settings.ocr_dpi/72
        for page in doc:
            native=page.get_text("text").strip()
            if len(native)>=settings.min_native_text_chars:
                texts.append(native)
            else:
                pix=page.get_pixmap(matrix=pymupdf.Matrix(scale,scale),alpha=False)
                img=Image.open(io.BytesIO(pix.tobytes("png")))
                texts.append(self._ocr(img)); used_ocr=True
            try:
                for t in page.find_tables().tables:
                    rows=t.extract();
                    if rows: tables.append(self._rows_to_records(rows))
            except Exception: pass
        text="\n\n".join(texts)
        quality=self._text_quality(text)
        return text,tables,(ExtractionMethod.pdf_ocr if used_ocr else ExtractionMethod.pdf_text),len(doc),quality

    def _image(self,path:Path):
        with Image.open(path) as img: text=self._ocr(img)
        return text,[],ExtractionMethod.image_ocr,1,self._text_quality(text)

    def _ocr(self,img:Image.Image)->str:
        img=ImageOps.exif_transpose(img).convert("L")
        img=ImageOps.autocontrast(img)
        return pytesseract.image_to_string(img,lang=settings.ocr_language,config="--oem 3 --psm 6").strip()

    def _csv(self,path:Path):
        try: df=pd.read_csv(path,sep=None,engine="python")
        except UnicodeDecodeError: df=pd.read_csv(path,sep=None,engine="python",encoding="latin-1")
        df.columns=[str(c).strip() for c in df.columns]
        df=df.where(pd.notna(df),None)
        records=df.to_dict(orient="records")
        text="\n".join([" | ".join(f"{k}: {v}" for k,v in r.items()) for r in records])
        return text,[records],ExtractionMethod.csv,None,.98 if len(df)>0 else .5

    @staticmethod
    def _rows_to_records(rows):
        header=[str(x or f"column_{i}").strip() for i,x in enumerate(rows[0])]
        return [dict(zip(header,[x for x in row])) for row in rows[1:]]
    @staticmethod
    def _text_quality(text):
        if not text: return 0.05
        printable=sum(c.isprintable() for c in text)/len(text)
        alnum=sum(c.isalnum() for c in text)/len(text)
        return min(1.0,.55*printable+.45*min(1,alnum/.35))
