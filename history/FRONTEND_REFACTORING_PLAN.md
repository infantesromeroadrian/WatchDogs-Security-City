# Frontend Refactoring Plan

## ✅ COMPLETED: CSS Modularization

**Before**: `style.css` (784 lines - 392% over limit)

**After**: Modular architecture (9 modules)
```
style.css (14 lines - main importer)
└── modules/
    ├── variables.css (29 lines) - Design tokens
    ├── base.css (90 lines) - Reset, body, header
    ├── layout.css (59 lines) - Container, sections
    ├── components.css (83 lines) - Buttons, controls, loading
    ├── video.css (38 lines) - Video player, ROI canvas
    ├── results.css (177 lines) - Results, tabs, chat
    ├── multiframe.css (112 lines) - Multi-frame analysis
    ├── professional.css (127 lines) - Professional features
    └── responsive.css (66 lines) - Media queries
```

**Result**: ✅ All modules under 200 lines (max 177 lines)

---

## 🔄 TODO: JavaScript Refactoring

### 1. api-client.js (709 lines → split into 3 classes)

**Problem**: God Object doing too much

**Solution**:
```javascript
// api-client.js (~200 lines) - Main orchestrator
class APIClient {
    constructor()
    checkBackendConnection()
    analyzeFrame()
    switchTab()
}

// chat-handler.js (~150 lines) - Chat functionality
class ChatHandler {
    sendChatMessage()
    addMessageToChat()
    clearChat()
}

// ui-updater.js (~180 lines) - UI updates
class UIUpdater {
    showLoading()
    hideLoading()
    displayResults()
    updatePreview()
}

// utils.js (~100 lines) - Utilities
function copyJSON()
function downloadReport()
function resetAnalysis()
```

### 2. professional-features.js (382 lines → split into 3 modules)

**Problem**: Multiple features mixed

**Solution**:
```javascript
// metadata-handler.js (~130 lines)
class MetadataHandler {
    extractMetadata()
    displayMetadata()
}

// pdf-generator.js (~130 lines)
class PDFGenerator {
    generatePDF()
    downloadPDF()
}

// evidence-handler.js (~130 lines)
class EvidenceHandler {
    generateEvidencePackage()
    displayEvidence()
}
```

### 3. multi-frame.js (272 lines → simplify to ~180 lines)

**Current**: Acceptable but can improve
- Extract frame collection management to separate class
- Simplify event handlers

### 4. roi-selector.js (206 lines → optimize to ~150 lines)

**Current**: Slightly over limit
- Extract canvas drawing logic
- Simplify coordinate calculations

---

## 📊 Expected Results

**Current**:
- 4/8 files critical (>200 lines)
- Total: 3,145 lines

**After refactoring**:
- 0/15 files critical
- All files < 200 lines
- Better separation of concerns
- Easier testing and maintenance

---

## 🎯 Implementation Priority

1. **High**: api-client.js (most critical, 709 lines)
2. **High**: professional-features.js (382 lines)
3. **Medium**: multi-frame.js (272 lines)
4. **Low**: roi-selector.js (206 lines, acceptable)

---

## 📝 Notes

- HTML files (index.html, dashboard.html) are acceptable as-is
  - HTML naturally tends to be longer
  - Functionality works correctly
  - Could use template system (Jinja2/Handlebars) if grows more

- video-player.js (153 lines) - ✅ Already good

---

## 🚀 Next Steps

1. Create `src/frontend/static/js/modules/` directory
2. Split api-client.js first
3. Test thoroughly after each refactoring
4. Update HTML imports
5. Verify no breaking changes

