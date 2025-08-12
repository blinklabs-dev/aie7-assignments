# Assignment 14: LangGraph Platform - Question Responses

---

## ❓ Question 1
**What is the purpose of the `chunk_overlap` parameter when using `RecursiveCharacterTextSplitter` to prepare documents for RAG, and what trade-offs arise as you increase or decrease its value?**

### ✅ Answer:

The `chunk_overlap` parameter ensures **continuity between adjacent text chunks** by creating overlapping sections. This prevents important contextual information from being lost at chunk boundaries, which is critical for maintaining semantic coherence in RAG applications.

#### 🔄 Trade-offs Analysis:

**📈 Increasing Overlap:**
- ✅ **Pros:** Better context preservation and semantic continuity across chunks
- ❌ **Cons:** Increased storage requirements and potential redundancy in retrieval results
- 📊 **Impact:** Higher quality but less efficient resource usage

**📉 Decreasing Overlap:**
- ✅ **Pros:** More efficient storage and reduced redundant information
- ❌ **Cons:** Higher risk of losing important context that spans chunk boundaries
- 📊 **Impact:** More efficient but potentially lower quality results

**🎯 Optimal Range:** Typically 10-20% of chunk size provides the best balance between context preservation and efficiency.

---

## ❓ Question 2
**Your retriever is configured with `search_kwargs={"k": 5}`. How would adjusting `k` likely affect RAGAS metrics such as Context Precision and Context Recall in practice, and why?**

### ✅ Answer:

The `k` parameter determines the **number of documents retrieved** from the vector store, which directly impacts RAGAS evaluation metrics through the precision-recall trade-off.

#### 📊 Impact on RAGAS Metrics:

**📈 Increasing k (e.g., k=10):**
- **Context Recall:** 📈 **Likely Improves** - More documents retrieved increases chance of capturing all relevant information
- **Context Precision:** 📉 **May Decrease** - Additional documents might include less relevant content, introducing noise
- **Overall Effect:** Better coverage but potentially noisier results

**📉 Decreasing k (e.g., k=3):**
- **Context Recall:** 📉 **May Decrease** - Fewer documents retrieved might miss relevant information
- **Context Precision:** 📈 **Likely Improves** - Only the most relevant documents are retrieved
- **Overall Effect:** More focused but potentially incomplete results

#### 🎯 Key Insight:
The optimal `k` value depends on your specific use case - prioritize higher `k` for comprehensive coverage or lower `k` for precision-focused applications.

---

## ❓ Question 3
**Compare the `agent` and `agent_helpful` assistants defined in `langgraph.json`. Where does the helpfulness evaluator fit in the graph, and under what condition should execution route back to the agent vs. terminate?**

### ✅ Answer:

#### 🤖 Agent Comparison:

| Aspect | `agent` (Simple) | `agent_helpful` (Enhanced) |
|--------|------------------|----------------------------|
| **Architecture** | Direct tool-using agent | Agent + helpfulness evaluation |
| **Flow** | Linear: Input → Agent → Tools → Output | Cyclical: Input → Agent → Evaluator → Output/Retry |
| **Quality Control** | None | Built-in helpfulness gate |
| **Performance** | Faster execution | More thorough but slower |

#### 🔄 Helpfulness Evaluator Placement:

The helpfulness evaluator acts as a **quality gate** positioned between the agent's initial response and final termination: