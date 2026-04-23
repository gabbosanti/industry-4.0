import os
import numpy as np
import tensorflow as tf

OUT_MODEL_H = os.path.join("src", "model_data.h")
OUT_TEST_H = os.path.join("src", "test_images.h")
NUM_TEST_SAMPLES = 20
EPOCHS = 3
BATCH_SIZE = 128

def c_array_bytes(name: str, data: bytes) -> str:
    lines = []
    lines.append(f"const unsigned char {name}[] = {{")
    for i, b in enumerate(data):
        if i % 12 == 0:
            lines.append("    ")
        lines[-1] += f"0x{b:02x}, "
    lines.append("};")
    lines.append(f"const unsigned int {name}_len = {len(data)};")
    return "\n".join(lines)

def c_array_int8_2d(name: str, arr: np.ndarray) -> str:
    assert arr.dtype == np.int8
    n, m = arr.shape
    lines = [f"const int8_t {name}[{n}][{m}] = {{"]
    for row in arr:
        vals = ", ".join(str(int(x)) for x in row)
        lines.append(f"    {{{vals}}},")
    lines.append("};")
    return "\n".join(lines)

def c_array_int(name: str, arr: np.ndarray) -> str:
    lines = [f"const int {name}[{len(arr)}] = {{"]
    vals = ", ".join(str(int(x)) for x in arr)
    lines.append(f"    {vals}")
    lines.append("};")
    return "\n".join(lines)

os.makedirs(os.path.join("components", "app"), exist_ok=True)

# 1) Load MNIST
(x_train, y_train), (x_test, y_test) = tf.keras.datasets.mnist.load_data()

# Normalize to [0,1]
x_train = x_train.astype(np.float32) / 255.0
x_test  = x_test.astype(np.float32) / 255.0

# Add channel dim
x_train = np.expand_dims(x_train, axis=-1)  # (N,28,28,1)
x_test  = np.expand_dims(x_test, axis=-1)

# 2) Tiny model
model = tf.keras.Sequential([
    tf.keras.layers.Input(shape=(28, 28, 1)),
    tf.keras.layers.Flatten(),
    tf.keras.layers.Dense(32, activation="relu"),
    tf.keras.layers.Dense(10, activation="softmax"),
])

model.compile(
    optimizer="adam",
    loss="sparse_categorical_crossentropy",
    metrics=["accuracy"]
)

model.fit(
    x_train, y_train,
    validation_split=0.1,
    epochs=EPOCHS,
    batch_size=BATCH_SIZE,
    verbose=2
)

test_loss, test_acc = model.evaluate(x_test, y_test, verbose=0)
print(f"Float model test accuracy: {test_acc:.4f}")

# 3) Representative dataset for int8 quantization
def representative_dataset():
    for i in range(200):
        img = x_train[i:i+1]
        yield [img]

converter = tf.lite.TFLiteConverter.from_keras_model(model)
converter.optimizations = [tf.lite.Optimize.DEFAULT]
converter.representative_dataset = representative_dataset
converter.target_spec.supported_ops = [tf.lite.OpsSet.TFLITE_BUILTINS_INT8]
converter.inference_input_type = tf.int8
converter.inference_output_type = tf.int8

tflite_model = converter.convert()
print(f"TFLite model size: {len(tflite_model)} bytes")

# Save raw tflite too
with open("mnist_int8.tflite", "wb") as f:
    f.write(tflite_model)

# 4) Check quantized model and grab input/output scales
interpreter = tf.lite.Interpreter(model_content=tflite_model)
interpreter.allocate_tensors()

input_details = interpreter.get_input_details()[0]
output_details = interpreter.get_output_details()[0]

in_scale, in_zero = input_details["quantization"]
out_scale, out_zero = output_details["quantization"]

print("Input quantization:", input_details["quantization"])
print("Output quantization:", output_details["quantization"])

# 5) Build small test set embedded in firmware
test_imgs = x_test[:NUM_TEST_SAMPLES]  # float [0,1]
test_labels = y_test[:NUM_TEST_SAMPLES]

# Quantize images as int8 to match model input
test_imgs_q = np.round(test_imgs / in_scale + in_zero).astype(np.int8)
test_imgs_q = test_imgs_q.reshape(NUM_TEST_SAMPLES, 28 * 28)

# 6) Export model_data.h
model_header = f"""#pragma once
#include <stdint.h>

{c_array_bytes("g_mnist_model_data", tflite_model)}
"""
with open(OUT_MODEL_H, "w") as f:
    f.write(model_header)

# 7) Export test_images.h
test_header = f"""#pragma once
#include <stdint.h>

static const int kNumTestSamples = {NUM_TEST_SAMPLES};
static const float kModelInputScale = {in_scale:.12f}f;
static const int kModelInputZeroPoint = {int(in_zero)};
static const float kModelOutputScale = {out_scale:.12f}f;
static const int kModelOutputZeroPoint = {int(out_zero)};

{c_array_int8_2d("g_test_images", test_imgs_q)}
{c_array_int("g_test_labels", test_labels)}
"""
with open(OUT_TEST_H, "w") as f:
    f.write(test_header)

print(f"Wrote {OUT_MODEL_H}")
print(f"Wrote {OUT_TEST_H}")