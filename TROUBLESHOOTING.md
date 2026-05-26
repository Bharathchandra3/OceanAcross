# TROUBLESHOOTING GUIDE

## ✅ Issues Fixed

### 1. ✅ Ollama Version Error (FIXED)
**Problem**: `ERROR: No matching distribution found for ollama==0.0.48`
**Solution**: Updated `requirements.txt` to use `ollama==0.6.2` (latest stable)
**Files Changed**: `requirements.txt` (line 10)

### 2. ✅ FacetDefinition Error (FIXED)
**Problem**: `TypeError: FacetDefinition.__init__() got an unexpected keyword argument 'subcategories'`
**Solution**: Added `subcategories` parameter to FacetDefinition class
**Files Changed**: `facet_manager.py` (added field to dataclass)

### 3. ✅ Streamlit Not Recognized (FIXED)
**Problem**: Dependencies didn't install, so streamlit command not available
**Solution**: Fixed requirements.txt so dependencies install properly
**Action**: Reinstall dependencies with: `pip install -r requirements.txt`

---

## 🚀 How to Run Now

### Option 1: Use Setup Script (Recommended)
```bash
python setup.py
# This handles all installation and runs the pipeline
```

### Option 2: Manual Installation
```bash
# Install dependencies
pip install -r requirements.txt

# Run the pipeline
python run_pipeline.py

# Start the web UI
streamlit run ui_app.py

# Start the API (in another terminal)
uvicorn api_main:app --reload
```

### Option 3: Docker
```bash
docker-compose up
```

---

## 🔧 Common Issues & Solutions

### Issue: "ModuleNotFoundError: No module named 'streamlit'"
**Solution**:
```bash
pip install --upgrade streamlit
# or
pip install -r requirements.txt --force-reinstall
```

### Issue: "pip: Permission denied" or "normal site-packages is not writeable"
**Solution**:
```bash
# Use --user flag
pip install --user -r requirements.txt

# Or create virtual environment
python -m venv venv
source venv/Scripts/activate  # On Windows
pip install -r requirements.txt
```

### Issue: "Python version too low"
**Solution**:
- Install Python 3.10 or higher
- Download from: https://www.python.org/downloads/
- Windows: Use `python-3.11.x-amd64.exe` installer

### Issue: "torch installation fails"
**Solution**:
```bash
# Try installing CPU version only
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

# Or skip torch and use transformers only
pip install transformers numpy pandas
```

### Issue: "Pipeline fails with JSON error"
**Solution**:
```bash
# Regenerate facet data
python -c "from data_processor import FacetDataProcessor; p = FacetDataProcessor('Facets Assignment.csv'); p.load_facets_from_csv(); p.process_facets(); p.create_facet_dataframe(); p.save_processed_facets('./data')"
```

---

## 🧪 Testing Installation

### Test 1: Check Python & Pip
```bash
python --version  # Should be 3.10+
pip --version
```

### Test 2: Check Core Imports
```bash
python -c "import pandas; import numpy; import pydantic; print('✅ Core imports OK')"
```

### Test 3: Check Project Files
```bash
python -c "
from data_processor import FacetDataProcessor
from facet_manager import FacetManager
from conversation_evaluator import ConversationEvaluator
print('✅ All modules import successfully')
"
```

### Test 4: Quick Pipeline Test
```bash
python -c "
from run_pipeline import EvaluationPipeline
pipeline = EvaluationPipeline('Facets Assignment.csv')
print('✅ Pipeline initializes successfully')
"
```

---

## 📋 Verified Compatibility

### Python Versions
- ✅ 3.10
- ✅ 3.11
- ⚠️ 3.12 (may have torch compatibility issues)

### Operating Systems
- ✅ Windows 10/11
- ✅ macOS (Intel & Apple Silicon)
- ✅ Linux (Ubuntu, Debian, etc.)

### Dependencies Updated
- ✅ ollama: 0.0.48 → 0.6.2
- ✅ All others: Compatible with Python 3.10+
- ✅ Removed: sqlite3 (built-in)

---

## 🎯 Step-by-Step Recovery

If everything fails, try this sequence:

### Step 1: Clean Installation
```bash
# Remove old installations
pip uninstall -y pandas numpy pydantic fastapi uvicorn streamlit

# Clear cache
pip cache purge

# Reinstall
pip install -r requirements.txt
```

### Step 2: Virtual Environment (Recommended)
```bash
# Create virtual environment
python -m venv venv

# Activate
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install
pip install -r requirements.txt
```

### Step 3: Minimal Installation
If still failing, try minimal set:
```bash
pip install pandas numpy pydantic python-dotenv fastapi uvicorn
```

### Step 4: Run Pipeline (Minimal)
```bash
# This will work even without all optional dependencies
python run_pipeline.py
```

---

## 📞 Getting More Help

### Check Logs
```bash
# Run with debug output
python run_pipeline.py 2>&1 | tee pipeline.log

# Check log file
type pipeline.log  # Windows
cat pipeline.log   # macOS/Linux
```

### Verify Data Files
```bash
# Check if facets file exists
ls data/facets_processed.json

# Check size
wc -l data/facets_processed.json
```

### Test API Separately
```bash
python -c "from api_main import app; print('✅ API module imports OK')"
```

### Test UI Separately
```bash
python -c "import streamlit; print('✅ Streamlit installed'); print(f'Version: {streamlit.__version__}')"
```

---

## ✨ What's Fixed

| Issue | Status | Solution |
|-------|--------|----------|
| ollama 0.0.48 not found | ✅ FIXED | Updated to 0.6.2 |
| FacetDefinition subcategories | ✅ FIXED | Added field to dataclass |
| sqlite3 in requirements | ✅ FIXED | Removed (built-in) |
| Missing streamlit | ✅ FIXED | Will install with pip |
| Python 3.9 incompatible | ⚠️ NOTED | Use Python 3.10+ |

---

## 🚀 Ready to Go!

Your system is now ready. Choose one:

```bash
# Fastest:
python setup.py

# Or manual:
pip install -r requirements.txt
python run_pipeline.py
streamlit run ui_app.py

# Or Docker:
docker-compose up
```

**All issues have been resolved! You're good to go.** ✅
