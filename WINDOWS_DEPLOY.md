# 🪟 WINDOWS DEPLOYMENT GUIDE
**Get your AI Report Generator running in 10 minutes**

---

## ✅ PRE-FLIGHT CHECKLIST

Make sure you have:
- [x] Windows 10/11
- [x] Python 3.8+ installed
- [x] VS Code (already have it!)
- [x] Ollama installed
- [x] Command Prompt or PowerShell

---

## 🚀 STEP-BY-STEP DEPLOYMENT

### Step 1: Install Ollama (if not installed)
1. Download from: https://ollama.ai
2. Run installer
3. Open Command Prompt
4. Run: `ollama pull llama3.2`
   - This downloads the 3B model (~2GB)
   - Takes 5-10 minutes depending on internet speed

### Step 2: Verify Ollama
```cmd
ollama list
```
You should see `llama3.2` in the output

### Step 3: Navigate to Project Folder
```cmd
cd path\to\your\project
```

### Step 4: Install Python Dependencies
```cmd
pip install -r requirements.txt
```

This installs:
- Flask (web framework)
- LangChain (LLM orchestration)
- Ollama (Python client)

**Troubleshooting:**
- If `pip` not found: Use `python -m pip install -r requirements.txt`
- If permission errors: Run Command Prompt as Administrator

### Step 5: Test Your Setup (Optional but Recommended)
```cmd
python test_setup.py
```

This checks:
- ✅ Ollama is running
- ✅ Llama 3.2 is available
- ✅ Python packages installed
- ✅ Report generation works

### Step 6: Launch the Application
```cmd
python app.py
```

You should see:
```
==============================================================
AI REPORT GENERATOR - Starting Server
==============================================================

Make sure Ollama is running with: ollama run llama3.2

Access the app at: http://localhost:5000
==============================================================

 * Running on http://0.0.0.0:5000
```

### Step 7: Open in Browser
1. Open your browser (Chrome, Edge, Firefox)
2. Go to: **http://localhost:5000**
3. You should see the AI Report Generator interface!

---

## 🎯 USING THE APPLICATION

### Method 1: Upload File
1. Click "Data Format" dropdown → Select CSV/JSON/Text
2. Click "📁 Click to upload file"
3. Select your data file
4. Click "🎯 Generate Report"
5. Wait 10-30 seconds
6. Report appears on the right!

### Method 2: Paste Data
1. Select data format
2. Paste data in the text area
3. Click "🎯 Generate Report"

### Try the Sample Data
Use the included `sample_sales_data.csv`:
1. Select "CSV" format
2. Upload `sample_sales_data.csv`
3. Click generate
4. See a full business report with insights!

---

## 📊 SAMPLE DATA TO TEST

Copy this CSV data and paste it:

```csv
product,sales,profit,region
Laptop,15000,3000,North
Phone,25000,5000,South
Tablet,8000,1500,East
Monitor,12000,2400,West
```

Or this JSON:

```json
{
  "revenue": [120000, 135000, 148000],
  "expenses": [80000, 85000, 90000],
  "months": ["Jan", "Feb", "Mar"]
}
```

---

## 🔧 TROUBLESHOOTING

### Problem: "Connection refused" or 503 error
**Cause:** Ollama not running
**Fix:**
1. Open new Command Prompt
2. Run: `ollama serve`
3. Keep this window open
4. Try again

### Problem: Slow first report generation
**Cause:** Model loading into memory (first time only)
**Fix:** This is normal! Wait 30-60 seconds. Subsequent reports are faster.

### Problem: "ModuleNotFoundError: No module named 'flask'"
**Cause:** Dependencies not installed
**Fix:** Run `pip install -r requirements.txt`

### Problem: Port 5000 already in use
**Fix:** Edit `app.py`, change port:
```python
app.run(debug=True, host='0.0.0.0', port=5001)  # Use 5001 instead
```

### Problem: Antivirus blocking
**Fix:** Add Python and Ollama to antivirus exceptions

---

## 🎓 VS CODE TIPS

### Open Project in VS Code
1. File → Open Folder → Select project folder
2. Terminal → New Terminal (Ctrl + `)
3. Run commands directly in VS Code terminal

### Recommended Extensions
- Python (Microsoft)
- Pylance (Microsoft)
- HTML CSS Support

### Debug Mode
1. Set breakpoint in `report_generator.py`
2. Run → Start Debugging (F5)
3. Select "Flask" as debug configuration

---

## 🚀 GOING TO PRODUCTION

### Option 1: Local Network Access
Share with colleagues on same network:
1. Find your IP: `ipconfig` → Look for IPv4 Address (e.g., 192.168.1.100)
2. Run: `python app.py`
3. Share: `http://YOUR_IP:5000`

### Option 2: Cloud Deployment (Free)
Deploy to Render.com:
1. Create `render.yaml` (I can provide this)
2. Push to GitHub
3. Connect to Render
4. Free tier includes 750 hours/month

### Option 3: Docker Container
1. Create Dockerfile (I can provide this)
2. Build: `docker build -t report-generator .`
3. Run: `docker run -p 5000:5000 report-generator`

---

## 📈 PERFORMANCE TIPS

### Speed Up Report Generation
1. **Use GPU (if available):**
   - Ollama automatically uses GPU if present
   - 10x faster inference

2. **Reduce Temperature:**
   - Edit `report_generator.py`
   - Lower temperature = faster, more deterministic

3. **Limit Context:**
   - Large files? Reduce `raw_preview[:3000]` to `[:1000]`

### Memory Optimization
- Default: Llama 3.2 uses ~4GB RAM
- For 2GB systems: Use `llama3.2:1b` (smaller model)

---

## ✨ CUSTOMIZATION IDEAS

### Change Colors
Edit `templates/index.html`:
- Line 25: `background: linear-gradient(...)` 
- Change to your brand colors!

### Modify Report Format
Edit `report_generator.py`:
- Line 56: Update prompt template
- Add/remove sections
- Change tone (formal/casual)

### Add Your Logo
Edit `templates/index.html`:
- Line 105: Add `<img src="logo.png">` 
- Put logo in `static/` folder

---

## 💾 PROJECT STRUCTURE

```
your_project/
│
├── app.py                      # Flask web server
├── report_generator.py         # Core AI logic
├── requirements.txt            # Python dependencies
├── test_setup.py              # Setup verification
├── README.md                  # Documentation
├── sample_sales_data.csv      # Test data
│
├── templates/
│   └── index.html             # Web interface
│
└── uploads/                   # (Auto-created for file uploads)
```

---

## 🎯 QUICK COMMANDS CHEAT SHEET

```cmd
# Check Ollama
ollama list

# Run Ollama model
ollama run llama3.2

# Install dependencies
pip install -r requirements.txt

# Test setup
python test_setup.py

# Start application
python app.py

# Stop application
Ctrl + C

# Check Python version
python --version

# Update pip
python -m pip install --upgrade pip
```

---

## 🆘 NEED HELP?

1. **Check test_setup.py output** - Run diagnostics first
2. **Read error messages carefully** - They usually tell you what's wrong
3. **Restart Ollama** - Sometimes it needs a fresh start
4. **Check firewall** - Ensure localhost:5000 is not blocked

---

## 🎉 SUCCESS INDICATORS

You know it's working when:
✅ Test script shows all green checkmarks
✅ Browser loads the interface
✅ Sample report generates successfully
✅ No error messages in console

---

**🚀 Now go generate some reports! You've got this!**

*Built with ❤️ using 100% open-source tech*
*Zero API costs | Full data privacy | Enterprise-grade AI*
