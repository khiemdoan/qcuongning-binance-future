import io
import json
from PIL import Image
import torch
import torchvision.transforms as transforms
from torchvision.models import resnet50
from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse, PlainTextResponse

app = FastAPI()

model = resnet50(pretrained=True)
model.eval()

preprocess = transforms.Compose([
    transforms.Resize(256),
    transforms.CenterCrop(224),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
])

with open('imagenet_classes.json') as f:
    imagenet_classes = json.load(f)

@app.post("/predict")
async def predict(file: UploadFile = File(...)):
    if not file:
        return JSONResponse(content={"error": "No file uploaded"}, status_code=400)
    
    image_bytes = await file.read()
    image = Image.open(io.BytesIO(image_bytes))
    image_tensor = preprocess(image).unsqueeze(0)
    
    with torch.no_grad():
        output = model(image_tensor)
    
    _, predicted_idx = torch.max(output, 1)
    predicted_label = imagenet_classes[str(predicted_idx.item())]
    
    return {"prediction": predicted_label}
@app.get("/", response_class=PlainTextResponse)
async def root():
    return "hello"

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=80)