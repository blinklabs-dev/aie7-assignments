# Research Bot Agent Flowchart

## Flow Description for Excalidraw

### Start
- **User Input** (Query/Research Topic)

### Step 1: Planning Phase
- **Planner Agent** 
  - Input: User query
  - Process: Analyzes query and generates 5-20 search terms
  - Output: Structured WebSearchPlan with search items and reasoning
  - Model: GPT-4.1
  - Tools: None (pure reasoning)

### Step 2: Search Phase
- **Search Agent**
  - Input: Individual search terms from Planner
  - Process: Performs web searches for each term
  - Output: Concise summaries (2-3 paragraphs, <300 words)
  - Model: GPT-4.1
  - Tools: WebSearchTool (required)

### Step 3: Writing Phase
- **Writer Agent**
  - Input: Original query + all search summaries
  - Process: Synthesizes research into comprehensive report
  - Output: Structured ReportData (summary + markdown report + follow-up questions)
  - Model: o3-mini (reasoning model)
  - Tools: None (pure synthesis)

### End
- **Final Report** (Markdown format, 5-10 pages)
- **Follow-up Questions** (5 unique research questions)

## Key Interactions:
1. **Planner → Search**: Search terms flow from Planner to Search Agent
2. **Search → Writer**: Summarized results flow from Search to Writer Agent
3. **User → Planner**: Initial query starts the process
4. **Writer → User**: Final report and questions delivered to user

## Data Flow:
- User Query → WebSearchPlan → Search Results → ReportData → Final Output

## Tools Used:
- **WebSearchTool**: Only used by Search Agent for web searches
- **Structured Outputs**: Used by Planner (WebSearchPlan) and Writer (ReportData)
- **Streaming**: Used by Writer for real-time progress updates

## Error Handling:
- Search failures are caught and logged
- Progress tracking via Printer class
- Trace IDs for debugging via OpenAI platform 