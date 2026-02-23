/* eslint-disable no-undef */

let model = null;

async function loadModel() {
    try {
        console.log("Mock TFLite Model Loaded in Worker");
        model = { predict: () => { } }; // Mock model
        postMessage({ type: 'LOADED' });
    } catch (e) {
        console.error("Failed to load TFLite model:", e);
        postMessage({ type: 'ERROR', error: e.message });
    }
}

onmessage = async (e) => {
    if (e.data.type === 'LOAD') {
        await loadModel();
    } else if (e.data.type === 'INFER') {
        if (!model) return;

        const { imageData } = e.data;

        // In a real scenario, we would convert imageData to a tensor
        // and run model.predict(tensor)
        // For now, we simulate the inference time and result

        setTimeout(() => {
            postMessage({
                type: 'INFERENCE_RESULT',
                text: "MOCK_OCR_TEXT", // This would be the actual model output
                confidence: 0.95
            });
        }, 100);
    }
};
