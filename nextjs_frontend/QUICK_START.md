# 🚀 Quick Start Guide

## Get Up and Running in 5 Minutes

### Step 1: Start the Backend
```bash
cd fastapi_backend

# Make sure dependencies are installed
pip install -r requirements.txt

# Set your OpenAI API key
export OPENAI_API_KEY="your-key-here"  # Linux/Mac
# OR
set OPENAI_API_KEY=your-key-here       # Windows

# Start the server
python -m uvicorn api.index:app --reload --host 127.0.0.1 --port 8000
```

### Step 2: Start the Frontend
Open a **new terminal**:
```bash
cd nextjs_frontend

# Install dependencies (first time only)
npm install

# Start the development server
npm run dev
```

### Step 3: Open Your Browser
Navigate to: **http://localhost:3000**

---

## 🎯 First Actions

### As a Professor:

1. **Click "Professor Portal"** on landing page

2. **Upload a Material**:
   - Click "Materials" in the top nav
   - Choose a PDF file
   - Click "Upload PDF"
   - Watch the progress bar!

3. **Generate Problems**:
   - Click "Problem Sets" → "Generate New Set"
   - Select your uploaded material
   - Click "Generate Problem Set"
   - Wait ~30-60 seconds
   - Export when done!

### As a Student:

1. **Click "Student Portal"** on landing page

2. **Try the AI Tutor**:
   - Click "Workspace" in the top nav
   - Select a material from the left panel
   - Type a question like "Explain the main concept"
   - Press Enter and get an AI-powered answer!

3. **Explore Problem Sets**:
   - Click "Problem Sets" to see available practice
   - Click "Grades" to view feedback

---

## 🎨 What You'll See

### Landing Page
Beautiful gradient with two portal cards - choose your role!

### Professor Dashboard
- Quick stats of your uploaded materials
- Action cards for common tasks
- Recent materials list

### Student Workspace
**3-column layout:**
- Left: Materials list
- Center: AI chat
- Right: Tips and help

---

## 📱 Features to Test

### Professor:
- ✅ Upload PDF materials
- ✅ View semantic chunks
- ✅ Generate AI problem sets
- ✅ Export in multiple formats
- ✅ View analytics

### Student:
- ✅ Chat with AI tutor
- ✅ Get context-aware answers
- ✅ View problem sets
- ✅ Track grades
- ✅ See progress

---

## 🐛 Troubleshooting

### Backend won't start?
- Check: OpenAI API key is set
- Check: Port 8000 is available
- Check: Dependencies are installed

### Frontend won't start?
- Run: `npm install` again
- Check: Port 3000 is available
- Check: Node.js version (14+ required)

### Can't connect to backend?
- Check: Backend is running on port 8000
- Check: CORS is configured (already done)
- Check: No firewall blocking localhost

### No materials showing?
- Upload a PDF first in Professor → Materials
- Make sure backend successfully processed it
- Refresh the page

---

## 🎓 Tips

1. **Upload Sample PDFs**: Use course notes, textbooks, or any educational PDF
2. **Ask Good Questions**: Be specific in the chat interface
3. **Try Different Formats**: Export problem sets as Markdown or JSON
4. **Check Chunks**: View how your PDFs are intelligently chunked
5. **Explore Analytics**: See statistics about your content

---

## 📚 Learn More

- **Full Documentation**: See `FRONTEND_COMPLETE.md`
- **Implementation Guide**: See `IMPLEMENTATION_GUIDE.md`
- **Backend API**: Check `fastapi_backend/api/index.py`

---

## ✅ You're Ready!

The system is fully functional and ready to use. Enjoy exploring the AUB Learning Management System!

**Happy Learning! 🎓**
