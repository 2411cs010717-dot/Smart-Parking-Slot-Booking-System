"""Command-line prediction: python deep_learning/predict.py path/to/image.jpg"""
import os, sys
import numpy as np
import tensorflow as tf
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
model_path = os.path.join(HERE, "model", "parking_cnn.keras")
if not os.path.exists(model_path):
    raise SystemExit("Model missing. Run generate_demo_dataset.py and train_cnn.py first.")
if len(sys.argv) < 2:
    raise SystemExit("Usage: python deep_learning/predict.py path/to/parking-space-image.jpg")
image = Image.open(sys.argv[1]).convert("RGB").resize((128, 128))
arr = np.asarray(image, dtype="float32") / 255.0
score = float(tf.keras.models.load_model(model_path).predict(arr[None, ...], verbose=0)[0][0])
label = "Occupied" if score >= 0.5 else "Vacant"
confidence = score if score >= 0.5 else 1.0 - score
print(f"Prediction: {label} ({confidence * 100:.1f}% model confidence)")
