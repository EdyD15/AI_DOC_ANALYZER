import json
import os
import asyncio
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, Response
from pydantic import BaseModel

import services

app = FastAPI(title="DocuMind API")

# Comma-separated list of extra allowed origins, e.g. the deployed frontend's
# URL (https://<frontend-service>-production.up.railway.app).
_extra_origins = [o.strip() for o in os.environ.get("ALLOWED_ORIGINS", "").split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", *_extra_origins],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Documents ──────────────────────────────────────────────────────────────────

@app.get("/api/documents")
def list_documents():
    return services.get_all_documents_from_db()


@app.post("/api/documents/upload")
async def upload_document(file: UploadFile = File(...)):
    content = await file.read()

    class _Buf:
        def __init__(self, name, data):
            self.name = name
            self._data = data
        def read(self, n=-1):
            return self._data

    ok = services.process_and_save_document(_Buf(file.filename, content))
    if not ok:
        raise HTTPException(status_code=422, detail="Could not process document.")
    return {"ok": True, "name": file.filename}


@app.delete("/api/documents")
def clear_documents():
    services.clear_db()
    return {"ok": True}


# ── Sessions ───────────────────────────────────────────────────────────────────

@app.get("/api/sessions")
def list_sessions():
    return services.load_all_chat_sessions()


class SaveSessionBody(BaseModel):
    messages: list


@app.put("/api/sessions/{name}")
def save_session(name: str, body: SaveSessionBody):
    services.save_chat_session(name, body.messages)
    return {"ok": True}


@app.delete("/api/sessions/{name}")
def delete_session(name: str):
    services.delete_chat_session(name)
    return {"ok": True}


# ── Chat ───────────────────────────────────────────────────────────────────────

class ChatBody(BaseModel):
    question: str
    selected_documents: list[str] = []
    image_base64: str | None = None
    image_mime: str | None = None
    chat_history: list[dict] = []


@app.post("/api/chat/stream")
def chat_stream(body: ChatBody):
    def generate():
        try:
            for chunk in services.query_openai_api(
                body.question,
                selected_documents=body.selected_documents or None,
                image_base64=body.image_base64,
                image_mime=body.image_mime,
                chat_history=body.chat_history,
            ):
                yield f"data: {json.dumps({'chunk': chunk})}\n\n"
            yield "data: [DONE]\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


# ── Export ─────────────────────────────────────────────────────────────────────

class ExportBody(BaseModel):
    messages: list


@app.post("/api/export/docx")
def export_docx(body: ExportBody):
    buf = services.generate_chat_export_docx(body.messages)
    return Response(
        content=buf.read(),
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": 'attachment; filename="export.docx"'},
    )


@app.post("/api/export/pdf")
def export_pdf(body: ExportBody):
    buf = services.generate_chat_export_pdf(body.messages)
    return Response(
        content=buf.read(),
        media_type="application/pdf",
        headers={"Content-Disposition": 'attachment; filename="export.pdf"'},
    )
