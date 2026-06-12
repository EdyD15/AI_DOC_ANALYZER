import io
import json
import os
import asyncio
from fastapi import FastAPI, File, UploadFile, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, Response
from pydantic import BaseModel

import auth
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


# ── Auth ───────────────────────────────────────────────────────────────────────

class RegisterBody(BaseModel):
    username: str
    password: str


class LoginBody(BaseModel):
    username: str
    password: str


@app.post("/api/auth/register")
def register(body: RegisterBody):
    username = body.username.strip()
    if len(username) < 3:
        raise HTTPException(status_code=400, detail="Username must be at least 3 characters.")
    if len(body.password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters.")

    user = services.create_user(username, body.password)
    if user is None:
        raise HTTPException(status_code=409, detail="Username already exists.")

    token = auth.create_access_token(user["id"], user["username"])
    return {"access_token": token, "token_type": "bearer", "username": user["username"]}


@app.post("/api/auth/login")
def login(body: LoginBody):
    user = services.authenticate_user(body.username.strip(), body.password)
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid username or password.")

    token = auth.create_access_token(user["id"], user["username"])
    return {"access_token": token, "token_type": "bearer", "username": user["username"]}


@app.get("/api/auth/me")
def get_me(user: dict = Depends(auth.get_current_user)):
    return {"id": user["id"], "username": user["username"]}


class ChangePasswordBody(BaseModel):
    current_password: str
    new_password: str


@app.post("/api/auth/change-password")
def change_password(body: ChangePasswordBody, user: dict = Depends(auth.get_current_user)):
    if len(body.new_password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters.")

    ok = services.change_password(user["id"], body.current_password, body.new_password)
    if not ok:
        raise HTTPException(status_code=401, detail="Current password is incorrect.")
    return {"ok": True}


# ── Documents ──────────────────────────────────────────────────────────────────

@app.get("/api/documents")
def list_documents(user: dict = Depends(auth.get_current_user)):
    return services.get_all_documents_from_db(user["id"])


@app.post("/api/documents/upload")
async def upload_document(file: UploadFile = File(...), user: dict = Depends(auth.get_current_user)):
    content = await file.read()

    buf = io.BytesIO(content)
    buf.name = file.filename

    ok, error = services.process_and_save_document(buf, user["id"])
    if not ok:
        raise HTTPException(status_code=422, detail=error or "Could not process document.")
    return {"ok": True, "name": file.filename}


@app.delete("/api/documents")
def clear_documents(user: dict = Depends(auth.get_current_user)):
    services.clear_db(user["id"])
    return {"ok": True}


# ── Sessions ───────────────────────────────────────────────────────────────────

@app.get("/api/sessions")
def list_sessions(user: dict = Depends(auth.get_current_user)):
    return services.load_all_chat_sessions(user["id"])


class SaveSessionBody(BaseModel):
    messages: list


@app.put("/api/sessions/{name}")
def save_session(name: str, body: SaveSessionBody, user: dict = Depends(auth.get_current_user)):
    services.save_chat_session(user["id"], name, body.messages)
    return {"ok": True}


@app.delete("/api/sessions/{name}")
def delete_session(name: str, user: dict = Depends(auth.get_current_user)):
    services.delete_chat_session(user["id"], name)
    return {"ok": True}


# ── Chat ───────────────────────────────────────────────────────────────────────

class ChatBody(BaseModel):
    question: str
    selected_documents: list[str] = []
    image_base64: str | None = None
    image_mime: str | None = None
    chat_history: list[dict] = []


@app.post("/api/chat/stream")
def chat_stream(body: ChatBody, user: dict = Depends(auth.get_current_user)):
    def generate():
        try:
            for chunk in services.query_openai_api(
                body.question,
                user["id"],
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
def export_docx(body: ExportBody, user: dict = Depends(auth.get_current_user)):
    buf = services.generate_chat_export_docx(body.messages)
    return Response(
        content=buf.read(),
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": 'attachment; filename="export.docx"'},
    )


@app.post("/api/export/pdf")
def export_pdf(body: ExportBody, user: dict = Depends(auth.get_current_user)):
    buf = services.generate_chat_export_pdf(body.messages)
    return Response(
        content=buf.read(),
        media_type="application/pdf",
        headers={"Content-Disposition": 'attachment; filename="export.pdf"'},
    )
