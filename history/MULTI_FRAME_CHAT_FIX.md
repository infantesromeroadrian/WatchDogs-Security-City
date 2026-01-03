# 🔧 Multi-Frame Chat Enhancement

## 🎯 Problem Solved

**Original Issue:** When using multi-frame analysis, the chat feature only analyzed the last captured frame instead of all frames in the collection.

**User Experience:**
```
User: "dime que ves en cada frame"
Bot: "En este frame veo un taxi amarillo..." [only 1 frame described]
```

**Expected:**
```
User: "dime que ves en cada frame"
Bot: "**Frame 1**: Un taxi amarillo con...
      **Frame 2**: Una calle con edificios...
      **Frame 3**: ..."
```

---

## ✅ Solution Implemented

### 1. **Frontend Changes** (`api-client.js`)

#### Added State Tracking:
```javascript
this.frameCollection = null;  // Stores all frames from multi-frame analysis
this.isMultiFrameAnalysis = false;  // Flag to differentiate modes
```

#### New Method: `displayBatchResults()`
- Called when multi-frame analysis completes
- Stores all frames for chat context
- Enables chat with multi-frame awareness
- Shows frame count in UI message

#### Enhanced `sendChatMessage()`:
```javascript
// Multi-frame mode detection
if (this.isMultiFrameAnalysis && this.frameCollection) {
    payload = {
        frames: this.frameCollection,  // Send ALL frames
        message: message,
        context: this.buildMultiFrameChatContext(message)
    };
} else {
    // Single-frame mode (original logic)
    payload = { frame: frameToSend, context: ... };
}
```

#### New Method: `buildMultiFrameChatContext()`
- Builds context explaining it's multi-frame analysis
- Instructs LLM to analyze ALL frames
- Adds specific instructions for frame-by-frame descriptions
- Includes conversation history

---

### 2. **Backend Changes** (`app.py`)

#### Enhanced `/api/chat-query` Endpoint:

**Now supports TWO modes:**

**Mode 1: Single-Frame (original)**
```json
{
    "frame": "base64_encoded_image",
    "context": "conversation context"
}
```

**Mode 2: Multi-Frame (NEW)**
```json
{
    "frames": [
        {"frame": "base64...", "description": "Frame 1"},
        {"frame": "base64...", "description": "Frame 2"},
        ...
    ],
    "message": "user question",
    "context": "conversation context"
}
```

**Processing Logic:**
```python
if "frames" in data:
    # Multi-frame mode
    for idx, frame_data in enumerate(frames):
        result = vision_agent.analyze(frame_base64, frame_context)
        frame_analyses.append(f"**{frame_desc}**: {analysis}")
    
    combined_response = "\n\n".join(frame_analyses)
    return combined_response
else:
    # Single-frame mode (original)
    result = vision_agent.analyze(frame_base64, context)
    return result["analysis"]
```

---

### 3. **Multi-Frame Module Integration** (`multi-frame.js`)

#### Updated `displayBatchResults()`:
```javascript
displayBatchResults(results) {
    // Delegate to apiClient for proper chat setup
    if (window.apiClient) {
        window.apiClient.displayBatchResults(results, this.frameCollection);
    }
}
```

This ensures the `apiClient` knows:
- Multi-frame analysis was performed
- All frames are available for chat
- Chat should use multi-frame mode

---

## 🚀 How It Works Now

### User Flow:

1. **Capture Multiple Frames:**
   - User captures 5 frames from video
   - Clicks "🔍 Analizar Colección (5 frames)"

2. **Multi-Frame Analysis:**
   - Backend analyzes all 5 frames with context accumulation
   - Results displayed with combined geolocation
   - Chat is enabled with multi-frame mode

3. **Multi-Frame Chat:**
   ```
   User: "dime que ves en cada frame"
   ```
   
   Frontend sends:
   ```javascript
   {
       frames: [frame1, frame2, frame3, frame4, frame5],
       message: "dime que ves en cada frame",
       context: "ANÁLISIS MULTI-FRAME: 5 frames..."
   }
   ```
   
   Backend processes:
   - Analyzes Frame 1 → "**Frame 1**: Un taxi amarillo..."
   - Analyzes Frame 2 → "**Frame 2**: Una calle con..."
   - ... (all 5 frames)
   - Combines responses

   User sees:
   ```
   **Frame 1**: Un taxi amarillo en primer plano, una mujer caminando...
   
   **Frame 2**: Vista de una calle concurrida con edificios modernos...
   
   **Frame 3**: Tráfico denso con varios vehículos, señal de alto visible...
   
   **Frame 4**: Edificio de oficinas con logo corporativo en fachada...
   
   **Frame 5**: Intersección con semáforo, peatones cruzando...
   ```

---

## 🔍 Technical Details

### Context Building:

**Multi-Frame Context:**
```
ANÁLISIS MULTI-FRAME: El usuario ha analizado 5 frames.

Pregunta: dime que ves en cada frame

IMPORTANTE: Recibirás 5 imágenes. Analiza TODAS y responde considerando 
información de todos los frames.

CONTEXTO DEL ANÁLISIS PREVIO:
Resumen: [summary from batch analysis]
Geolocalización: [combined geolocation data]

HISTORIAL DE CONVERSACIÓN:
Usuario: pregunta anterior
Asistente: respuesta anterior

INSTRUCCIONES:
- Analiza TODAS las imágenes que recibes
- Si preguntan "qué ves en cada frame", describe cada frame por separado
- Numera tus respuestas: "Frame 1: ..., Frame 2: ..."
- Sé específico y conciso
```

### Logging:

**Frontend Console:**
```
💬 sendChatMessage() called
   - isMultiFrameAnalysis: true
   - frameCollection: 5
📊 Multi-frame chat mode: 5 frames
```

**Backend Logs:**
```
💬 Processing MULTI-FRAME chat query (5 frames)
   ✓ Frame 1 analyzed
   ✓ Frame 2 analyzed
   ✓ Frame 3 analyzed
   ✓ Frame 4 analyzed
   ✓ Frame 5 analyzed
✅ Multi-frame chat query complete
```

---

## 🐛 Edge Cases Handled

### 1. **No Analysis Performed:**
```javascript
if (!this.currentFrame && !this.frameCollection) {
    alert('⚠️ Debes realizar un análisis primero');
    return;
}
```

### 2. **Single-Frame After Multi-Frame:**
- When user does single-frame analysis, flags are reset:
```javascript
this.isMultiFrameAnalysis = false;
this.frameCollection = null;
```

### 3. **Empty Chat Message:**
```javascript
if (!message) {
    console.warn('⚠️ Chat message is empty');
    return;
}
```

### 4. **Backend Fallback:**
```python
# If payload is invalid
if "frames" not in data and "frame" not in data:
    return jsonify({
        "success": False, 
        "error": "Invalid payload: need 'frame' or 'frames'"
    }), 400
```

---

## 📊 Performance Considerations

### Multi-Frame Chat Cost:
- **5 frames** = 5 Vision API calls per chat message
- **Tokens:** ~1,000 tokens × 5 frames = ~5,000 tokens/query
- **Latency:** ~1.5s × 5 = ~7.5s response time

### Optimization (Future):
1. **Parallel Processing:** Analyze all frames concurrently
2. **Caching:** Cache individual frame analyses
3. **Smart Selection:** Allow user to select specific frames for chat
4. **Summary Mode:** Generate summary upfront, chat uses summary

---

## 🧪 Testing

### Test Case 1: Multi-Frame General Question
```
Input: "describe each frame"
Expected: 5 separate descriptions numbered Frame 1-5
```

### Test Case 2: Multi-Frame Specific Search
```
Input: "en qué frame ves un taxi amarillo?"
Expected: "Veo un taxi amarillo en Frame 1 y Frame 3..."
```

### Test Case 3: Multi-Frame OCR
```
Input: "qué texto lees en cada frame?"
Expected: "Frame 1: 'TAXI', Frame 2: 'STOP', ..."
```

### Test Case 4: Single-Frame Still Works
```
1. Capture 1 frame
2. Analyze with "Analizar Frame Actual"
3. Ask: "describe the image"
Expected: Single frame description (original behavior)
```

---

## 🚀 Deployment

### 1. Rebuild Docker:
```bash
docker compose down
docker compose up --build -d
```

### 2. Verify:
```bash
# Check logs
docker compose logs -f backend

# Test endpoint
curl -X POST http://localhost:5000/api/chat-query \
  -H "Content-Type: application/json" \
  -d '{
    "frames": [
      {"frame": "base64...", "description": "Frame 1"},
      {"frame": "base64...", "description": "Frame 2"}
    ],
    "message": "describe each frame"
  }'
```

### 3. Frontend Test:
1. Open browser → http://localhost:5000
2. F12 → Console
3. Load video, capture 5 frames
4. Click "Analizar Colección"
5. In chat: "dime que ves en cada frame"
6. Verify: 5 separate descriptions

---

## 📝 Files Modified

| File | Changes |
|------|---------|
| `src/frontend/static/js/api-client.js` | +150 lines (multi-frame chat logic) |
| `src/backend/app.py` | +60 lines (dual-mode chat endpoint) |
| `src/frontend/static/js/multi-frame.js` | Modified `displayBatchResults()` |

---

## ✅ Checklist

- [x] Frontend tracks multi-frame vs single-frame mode
- [x] Chat sends all frames when in multi-frame mode
- [x] Backend processes multiple frames sequentially
- [x] Responses are numbered and frame-specific
- [x] Single-frame mode still works (backward compatible)
- [x] Error handling for edge cases
- [x] Logging for debugging
- [x] Documentation updated

---

## 🎯 Result

**Before:**
```
User: "dime que ves en cada frame"
Bot: "En este frame veo un taxi amarillo..."  ❌ Only 1 frame
```

**After:**
```
User: "dime que ves en cada frame"
Bot: 
**Frame 1**: Un taxi amarillo en primer plano...

**Frame 2**: Una calle con edificios modernos...

**Frame 3**: Tráfico denso con señal de alto...

**Frame 4**: Edificio de oficinas con logo...

**Frame 5**: Intersección con semáforo...
```
✅ All 5 frames analyzed and described separately!

---

**Status:** ✅ READY FOR TESTING
**Version:** 1.1.0 - Multi-Frame Chat Enhancement
**Date:** 2026-01-03
