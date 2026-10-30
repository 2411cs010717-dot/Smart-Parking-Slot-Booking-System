"""Train a simple CNN on the generated or a compatible folder-based dataset."""
import os
import tensorflow as tf

HERE = os.path.dirname(os.path.abspath(__file__))
DATASET = os.path.join(HERE, "dataset")
MODEL_DIR = os.path.join(HERE, "model")
os.makedirs(MODEL_DIR, exist_ok=True)

train_dir = os.path.join(DATASET, "train")
val_dir = os.path.join(DATASET, "validation")
if not os.path.isdir(train_dir) or not os.path.isdir(val_dir):
    raise SystemExit("Dataset missing. Run: python deep_learning/generate_demo_dataset.py")

train = tf.keras.utils.image_dataset_from_directory(
    train_dir, image_size=(128, 128), batch_size=32,
    label_mode="binary", class_names=["vacant", "occupied"], seed=42
)
val = tf.keras.utils.image_dataset_from_directory(
    val_dir, image_size=(128, 128), batch_size=32,
    label_mode="binary", class_names=["vacant", "occupied"], seed=42
)
AUTOTUNE = tf.data.AUTOTUNE
train = train.map(lambda x, y: (tf.cast(x, tf.float32) / 255.0, y)).prefetch(AUTOTUNE)
val = val.map(lambda x, y: (tf.cast(x, tf.float32) / 255.0, y)).prefetch(AUTOTUNE)

model = tf.keras.Sequential([
    tf.keras.layers.Input(shape=(128, 128, 3)),
    tf.keras.layers.Conv2D(16, 3, activation="relu"),
    tf.keras.layers.MaxPooling2D(),
    tf.keras.layers.Conv2D(32, 3, activation="relu"),
    tf.keras.layers.MaxPooling2D(),
    tf.keras.layers.Conv2D(64, 3, activation="relu"),
    tf.keras.layers.MaxPooling2D(),
    tf.keras.layers.Flatten(),
    tf.keras.layers.Dense(64, activation="relu"),
    tf.keras.layers.Dropout(0.25),
    tf.keras.layers.Dense(1, activation="sigmoid")
])
model.compile(optimizer="adam", loss="binary_crossentropy", metrics=["accuracy"])
model.summary()
model.fit(train, validation_data=val, epochs=8)
loss, accuracy = model.evaluate(val, verbose=0)
out = os.path.join(MODEL_DIR, "parking_cnn.keras")
model.save(out)
print(f"\nSaved model: {out}")
print(f"Validation accuracy on synthetic data: {accuracy:.3f}")
print("Synthetic-data accuracy is only for testing the workflow, not real-world performance.")
