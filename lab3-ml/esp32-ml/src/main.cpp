#include <stdio.h>
#include <stdint.h>
#include <inttypes.h>
#include <string.h>

#include "esp_log.h"
#include "esp_timer.h"
#include "esp_heap_caps.h"

#include "tensorflow/lite/c/common.h"
#include "tensorflow/lite/micro/micro_interpreter.h"
#include "tensorflow/lite/micro/micro_log.h"
#include "tensorflow/lite/micro/micro_mutable_op_resolver.h"
#include "tensorflow/lite/schema/schema_generated.h"

#include "model_data.h"
#include "test_images.h"

static const char *TAG = "MNIST_DEMO";

constexpr int kTensorArenaSize = 150 * 1024;
static uint8_t *tensor_arena = nullptr;

static int argmax_int8(const int8_t *data, int len) {
    int best_idx = 0;
    int8_t best_val = data[0];
    for (int i = 1; i < len; i++) {
        if (data[i] > best_val) {
            best_val = data[i];
            best_idx = i;
        }
    }
    return best_idx;
}

extern "C" void app_main(void) {
    ESP_LOGI(TAG, "Starting MNIST TFLite Micro demo");


    tensor_arena = (uint8_t *)heap_caps_malloc(kTensorArenaSize, MALLOC_CAP_8BIT);
    if (!tensor_arena) {
        ESP_LOGE(TAG, "Failed to allocate tensor arena (%d bytes)", kTensorArenaSize);
        return;
    }

    const tflite::Model *model = tflite::GetModel(g_mnist_model_data);

    tflite::MicroMutableOpResolver<8> resolver;
    resolver.AddConv2D();
    resolver.AddMaxPool2D();
    resolver.AddFullyConnected();
    resolver.AddReshape();
    resolver.AddSoftmax();
    resolver.AddShape();
    resolver.AddStridedSlice();
    resolver.AddPack();

    tflite::MicroInterpreter interpreter(model, resolver, tensor_arena, kTensorArenaSize);

    TfLiteStatus alloc_status = interpreter.AllocateTensors();
    if (alloc_status != kTfLiteOk) {
        ESP_LOGE(TAG, "AllocateTensors() failed");
        free(tensor_arena);
        return;
    }

    TfLiteTensor *input = interpreter.input(0);
    TfLiteTensor *output = interpreter.output(0);

    ESP_LOGI(TAG, "Input dims: [%d, %d, %d, %d], type=%d",
             input->dims->data[0], input->dims->data[1],
             input->dims->data[2], input->dims->data[3], input->type);

    ESP_LOGI(TAG, "Output dims: [%d, %d], type=%d",
             output->dims->data[0], output->dims->data[1], output->type);

    if (input->type != kTfLiteInt8 || output->type != kTfLiteInt8) {
        ESP_LOGE(TAG, "Expected int8 input/output tensors");
        free(tensor_arena);
        return;
    }

    int correct = 0;
    int64_t total_us = 0;

    for (int sample = 0; sample < kNumTestSamples; sample++) {
        memcpy(input->data.int8, g_test_images[sample], 28 * 28 * sizeof(int8_t));

        int64_t t0 = esp_timer_get_time();
        TfLiteStatus invoke_status = interpreter.Invoke();
        int64_t t1 = esp_timer_get_time();

        if (invoke_status != kTfLiteOk) {
            ESP_LOGE(TAG, "Invoke failed on sample %d", sample);
            continue;
        }

        int pred = argmax_int8(output->data.int8, 10);
        int truth = g_test_labels[sample];
        int8_t raw_score = output->data.int8[pred];
        float approx_confidence = (raw_score - kModelOutputZeroPoint) * kModelOutputScale;

        int64_t dt = t1 - t0;
        total_us += dt;

        if (pred == truth) {
            correct++;
        }

        ESP_LOGI(TAG,
                 "sample=%02d truth=%d pred=%d conf~=%.4f latency=%" PRId64 " us %s",
                 sample, truth, pred, approx_confidence, dt,
                 (pred == truth) ? "OK" : "ERR");
    }

    float acc = (float)correct / (float)kNumTestSamples * 100.0f;
    float avg_ms = ((float)total_us / (float)kNumTestSamples) / 1000.0f;

    ESP_LOGI(TAG, "======================================");
    ESP_LOGI(TAG, "Final accuracy on embedded test set: %d/%d = %.2f%%",
             correct, kNumTestSamples, acc);
    ESP_LOGI(TAG, "Average inference time: %.3f ms", avg_ms);
    ESP_LOGI(TAG, "Tensor arena size: %d bytes", kTensorArenaSize);
    ESP_LOGI(TAG, "Demo finished");
}