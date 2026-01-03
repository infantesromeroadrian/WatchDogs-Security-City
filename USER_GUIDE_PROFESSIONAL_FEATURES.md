# 🎯 User Guide: Professional OSINT Features

## Quick Start Guide

After analyzing an image or video frame, you'll see **3 new professional buttons**:

```
📊 Extract Metadata  |  📄 Generate PDF Report  |  📦 Evidence Package
```

---

## 📊 1. EXTRACT METADATA

### What It Does:
Extracts comprehensive technical and forensic information from your analyzed image.

### How To Use:
1. **Analyze a frame** (single or multi-frame)
2. Click **"📊 Extract Metadata"**
3. Wait 1-2 seconds
4. View results in expandable panel below

### What You Get:

#### 🖼️ Technical Specifications:
- Image format (JPEG, PNG, etc.)
- Dimensions (pixels)
- Color mode (RGB, CMYK, etc.)
- File size

#### 📍 GPS Coordinates (if available):
- **Latitude** - Exact geographic coordinate
- **Longitude** - Exact geographic coordinate
- **Altitude** - Height above sea level (meters)
- **Date** - When photo was taken
- **🗺️ Link to Google Maps** - Click to view location

#### 📷 Camera Information (if available):
- Camera make (Apple, Samsung, Canon, etc.)
- Camera model (iPhone 13, Galaxy S21, etc.)
- Software used (iOS version, editing apps, etc.)

#### 🕐 Timestamps:
- **Original** - When photo was actually taken
- **Digitized** - When it was saved/processed

#### 🔒 Forensic Hashes:
- **SHA-256** - Primary hash for integrity verification
- **MD5** - Secondary hash
- Used to prove the image hasn't been tampered with

### Real-World Use Cases:

**📍 Geolocation:**
```
You find a photo online. Extract metadata → Find GPS coords 
→ Discover it was taken at specific location
```

**📅 Timeline Construction:**
```
Multiple photos → Extract timestamps → Build timeline of events
```

**🔍 Source Verification:**
```
Someone claims photo is original → Extract metadata → 
Verify camera/software matches their claim
```

**⚖️ Legal Evidence:**
```
Extract SHA-256 hash → Document it → Prove image integrity in court
```

---

## 📄 2. GENERATE PDF REPORT

### What It Does:
Creates a professional, forensic-grade PDF report of your analysis.

### How To Use:
1. **Analyze a frame**
2. (Optional) Click "📊 Extract Metadata" first for more complete report
3. Click **"📄 Generate PDF Report"**
4. Wait 2-3 seconds
5. PDF automatically downloads

### Report Sections:

#### 1. Header
- Report generation date/time
- Evidence ID (if you created an evidence package)
- System information

#### 2. Executive Summary
- Quick overview of key findings
- Summary of what was detected

#### 3. Technical Analysis
- **Visual Analysis:** What the AI saw in the image
- **Text Recognition (OCR):** Any text found
- **Object Detection:** People, vehicles, objects detected

#### 4. Geolocation Intelligence
- Probable location (city, country)
- Confidence level (HIGH/MEDIUM/LOW)
- Geographic clues found

#### 5. Technical Metadata
- Image specifications
- GPS coordinates (if available)
- Camera information

#### 6. Forensic Evidence
- SHA-256 and MD5 hashes
- File size
- Chain of custody note

#### 7. Legal Disclaimer
- Usage terms
- Accuracy limitations

### File Name Format:
```
watchdogs_report_2026-01-03.pdf
```

### Use Cases:

**👔 Client Reports:**
```
Freelance investigator → Analyze evidence → Generate PDF → 
Send professional report to client
```

**📚 Case Documentation:**
```
Law enforcement → Analyze crime scene photo → PDF report → 
Add to case file
```

**🎓 Academic Research:**
```
Researcher → Analyze historical photos → PDFs for documentation
```

**📰 Journalism:**
```
Journalist → Verify viral photo → PDF report as evidence
```

---

## 📦 3. EVIDENCE PACKAGE

### What It Does:
Creates a complete forensic evidence package with:
- Unique Evidence ID
- All metadata
- Analysis results
- **Chain of Custody** tracking
- Integrity verification hashes

### How To Use:
1. **Analyze a frame**
2. Click **"📦 Evidence Package"**
3. Wait 1-2 seconds
4. View evidence details in panel
5. Click **"💾 Download Evidence Package (JSON)"** to save

### What's Included:

#### 🆔 Evidence ID:
```
Example: a1b2c3d4e5f67890
```
Unique identifier for this specific evidence.

#### 🔗 Chain of Custody:
```
1. CAPTURED
   Timestamp: 2026-01-03 22:30:45
   Hash: sha256_hash_here

2. ANALYZED
   Timestamp: 2026-01-03 22:30:50
   System: WatchDogs-OSINT
```

Proves:
- **When** evidence was captured
- **What** system processed it
- **Hash** at each step

#### ✓ Integrity Verification:
- **SHA-256 hash** of original image
- **Verified** status
- **Timestamp** of verification

#### 📊 Complete Data:
- All metadata (EXIF, GPS, technical)
- Full analysis results (Vision, OCR, Detection, Geo)
- Forensic hashes

### JSON File Format:
```json
{
  "evidence_id": "a1b2c3d4e5f67890",
  "timestamp": "2026-01-03T22:30:45.123456",
  "metadata": {...},
  "analysis": {...},
  "chain_of_custody": [...],
  "integrity": {
    "sha256": "hash_here",
    "verified": true
  }
}
```

### Use Cases:

**⚖️ Court Evidence:**
```
Generate evidence package → JSON file proves chain of custody → 
Admissible in legal proceedings
```

**🔍 Investigation Archive:**
```
Multiple evidence packages → Store in case folder → 
Complete audit trail
```

**🔐 Integrity Verification:**
```
Share evidence package → Recipient verifies SHA-256 → 
Proves no tampering
```

**📋 Audit Trail:**
```
Who did what when → Chain of custody shows all steps → 
Accountability
```

---

## 🔄 COMPLETE WORKFLOW EXAMPLE

### Scenario: Investigating a Viral Photo

**Step 1: Upload & Analyze**
```
1. Upload video or image
2. Capture frame or select image
3. Click "🔍 Analizar Frame Actual"
4. Wait for AI analysis (~10-15 seconds)
```

**Step 2: Extract Metadata**
```
5. Click "📊 Extract Metadata"
6. Review GPS coordinates (if available)
7. Note camera/device information
8. Save forensic hashes
```

**Step 3: Generate Evidence Package**
```
9. Click "📦 Evidence Package"
10. Note Evidence ID
11. Download JSON file
12. Store securely
```

**Step 4: Create PDF Report**
```
13. Click "📄 Generate PDF Report"
14. PDF downloads automatically
15. Send to client/add to case file
```

**Step 5: Verify with Chat**
```
16. Ask specific questions in chat
17. "What text do you see in frame 3?"
18. "Where was this photo taken?"
19. Get detailed answers
```

---

## 💡 PRO TIPS

### GPS Coordinates:
- **Not all images have GPS data** - Modern phones often strip it
- If no GPS found, use visual clues + geolocation agent
- Click "Open in Google Maps" to verify location visually

### Metadata Extraction:
- **Works best with photos from cameras/phones**
- Screenshots usually have minimal metadata
- Edited images may have altered metadata

### PDF Reports:
- **Extract metadata BEFORE generating PDF** for complete report
- PDF includes all available data at time of generation
- Great for presenting findings professionally

### Evidence Packages:
- **Generate early in investigation** to document original state
- JSON file is human-readable and machine-parsable
- SHA-256 hash proves file integrity over time

### Multi-Frame Analysis:
- Analyze 3-5 frames from same location
- **Then** use professional features
- More frames = better geolocation + richer PDF

---

## 🚨 LIMITATIONS & WARNINGS

### What These Features CAN'T Do:

❌ **Cannot reverse image search** (would need Google API)
❌ **Cannot verify if photo is manipulated** (basic feature only)
❌ **Cannot extract metadata from screenshots** (no EXIF data)
❌ **Cannot add GPS if it wasn't in original** (not magic)

### Important Notes:

⚠️ **Metadata can be faked** - Use as one piece of evidence, not sole proof
⚠️ **Chain of custody is digital** - Not legally binding without proper procedures
⚠️ **AI analysis isn't perfect** - Always verify critical findings manually
⚠️ **GPS coordinates** - Accuracy depends on device (±5-50 meters typical)

---

## 📊 FEATURE COMPARISON

| Feature | Free Tools | WatchDogs Professional |
|---------|------------|----------------------|
| **Basic Analysis** | ✅ Yes | ✅ Yes |
| **Multi-Frame** | ❌ No | ✅ Yes |
| **GPS Extraction** | ⚠️ Manual | ✅ Automatic |
| **PDF Reports** | ❌ No | ✅ Professional |
| **Evidence Packages** | ❌ No | ✅ With chain of custody |
| **Forensic Hashes** | ⚠️ Manual | ✅ Automatic |
| **AI Chat** | ❌ No | ✅ Conversational |

---

## ❓ FAQ

**Q: Do these features work offline?**
A: Yes, except for the AI vision analysis (needs OpenAI API). Metadata extraction, PDF generation, and evidence packages work offline.

**Q: Can I customize the PDF report?**
A: Currently no, but it's planned for future versions.

**Q: How secure are the evidence packages?**
A: Very secure. SHA-256 hashing is military-grade. However, store the JSON files securely as they contain all analysis data.

**Q: Can I use this in court?**
A: Consult with legal counsel. While the features are forensically sound, admissibility depends on jurisdiction and proper handling procedures.

**Q: Why no GPS in my extracted metadata?**
A: Many reasons:
- Social media platforms strip GPS
- Screenshot (no original photo)
- Camera had GPS disabled
- Indoor photo (no GPS signal)

**Q: Can I batch-process multiple images?**
A: Currently no, but it's on the roadmap.

---

## 🆘 TROUBLESHOOTING

### "Extract Metadata" button is disabled:
✅ **Solution:** Analyze a frame first

### No GPS coordinates found:
✅ **Solution:** Image may not have GPS data (normal for screenshots, social media images)

### PDF download failed:
✅ **Solution:** Check browser pop-up blocker, try again

### Evidence Package shows error:
✅ **Solution:** Ensure you've analyzed a frame first

### Metadata extraction is slow:
✅ **Solution:** Large images take longer. Normal for 4K+ photos.

---

## 📞 SUPPORT

**Having issues?**
1. Check browser console (F12 → Console tab)
2. Look for error messages
3. Verify Docker is running: `docker compose ps`
4. Check backend logs: `docker compose logs backend`

**Found a bug?**
Create an issue on GitHub with:
- Steps to reproduce
- Browser console screenshot
- Expected vs actual behavior

---

## 🎓 LEARNING RESOURCES

**Want to learn more about OSINT?**
- Bellingcat's Open Source Investigation guides
- OSINT Framework online tools
- Trace Labs resources

**Metadata & EXIF:**
- exiftool.org - Industry standard tool
- Understanding EXIF data

**Forensic Analysis:**
- Digital forensics fundamentals
- Chain of custody best practices

---

**Version:** 1.1.0  
**Last Updated:** 2026-01-03  
**Author:** WatchDogs OSINT Team

---

## 🎯 NEXT STEPS

Now that you know how to use these features:

1. **Try the workflow** with a test image
2. **Practice** extracting metadata from your own photos
3. **Generate** your first professional PDF report
4. **Experiment** with multi-frame analysis + evidence packages

**Remember:** These are professional-grade OSINT tools. Use them responsibly and ethically.

Happy investigating! 🕵️‍♂️
