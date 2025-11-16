from fastapi import FastAPI, UploadFile, Form, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os
import json
import shutil
import aiofiles
import torch
from PIL import Image
import open_clip

app = FastAPI()

@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/ready")
async def ready():
    ready_state = hasattr(app.state, "model") and app.state.model is not None
    return {"ready": ready_state}

FRONTEND_ORIGIN = os.environ.get(
    "FRONTEND_ORIGIN",
    "https://frontend-6zqct85x2-scofields-projects-b3359916.vercel.app",
)
origins = [FRONTEND_ORIGIN, "http://localhost:3000"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)

DATA_DIR = "data"
UPLOAD_DIR = "uploads"
EMBED_DIR = "embeddings"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(EMBED_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)

captions_file = os.path.join(DATA_DIR, "captions.json")
if not os.path.exists(captions_file):
    with open(captions_file, "w") as f:
        json.dump({}, f)


def get_next_embedding_name():
    existing = [f for f in os.listdir(EMBED_DIR) if f.startswith("embedding_") and f.endswith(".pt")]
    if not existing:
        return "embedding_001.pt"
    existing_numbers = [int(f.split("_")[1].split(".")[0]) for f in existing]
    next_number = max(existing_numbers) + 1
    return f"embedding_{next_number:03d}.pt"


@app.on_event("startup")
def load_model():
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model, _, preprocess = open_clip.create_model_and_transforms('ViT-B-32', pretrained='openai')
    model = model.to(device)
    model.eval()
    app.state.model = model
    app.state.preprocess = preprocess
    app.state.device = device
    app.state.tokenizer = open_clip.get_tokenizer('ViT-B-32')


@app.post("/upload/")
async def upload_image(file: UploadFile = File(...), caption: str | None = Form(None)):
    filename = file.filename
    file_location = os.path.join(UPLOAD_DIR, filename)
    async with aiofiles.open(file_location, "wb") as out_file:
        content = await file.read()
        await out_file.write(content)

    if caption:
        try:
            with open(captions_file, "r") as f:
                captions = json.load(f)
        except Exception:
            captions = {}
        captions[filename] = caption
        with open(captions_file, "w") as f:
            json.dump(captions, f, indent=2)

    return {"status": "success", "filename": filename}


@app.post("/embed/")
async def generate_embedding(
    caption: str = Form(...),
    file: UploadFile | None = File(None),
    filename: str | None = Form(None),
):
 
    if file is not None:
        filename = file.filename
        file_location = os.path.join(UPLOAD_DIR, filename)
        async with aiofiles.open(file_location, "wb") as out_file:
            content = await file.read()
            await out_file.write(content)

    if not filename:
        raise HTTPException(status_code=400, detail="No filename or file provided")

    image_path = os.path.join(UPLOAD_DIR, filename)
    if not os.path.exists(image_path):
        raise HTTPException(status_code=404, detail=f"File not found: {filename}")

    try:
        with open(captions_file, "r") as f:
            captions = json.load(f)
    except Exception:
        captions = {}
    captions[filename] = caption
    with open(captions_file, "w") as f:
        json.dump(captions, f, indent=2)

    model = app.state.model
    preprocess = app.state.preprocess
    device = app.state.device
    tokenizer = app.state.tokenizer

    image = preprocess(Image.open(image_path)).unsqueeze(0).to(device)
    text = tokenizer([caption]).to(device)

    with torch.no_grad():
        image_embedding = model.encode_image(image)
        text_embedding = model.encode_text(text)

    image_embedding = image_embedding / image_embedding.norm(dim=-1, keepdim=True)
    text_embedding = text_embedding / text_embedding.norm(dim=-1, keepdim=True)

    combined = torch.cat([image_embedding, text_embedding], dim=-1)
    emb_filename = get_next_embedding_name()
    emb_path = os.path.join(EMBED_DIR, emb_filename)
    torch.save(combined.cpu(), emb_path)

    matrix = combined.cpu().numpy().tolist()

    return JSONResponse({"filename": filename, "embedding_file": emb_path, "matrix": matrix})


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run("main:app", host="0.0.0.0", port=port, log_level="info")
