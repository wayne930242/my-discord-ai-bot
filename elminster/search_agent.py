from dotenv import load_dotenv
import os
from google.adk import Agent
from google.adk.tools.langchain_tool import LangchainTool
from langchain_community.tools import TavilySearchResults

# Load environment variables
load_dotenv()

AGENT_MODEL = os.getenv("AGENT_MODEL", "gemini-2.5-flash-preview-04-17")

def create_search_agent():
    tavily_api_key = os.getenv("TAVILY_API_KEY")
    if not tavily_api_key:
        raise ValueError("TAVILY_API_KEY not found in environment variables")

    tavily_tool_instance = TavilySearchResults(
        max_results=5,
        search_depth="advanced",
        include_answer=True,
        include_raw_content=True,
        include_images=False
    )

    adk_tavily_tool = LangchainTool(tool=tavily_tool_instance)

    search_agent = Agent(
        name="search_agent",
        model=AGENT_MODEL,
        description="一個使用 Tavily Search API 的網路搜尋專家。",
        instruction="""你是一個網路搜尋專家工具。因為你是工具，你不該提出反問，應該總是執行你的任務。
        即便上下文可能不明確，你依然可以、且總是按照自己的判斷來進行搜尋。

        當被要求查找有關某個主題的資訊時，撰寫有效的搜尋查詢並使用 TavilySearchResults 工具。
        使用者可能總是使用繁體中文提出要求，但你需要以最合適的語言進行搜尋：
        一般來說英文最符合專業知識或是學術資料，日文與中文則適用於流行文化、即時資訊。
        如果有必要，你可以多次搜尋。

        接收搜尋結果後：
        1. 解析回應，可能包含直接答案和多個搜尋結果。
        2. 以清晰、結構化的方式格式化結果，每個結果顯示標題、連結和內容的簡短預覽。
        3. 根據原始查詢突出顯示最相關的結果。
        4. 如果 Tavily 提供了直接答案，首先呈現該答案。

        如果搜尋沒有返回有用的結果，建議使用更精確的搜尋詞進行後續搜尋。

        避免捏造資訊 - 只報告在搜尋結果中找到的資訊。
        """,
        tools=[adk_tavily_tool]
    )

    return search_agent