import os
import json
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage, AIMessage
from langgraph.graph import StateGraph, START, END
from typing import TypedDict, Annotated, List, Dict, Any
from langgraph.graph.message import add_messages
from schemas import PolicyEvaluateRequest, Cart
from engine import evaluate_policy
from database import SessionLocal
from razorpay_node import create_razorpay_order

class State(TypedDict):
    messages: Annotated[list, add_messages]
    session_id: str
    cart_items: list
    payment_link: str
    status: str
    requires_payment: bool

# Initialize LLM
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

system_prompt = """You are an AI shopping assistant for a merchant. 
Your job is to help users find products and add them to their cart for checkout. 
The catalog is:
- P_101: Flagship Gaming Laptop (Price: 150000)
- P_902: Mechanical Keyboard (Price: 3500)
- P_304: Wireless Mouse (Price: 1500)

When a user asks to buy something, find the relevant product and use the 'submit_cart_for_checkout' tool.
If the tool returns a rejection (status: BLOCKED), you MUST apologize to the user and explain the reason exactly as provided, and suggest an alternative if applicable.
Do not make up products not in the catalog.
"""

def submit_cart_for_checkout(items: List[str], calculated_total: float, session_id: str):
    """
    Submits the cart to the Policy Engine for evaluation.
    items: List of product IDs (e.g., ["P_101"])
    calculated_total: Total price in INR
    session_id: The session string
    """
    db = SessionLocal()
    req = PolicyEvaluateRequest(
        session_id=session_id,
        customer_intent_budget=5000, # Mock intent budget for now
        proposed_cart=Cart(items=items, calculated_total=calculated_total)
    )
    
    response = evaluate_policy(db, req)
    db.close()
    
    if response.status == "APPROVED":
        # Create Razorpay order
        order = create_razorpay_order(calculated_total, session_id)
        return json.dumps({"status": "APPROVED", "order": order})
    else:
        return json.dumps({
            "status": "BLOCKED",
            "reason_code": response.reason_code,
            "message": response.message,
            "action_required": response.action_required
        })

llm_with_tools = llm.bind_tools([submit_cart_for_checkout])

def agent_node(state: State):
    messages = state["messages"]
    if not any(isinstance(m, SystemMessage) for m in messages):
        messages = [SystemMessage(content=system_prompt)] + messages
        
    response = llm_with_tools.invoke(messages)
    return {"messages": [response]}

def tool_node(state: State):
    messages = state["messages"]
    last_message = messages[-1]
    
    tool_responses = []
    payment_link = state.get("payment_link", "")
    requires_payment = state.get("requires_payment", False)
    
    for tool_call in last_message.tool_calls:
        if tool_call["name"] == "submit_cart_for_checkout":
            args = tool_call["args"]
            args["session_id"] = state["session_id"]
            res = submit_cart_for_checkout(**args)
            
            res_dict = json.loads(res)
            if res_dict.get("status") == "APPROVED":
                payment_link = res_dict['order'].get('short_url', 'https://rzp.io/mock')
                requires_payment = True
                
            tool_responses.append(ToolMessage(content=res, tool_call_id=tool_call["id"]))
            
    return {"messages": tool_responses, "payment_link": payment_link, "requires_payment": requires_payment}

def should_continue(state: State):
    messages = state["messages"]
    last_message = messages[-1]
    if last_message.tool_calls:
        return "tools"
    return END

graph_builder = StateGraph(State)
graph_builder.add_node("agent", agent_node)
graph_builder.add_node("tools", tool_node)

graph_builder.add_edge(START, "agent")
graph_builder.add_conditional_edges("agent", should_continue, {"tools": "tools", END: END})
graph_builder.add_edge("tools", "agent")

app = graph_builder.compile()

def process_chat(session_id: str, message: str, existing_messages: list = None):
    if existing_messages is None:
        existing_messages = []
        
    state = {
        "session_id": session_id,
        "messages": existing_messages + [HumanMessage(content=message)],
        "payment_link": "",
        "requires_payment": False
    }
    
    final_state = app.invoke(state)
    
    # Extract the last AI message that is not a tool call (if any), or just return the final text
    ai_messages = [m for m in final_state["messages"] if isinstance(m, AIMessage) and not m.tool_calls]
    final_response = ai_messages[-1].content if ai_messages else "I've processed your request."
    
    return {
        "response": final_response,
        "requires_payment": final_state["requires_payment"],
        "payment_link": final_state.get("payment_link")
    }
