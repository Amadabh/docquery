# 🧪 Test Workflow

Upload both sample files (`therapy_tips.txt` and `school_guide.txt`) via the paperclip icon, then run these queries:

| Step | Query | Expected |
|------|-------|----------|
| 1 | "What's a good therapy for anxiety?" | CBT, deep breathing, mindfulness |
| 2 | "What accommodations can we request?" | IEP, 504 plan, extended time |
| 3 | "Should therapy come before accommodations?" | Synthesizes content from **both** files |

Step 3 is the key test — a correct response means cross-document retrieval is working.
